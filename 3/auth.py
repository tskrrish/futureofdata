"""
SSO Authentication with Google and Microsoft Identity
"""
from authlib.integrations.fastapi_oauth2 import OAuth2Token
from authlib.integrations.httpx_oauth2 import OAuth2Client
from authlib.oauth2 import OAuth2Error
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import httpx
import logging

from config import settings
from database import VolunteerDatabase

logger = logging.getLogger(__name__)

class SSOAuth:
    def __init__(self, database: VolunteerDatabase):
        self.database = database
        self.security = HTTPBearer()
        
        # Initialize OAuth2 clients
        self.google_client = OAuth2Client(
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            server_metadata_url='https://accounts.google.com/.well-known/openid_configuration'
        )
        
        self.microsoft_client = OAuth2Client(
            client_id=settings.MICROSOFT_CLIENT_ID,
            client_secret=settings.MICROSOFT_CLIENT_SECRET,
            server_metadata_url=f'https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/v2.0/.well-known/openid_configuration'
        )
    
    def create_jwt_token(self, user_data: Dict[str, Any]) -> str:
        """Create JWT token for authenticated user"""
        expiry = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            'sub': user_data['id'],
            'email': user_data['email'],
            'name': f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip(),
            'exp': expiry,
            'iat': datetime.utcnow(),
            'iss': 'ymca-volunteer-pathfinder'
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    def verify_token(self, credentials: HTTPAuthorizationCredentials) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                credentials.credentials,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            return payload
        except JWTError as e:
            logger.error(f"JWT verification failed: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = None) -> Optional[Dict[str, Any]]:
        """Get current user from token"""
        if not credentials:
            return None
        
        try:
            payload = self.verify_token(credentials)
            user = await self.database.get_user(user_id=payload.get('sub'))
            return user
        except HTTPException:
            return None
    
    def get_google_auth_url(self, state: str = None) -> str:
        """Generate Google OAuth authorization URL"""
        return self.google_client.create_authorization_url(
            redirect_uri=settings.OAUTH_REDIRECT_URI + '/google',
            scope='openid email profile',
            state=state
        )[0]
    
    def get_microsoft_auth_url(self, state: str = None) -> str:
        """Generate Microsoft OAuth authorization URL"""  
        return self.microsoft_client.create_authorization_url(
            redirect_uri=settings.OAUTH_REDIRECT_URI + '/microsoft',
            scope='openid email profile',
            state=state
        )[0]
    
    async def handle_google_callback(self, request: Request) -> Dict[str, Any]:
        """Handle Google OAuth callback and create/login user"""
        try:
            # Get authorization code from callback
            code = request.query_params.get('code')
            if not code:
                raise HTTPException(status_code=400, detail="Authorization code not found")
            
            # Exchange code for token
            token = await self.google_client.fetch_token(
                code=code,
                redirect_uri=settings.OAUTH_REDIRECT_URI + '/google'
            )
            
            # Get user info from Google
            user_info = await self._get_google_user_info(token['access_token'])
            
            # Create or update user
            user = await self._create_or_update_sso_user(user_info, 'google')
            
            # Generate JWT token
            jwt_token = self.create_jwt_token(user)
            
            return {
                'access_token': jwt_token,
                'token_type': 'bearer',
                'user': user,
                'provider': 'google'
            }
            
        except OAuth2Error as e:
            logger.error(f"Google OAuth error: {e}")
            raise HTTPException(status_code=400, detail="Google authentication failed")
        except Exception as e:
            logger.error(f"Google callback error: {e}")
            raise HTTPException(status_code=500, detail="Authentication error")
    
    async def handle_microsoft_callback(self, request: Request) -> Dict[str, Any]:
        """Handle Microsoft OAuth callback and create/login user"""
        try:
            # Get authorization code from callback
            code = request.query_params.get('code')
            if not code:
                raise HTTPException(status_code=400, detail="Authorization code not found")
            
            # Exchange code for token
            token = await self.microsoft_client.fetch_token(
                code=code,
                redirect_uri=settings.OAUTH_REDIRECT_URI + '/microsoft'
            )
            
            # Get user info from Microsoft
            user_info = await self._get_microsoft_user_info(token['access_token'])
            
            # Create or update user
            user = await self._create_or_update_sso_user(user_info, 'microsoft')
            
            # Generate JWT token
            jwt_token = self.create_jwt_token(user)
            
            return {
                'access_token': jwt_token,
                'token_type': 'bearer',
                'user': user,
                'provider': 'microsoft'
            }
            
        except OAuth2Error as e:
            logger.error(f"Microsoft OAuth error: {e}")
            raise HTTPException(status_code=400, detail="Microsoft authentication failed")
        except Exception as e:
            logger.error(f"Microsoft callback error: {e}")
            raise HTTPException(status_code=500, detail="Authentication error")
    
    async def _get_google_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Google API"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            response.raise_for_status()
            return response.json()
    
    async def _get_microsoft_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Microsoft Graph API"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://graph.microsoft.com/v1.0/me',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            response.raise_for_status()
            return response.json()
    
    async def _create_or_update_sso_user(self, user_info: Dict[str, Any], provider: str) -> Dict[str, Any]:
        """Create or update user from SSO provider information"""
        try:
            email = user_info.get('email', '').lower().strip()
            if not email:
                raise HTTPException(status_code=400, detail="Email not provided by OAuth provider")
            
            # Check if user exists
            existing_user = await self.database.get_user(email=email)
            
            if existing_user:
                # Update existing user with new info if needed
                updates = {}
                if provider == 'google':
                    if user_info.get('given_name') and not existing_user.get('first_name'):
                        updates['first_name'] = user_info['given_name']
                    if user_info.get('family_name') and not existing_user.get('last_name'):
                        updates['last_name'] = user_info['family_name']
                elif provider == 'microsoft':
                    if user_info.get('givenName') and not existing_user.get('first_name'):
                        updates['first_name'] = user_info['givenName']
                    if user_info.get('surname') and not existing_user.get('last_name'):
                        updates['last_name'] = user_info['surname']
                
                # Update SSO provider info
                updates['sso_provider'] = provider
                updates['sso_id'] = user_info.get('id', user_info.get('sub', ''))
                
                if updates:
                    await self.database.update_user(existing_user['id'], updates)
                    # Return updated user data
                    return await self.database.get_user(user_id=existing_user['id'])
                
                return existing_user
            else:
                # Create new user
                if provider == 'google':
                    user_data = {
                        'email': email,
                        'first_name': user_info.get('given_name', ''),
                        'last_name': user_info.get('family_name', ''),
                        'sso_provider': provider,
                        'sso_id': user_info.get('id', user_info.get('sub', '')),
                    }
                elif provider == 'microsoft':
                    user_data = {
                        'email': email,
                        'first_name': user_info.get('givenName', ''),
                        'last_name': user_info.get('surname', ''),
                        'sso_provider': provider,
                        'sso_id': user_info.get('id', ''),
                    }
                else:
                    raise HTTPException(status_code=400, detail="Unsupported SSO provider")
                
                user = await self.database.create_user(user_data)
                if not user:
                    raise HTTPException(status_code=500, detail="Failed to create user")
                
                # Track user creation event
                await self.database.track_event(
                    'user_sso_signup',
                    {'provider': provider},
                    user['id']
                )
                
                return user
                
        except Exception as e:
            logger.error(f"Error creating/updating SSO user: {e}")
            raise HTTPException(status_code=500, detail="User provisioning failed")

# Helper function to extract user from token
async def get_current_user_optional(
    database: VolunteerDatabase,
    credentials: HTTPAuthorizationCredentials = None
) -> Optional[Dict[str, Any]]:
    """Optional user extraction - returns None if not authenticated"""
    if not credentials:
        return None
    
    auth = SSOAuth(database)
    return await auth.get_current_user(credentials)

async def get_current_user_required(
    database: VolunteerDatabase,
    credentials: HTTPAuthorizationCredentials
) -> Dict[str, Any]:
    """Required user extraction - raises 401 if not authenticated"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    auth = SSOAuth(database)
    user = await auth.get_current_user(credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return user