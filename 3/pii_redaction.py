"""
PII Redaction System for Volunteer PathFinder
Implements masking of sensitive fields for unauthorized views
"""
import re
import json
from typing import Dict, Any, List, Optional, Set
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import hashlib


class PIIFieldType(Enum):
    """Types of PII fields that can be masked"""
    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "address"
    SSN = "ssn"
    DATE_OF_BIRTH = "date_of_birth"
    FULL_NAME = "full_name"
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    ZIP_CODE = "zip_code"
    CREDIT_CARD = "credit_card"
    MEDICAL_INFO = "medical_info"
    EMERGENCY_CONTACT = "emergency_contact"


class ViewPermissionLevel(Enum):
    """Different permission levels for viewing data"""
    PUBLIC = "public"           # No PII access
    VOLUNTEER = "volunteer"     # Basic volunteer info only
    COORDINATOR = "coordinator" # Branch-level volunteer coordination
    MANAGER = "manager"         # Full branch access
    ADMIN = "admin"            # System-wide access
    

@dataclass
class PIIField:
    """Configuration for a PII field"""
    field_name: str
    field_type: PIIFieldType
    required_permission: ViewPermissionLevel
    mask_pattern: str = "***"
    partial_show: int = 0  # Number of characters to show (e.g., first 2 chars of phone)


@dataclass
class UserContext:
    """User context for permission checking"""
    user_id: Optional[str] = None
    permission_level: ViewPermissionLevel = ViewPermissionLevel.PUBLIC
    branch_access: Set[str] = None
    organization_id: Optional[str] = None
    is_staff: bool = False
    is_admin: bool = False
    
    def __post_init__(self):
        if self.branch_access is None:
            self.branch_access = set()


