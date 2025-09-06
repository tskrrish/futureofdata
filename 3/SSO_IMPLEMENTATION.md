# SSO Implementation for YMCA Volunteer PathFinder

This document describes the complete Single Sign-On (SSO) implementation with Google and Microsoft Identity integration.

## Overview

The SSO implementation provides:
- **Google OAuth 2.0** authentication
- **Microsoft Identity Platform** authentication  
- **JWT-based** session management
- **Automatic user provisioning** from SSO providers
- **Seamless frontend integration** with existing chat interface

## Files Added/Modified

### New Files
- `auth.py` - Core SSO authentication logic
- `static/login.html` - Login page with SSO buttons
- `static/auth-callback.html` - OAuth callback handling page
- `setup_sso.py` - Setup and configuration helper
- `test_sso.py` - Test suite for SSO functionality
- `config.py` - Configuration with OAuth settings

### Modified Files
- `main.py` - Added SSO routes and authentication-aware endpoints
- `database.py` - Added SSO fields to user schema
- `requirements.txt` - Added OAuth dependencies
- `static/chat.html` - Added authentication UI and token handling

## Architecture

### Authentication Flow

1. **User visits login page** (`/login`)
2. **Clicks Google/Microsoft button** → redirects to OAuth provider
3. **User authenticates** with provider
4. **Provider redirects back** to `/auth/callback/{provider}`
5. **Backend exchanges code for user info** and creates/updates user
6. **JWT token generated** and returned to frontend
7. **Frontend stores token** and redirects to chat

### Database Schema

```sql
-- Users table with SSO support
CREATE TABLE users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    sso_provider VARCHAR(20), -- 'google', 'microsoft', null
    sso_id VARCHAR(255), -- SSO provider user ID
    -- ... other existing fields
);
```

### Key Components

#### 1. SSOAuth Class (`auth.py`)
- **OAuth client management** for Google and Microsoft
- **JWT token creation/verification**
- **User provisioning** from OAuth provider data
- **Token validation** for API endpoints

#### 2. API Endpoints (`main.py`)
- `GET /auth/google` - Start Google OAuth flow
- `GET /auth/microsoft` - Start Microsoft OAuth flow  
- `GET /auth/callback/google` - Handle Google callback
- `GET /auth/callback/microsoft` - Handle Microsoft callback
- `GET /auth/me` - Get current user info
- `POST /auth/logout` - Logout endpoint

#### 3. Frontend Integration (`static/`)
- **Login page** with SSO provider buttons
- **Authentication headers** in API calls
- **User session management** with localStorage
- **Sign-in/sign-out UI** in chat interface

## Configuration

### Environment Variables

```bash
# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Microsoft OAuth  
MICROSOFT_CLIENT_ID=your_microsoft_client_id
MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret
MICROSOFT_TENANT_ID=common  # or specific tenant

# JWT
SECRET_KEY=your_jwt_secret_key

# OAuth Redirect
OAUTH_REDIRECT_URI=http://localhost:8000/auth/callback

# Database (Supabase)
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### OAuth Provider Setup

#### Google OAuth Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create project → Enable Google+ API
3. Credentials → Create OAuth 2.0 Client ID
4. Set redirect URI: `http://localhost:8000/auth/callback/google`
5. Copy Client ID and Secret

