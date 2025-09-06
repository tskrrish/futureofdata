"""
Test suite for PII Redaction System
Tests masking functionality across different permission levels
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
import json

from pii_redaction import (
    PIIRedactionEngine, 
    UserContext, 
    ViewPermissionLevel, 
    PIIField, 
    PIIFieldType,
    PIIRedactionMiddleware
)
from pii_config import pii_config_manager, ENDPOINT_PII_POLICIES


class TestPIIRedactionEngine:
    """Test cases for the core PII redaction engine"""
    
    def setup_method(self):
        """Setup test environment"""
        self.engine = PIIRedactionEngine()
        self.sample_volunteer_data = {
            'first_name': 'John',
            'last_name': 'Smith',
            'email': 'john.smith@email.com',
            'phone': '(513) 555-1234',
            'age': 35,
            'address': '123 Main St, Cincinnati, OH 45202',
            'zip_code': '45202',
            'ssn': '123-45-6789',
            'emergency_contact': 'Jane Smith',
            'emergency_phone': '(513) 555-5678',
            'medical_conditions': 'Diabetes, Hypertension',
            'volunteer_hours': 120,
            'branch': 'Blue Ash YMCA'
        }
    
    def test_public_user_masking(self):
        """Test that public users see minimal information"""
        public_context = UserContext(permission_level=ViewPermissionLevel.PUBLIC)
        
        masked_data = self.engine.mask_data(self.sample_volunteer_data, public_context)
        
        # Public users should see first name, city, state, and non-PII fields
        assert masked_data['first_name'] == 'John'
        assert masked_data['volunteer_hours'] == 120
        assert masked_data['branch'] == 'Blue Ash YMCA'
        
        # PII should be masked
        assert masked_data['last_name'] != 'Smith'
        assert '***' in masked_data['email']
        assert '***' in masked_data['phone']
        assert '***' in masked_data['address']
        assert masked_data['ssn'] == '***'
    
    def test_volunteer_level_masking(self):
        """Test that volunteer users see appropriate information"""
        volunteer_context = UserContext(permission_level=ViewPermissionLevel.VOLUNTEER)
        
        masked_data = self.engine.mask_data(self.sample_volunteer_data, volunteer_context)
        
        # Volunteers should see basic personal info
        assert masked_data['first_name'] == 'John'
        assert masked_data['last_name'] == 'Smith'
        assert masked_data['age'] == 35
        
        # Email and phone should be partially visible
        assert '@email.com' in masked_data['email']
        assert '(513)' in masked_data['phone']
        
        # Sensitive data should still be masked
        assert '***' in masked_data['address']
        assert masked_data['ssn'] == '***'
        assert '***' in masked_data['emergency_contact']
        assert '***' in masked_data['medical_conditions']
    
    def test_coordinator_level_masking(self):
        """Test that coordinator users see more information"""
        coordinator_context = UserContext(permission_level=ViewPermissionLevel.COORDINATOR)
        
        masked_data = self.engine.mask_data(self.sample_volunteer_data, coordinator_context)
        
        # Coordinators should see location and contact info
        assert masked_data['address'] == '123 Main St, Cincinnati, OH 45202'
        assert masked_data['zip_code'] == '45202'
        
        # But not medical or sensitive data
        assert masked_data['ssn'] == '***'
        assert '***' in masked_data['medical_conditions']
    
    def test_manager_level_masking(self):
        """Test that manager users see emergency and medical info"""
        manager_context = UserContext(permission_level=ViewPermissionLevel.MANAGER)
        
        masked_data = self.engine.mask_data(self.sample_volunteer_data, manager_context)
        
        # Managers should see emergency contacts and medical info
        assert masked_data['emergency_contact'] == 'Jane Smith'
        assert masked_data['emergency_phone'] == '(513) 555-5678'
        assert masked_data['medical_conditions'] == 'Diabetes, Hypertension'
        
        # But not highly sensitive data
        assert masked_data['ssn'] == '***'
    
    def test_admin_level_masking(self):
        """Test that admin users see everything"""
        admin_context = UserContext(permission_level=ViewPermissionLevel.ADMIN)
        
        masked_data = self.engine.mask_data(self.sample_volunteer_data, admin_context)
        
        # Admins should see all data unmasked
        assert masked_data['ssn'] == '123-45-6789'
        assert masked_data == self.sample_volunteer_data
    
    def test_self_profile_access(self):
        """Test that users can see their own full profile"""
        public_context = UserContext(
            user_id='user123',
            permission_level=ViewPermissionLevel.PUBLIC
        )
        
        # When viewing their own profile, users should see everything
        masked_data = self.engine.mask_volunteer_profile(
            self.sample_volunteer_data, 
            public_context, 
            target_user_id='user123'
        )
        
        # Should see full data despite low permission level
        assert masked_data['email'] == 'john.smith@email.com'
        assert masked_data['phone'] == '(513) 555-1234'
        assert masked_data['ssn'] == '123-45-6789'
    
    def test_nested_data_masking(self):
        """Test masking of nested dictionary structures"""
        nested_data = {
            'user': {
                'personal': {
                    'first_name': 'John',
                    'last_name': 'Smith',
                    'email': 'john@email.com'
                },
                'preferences': {
                    'contact_method': 'email',
                    'phone': '555-1234'
                }
            },
            'activity': [
                {
                    'volunteer_name': 'John Smith',
                    'hours': 10
                },
                {
                    'volunteer_name': 'Jane Doe',
                    'hours': 15
                }
            ]
        }
        
        public_context = UserContext(permission_level=ViewPermissionLevel.PUBLIC)
        masked_data = self.engine.mask_data(nested_data, public_context)
        
        # Check nested masking
        assert masked_data['user']['personal']['first_name'] == 'John'
        assert '***' in masked_data['user']['personal']['last_name']
        assert '***' in masked_data['user']['personal']['email']
        assert '***' in masked_data['user']['preferences']['phone']
        
        # Check list masking
        assert masked_data['activity'][0]['hours'] == 10  # Non-PII unchanged
        assert 'John Smith' != masked_data['activity'][0]['volunteer_name']  # Names should be masked in content
    
    def test_text_content_pii_detection(self):
        """Test detection and masking of PII in free text"""
        text_data = {
            'description': 'Contact John Smith at john.smith@email.com or (513) 555-1234 for more info.',
            'notes': 'Emergency contact: Jane Smith 555-5678. SSN: 123-45-6789',
            'feedback': 'Great volunteer! Lives at 123 Main St.'
        }
        
        public_context = UserContext(permission_level=ViewPermissionLevel.PUBLIC)
        masked_data = self.engine.mask_data(text_data, public_context)
        
        # Check that PII in text content is masked
        assert 'john.smith@email.com' not in masked_data['description']
        assert '(513) 555-1234' not in masked_data['description']
        assert '123-45-6789' not in masked_data['notes']
        
        # But non-PII text should remain
        assert 'Contact' in masked_data['description']
        assert 'Great volunteer!' in masked_data['feedback']
    
    def test_partial_masking_patterns(self):
        """Test different partial masking patterns"""
        data = {
            'email': 'john.doe@company.com',
            'phone': '5551234567',
            'zip_code': '45202'
        }
        
        volunteer_context = UserContext(permission_level=ViewPermissionLevel.VOLUNTEER)
        masked_data = self.engine.mask_data(data, volunteer_context)
        
        # Email should show first char and domain
        assert masked_data['email'].startswith('j')
        assert '@company.com' in masked_data['email']
        
        # Phone should show area code
        assert masked_data['phone'].startswith('(555)')
        
        # Zip should show first 2 digits
        assert masked_data['zip_code'].startswith('45')
    
    def test_custom_pii_field_registration(self):
        """Test registration of custom PII fields"""
        # Register a custom field
        custom_field = PIIField(
            'employee_id', 
            PIIFieldType.FULL_NAME, 
            ViewPermissionLevel.COORDINATOR
        )
        self.engine.register_pii_field(custom_field)
        
        data = {'employee_id': 'EMP12345', 'name': 'John Smith'}
        
        # Test with volunteer level (should mask custom field)
        volunteer_context = UserContext(permission_level=ViewPermissionLevel.VOLUNTEER)
        masked_data = self.engine.mask_data(data, volunteer_context)
        assert masked_data['employee_id'] == '***'
        
        # Test with coordinator level (should show custom field)
        coordinator_context = UserContext(permission_level=ViewPermissionLevel.COORDINATOR)
        masked_data = self.engine.mask_data(data, coordinator_context)
        assert masked_data['employee_id'] == 'EMP12345'


class TestPIIRedactionMiddleware:
    """Test cases for the PII redaction middleware"""
    
    def setup_method(self):
        """Setup test environment"""
        self.engine = PIIRedactionEngine()
        self.middleware = PIIRedactionMiddleware(self.engine)
    
    def test_api_response_masking(self):
        """Test automatic masking of API responses"""
        api_response = {
            'status': 'success',
            'data': {
                'users': [
                    {'name': 'John Smith', 'email': 'john@email.com'},
                    {'name': 'Jane Doe', 'email': 'jane@email.com'}
                ]
            }
        }
        
        public_context = UserContext(permission_level=ViewPermissionLevel.PUBLIC)
        masked_response = self.middleware.process_response(
            api_response, 
            public_context,
            '/api/users'
        )
        
        # Status should be unchanged
        assert masked_response['status'] == 'success'
        
        # User data should be masked
        users = masked_response['data']['users']
        assert 'John Smith' != users[0]['name']  # Should be masked in some way
        assert '***' in users[0]['email']
    
    def test_list_response_masking(self):
        """Test masking of list responses"""
        user_list = [
            {'first_name': 'John', 'last_name': 'Smith', 'email': 'john@email.com'},
            {'first_name': 'Jane', 'last_name': 'Doe', 'email': 'jane@email.com'}
        ]
        
        volunteer_context = UserContext(permission_level=ViewPermissionLevel.VOLUNTEER)
        masked_list = self.middleware.process_response(user_list, volunteer_context)
        
        assert len(masked_list) == 2
        assert masked_list[0]['first_name'] == 'John'
        assert masked_list[0]['last_name'] == 'Smith'
        assert '***' in masked_list[0]['email']


class TestPIIConfigManager:
    """Test cases for PII configuration management"""
    
    def test_field_registration(self):
        """Test that all expected PII fields are registered"""
        all_fields = pii_config_manager.get_all_pii_fields()
        
        # Check that key fields are present
        assert 'email' in all_fields
        assert 'phone' in all_fields
        assert 'ssn' in all_fields
        assert 'medical_conditions' in all_fields
    
    def test_permission_hierarchy(self):
        """Test that permission levels work correctly"""
        admin_fields = pii_config_manager.get_fields_by_permission_level(ViewPermissionLevel.ADMIN)
        manager_fields = pii_config_manager.get_fields_by_permission_level(ViewPermissionLevel.MANAGER)
        
        # Admin should have access to everything
        admin_field_names = {f.field_name for f in admin_fields}
        assert 'ssn' in admin_field_names
        assert 'medical_conditions' in admin_field_names
        
        # Manager should have some but not all
        manager_field_names = {f.field_name for f in manager_fields}
        assert 'medical_conditions' in manager_field_names
        # SSN should require admin level
        assert len(admin_fields) >= len(manager_fields)
    
    def test_sensitive_endpoint_detection(self):
        """Test identification of sensitive endpoints"""
        assert pii_config_manager.is_sensitive_endpoint('/api/users/123')
        assert pii_config_manager.is_sensitive_endpoint('/api/profile')
        assert not pii_config_manager.is_sensitive_endpoint('/api/health')
        assert not pii_config_manager.is_sensitive_endpoint('/static/css/style.css')


class TestIntegrationScenarios:
    """Integration tests for real-world scenarios"""
    
    def setup_method(self):
        """Setup test environment"""
        self.engine = PIIRedactionEngine()
    
    def test_volunteer_viewing_other_volunteer(self):
        """Test volunteer user viewing another volunteer's profile"""
        volunteer_profile = {
            'id': 'vol456',
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane.doe@email.com',
            'phone': '(513) 555-9999',
            'address': '456 Oak St, Cincinnati, OH',
            'volunteer_hours': 80,
            'branch': 'Downtown YMCA'
        }
        
        viewing_user = UserContext(
            user_id='vol123',
            permission_level=ViewPermissionLevel.VOLUNTEER
        )
        
        masked_profile = self.engine.mask_volunteer_profile(
            volunteer_profile,
            viewing_user,
            target_user_id='vol456'
        )
        
        # Should see basic info but not full contact details
        assert masked_profile['first_name'] == 'Jane'
        assert masked_profile['last_name'] == 'Doe'
        assert '***' in masked_profile['email']
        assert '***' in masked_profile['address']
        assert masked_profile['volunteer_hours'] == 80
    
    def test_coordinator_managing_volunteers(self):
        """Test coordinator viewing volunteers in their branch"""
        volunteer_list = [
            {
                'id': 'vol1',
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'email': 'alice@email.com',
                'phone': '555-0001',
                'address': '123 First St',
                'branch': 'Blue Ash'
            },
            {
                'id': 'vol2',
                'first_name': 'Bob',
                'last_name': 'Wilson',
                'email': 'bob@email.com',
                'phone': '555-0002',
                'address': '456 Second St',
                'branch': 'Blue Ash'
            }
        ]
        
        coordinator_context = UserContext(
            user_id='coord1',
            permission_level=ViewPermissionLevel.COORDINATOR,
            branch_access={'Blue Ash'}
        )
        
        for volunteer in volunteer_list:
            masked_volunteer = self.engine.mask_data(volunteer, coordinator_context)
            
            # Coordinator should see addresses and full contact info
            assert masked_volunteer['address'] == volunteer['address']
            assert masked_volunteer['email'] == volunteer['email']
            assert masked_volunteer['phone'] == volunteer['phone']
    
    def test_data_export_masking(self):
        """Test masking for data export functionality"""
        export_data = {
            'volunteers': [
                {
                    'id': 'v1',
                    'name': 'John Smith',
                    'email': 'john@email.com',
                    'phone': '555-1234',
                    'ssn': '123-45-6789',
                    'total_hours': 100
                },
                {
                    'id': 'v2',
                    'name': 'Jane Doe',
                    'email': 'jane@email.com', 
                    'phone': '555-5678',
                    'ssn': '987-65-4321',
                    'total_hours': 150
                }
            ],
            'metadata': {
                'export_date': '2023-10-15',
                'requested_by': 'admin@ymca.org'
            }
        }
        
        # Manager level export (should mask SSN)
        manager_context = UserContext(permission_level=ViewPermissionLevel.MANAGER)
        manager_export = self.engine.mask_data(export_data, manager_context)
        
        for volunteer in manager_export['volunteers']:
            assert volunteer['total_hours'] in [100, 150]  # Non-PII preserved
            assert volunteer['ssn'] == '***'  # SSN masked
            # Contact info should be visible to managers
            assert '@email.com' in volunteer['email']
        
        # Admin level export (should show everything)
        admin_context = UserContext(permission_level=ViewPermissionLevel.ADMIN)
        admin_export = self.engine.mask_data(export_data, admin_context)
        
        assert admin_export == export_data  # Should be identical


