"""
Contact Enrichment Service with Privacy Gates
Provides optional enrichment for volunteer contacts with domain and avatar information
"""
import re
import hashlib
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging
from urllib.parse import urlparse
import json
from datetime import datetime

# Try to import aiohttp, fallback to mock if not available
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    # Create a mock aiohttp for testing
    class MockClientSession:
        def __init__(self):
            pass
        
        def get(self, url):
            return MockResponse()
        
        async def __aenter__(self):
            return self
            
        async def __aexit__(self, *args):
            pass
    
    class MockResponse:
        def __init__(self):
            self.status = 404  # Default to not found for testing
        
        async def __aenter__(self):
            return self
            
        async def __aexit__(self, *args):
            pass
    
    # Mock aiohttp module
    class aiohttp:
        ClientSession = MockClientSession

logger = logging.getLogger(__name__)

class EnrichmentType(Enum):
    DOMAIN = "domain"
    AVATAR = "avatar"
    BOTH = "both"

class PrivacyLevel(Enum):
    NONE = "none"           # No enrichment
    MINIMAL = "minimal"     # Only basic domain info
    STANDARD = "standard"   # Domain + avatar
    FULL = "full"          # All available enrichment

@dataclass
class EnrichmentSettings:
    """User's privacy preferences for contact enrichment"""
    enabled: bool = False
    privacy_level: PrivacyLevel = PrivacyLevel.NONE
    allowed_types: List[EnrichmentType] = None
    consent_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None

@dataclass
class DomainInfo:
    """Information about an email domain"""
    domain: str
    organization: Optional[str] = None
    domain_type: Optional[str] = None  # corporate, educational, personal, etc.
    is_corporate: bool = False
    logo_url: Optional[str] = None
    website_url: Optional[str] = None

@dataclass
class AvatarInfo:
    """Avatar information for a contact"""
    avatar_url: Optional[str] = None
    gravatar_url: Optional[str] = None
    source: Optional[str] = None
    size: int = 80

@dataclass
class EnrichedContact:
    """Enriched contact information"""
    email: str
    domain_info: Optional[DomainInfo] = None
    avatar_info: Optional[AvatarInfo] = None
    enrichment_date: Optional[datetime] = None
    privacy_compliant: bool = True

