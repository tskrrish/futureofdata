"""
PII Redaction Configuration for Volunteer PathFinder
Defines field mappings, permission levels, and masking rules
"""
from typing import Dict, List, Set
from pii_redaction import PIIField, PIIFieldType, ViewPermissionLevel


class PIIConfigManager:
    """Manages PII configuration and field mappings"""
    
    def __init__(self):
        self.volunteer_fields = self._define_volunteer_pii_fields()
        self.conversation_fields = self._define_conversation_pii_fields()
        self.analytics_fields = self._define_analytics_pii_fields()
        
    def _define_volunteer_pii_fields(self) -> Dict[str, PIIField]:
        """Define PII fields specific to volunteer data"""
        return {
            # Core identity fields
            'email': PIIField('email', PIIFieldType.EMAIL, ViewPermissionLevel.VOLUNTEER, partial_show=3),
            'phone': PIIField('phone', PIIFieldType.PHONE, ViewPermissionLevel.VOLUNTEER, partial_show=3),
            'first_name': PIIField('first_name', PIIFieldType.FIRST_NAME, ViewPermissionLevel.PUBLIC),
            'last_name': PIIField('last_name', PIIFieldType.LAST_NAME, ViewPermissionLevel.VOLUNTEER),
            'full_name': PIIField('full_name', PIIFieldType.FULL_NAME, ViewPermissionLevel.VOLUNTEER),
            'name': PIIField('name', PIIFieldType.FULL_NAME, ViewPermissionLevel.VOLUNTEER),
            
            # Location and demographic data
            'address': PIIField('address', PIIFieldType.ADDRESS, ViewPermissionLevel.COORDINATOR),
            'street_address': PIIField('street_address', PIIFieldType.ADDRESS, ViewPermissionLevel.COORDINATOR),
            'home_address': PIIField('home_address', PIIFieldType.ADDRESS, ViewPermissionLevel.COORDINATOR),
            'zip_code': PIIField('zip_code', PIIFieldType.ZIP_CODE, ViewPermissionLevel.VOLUNTEER, partial_show=2),
            'postal_code': PIIField('postal_code', PIIFieldType.ZIP_CODE, ViewPermissionLevel.VOLUNTEER, partial_show=2),
            'city': PIIField('city', PIIFieldType.ADDRESS, ViewPermissionLevel.PUBLIC),
            'state': PIIField('state', PIIFieldType.ADDRESS, ViewPermissionLevel.PUBLIC),
            
            # Age and birth info
            'age': PIIField('age', PIIFieldType.DATE_OF_BIRTH, ViewPermissionLevel.VOLUNTEER),
            'date_of_birth': PIIField('date_of_birth', PIIFieldType.DATE_OF_BIRTH, ViewPermissionLevel.COORDINATOR),
            'birth_date': PIIField('birth_date', PIIFieldType.DATE_OF_BIRTH, ViewPermissionLevel.COORDINATOR),
            'birthdate': PIIField('birthdate', PIIFieldType.DATE_OF_BIRTH, ViewPermissionLevel.COORDINATOR),
            
            # Emergency contacts
            'emergency_contact': PIIField('emergency_contact', PIIFieldType.EMERGENCY_CONTACT, ViewPermissionLevel.MANAGER),
            'emergency_contact_name': PIIField('emergency_contact_name', PIIFieldType.EMERGENCY_CONTACT, ViewPermissionLevel.MANAGER),
            'emergency_contact_phone': PIIField('emergency_contact_phone', PIIFieldType.EMERGENCY_CONTACT, ViewPermissionLevel.MANAGER),
            'emergency_phone': PIIField('emergency_phone', PIIFieldType.EMERGENCY_CONTACT, ViewPermissionLevel.MANAGER),
            'next_of_kin': PIIField('next_of_kin', PIIFieldType.EMERGENCY_CONTACT, ViewPermissionLevel.MANAGER),
            
            # Medical and health information
            'medical_conditions': PIIField('medical_conditions', PIIFieldType.MEDICAL_INFO, ViewPermissionLevel.MANAGER),
            'medications': PIIField('medications', PIIFieldType.MEDICAL_INFO, ViewPermissionLevel.MANAGER),
            'allergies': PIIField('allergies', PIIFieldType.MEDICAL_INFO, ViewPermissionLevel.MANAGER),
            'medical_notes': PIIField('medical_notes', PIIFieldType.MEDICAL_INFO, ViewPermissionLevel.MANAGER),
            'health_conditions': PIIField('health_conditions', PIIFieldType.MEDICAL_INFO, ViewPermissionLevel.MANAGER),
            
            # Sensitive identifiers
            'ssn': PIIField('ssn', PIIFieldType.SSN, ViewPermissionLevel.ADMIN),
            'social_security_number': PIIField('social_security_number', PIIFieldType.SSN, ViewPermissionLevel.ADMIN),
            'tax_id': PIIField('tax_id', PIIFieldType.SSN, ViewPermissionLevel.ADMIN),
            'credit_card': PIIField('credit_card', PIIFieldType.CREDIT_CARD, ViewPermissionLevel.ADMIN),
            'credit_card_number': PIIField('credit_card_number', PIIFieldType.CREDIT_CARD, ViewPermissionLevel.ADMIN),
            'bank_account': PIIField('bank_account', PIIFieldType.CREDIT_CARD, ViewPermissionLevel.ADMIN),
            
            # Contact preferences and personal details
            'contact_preference': PIIField('contact_preference', PIIFieldType.PHONE, ViewPermissionLevel.VOLUNTEER),
            'preferred_contact': PIIField('preferred_contact', PIIFieldType.PHONE, ViewPermissionLevel.VOLUNTEER),
            'mobile_phone': PIIField('mobile_phone', PIIFieldType.PHONE, ViewPermissionLevel.VOLUNTEER, partial_show=3),
            'home_phone': PIIField('home_phone', PIIFieldType.PHONE, ViewPermissionLevel.VOLUNTEER, partial_show=3),
            'work_phone': PIIField('work_phone', PIIFieldType.PHONE, ViewPermissionLevel.COORDINATOR, partial_show=3),
            
            # Demographic information
            'gender': PIIField('gender', PIIFieldType.DATE_OF_BIRTH, ViewPermissionLevel.VOLUNTEER),
            'ethnicity': PIIField('ethnicity', PIIFieldType.DATE_OF_BIRTH, ViewPermissionLevel.COORDINATOR),
            'race': PIIField('race', PIIFieldType.DATE_OF_BIRTH, ViewPermissionLevel.COORDINATOR),
        }
    
    def _define_conversation_pii_fields(self) -> Dict[str, PIIField]:
        """Define PII fields that may appear in conversation data"""
        return {
            'user_id': PIIField('user_id', PIIFieldType.FULL_NAME, ViewPermissionLevel.VOLUNTEER),
            'session_id': PIIField('session_id', PIIFieldType.FULL_NAME, ViewPermissionLevel.COORDINATOR),
            'ip_address': PIIField('ip_address', PIIFieldType.ADDRESS, ViewPermissionLevel.MANAGER),
            'user_agent': PIIField('user_agent', PIIFieldType.ADDRESS, ViewPermissionLevel.COORDINATOR),
        }
    
    def _define_analytics_pii_fields(self) -> Dict[str, PIIField]:
        """Define PII fields in analytics and tracking data"""
        return {
            'event_data': PIIField('event_data', PIIFieldType.FULL_NAME, ViewPermissionLevel.COORDINATOR),
            'metadata': PIIField('metadata', PIIFieldType.FULL_NAME, ViewPermissionLevel.COORDINATOR),
            'tracking_id': PIIField('tracking_id', PIIFieldType.FULL_NAME, ViewPermissionLevel.VOLUNTEER),
        }
    
    def get_all_pii_fields(self) -> Dict[str, PIIField]:
        """Get all PII field configurations"""
        all_fields = {}
        all_fields.update(self.volunteer_fields)
        all_fields.update(self.conversation_fields)
        all_fields.update(self.analytics_fields)
        return all_fields
    
    def get_fields_by_permission_level(self, level: ViewPermissionLevel) -> List[PIIField]:
        """Get all fields that require a specific permission level or higher"""
        all_fields = self.get_all_pii_fields()
        
        permission_hierarchy = {
            ViewPermissionLevel.PUBLIC: 0,
            ViewPermissionLevel.VOLUNTEER: 1,
            ViewPermissionLevel.COORDINATOR: 2,
            ViewPermissionLevel.MANAGER: 3,
            ViewPermissionLevel.ADMIN: 4,
        }
        
        level_value = permission_hierarchy.get(level, 0)
        
        return [
            field for field in all_fields.values()
            if permission_hierarchy.get(field.required_permission, 0) >= level_value
        ]
    
    def is_sensitive_endpoint(self, endpoint: str) -> bool:
        """Check if an endpoint typically contains sensitive data"""
        sensitive_patterns = [
            '/api/users/',
            '/api/profile',
            '/api/conversations/',
            '/api/feedback',
            '/api/match',
            '/analytics'
        ]
        
        return any(pattern in endpoint for pattern in sensitive_patterns)
    
    def get_default_masking_rules(self) -> Dict[str, str]:
        """Get default masking patterns for different field types"""
        return {
            'email': 'partial_domain',  # show first char + domain
            'phone': 'area_code_only',  # show area code only
            'name': 'first_char_only',  # show first character only
            'address': 'city_state_only',  # show city and state only
            'age': 'age_range',  # show age range (20-30, 30-40, etc.)
            'date': 'year_only',  # show year only
            'id': 'hash',  # show hash of original value
            'default': 'asterisk'  # default *** masking
        }


