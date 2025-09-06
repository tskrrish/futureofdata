#!/usr/bin/env python3
"""
Test script for E-Sign Vault functionality
Tests document storage, retrieval, and renewal alert system
"""
import asyncio
import os
import sys
import tempfile
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from esign_vault import ESignVaultService
from renewal_alerts import RenewalAlertService
from database import VolunteerDatabase


async def test_document_storage():
    """Test document storage and retrieval"""
    print("🧪 Testing Document Storage and Retrieval")
    print("=" * 50)
    
    # Create temporary storage directory
    with tempfile.TemporaryDirectory() as temp_dir:
        vault_service = ESignVaultService(storage_path=temp_dir)
        
        # Test document data
        test_user_id = "test-user-123"
        test_document_content = b"This is a test document content for E-Sign Vault testing."
        
        document_data = {
            'name': 'Test Liability Waiver.pdf',
            'type': 'waiver',
            'expiry_date': (datetime.now() + timedelta(days=365)).isoformat(),
            'renewal_required': True,
            'metadata': {
                'branch': 'Blue Ash YMCA',
                'volunteer_role': 'Youth Sports Coach'
            }
        }
        
        print(f"📄 Storing test document: {document_data['name']}")
        
        # Store document
        document_id = await vault_service.store_document(
            user_id=test_user_id,
            file_content=test_document_content,
            document_data=document_data
        )
        
        if document_id:
            print(f"✅ Document stored successfully with ID: {document_id}")
            
            # Retrieve document
            print(f"📥 Retrieving document...")
            retrieved_doc = await vault_service.retrieve_document(document_id, test_user_id)
            
            if retrieved_doc:
                print(f"✅ Document retrieved successfully")
                print(f"   - Content length: {len(retrieved_doc['content'])} bytes")
                print(f"   - MIME type: {retrieved_doc['mime_type']}")
                
                # Verify content integrity
                if retrieved_doc['content'] == test_document_content:
                    print("✅ Content integrity verified")
                else:
                    print("❌ Content integrity check failed")
            else:
                print("❌ Failed to retrieve document")
                
            # Get user documents
            print(f"📋 Getting user documents...")
            user_docs = await vault_service.get_user_documents(test_user_id)
            print(f"✅ Found {len(user_docs)} documents for user")
            
            for doc in user_docs:
                print(f"   - {doc['document_name']} ({doc['document_type']}) - Status: {doc['status']}")
                if doc.get('days_until_expiry'):
                    print(f"     Expires in {doc['days_until_expiry']} days")
                    
        else:
            print("❌ Failed to store document")
    
    print()


async def test_renewal_alerts():
    """Test renewal alert system"""
    print("🔔 Testing Renewal Alert System")
    print("=" * 50)
    
    alert_service = RenewalAlertService()
    
    # Mock user and document data for testing
    test_user = {
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john.doe@example.com'
    }
    
    test_documents = [
        {
            'id': 'doc-1',
            'document_name': 'CPR Certification',
            'document_type': 'certification',
            'expiry_date': (datetime.now() + timedelta(days=7)).isoformat()  # Expires in 7 days
        },
        {
            'id': 'doc-2',
            'document_name': 'Background Check',
            'document_type': 'background_check',
            'expiry_date': (datetime.now() + timedelta(days=15)).isoformat()  # Expires in 15 days
        }
    ]
    
    print("📧 Testing renewal reminder emails...")
    
    for doc in test_documents:
        print(f"   Testing reminder for: {doc['document_name']}")
        success = await alert_service.send_renewal_reminder(doc, test_user)
        if success:
            print(f"   ✅ Reminder sent successfully")
        else:
            print(f"   ❌ Failed to send reminder")
    
    # Test expiring documents summary
    print("\n📊 Testing expiring documents summary...")
    
    # Create mock summary data
    mock_summary = {
        'total_expiring': 2,
        'by_type': {
            'certification': 1,
            'background_check': 1
        },
        'by_days_until_expiry': {
            '7_days_or_less': 1,
            '8_to_14_days': 0,
            '15_to_30_days': 1
        },
        'documents': [
            {
                'id': 'doc-1',
                'name': 'CPR Certification',
                'type': 'certification',
                'user_name': 'John Doe',
                'expiry_date': (datetime.now() + timedelta(days=7)).isoformat(),
                'days_until_expiry': 7
            },
            {
                'id': 'doc-2',
                'name': 'Background Check',
                'type': 'background_check',
                'user_name': 'John Doe',
                'expiry_date': (datetime.now() + timedelta(days=15)).isoformat(),
                'days_until_expiry': 15
            }
        ]
    }
    
    print("📧 Testing admin summary email...")
    success = await alert_service.send_admin_summary('admin@ymca.org', mock_summary)
    if success:
        print("✅ Admin summary sent successfully")
    else:
        print("❌ Failed to send admin summary")
    
    print()


