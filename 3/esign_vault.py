"""
E-Sign Vault Service for Secure Document Storage
Handles document encryption, storage, and retrieval with renewal alerts
"""
import hashlib
import uuid
import os
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, BinaryIO
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import asyncio
import aiofiles
from pathlib import Path
import mimetypes
import logging

from database import VolunteerDatabase

logger = logging.getLogger(__name__)

class ESignVaultService:
    def __init__(self, storage_path: str = "vault_storage", encryption_key: str = None):
        """Initialize the E-Sign Vault Service"""
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.database = VolunteerDatabase()
        
        # Initialize encryption
        if encryption_key:
            self.encryption_key = encryption_key.encode()
        else:
            self.encryption_key = os.environ.get('VAULT_ENCRYPTION_KEY', 'default-dev-key-change-in-production').encode()
        
        self.fernet = self._initialize_encryption()
    
    def _initialize_encryption(self) -> Fernet:
        """Initialize Fernet encryption with PBKDF2 key derivation"""
        salt = b'vault_salt_2024'  # In production, use a random salt stored securely
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.encryption_key))
        return Fernet(key)
    
    def _calculate_file_hash(self, file_content: bytes) -> str:
        """Calculate SHA-256 hash of file content"""
        return hashlib.sha256(file_content).hexdigest()
    
    async def store_document(self, user_id: str, file_content: bytes, document_data: Dict[str, Any]) -> Optional[str]:
        """Store a document securely with encryption"""
        try:
            # Generate unique document ID
            document_id = str(uuid.uuid4())
            
            # Calculate file hash for integrity
            file_hash = self._calculate_file_hash(file_content)
            
            # Encrypt file content
            encrypted_content = self.fernet.encrypt(file_content)
            
            # Create storage path
            user_dir = self.storage_path / user_id
            user_dir.mkdir(exist_ok=True)
            
            # Store encrypted file
            file_path = user_dir / f"{document_id}.encrypted"
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(encrypted_content)
            
            # Prepare document metadata
            document_record = {
                'name': document_data.get('name', ''),
                'type': document_data.get('type', ''),
                'file_url': str(file_path),
                'file_hash': file_hash,
                'file_size': len(file_content),
                'mime_type': document_data.get('mime_type', 'application/octet-stream'),
                'status': 'active',
                'signed_date': document_data.get('signed_date', datetime.now().isoformat()),
                'expiry_date': document_data.get('expiry_date'),
                'renewal_required': document_data.get('renewal_required', False),
                'metadata': document_data.get('metadata', {})
            }
            
            # Store in database
            stored_id = await self.database.store_document(user_id, document_record)
            
            if stored_id:
                # Schedule renewal alerts if expiry date is set
                if document_record.get('expiry_date'):
                    await self._schedule_renewal_alerts(stored_id, user_id, document_record['expiry_date'])
                
                logger.info(f"Document stored successfully: {stored_id}")
                return stored_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error storing document: {e}")
            return None
    
    async def retrieve_document(self, document_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve and decrypt a document"""
        try:
            # Get document metadata from database
            doc_info = await self.database.get_document_by_id(document_id, user_id)
            if not doc_info:
                return None
            
            # Read encrypted file
            file_path = Path(doc_info['file_url'])
            if not file_path.exists():
                logger.error(f"Document file not found: {file_path}")
                return None
            
            async with aiofiles.open(file_path, 'rb') as f:
                encrypted_content = await f.read()
            
            # Decrypt content
            decrypted_content = self.fernet.decrypt(encrypted_content)
            
            # Verify file integrity
            file_hash = self._calculate_file_hash(decrypted_content)
            if file_hash != doc_info.get('file_hash'):
                logger.error(f"File integrity check failed for document {document_id}")
                return None
            
            # Log document access
            await self.database.log_document_action(document_id, user_id, 'downloaded')
            
            return {
                'document_id': document_id,
                'content': decrypted_content,
                'metadata': doc_info,
                'mime_type': doc_info.get('mime_type', 'application/octet-stream')
            }
            
        except Exception as e:
            logger.error(f"Error retrieving document: {e}")
            return None
    
    async def get_user_documents(self, user_id: str, include_expired: bool = False) -> List[Dict[str, Any]]:
        """Get all documents for a user"""
        try:
            documents = await self.database.get_user_documents(user_id)
            
            if not include_expired:
                # Filter out expired documents
                current_date = datetime.now()
                documents = [
                    doc for doc in documents 
                    if not doc.get('expiry_date') or 
                    datetime.fromisoformat(doc['expiry_date'].replace('Z', '+00:00')) > current_date
                ]
            
            # Add status information
            for doc in documents:
                doc['is_expired'] = self._is_document_expired(doc)
                doc['days_until_expiry'] = self._calculate_days_until_expiry(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error getting user documents: {e}")
            return []
    
    async def update_document_status(self, document_id: str, status: str, user_id: str) -> bool:
        """Update document status"""
        return await self.database.update_document_status(document_id, status, user_id)
    
    async def delete_document(self, document_id: str, user_id: str) -> bool:
        """Securely delete a document"""
        try:
            # Get document info
            doc_info = await self.database.get_document_by_id(document_id, user_id)
            if not doc_info:
                return False
            
            # Delete physical file
            file_path = Path(doc_info['file_url'])
            if file_path.exists():
                # Secure deletion - overwrite file before deletion
                file_size = file_path.stat().st_size
                with open(file_path, 'rb+') as f:
                    f.write(os.urandom(file_size))
                file_path.unlink()
            
            # Update status in database instead of deleting record (for audit)
            await self.database.update_document_status(document_id, 'deleted', user_id)
            
            # Log the deletion
            await self.database.log_document_action(document_id, user_id, 'deleted')
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False
    
    def _is_document_expired(self, document: Dict[str, Any]) -> bool:
        """Check if document is expired"""
        if not document.get('expiry_date'):
            return False
        
        expiry_date = datetime.fromisoformat(document['expiry_date'].replace('Z', '+00:00'))
        return datetime.now() > expiry_date
    
    def _calculate_days_until_expiry(self, document: Dict[str, Any]) -> Optional[int]:
        """Calculate days until document expires"""
        if not document.get('expiry_date'):
            return None
        
        expiry_date = datetime.fromisoformat(document['expiry_date'].replace('Z', '+00:00'))
        days_until = (expiry_date - datetime.now()).days
        return max(0, days_until)
    
    async def _schedule_renewal_alerts(self, document_id: str, user_id: str, expiry_date: str) -> None:
        """Schedule renewal alerts for a document"""
        try:
            expiry_dt = datetime.fromisoformat(expiry_date.replace('Z', '+00:00'))
            
            # Schedule alerts at 30, 14, and 7 days before expiry
            alert_days = [30, 14, 7]
            
            for days_before in alert_days:
                alert_date = expiry_dt - timedelta(days=days_before)
                
                # Only schedule if alert date is in the future
                if alert_date > datetime.now():
                    alert_data = {
                        'type': 'email',
                        'alert_date': alert_date.isoformat(),
                        'days_before': days_before,
                        'message': f'Your document expires in {days_before} days. Please renew it to maintain access.'
                    }
                    
                    await self.database.create_renewal_alert(document_id, user_id, alert_data)
            
        except Exception as e:
            logger.error(f"Error scheduling renewal alerts: {e}")
    
    async def process_renewal_alerts(self) -> int:
        """Process pending renewal alerts"""
        try:
            alerts = await self.database.get_pending_alerts()
            processed_count = 0
            
            for alert in alerts:
                try:
                    # In a real implementation, you would send actual emails/SMS here
                    # For now, we'll just mark as sent and log
                    logger.info(f"Processing renewal alert for user {alert['user_id']}: {alert['message_content']}")
                    
                    await self.database.mark_alert_sent(alert['id'])
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing alert {alert['id']}: {e}")
            
            return processed_count
            
        except Exception as e:
            logger.error(f"Error processing renewal alerts: {e}")
            return 0
    
    async def get_expiring_documents_summary(self, days_ahead: int = 30) -> Dict[str, Any]:
        """Get summary of documents expiring soon"""
        try:
            expiring_docs = await self.database.get_expiring_documents(days_ahead)
            
            summary = {
                'total_expiring': len(expiring_docs),
                'by_type': {},
                'by_days_until_expiry': {},
                'documents': []
            }
            
            for doc in expiring_docs:
                doc_type = doc.get('document_type', 'unknown')
                summary['by_type'][doc_type] = summary['by_type'].get(doc_type, 0) + 1
                
                # Calculate days until expiry
                if doc.get('expiry_date'):
                    expiry_date = datetime.fromisoformat(doc['expiry_date'].replace('Z', '+00:00'))
                    days_until = (expiry_date - datetime.now()).days
                    
                    if days_until <= 7:
                        category = '7_days_or_less'
                    elif days_until <= 14:
                        category = '8_to_14_days'
                    else:
                        category = '15_to_30_days'
                    
                    summary['by_days_until_expiry'][category] = summary['by_days_until_expiry'].get(category, 0) + 1
                
                summary['documents'].append({
                    'id': doc['id'],
                    'name': doc['document_name'],
                    'type': doc['document_type'],
                    'user_name': f"{doc.get('users', {}).get('first_name', '')} {doc.get('users', {}).get('last_name', '')}".strip(),
                    'expiry_date': doc['expiry_date'],
                    'days_until_expiry': days_until if doc.get('expiry_date') else None
                })
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting expiring documents summary: {e}")
            return {'total_expiring': 0, 'by_type': {}, 'by_days_until_expiry': {}, 'documents': []}