# Endpoint-specific PII policies
ENDPOINT_PII_POLICIES = {
    '/api/profile': {
        'public_fields': ['first_name', 'city', 'state', 'volunteer_type'],
        'volunteer_fields': ['email', 'phone', 'age', 'last_name', 'zip_code'],
        'coordinator_fields': ['address', 'date_of_birth', 'emergency_contact'],
        'manager_fields': ['medical_conditions', 'emergency_contact_phone'],
        'admin_fields': ['ssn', 'credit_card', 'bank_account']
    },
    '/api/users': {
        'public_fields': ['first_name', 'city', 'state'],
        'volunteer_fields': ['email', 'phone', 'age', 'last_name'],
        'coordinator_fields': ['address', 'zip_code', 'date_of_birth'],
        'manager_fields': ['emergency_contact', 'medical_conditions'],
        'admin_fields': ['ssn', 'tax_id']
    },
    '/api/conversations': {
        'public_fields': [],
        'volunteer_fields': ['user_id'],
        'coordinator_fields': ['session_id', 'user_agent'],
        'manager_fields': ['ip_address'],
        'admin_fields': ['tracking_data']
    },
    'default': {
        'public_fields': ['first_name', 'city', 'state'],
        'volunteer_fields': ['email', 'last_name', 'age'],
        'coordinator_fields': ['phone', 'zip_code'],
        'manager_fields': ['address', 'emergency_contact'],
        'admin_fields': ['ssn', 'medical_conditions']
    }
}

# Global configuration instance
pii_config_manager = PIIConfigManager()