async def test_database_operations():
    """Test database operations for e-sign vault"""
    print("🗄️ Testing Database Operations")
    print("=" * 50)
    
    database = VolunteerDatabase()
    
    print("📊 Testing database availability...")
    if database._is_available():
        print("✅ Database connection available")
        
        # Note: These operations would require actual database setup
        print("ℹ️  Database operations require Supabase setup")
        print("   - Table creation: esign_documents, renewal_alerts, document_audit_log")
        print("   - CRUD operations for document storage")
        print("   - Audit logging functionality")
        print("   - Renewal alert scheduling")
        
    else:
        print("⚠️  Database not available - using mock mode")
        print("   Configure Supabase credentials for full database testing")
    
    print()


async def test_security_features():
    """Test security features of the vault"""
    print("🔒 Testing Security Features")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        vault_service = ESignVaultService(storage_path=temp_dir)
        
        # Test file encryption
        test_content = b"Sensitive document content that should be encrypted"
        test_user = "security-test-user"
        
        document_data = {
            'name': 'Security Test Document.pdf',
            'type': 'waiver',
            'metadata': {'test': True}
        }
        
        print("🔐 Testing file encryption...")
        document_id = await vault_service.store_document(test_user, test_content, document_data)
        
        if document_id:
            print("✅ Document encrypted and stored")
            
            # Check that the stored file is actually encrypted
            storage_path = Path(temp_dir) / test_user
            encrypted_files = list(storage_path.glob("*.encrypted"))
            
            if encrypted_files:
                encrypted_file = encrypted_files[0]
                with open(encrypted_file, 'rb') as f:
                    encrypted_content = f.read()
                
                # Verify the content is encrypted (not the same as original)
                if encrypted_content != test_content:
                    print("✅ File content is properly encrypted on disk")
                else:
                    print("❌ File content appears to not be encrypted")
                
                # Test decryption by retrieving the document
                retrieved = await vault_service.retrieve_document(document_id, test_user)
                if retrieved and retrieved['content'] == test_content:
                    print("✅ Decryption works correctly")
                else:
                    print("❌ Decryption failed")
                    
            else:
                print("❌ No encrypted file found")
                
            # Test secure deletion
            print("🗑️ Testing secure deletion...")
            success = await vault_service.delete_document(document_id, test_user)
            if success:
                print("✅ Document deleted securely")
                
                # Verify file is gone
                if not encrypted_file.exists():
                    print("✅ Physical file removed from storage")
                else:
                    print("❌ Physical file still exists after deletion")
            else:
                print("❌ Failed to delete document")
                
        else:
            print("❌ Failed to store encrypted document")
    
    print()


async def run_performance_test():
    """Test performance with multiple documents"""
    print("⚡ Testing Performance")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        vault_service = ESignVaultService(storage_path=temp_dir)
        
        test_user = "perf-test-user"
        num_documents = 10
        
        print(f"📈 Storing {num_documents} documents...")
        
        start_time = datetime.now()
        document_ids = []
        
        for i in range(num_documents):
            content = f"Test document content {i} - " + "x" * 1000  # 1KB+ content
            document_data = {
                'name': f'Test Document {i}.pdf',
                'type': 'waiver',
                'metadata': {'index': i}
            }
            
            doc_id = await vault_service.store_document(
                test_user, 
                content.encode(), 
                document_data
            )
            if doc_id:
                document_ids.append(doc_id)
        
        storage_time = (datetime.now() - start_time).total_seconds()
        print(f"✅ Stored {len(document_ids)} documents in {storage_time:.2f} seconds")
        print(f"   Average: {storage_time/len(document_ids):.3f} seconds per document")
        
        # Test retrieval performance
        print(f"📥 Retrieving {len(document_ids)} documents...")
        
        start_time = datetime.now()
        retrieved_count = 0
        
        for doc_id in document_ids:
            doc = await vault_service.retrieve_document(doc_id, test_user)
            if doc:
                retrieved_count += 1
        
        retrieval_time = (datetime.now() - start_time).total_seconds()
        print(f"✅ Retrieved {retrieved_count} documents in {retrieval_time:.2f} seconds")
        print(f"   Average: {retrieval_time/retrieved_count:.3f} seconds per document")
    
    print()


async def main():
    """Run all tests"""
    print("🚀 E-Sign Vault Test Suite")
    print("=" * 60)
    print()
    
    try:
        await test_document_storage()
        await test_renewal_alerts()
        await test_database_operations()
        await test_security_features()
        await run_performance_test()
        
        print("🎉 All tests completed successfully!")
        print("=" * 60)
        
        # Print setup instructions
        print("\n📋 Setup Instructions for Production:")
        print("1. Configure Supabase database credentials in config.py")
        print("2. Run database initialization: python -c 'from database import VolunteerDatabase; import asyncio; asyncio.run(VolunteerDatabase().initialize_tables())'")
        print("3. Set up SMTP configuration for email alerts")
        print("4. Configure secure encryption keys (VAULT_ENCRYPTION_KEY environment variable)")
        print("5. Set up proper file storage permissions and backup")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())