#### Microsoft OAuth Setup  
1. Go to [Azure Portal](https://portal.azure.com/)
2. Azure AD → App registrations → New registration
3. Set redirect URI: `http://localhost:8000/auth/callback/microsoft`
4. Certificates & secrets → New client secret
5. Copy Application ID and secret

## Installation & Usage

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp config.example.py config.py
# Set environment variables or update config.py
```

### 3. Setup Database
```bash
python setup_database.py  # Run SQL commands in Supabase
```

### 4. Test Configuration
```bash
python test_sso.py
```

### 5. Start Application
```bash
python main.py
```

### 6. Test SSO Flow
1. Visit `http://localhost:8000`
2. Click "Sign In to Start"
3. Try Google and Microsoft authentication
4. Verify user creation in database
5. Test chat functionality with authenticated user

## Security Features

### JWT Tokens
- **Short expiration** (30 minutes default)
- **Secure signing** with configurable secret
- **User identity verification** on each request

### OAuth Security
- **State parameter** protection against CSRF
- **Secure redirect handling** to prevent hijacking  
- **Token exchange** server-side only
- **User data validation** from providers

### Database Security
- **Email uniqueness** enforcement
- **SSO provider validation**
- **Secure user lookups** by email/ID only

## User Experience

### For New Users
1. **Choose sign-in method** (Google/Microsoft/Guest)
2. **One-click authentication** with existing accounts
3. **Automatic profile creation** from SSO data
4. **Immediate access** to personalized features

### For Returning Users  
1. **Automatic sign-in** with stored tokens
2. **Profile persistence** across sessions
3. **Provider switching** supported
4. **Graceful logout** with session cleanup

## API Changes

### Authentication-Aware Endpoints
All existing endpoints now support optional authentication:
- `POST /api/chat` - Uses authenticated user ID if available
- `POST /api/match` - Saves preferences for authenticated users
- `POST /api/conversations` - Links to user account

### New Endpoints
- Authentication flow endpoints
- User profile management
- Token validation endpoints

## Testing

### Automated Tests (`test_sso.py`)
- Database connectivity
- OAuth URL generation  
- JWT token creation
- API endpoint availability

### Manual Testing Checklist
- [ ] Google OAuth login flow
- [ ] Microsoft OAuth login flow
- [ ] User creation in database
- [ ] JWT token storage and validation
- [ ] Chat functionality with authentication
- [ ] Logout and session cleanup
- [ ] Guest mode still works

## Troubleshooting

### Common Issues

#### OAuth Provider Errors
- **Invalid redirect URI** - Check OAuth app configuration
- **Client secret mismatch** - Verify environment variables
- **Scope permissions** - Ensure correct OAuth scopes

#### Database Issues  
- **Connection failed** - Check Supabase credentials
- **Table not found** - Run database initialization SQL
- **User creation failed** - Check schema and permissions

#### JWT Token Issues
- **Token invalid** - Check SECRET_KEY configuration  
- **Token expired** - Normal behavior, user needs to re-authenticate
- **No token sent** - Frontend localStorage issue

### Debug Mode
Set `DEBUG=true` in environment to enable:
- Detailed error messages
- OAuth flow logging
- Database query logging

## Production Deployment

### Security Checklist
- [ ] Use HTTPS for OAuth redirects
- [ ] Set strong JWT secret key
- [ ] Configure proper CORS origins
- [ ] Use production database credentials
- [ ] Enable rate limiting on auth endpoints

### Environment Setup
- Update `OAUTH_REDIRECT_URI` for production domain
- Set `ENVIRONMENT=production`  
- Configure proper CORS origins
- Use secure session storage

## Future Enhancements

### Potential Additions
- **Azure AD B2C** for enterprise customers
- **SAML SSO** for corporate identity providers
- **Multi-factor authentication** integration
- **Role-based access control** (RBAC)
- **Audit logging** for authentication events

### Integration Opportunities
- **YMCA member verification** via SSO attributes
- **Branch assignment** from organizational data
- **Group permissions** based on SSO roles
- **Automated onboarding** workflows

---

## Implementation Complete ✅

The SSO implementation is complete and ready for testing. All major features are implemented:

- ✅ Google OAuth 2.0 integration
- ✅ Microsoft Identity Platform integration  
- ✅ JWT-based session management
- ✅ User provisioning and profile management
- ✅ Frontend login/logout interface
- ✅ Authentication-aware API endpoints
- ✅ Database schema with SSO support
- ✅ Comprehensive testing and setup tools

The system now supports centralized identity and provisioning as requested, allowing users to authenticate with their existing Google or Microsoft accounts while maintaining the existing guest functionality.