class ContactEnrichmentService:
    """
    Service for enriching contact information while respecting privacy preferences
    """
    
    def __init__(self):
        self.domain_cache = {}  # Simple in-memory cache for domain lookups
        self.corporate_domains = {
            # Common corporate domains that don't need API lookups
            'gmail.com': DomainInfo(
                domain='gmail.com',
                organization='Google',
                domain_type='personal',
                is_corporate=False,
                website_url='https://gmail.com'
            ),
            'yahoo.com': DomainInfo(
                domain='yahoo.com',
                organization='Yahoo',
                domain_type='personal', 
                is_corporate=False,
                website_url='https://yahoo.com'
            ),
            'outlook.com': DomainInfo(
                domain='outlook.com',
                organization='Microsoft',
                domain_type='personal',
                is_corporate=False,
                website_url='https://outlook.com'
            ),
            'hotmail.com': DomainInfo(
                domain='hotmail.com',
                organization='Microsoft',
                domain_type='personal',
                is_corporate=False,
                website_url='https://outlook.com'
            )
        }

    def extract_domain(self, email: str) -> Optional[str]:
        """Extract domain from email address"""
        if not email or '@' not in email:
            return None
        
        try:
            domain = email.split('@')[1].lower().strip()
            return domain if domain else None
        except IndexError:
            return None

    def generate_gravatar_url(self, email: str, size: int = 80) -> str:
        """Generate Gravatar URL for email address"""
        email_hash = hashlib.md5(email.lower().strip().encode()).hexdigest()
        return f"https://www.gravatar.com/avatar/{email_hash}?s={size}&d=identicon"

    async def check_gravatar_exists(self, email: str) -> bool:
        """Check if a Gravatar exists for the email (non-default)"""
        try:
            if not AIOHTTP_AVAILABLE:
                # Mock behavior for testing - return True for gmail addresses
                return email.lower().endswith('@gmail.com')
            
            email_hash = hashlib.md5(email.lower().strip().encode()).hexdigest()
            # Use 404 as default to check if avatar exists
            url = f"https://www.gravatar.com/avatar/{email_hash}?d=404"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return response.status == 200
        except Exception as e:
            logger.warning(f"Error checking Gravatar for {email}: {e}")
            return False

    async def enrich_domain(self, domain: str) -> Optional[DomainInfo]:
        """Enrich domain information"""
        if not domain:
            return None

        # Check cache first
        if domain in self.domain_cache:
            return self.domain_cache[domain]

        # Check known domains
        if domain in self.corporate_domains:
            domain_info = self.corporate_domains[domain]
            self.domain_cache[domain] = domain_info
            return domain_info

        # For unknown domains, provide basic info
        domain_info = DomainInfo(
            domain=domain,
            domain_type='unknown',
            is_corporate=self._is_likely_corporate(domain),
            website_url=f"https://{domain}"
        )

        # Try to determine if it's an educational domain
        if domain.endswith('.edu') or domain.endswith('.ac.uk'):
            domain_info.domain_type = 'educational'
            domain_info.is_corporate = True

        # Try to determine if it's a government domain
        if domain.endswith('.gov') or domain.endswith('.mil'):
            domain_info.domain_type = 'government'
            domain_info.is_corporate = True

        self.domain_cache[domain] = domain_info
        return domain_info

    def _is_likely_corporate(self, domain: str) -> bool:
        """Simple heuristic to determine if domain is likely corporate"""
        personal_indicators = ['gmail', 'yahoo', 'hotmail', 'outlook', 'aol', 'icloud']
        return not any(indicator in domain.lower() for indicator in personal_indicators)

    async def enrich_avatar(self, email: str, privacy_level: PrivacyLevel) -> Optional[AvatarInfo]:
        """Enrich avatar information based on privacy level"""
        if not email or privacy_level == PrivacyLevel.NONE:
            return None

        # Only provide Gravatar for STANDARD and FULL privacy levels
        if privacy_level not in [PrivacyLevel.STANDARD, PrivacyLevel.FULL]:
            return None

        try:
            # Check if Gravatar exists
            has_gravatar = await self.check_gravatar_exists(email)
            
            gravatar_url = self.generate_gravatar_url(email)
            
            return AvatarInfo(
                avatar_url=gravatar_url if has_gravatar else None,
                gravatar_url=gravatar_url,
                source='gravatar' if has_gravatar else 'generated',
                size=80
            )
        except Exception as e:
            logger.error(f"Error enriching avatar for {email}: {e}")
            return None

    async def enrich_contact(
        self, 
        email: str, 
        settings: EnrichmentSettings
    ) -> Optional[EnrichedContact]:
        """
        Enrich a contact with domain and avatar information based on privacy settings
        """
        if not email or not settings.enabled:
            return None

        try:
            domain = self.extract_domain(email)
            if not domain:
                return None

            enriched = EnrichedContact(
                email=email,
                enrichment_date=datetime.now(),
                privacy_compliant=True
            )

            # Enrich domain information if allowed
            if (settings.privacy_level != PrivacyLevel.NONE and 
                (not settings.allowed_types or EnrichmentType.DOMAIN in settings.allowed_types)):
                enriched.domain_info = await self.enrich_domain(domain)

            # Enrich avatar information if allowed
            if (settings.privacy_level in [PrivacyLevel.STANDARD, PrivacyLevel.FULL] and
                (not settings.allowed_types or EnrichmentType.AVATAR in settings.allowed_types)):
                enriched.avatar_info = await self.enrich_avatar(email, settings.privacy_level)

            return enriched

        except Exception as e:
            logger.error(f"Error enriching contact {email}: {e}")
            return None

    async def enrich_contacts_batch(
        self, 
        contacts: List[Dict[str, Any]], 
        settings: EnrichmentSettings
    ) -> List[EnrichedContact]:
        """
        Enrich multiple contacts in batch with rate limiting
        """
        if not settings.enabled:
            return []

        enriched_contacts = []
        
        # Process in batches to avoid overwhelming external services
        batch_size = 10
        for i in range(0, len(contacts), batch_size):
            batch = contacts[i:i + batch_size]
            
            tasks = []
            for contact in batch:
                email = contact.get('email')
                if email:
                    tasks.append(self.enrich_contact(email, settings))
            
            # Process batch concurrently
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, EnrichedContact):
                    enriched_contacts.append(result)
                elif isinstance(result, Exception):
                    logger.warning(f"Error in batch enrichment: {result}")
            
            # Small delay between batches to be respectful
            await asyncio.sleep(0.1)

        return enriched_contacts