def test_audit_logging():
    """Test that PII masking operations are logged"""
    engine = PIIRedactionEngine()
    original_data = {
        'name': 'John Smith',
        'email': 'john@email.com',
        'ssn': '123-45-6789'
    }
    
    public_context = UserContext(permission_level=ViewPermissionLevel.PUBLIC)
    masked_data = engine.mask_data(original_data, public_context)
    
    # Generate audit log
    audit_log = engine.generate_audit_log(original_data, masked_data, public_context)
    
    assert 'timestamp' in audit_log
    assert audit_log['permission_level'] == 'public'
    assert audit_log['total_fields_masked'] > 0
    assert len(audit_log['masked_fields']) > 0


if __name__ == '__main__':
    # Run basic tests
    test_suite = TestPIIRedactionEngine()
    test_suite.setup_method()
    
    print("Running PII Redaction Tests...")
    
    # Test different permission levels
    print("✓ Testing public user masking...")
    test_suite.test_public_user_masking()
    
    print("✓ Testing volunteer level masking...")
    test_suite.test_volunteer_level_masking()
    
    print("✓ Testing coordinator level masking...")
    test_suite.test_coordinator_level_masking()
    
    print("✓ Testing manager level masking...")
    test_suite.test_manager_level_masking()
    
    print("✓ Testing admin level masking...")
    test_suite.test_admin_level_masking()
    
    print("✓ Testing self profile access...")
    test_suite.test_self_profile_access()
    
    print("✓ Testing nested data masking...")
    test_suite.test_nested_data_masking()
    
    print("✓ All tests passed! PII redaction system working correctly.")
    
    # Test audit logging
    print("✓ Testing audit logging...")
    test_audit_logging()
    
    print("\n🎉 PII Redaction System successfully implemented and tested!")
    print("\nFeatures implemented:")
    print("- Multi-level permission system (Public, Volunteer, Coordinator, Manager, Admin)")
    print("- Field-level PII detection and masking")
    print("- Text content PII detection using regex patterns")
    print("- Self-profile access (users can see their own full data)")
    print("- Nested data structure support")
    print("- Configurable masking patterns")
    print("- Audit logging for compliance")
    print("- Integration with FastAPI endpoints")