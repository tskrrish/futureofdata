# PII Redaction System for Volunteer PathFinder

## Overview

The PII (Personally Identifiable Information) Redaction System implements comprehensive data masking for the YMCA Volunteer PathFinder application. It automatically masks sensitive fields based on user authorization levels, ensuring data privacy compliance while maintaining system functionality.

## Features

### 🔐 Multi-Level Permission System
- **Public**: Minimal information access (first name, city, state, non-PII fields)
- **Volunteer**: Basic personal info (email partial, phone partial, age, last name)  
- **Coordinator**: Location and contact details (full address, zip code)
- **Manager**: Emergency contacts and medical information
- **Admin**: Full access to all data including SSN and financial information

### 🎭 Intelligent Masking
- **Field-level masking**: Configurable per-field masking rules
- **Text content detection**: Regex-based PII detection in free text
- **Partial masking**: Show partial information (e.g., area code only for phones)
- **Nested data support**: Masks PII in complex nested structures
- **Self-access**: Users can always see their own complete profile

### 📊 Audit & Compliance
- **Audit logging**: Track all masking operations for compliance
- **Configurable policies**: Endpoint-specific PII policies
- **Custom field registration**: Add new PII field types dynamically

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Endpoints                        │
├─────────────────────────────────────────────────────────────────┤
│              PIIRedactionMiddleware                             │
├─────────────────────────────────────────────────────────────────┤
│                  PIIRedactionEngine                             │
├─────────────────────────────────────────────────────────────────┤
│         PIIConfigManager  │  UserContext  │  PIIField          │
└─────────────────────────────────────────────────────────────────┘
```

## Files Structure

```
3/
├── pii_redaction.py          # Core PII redaction engine
├── pii_config.py             # Configuration and field definitions  
├── test_pii_redaction.py     # Comprehensive test suite
├── main.py                   # FastAPI integration (modified)
└── PII_REDACTION_README.md   # This documentation
```

## Integration

The system has been integrated into the following FastAPI endpoints:

### `/api/profile` - Volunteer Profile Analysis
- Applies masking based on viewing user's permission level
- Supports self-profile access (users see their own full data)
- Masks volunteer history and sensitive information

### `/api/users/{user_id}` - User Profile Access  
- Masks user profiles based on permission levels
- Preserves user preferences and match data appropriately
- Implements self-access exception for profile owners

## Configuration

### Permission Levels

```python
class ViewPermissionLevel(Enum):
    PUBLIC = "public"           # No PII access
    VOLUNTEER = "volunteer"     # Basic volunteer info only  
    COORDINATOR = "coordinator" # Branch-level coordination
    MANAGER = "manager"         # Full branch access
    ADMIN = "admin"            # System-wide access
```

### PII Field Types

```python
class PIIFieldType(Enum):
    EMAIL = "email"
    PHONE = "phone" 
    ADDRESS = "address"
    SSN = "ssn"
    DATE_OF_BIRTH = "date_of_birth"
    FULL_NAME = "full_name"
    MEDICAL_INFO = "medical_info"
    EMERGENCY_CONTACT = "emergency_contact"
    # ... and more
```

## Usage Examples

### Basic Data Masking

```python
from pii_redaction import pii_engine, UserContext, ViewPermissionLevel

# Sample volunteer data
volunteer_data = {
    'first_name': 'John',
    'last_name': 'Smith',
    'email': 'john.smith@email.com',
    'phone': '(513) 555-1234',
    'ssn': '123-45-6789'
}

# Create user context
public_user = UserContext(permission_level=ViewPermissionLevel.PUBLIC)

# Apply masking
masked_data = pii_engine.mask_data(volunteer_data, public_user)

print(masked_data)
# Output: {
#   'first_name': 'John',
#   'last_name': 'S***', 
#   'email': 'j***@email.com',
#   'phone': '(513) ***-****',
#   'ssn': '***'
# }
```

### FastAPI Integration

```python
from fastapi import Request
from pii_redaction import get_user_context_from_request, pii_engine