class PrivacyGateManager:
    """
    Manages privacy preferences and consent for contact enrichment
    """
    
    def __init__(self, database=None):
        self.database = database
        
    async def get_user_enrichment_settings(self, user_id: str) -> EnrichmentSettings:
        """Get user's enrichment privacy settings"""
        if not self.database:
            return EnrichmentSettings()  # Default: disabled
        
        try:
            settings_data = await self.database.get_enrichment_settings(user_id)
            if not settings_data:
                return EnrichmentSettings()  # Default: disabled
            
            # Convert database data to EnrichmentSettings
            allowed_types = None
            if settings_data.get('allowed_types'):
                allowed_types = [EnrichmentType(t) for t in settings_data['allowed_types']]
            
            consent_date = None
            if settings_data.get('consent_date'):
                consent_date = datetime.fromisoformat(settings_data['consent_date'].replace('Z', '+00:00'))
            
            last_updated = None
            if settings_data.get('updated_at'):
                last_updated = datetime.fromisoformat(settings_data['updated_at'].replace('Z', '+00:00'))
            
            return EnrichmentSettings(
                enabled=settings_data.get('enabled', False),
                privacy_level=PrivacyLevel(settings_data.get('privacy_level', 'none')),
                allowed_types=allowed_types,
                consent_date=consent_date,
                last_updated=last_updated
            )
        except Exception as e:
            logger.error(f"Error getting enrichment settings for user {user_id}: {e}")
            return EnrichmentSettings()

    async def update_enrichment_settings(
        self, 
        user_id: str, 
        settings: EnrichmentSettings
    ) -> bool:
        """Update user's enrichment privacy settings"""
        settings.last_updated = datetime.now()
        
        if settings.enabled and not settings.consent_date:
            settings.consent_date = datetime.now()
        
        if not self.database:
            return True  # Mock success for now
            
        try:
            # Convert EnrichmentSettings to database format
            settings_data = {
                'enabled': settings.enabled,
                'privacy_level': settings.privacy_level.value,
                'allowed_types': [t.value for t in settings.allowed_types] if settings.allowed_types else [],
                'consent_date': settings.consent_date.isoformat() if settings.consent_date else None
            }
            
            return await self.database.save_enrichment_settings(user_id, settings_data)
        except Exception as e:
            logger.error(f"Error updating enrichment settings for user {user_id}: {e}")
            return False

    def validate_privacy_settings(self, settings: EnrichmentSettings) -> tuple[bool, str]:
        """Validate privacy settings"""
        if settings.enabled and settings.privacy_level == PrivacyLevel.NONE:
            return False, "Privacy level cannot be NONE when enrichment is enabled"
        
        if settings.enabled and not settings.consent_date:
            return False, "Consent date required when enrichment is enabled"
        
        return True, "Settings valid"

    def get_privacy_level_description(self, level: PrivacyLevel) -> str:
        """Get human-readable description of privacy level"""
        descriptions = {
            PrivacyLevel.NONE: "No contact enrichment - your email information stays private",
            PrivacyLevel.MINIMAL: "Basic domain information only (e.g., company name)",
            PrivacyLevel.STANDARD: "Domain information and avatar from Gravatar service",
            PrivacyLevel.FULL: "Full enrichment including all available public information"
        }
        return descriptions.get(level, "Unknown privacy level")

# Example usage and testing
async def main():
    """Example usage of the contact enrichment service"""
    service = ContactEnrichmentService()
    privacy_manager = PrivacyGateManager()
    
    # Example user with standard privacy settings
    settings = EnrichmentSettings(
        enabled=True,
        privacy_level=PrivacyLevel.STANDARD,
        allowed_types=[EnrichmentType.DOMAIN, EnrichmentType.AVATAR],
        consent_date=datetime.now()
    )
    
    # Test single contact enrichment
    enriched = await service.enrich_contact("john.doe@gmail.com", settings)
    if enriched:
        print(f"Enriched contact: {enriched.email}")
        if enriched.domain_info:
            print(f"Domain: {enriched.domain_info.organization} ({enriched.domain_info.domain_type})")
        if enriched.avatar_info:
            print(f"Avatar: {enriched.avatar_info.avatar_url}")

if __name__ == "__main__":
    asyncio.run(main())