class PIIRedactionEngine:
    """Main engine for PII detection and masking"""
    
    def __init__(self):
        self.pii_fields = self._initialize_pii_fields()
        self.field_patterns = self._compile_detection_patterns()
    
    def _initialize_pii_fields(self) -> Dict[str, PIIField]:
        """Initialize PII field configurations"""
        fields = {
            # Personal identification
            'email': PIIField('email', PIIFieldType.EMAIL, ViewPermissionLevel.VOLUNTEER, partial_show=3),
            'phone': PIIField('phone', PIIFieldType.PHONE, ViewPermissionLevel.VOLUNTEER, partial_show=3),
            'first_name': PIIField('first_name', PIIFieldType.FIRST_NAME, ViewPermissionLevel.PUBLIC),
            'last_name': PIIField('last_name', PIIFieldType.LAST_NAME, ViewPermissionLevel.VOLUNTEER),
            'full_name': PIIField('full_name', PIIFieldType.FULL_NAME, ViewPermissionLevel.VOLUNTEER),
            
            # Location data
            'address': PIIField('address', PIIFieldType.ADDRESS, ViewPermissionLevel.COORDINATOR),
            'street_address': PIIField('street_address', PIIFieldType.ADDRESS, ViewPermissionLevel.COORDINATOR),
            'zip_code': PIIField('zip_code', PIIFieldType.ZIP_CODE, ViewPermissionLevel.VOLUNTEER, partial_show=2),
            
            # Demographics
            'age': PIIField('age', PIIFieldType.DATE_OF_BIRTH, ViewPermissionLevel.VOLUNTEER),
            'date_of_birth': PIIField('date_of_birth', PIIFieldType.DATE_OF_BIRTH, ViewPermissionLevel.COORDINATOR),
            'birth_date': PIIField('birth_date', PIIFieldType.DATE_OF_BIRTH, ViewPermissionLevel.COORDINATOR),
            
            # Emergency and medical
            'emergency_contact': PIIField('emergency_contact', PIIFieldType.EMERGENCY_CONTACT, ViewPermissionLevel.MANAGER),
            'emergency_phone': PIIField('emergency_phone', PIIFieldType.EMERGENCY_CONTACT, ViewPermissionLevel.MANAGER),
            'medical_conditions': PIIField('medical_conditions', PIIFieldType.MEDICAL_INFO, ViewPermissionLevel.MANAGER),
            'medications': PIIField('medications', PIIFieldType.MEDICAL_INFO, ViewPermissionLevel.MANAGER),
            
            # Sensitive identifiers
            'ssn': PIIField('ssn', PIIFieldType.SSN, ViewPermissionLevel.ADMIN),
            'social_security_number': PIIField('social_security_number', PIIFieldType.SSN, ViewPermissionLevel.ADMIN),
            'credit_card': PIIField('credit_card', PIIFieldType.CREDIT_CARD, ViewPermissionLevel.ADMIN),
        }
        return fields
    
    def _compile_detection_patterns(self) -> Dict[PIIFieldType, re.Pattern]:
        """Compile regex patterns for PII detection in text"""
        patterns = {
            PIIFieldType.EMAIL: re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            PIIFieldType.PHONE: re.compile(r'\b(\d{3}[-.]?\d{3}[-.]?\d{4}|\(\d{3}\)\s?\d{3}[-.]?\d{4})\b'),
            PIIFieldType.SSN: re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            PIIFieldType.CREDIT_CARD: re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
            PIIFieldType.ZIP_CODE: re.compile(r'\b\d{5}(-\d{4})?\b'),
        }
        return patterns
    
    def register_pii_field(self, field: PIIField) -> None:
        """Register a new PII field configuration"""
        self.pii_fields[field.field_name] = field
    
    def _mask_value(self, value: Any, pii_field: PIIField) -> str:
        """Apply masking to a specific value"""
        if value is None:
            return None
            
        str_value = str(value)
        
        # Handle partial showing
        if pii_field.partial_show > 0 and len(str_value) > pii_field.partial_show:
            visible_part = str_value[:pii_field.partial_show]
            masked_part = '*' * max(3, len(str_value) - pii_field.partial_show)
            return f"{visible_part}{masked_part}"
        
        # Full masking
        if pii_field.field_type == PIIFieldType.EMAIL:
            # Show first character and domain
            if '@' in str_value:
                parts = str_value.split('@')
                return f"{parts[0][0]}***@{parts[1]}"
        
        elif pii_field.field_type == PIIFieldType.PHONE:
            # Show area code only
            clean_phone = re.sub(r'[^\d]', '', str_value)
            if len(clean_phone) >= 10:
                return f"({clean_phone[:3]}) ***-****"
        
        elif pii_field.field_type in [PIIFieldType.FIRST_NAME, PIIFieldType.LAST_NAME]:
            # Show first character
            return f"{str_value[0]}***" if str_value else "***"
        
        # Default masking
        mask_length = max(3, min(len(str_value), 8))
        return '*' * mask_length
    
    def _detect_pii_in_text(self, text: str) -> List[tuple]:
        """Detect PII patterns in free text"""
        detected = []
        for pii_type, pattern in self.field_patterns.items():
            matches = pattern.finditer(text)
            for match in matches:
                detected.append((match.start(), match.end(), pii_type, match.group()))
        return detected
    
    def _mask_text_content(self, text: str, user_context: UserContext) -> str:
        """Mask PII content found in text fields"""
        if not text or not isinstance(text, str):
            return text
            
        detected_pii = self._detect_pii_in_text(text)
        if not detected_pii:
            return text
        
        # Sort by position (reverse order to maintain positions during replacement)
        detected_pii.sort(key=lambda x: x[0], reverse=True)
        
        masked_text = text
        for start, end, pii_type, original_value in detected_pii:
            # Check if user has permission to see this PII type
            required_level = self._get_required_permission_for_type(pii_type)
            if not self._has_permission(user_context, required_level):
                # Create a temporary PIIField for masking
                temp_field = PIIField("temp", pii_type, required_level)
                masked_value = self._mask_value(original_value, temp_field)
                masked_text = masked_text[:start] + masked_value + masked_text[end:]
        
        return masked_text
    
    def _get_required_permission_for_type(self, pii_type: PIIFieldType) -> ViewPermissionLevel:
        """Get required permission level for a PII type"""
        permission_map = {
            PIIFieldType.EMAIL: ViewPermissionLevel.VOLUNTEER,
            PIIFieldType.PHONE: ViewPermissionLevel.VOLUNTEER,
            PIIFieldType.SSN: ViewPermissionLevel.ADMIN,
            PIIFieldType.CREDIT_CARD: ViewPermissionLevel.ADMIN,
            PIIFieldType.ADDRESS: ViewPermissionLevel.COORDINATOR,
            PIIFieldType.ZIP_CODE: ViewPermissionLevel.VOLUNTEER,
            PIIFieldType.MEDICAL_INFO: ViewPermissionLevel.MANAGER,
            PIIFieldType.EMERGENCY_CONTACT: ViewPermissionLevel.MANAGER,
        }
        return permission_map.get(pii_type, ViewPermissionLevel.VOLUNTEER)
    
    def _has_permission(self, user_context: UserContext, required_level: ViewPermissionLevel) -> bool:
        """Check if user has required permission level"""
        permission_hierarchy = {
            ViewPermissionLevel.PUBLIC: 0,
            ViewPermissionLevel.VOLUNTEER: 1,
            ViewPermissionLevel.COORDINATOR: 2,
            ViewPermissionLevel.MANAGER: 3,
            ViewPermissionLevel.ADMIN: 4,
        }
        
        user_level = permission_hierarchy.get(user_context.permission_level, 0)
        required_level_value = permission_hierarchy.get(required_level, 0)
        
        return user_level >= required_level_value
    
    def mask_data(self, data: Dict[str, Any], user_context: UserContext) -> Dict[str, Any]:
        """
        Main method to mask PII data based on user permissions
        
        Args:
            data: Dictionary containing potentially sensitive data
            user_context: User's permission context
            
        Returns:
            Dictionary with PII fields masked according to permissions
        """
        if not data:
            return data
        
        masked_data = {}
        
        for key, value in data.items():
            # Handle nested dictionaries
            if isinstance(value, dict):
                masked_data[key] = self.mask_data(value, user_context)
                continue
            
            # Handle lists
            if isinstance(value, list):
                masked_list = []
                for item in value:
                    if isinstance(item, dict):
                        masked_list.append(self.mask_data(item, user_context))
                    elif isinstance(item, str):
                        masked_list.append(self._mask_text_content(item, user_context))
                    else:
                        masked_list.append(item)
                masked_data[key] = masked_list
                continue
            
            # Check if this field is configured as PII
            pii_field = self.pii_fields.get(key.lower())
            if pii_field:
                if self._has_permission(user_context, pii_field.required_permission):
                    # User has permission - show original value
                    masked_data[key] = value
                else:
                    # User lacks permission - mask the value
                    masked_data[key] = self._mask_value(value, pii_field)
            else:
                # Not a configured PII field, but check for PII in text content
                if isinstance(value, str):
                    masked_data[key] = self._mask_text_content(value, user_context)
                else:
                    masked_data[key] = value
        
        return masked_data
    
    def mask_volunteer_profile(self, profile: Dict[str, Any], user_context: UserContext, 
                              target_user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Mask a volunteer profile with special handling for self-access
        
        Args:
            profile: Volunteer profile data
            user_context: Viewing user's context  
            target_user_id: ID of the profile being viewed
            
        Returns:
            Masked profile data
        """
        # Users can always see their own full profile
        if target_user_id and user_context.user_id == target_user_id:
            enhanced_context = UserContext(
                user_id=user_context.user_id,
                permission_level=ViewPermissionLevel.ADMIN,
                branch_access=user_context.branch_access,
                organization_id=user_context.organization_id,
                is_staff=user_context.is_staff,
                is_admin=user_context.is_admin
            )
            return self.mask_data(profile, enhanced_context)
        
        return self.mask_data(profile, user_context)
    
    def generate_audit_log(self, original_data: Dict[str, Any], masked_data: Dict[str, Any], 
                          user_context: UserContext) -> Dict[str, Any]:
        """Generate audit log for PII masking operation"""
        masked_fields = []
        
        def find_masked_fields(orig: Dict, masked: Dict, path: str = ""):
            for key in orig.keys():
                current_path = f"{path}.{key}" if path else key
                if key in masked:
                    if isinstance(orig[key], dict) and isinstance(masked[key], dict):
                        find_masked_fields(orig[key], masked[key], current_path)
                    elif orig[key] != masked[key]:
                        masked_fields.append({
                            'field': current_path,
                            'original_type': type(orig[key]).__name__,
                            'was_masked': True
                        })
        
        find_masked_fields(original_data, masked_data)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_context.user_id,
            'permission_level': user_context.permission_level.value,
            'masked_fields': masked_fields,
            'total_fields_masked': len(masked_fields)
        }


class PIIRedactionMiddleware:
    """Middleware for automatic PII redaction in API responses"""
    
    def __init__(self, redaction_engine: PIIRedactionEngine):
        self.redaction_engine = redaction_engine
    
    def process_response(self, response_data: Any, user_context: UserContext, 
                        endpoint: str = None) -> Any:
        """Process API response to mask PII fields"""
        if isinstance(response_data, dict):
            return self.redaction_engine.mask_data(response_data, user_context)
        elif isinstance(response_data, list):
            return [
                self.redaction_engine.mask_data(item, user_context) 
                if isinstance(item, dict) else item 
                for item in response_data
            ]
        return response_data


# Utility functions for FastAPI integration
def get_user_context_from_request(request, supabase_user=None) -> UserContext:
    """Extract user context from FastAPI request"""
    # This would typically integrate with your authentication system
    user_context = UserContext()
    
    if supabase_user:
        user_context.user_id = str(supabase_user.id)
        # Determine permission level based on user metadata, roles, etc.
        user_metadata = getattr(supabase_user, 'user_metadata', {})
        app_metadata = getattr(supabase_user, 'app_metadata', {})
        
        if app_metadata.get('is_admin'):
            user_context.permission_level = ViewPermissionLevel.ADMIN
            user_context.is_admin = True
        elif app_metadata.get('is_manager'):
            user_context.permission_level = ViewPermissionLevel.MANAGER
            user_context.is_staff = True
        elif app_metadata.get('is_coordinator'):
            user_context.permission_level = ViewPermissionLevel.COORDINATOR
            user_context.is_staff = True
        elif supabase_user.email:
            user_context.permission_level = ViewPermissionLevel.VOLUNTEER
        
        # Extract branch access
        branch_access = app_metadata.get('branch_access', [])
        user_context.branch_access = set(branch_access) if branch_access else set()
        user_context.organization_id = app_metadata.get('organization_id')
    
    return user_context


# Global instance
pii_engine = PIIRedactionEngine()
pii_middleware = PIIRedactionMiddleware(pii_engine)