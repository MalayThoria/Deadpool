"""
Data Protection and Security Module for Prescription Integration
Implements encryption, data validation, and secure storage for health data
"""

import hashlib
import hmac
import secrets
import base64
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)

class DataEncryption:
    """Handles encryption and decryption of sensitive health data"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        if encryption_key:
            self.key = encryption_key.encode()
        else:
            self.key = Fernet.generate_key()
        self.cipher = Fernet(self.key)
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        try:
            encrypted_data = self.cipher.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.cipher.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def encrypt_json(self, data: Dict[str, Any]) -> str:
        """Encrypt JSON data"""
        json_string = json.dumps(data, separators=(',', ':'))
        return self.encrypt_data(json_string)
    
    def decrypt_json(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt JSON data"""
        decrypted_string = self.decrypt_data(encrypted_data)
        return json.loads(decrypted_string)

class DataValidator:
    """Validates and sanitizes health data"""
    
    @staticmethod
    def validate_prescription_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate prescription data structure and content"""
        required_fields = ['medications', 'conditions']
        validated_data = {}
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate medications
        if not isinstance(data['medications'], list):
            raise ValueError("Medications must be a list")
        
        validated_medications = []
        for med in data['medications']:
            if not isinstance(med, dict):
                continue
            
            validated_med = {
                'name': DataValidator.sanitize_string(med.get('name', '')),
                'dosage': DataValidator.sanitize_string(med.get('dosage', '')),
                'frequency': DataValidator.sanitize_string(med.get('frequency', '')),
                'duration': DataValidator.sanitize_string(med.get('duration', '')),
                'instructions': DataValidator.sanitize_string(med.get('instructions', ''))
            }
            
            if validated_med['name']:  # Only include if name is present
                validated_medications.append(validated_med)
        
        validated_data['medications'] = validated_medications
        
        # Validate conditions
        if not isinstance(data['conditions'], list):
            raise ValueError("Conditions must be a list")
        
        validated_conditions = [
            DataValidator.sanitize_string(condition) 
            for condition in data['conditions'] 
            if isinstance(condition, str) and condition.strip()
        ]
        validated_data['conditions'] = validated_conditions
        
        # Validate optional fields
        if 'doctor_info' in data and isinstance(data['doctor_info'], dict):
            validated_data['doctor_info'] = {
                'name': DataValidator.sanitize_string(data['doctor_info'].get('name', '')),
                'specialty': DataValidator.sanitize_string(data['doctor_info'].get('specialty', '')),
                'contact': DataValidator.sanitize_string(data['doctor_info'].get('contact', ''))
            }
        
        if 'prescription_date' in data:
            validated_data['prescription_date'] = data['prescription_date']
        
        if 'confidence_score' in data:
            score = data['confidence_score']
            if isinstance(score, (int, float)) and 0 <= score <= 1:
                validated_data['confidence_score'] = score
        
        return validated_data
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 500) -> str:
        """Sanitize string input to prevent injection attacks"""
        if not isinstance(value, str):
            return ""
        
        # Remove potentially dangerous characters
        sanitized = value.strip()
        
        # Remove HTML tags and script content
        import re
        sanitized = re.sub(r'<[^>]*>', '', sanitized)
        sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'on\w+\s*=', '', sanitized, flags=re.IGNORECASE)
        
        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized
    
    @staticmethod
    def validate_user_id(user_id: Any) -> int:
        """Validate user ID"""
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("Invalid user ID")
        return user_id

class SecureStorage:
    """Handles secure storage of sensitive data"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        self.encryptor = DataEncryption(encryption_key)
    
    def store_prescription_securely(self, prescription_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store prescription data with encryption"""
        # Validate data first
        validated_data = DataValidator.validate_prescription_data(prescription_data)
        
        # Encrypt sensitive fields
        secure_data = validated_data.copy()
        
        # Encrypt medication details
        if 'medications' in secure_data:
            encrypted_medications = []
            for med in secure_data['medications']:
                encrypted_med = med.copy()
                # Encrypt sensitive medication info
                if 'instructions' in encrypted_med:
                    encrypted_med['instructions'] = self.encryptor.encrypt_data(
                        encrypted_med['instructions']
                    )
                encrypted_medications.append(encrypted_med)
            secure_data['medications'] = encrypted_medications
        
        # Encrypt doctor info if present
        if 'doctor_info' in secure_data and secure_data['doctor_info']:
            secure_data['doctor_info'] = self.encryptor.encrypt_json(
                secure_data['doctor_info']
            )
        
        return secure_data
    
    def retrieve_prescription_securely(self, stored_data: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve and decrypt prescription data"""
        decrypted_data = stored_data.copy()
        
        # Decrypt medication instructions
        if 'medications' in decrypted_data:
            decrypted_medications = []
            for med in decrypted_data['medications']:
                decrypted_med = med.copy()
                if 'instructions' in decrypted_med and decrypted_med['instructions']:
                    try:
                        decrypted_med['instructions'] = self.encryptor.decrypt_data(
                            decrypted_med['instructions']
                        )
                    except Exception as e:
                        logger.warning(f"Failed to decrypt medication instructions: {e}")
                        decrypted_med['instructions'] = "Instructions unavailable"
                decrypted_medications.append(decrypted_med)
            decrypted_data['medications'] = decrypted_medications
        
        # Decrypt doctor info
        if 'doctor_info' in decrypted_data and decrypted_data['doctor_info']:
            try:
                decrypted_data['doctor_info'] = self.encryptor.decrypt_json(
                    decrypted_data['doctor_info']
                )
            except Exception as e:
                logger.warning(f"Failed to decrypt doctor info: {e}")
                decrypted_data['doctor_info'] = None
        
        return decrypted_data

class AccessControl:
    """Manages access control and audit logging"""
    
    @staticmethod
    def log_data_access(user_id: int, action: str, data_type: str, 
                       resource_id: Optional[int] = None, 
                       additional_info: Optional[Dict[str, Any]] = None):
        """Log data access for audit purposes"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'action': action,
            'data_type': data_type,
            'resource_id': resource_id,
            'additional_info': additional_info or {}
        }
        
        logger.info(f"Data access: {json.dumps(log_entry)}")
    
    @staticmethod
    def verify_data_integrity(data: Dict[str, Any], expected_hash: str) -> bool:
        """Verify data integrity using hash comparison"""
        try:
            data_string = json.dumps(data, sort_keys=True, separators=(',', ':'))
            calculated_hash = hashlib.sha256(data_string.encode()).hexdigest()
            return hmac.compare_digest(expected_hash, calculated_hash)
        except Exception as e:
            logger.error(f"Data integrity verification failed: {e}")
            return False
    
    @staticmethod
    def generate_data_hash(data: Dict[str, Any]) -> str:
        """Generate hash for data integrity verification"""
        data_string = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(data_string.encode()).hexdigest()

class WebSocketSecurity:
    """Security measures for WebSocket connections"""
    
    @staticmethod
    def validate_websocket_token(token: str) -> bool:
        """Validate WebSocket authentication token"""
        # This should integrate with your existing JWT validation
        # For now, basic validation
        if not token or len(token) < 10:
            return False
        return True
    
    @staticmethod
    def sanitize_websocket_message(message: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize WebSocket messages to prevent XSS and injection"""
        sanitized = {}
        
        for key, value in message.items():
            if isinstance(value, str):
                sanitized[key] = DataValidator.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[key] = WebSocketSecurity.sanitize_websocket_message(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    DataValidator.sanitize_string(item) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        
        return sanitized
    
    @staticmethod
    def rate_limit_check(user_id: int, action: str, window_minutes: int = 5, 
                        max_requests: int = 100) -> bool:
        """Basic rate limiting for WebSocket actions"""
        # This is a simplified implementation
        # In production, use Redis or similar for distributed rate limiting
        current_time = datetime.utcnow()
        # Implementation would track requests per user per time window
        return True  # Placeholder

# Security configuration
SECURITY_CONFIG = {
    'encryption_enabled': True,
    'data_validation_strict': True,
    'audit_logging_enabled': True,
    'websocket_rate_limit': {
        'window_minutes': 5,
        'max_requests': 100
    },
    'data_retention_days': 365,
    'backup_encryption_enabled': True
}

def get_security_config() -> Dict[str, Any]:
    """Get current security configuration"""
    return SECURITY_CONFIG.copy()

def initialize_security_services(encryption_key: Optional[str] = None) -> Dict[str, Any]:
    """Initialize all security services"""
    return {
        'encryptor': DataEncryption(encryption_key),
        'validator': DataValidator(),
        'secure_storage': SecureStorage(encryption_key),
        'access_control': AccessControl(),
        'websocket_security': WebSocketSecurity()
    }