@app.get("/api/sensitive-data")
async def get_sensitive_data(request: Request):
    # Get user context from request
    user_context = get_user_context_from_request(request)
    
    # Fetch data
    data = get_volunteer_data()
    
    # Apply PII masking  
    masked_data = pii_engine.mask_data(data, user_context)
    
    return JSONResponse(content=masked_data)
```

### Custom PII Field Registration

```python
from pii_redaction import PIIField, PIIFieldType, ViewPermissionLevel

# Register custom PII field
custom_field = PIIField(
    field_name='employee_id',
    field_type=PIIFieldType.FULL_NAME,
    required_permission=ViewPermissionLevel.COORDINATOR,
    partial_show=2  # Show first 2 characters
)

pii_engine.register_pii_field(custom_field)
```

## Masking Patterns

### Email Masking
- **Public**: `j***@email.com` (first char + domain)
- **Volunteer+**: Full email visible

### Phone Masking  
- **Public**: `(513) ***-****` (area code only)
- **Volunteer+**: Full phone visible

### Name Masking
- **Public**: First name visible, last name as `S***`
- **Volunteer+**: Full name visible

### Address Masking
- **Public/Volunteer**: `***`
- **Coordinator+**: Full address visible

### SSN/Financial Masking
- **Public/Volunteer/Coordinator/Manager**: `***`
- **Admin**: Full SSN visible

## Testing

The system includes comprehensive tests covering:

- Permission level masking
- Nested data structures
- Text content PII detection
- Self-access scenarios
- Edge cases and error handling

Run tests:
```bash
cd 3/
python test_pii_redaction.py
```

## Security Considerations

### Data Flow
1. **Raw Data**: Original data is never logged or exposed
2. **Context Evaluation**: User permissions determined from request context
3. **Field-Level Masking**: Each field masked according to its sensitivity level
4. **Response**: Only masked data returned to client
5. **Audit**: Masking operations logged for compliance

### Best Practices
- Always use the masking system for any user-facing data
- Regularly review and update PII field configurations
- Monitor audit logs for unusual access patterns
- Test permission levels thoroughly during development

### Compliance Features
- **Audit Trail**: Complete logging of what data was masked for whom
- **Principle of Least Privilege**: Users see only what they need
- **Self-Access Rights**: Users maintain access to their own data
- **Configurable Policies**: Adjust masking rules per business requirements

## Performance Considerations

- **Lazy Loading**: Masking applied only when needed
- **Caching**: Field configurations cached for performance
- **Minimal Overhead**: Efficient regex patterns for text scanning
- **Memory Efficient**: Processes data structures in-place where possible

## Future Enhancements

### Planned Features
- **Role-Based Access Control**: Integration with organizational roles
- **Geographic Restrictions**: Mask data based on user location
- **Time-Based Access**: Temporary elevated permissions
- **Data Classification**: Automatic PII field detection
- **Encryption Integration**: Encrypt sensitive data at rest

### API Enhancements
- **Bulk Operations**: Efficient masking for large datasets
- **Streaming Support**: Mask data in streams for real-time processing
- **Custom Mask Patterns**: User-defined masking templates
- **Field-Level Permissions**: Granular field access controls

## Troubleshooting

### Common Issues

#### "PII redaction error" in logs
- Check that user context is properly initialized
- Verify field configurations are valid
- Ensure required permissions are correctly defined

#### Unexpected masking behavior
- Review field name mappings in `pii_config.py`
- Check permission level hierarchy
- Verify user context permissions

#### Performance issues
- Review regex patterns for efficiency
- Consider field-level caching for frequent operations
- Monitor audit log size and rotation

### Debug Mode
Enable detailed logging:
```python
import logging
logging.getLogger('pii_redaction').setLevel(logging.DEBUG)
```

## Support

For questions or issues with the PII redaction system:

1. Check this documentation
2. Review test cases for usage examples  
3. Examine audit logs for debugging information
4. Contact the development team with specific error messages

---

**Note**: This PII redaction system is designed for the YMCA Volunteer PathFinder application and may need customization for other use cases. Always test thoroughly in a development environment before deploying to production.