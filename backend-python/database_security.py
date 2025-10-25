"""
Database security utilities for MommyShops backend.
Implements secure database operations and SQL injection prevention.
"""

import os
import re
import logging
from typing import Any, Dict, List, Optional, Union
from sqlalchemy import text, create_engine, MetaData, Table, Column, String, Integer
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
import hashlib
import hmac
from datetime import datetime, timedelta

# Database security logger
db_security_logger = logging.getLogger("database_security")

class SecureQuery:
    """Secure database query operations"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.audit_logger = db_security_logger
    
    def safe_execute(self, query: str, params: Dict[str, Any] = None) -> Any:
        """Execute parameterized query safely"""
        try:
            # Validate query for dangerous patterns
            if not self._validate_query_safety(query):
                raise ValueError("Query contains potentially dangerous patterns")
            
            # Execute with parameters
            result = self.db.execute(text(query), params or {})
            self.db.commit()
            
            # Log successful query
            self.audit_logger.info({
                "event": "safe_query_executed",
                "query_hash": hashlib.sha256(query.encode()).hexdigest()[:16],
                "params_count": len(params) if params else 0,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return result
            
        except SQLAlchemyError as e:
            self.db.rollback()
            self.audit_logger.error({
                "event": "query_execution_failed",
                "error": str(e),
                "query_hash": hashlib.sha256(query.encode()).hexdigest()[:16],
                "timestamp": datetime.utcnow().isoformat()
            })
            raise
    
    def _validate_query_safety(self, query: str) -> bool:
        """Validate query for dangerous patterns"""
        dangerous_patterns = [
            r';\s*drop\s+', r';\s*delete\s+', r';\s*insert\s+', r';\s*update\s+',
            r';\s*create\s+', r';\s*alter\s+', r';\s*exec\s+', r';\s*execute\s+',
            r'union\s+select', r'--', r'/\*', r'\*/', r'xp_', r'sp_',
            r'waitfor\s+delay', r'benchmark\s*\(', r'sleep\s*\('
        ]
        
        query_lower = query.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, query_lower):
                self.audit_logger.warning({
                    "event": "dangerous_query_detected",
                    "pattern": pattern,
                    "query_hash": hashlib.sha256(query.encode()).hexdigest()[:16],
                    "timestamp": datetime.utcnow().isoformat()
                })
                return False
        
        return True
    
    def safe_select(self, table: str, columns: List[str], where_clause: str = None, 
                   params: Dict[str, Any] = None, limit: int = None) -> List[Dict]:
        """Safe SELECT query with parameterized conditions"""
        # Build safe SELECT query
        columns_str = ", ".join(columns)
        query = f"SELECT {columns_str} FROM {table}"
        
        if where_clause:
            query += f" WHERE {where_clause}"
        
        if limit:
            query += f" LIMIT {limit}"
        
        # Execute safely
        result = self.safe_execute(query, params)
        return [dict(row) for row in result]
    
    def safe_insert(self, table: str, data: Dict[str, Any]) -> int:
        """Safe INSERT query with parameterized data"""
        columns = list(data.keys())
        values = [f":{col}" for col in columns]
        
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(values)})"
        
        result = self.safe_execute(query, data)
        return result.lastrowid if hasattr(result, 'lastrowid') else 0
    
    def safe_update(self, table: str, data: Dict[str, Any], where_clause: str, 
                   where_params: Dict[str, Any]) -> int:
        """Safe UPDATE query with parameterized data and conditions"""
        set_clause = ", ".join([f"{col} = :{col}" for col in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        
        # Combine data and where parameters
        all_params = {**data, **where_params}
        
        result = self.safe_execute(query, all_params)
        return result.rowcount if hasattr(result, 'rowcount') else 0
    
    def safe_delete(self, table: str, where_clause: str, params: Dict[str, Any]) -> int:
        """Safe DELETE query with parameterized conditions"""
        query = f"DELETE FROM {table} WHERE {where_clause}"
        
        result = self.safe_execute(query, params)
        return result.rowcount if hasattr(result, 'rowcount') else 0

class DatabaseAccessControl:
    """Database access control and permissions"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.audit_logger = db_security_logger
    
    def check_table_permission(self, user_id: str, table: str, operation: str) -> bool:
        """Check if user has permission to access table"""
        # Define table permissions
        table_permissions = {
            "users": ["select", "update"],
            "product_analysis": ["select", "insert", "update"],
            "ingredient_analysis": ["select", "insert"],
            "recommendations": ["select", "insert", "update"],
            "user_preferences": ["select", "insert", "update", "delete"]
        }
        
        # Check if table exists in permissions
        if table not in table_permissions:
            self.audit_logger.warning({
                "event": "unauthorized_table_access",
                "user_id": user_id,
                "table": table,
                "operation": operation,
                "timestamp": datetime.utcnow().isoformat()
            })
            return False
        
        # Check if operation is allowed
        if operation not in table_permissions[table]:
            self.audit_logger.warning({
                "event": "unauthorized_operation",
                "user_id": user_id,
                "table": table,
                "operation": operation,
                "timestamp": datetime.utcnow().isoformat()
            })
            return False
        
        return True
    
    def log_database_access(self, user_id: str, table: str, operation: str, 
                           query_hash: str = None):
        """Log database access for audit trail"""
        self.audit_logger.info({
            "event": "database_access",
            "user_id": user_id,
            "table": table,
            "operation": operation,
            "query_hash": query_hash,
            "timestamp": datetime.utcnow().isoformat()
        })

class DatabaseEncryption:
    """Database encryption utilities"""
    
    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or os.getenv("DB_ENCRYPTION_KEY", "default-key")
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data before storing"""
        if not data:
            return data
        
        # Simple encryption (in production, use proper encryption)
        encrypted = hashlib.sha256(f"{data}{self.secret_key}".encode()).hexdigest()
        return encrypted
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data (placeholder - implement proper decryption)"""
        # This is a placeholder - implement proper decryption
        return encrypted_data
    
    def hash_password(self, password: str) -> str:
        """Hash password securely"""
        salt = os.urandom(32)
        pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return salt.hex() + pwdhash.hex()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        salt = bytes.fromhex(hashed[:64])
        pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return pwdhash.hex() == hashed[64:]

class DatabaseConnectionSecurity:
    """Secure database connection management"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.session_factory = None
        self.audit_logger = db_security_logger
    
    def create_secure_engine(self):
        """Create secure database engine with proper configuration"""
        # Parse database URL to extract components
        url_parts = self._parse_database_url(self.database_url)
        
        # Create engine with security configurations
        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,
            echo=False,  # Disable SQL echo in production
            connect_args={
                "sslmode": "require",  # Require SSL
                "application_name": "mommyshops_backend"
            }
        )
        
        # Create session factory
        self.session_factory = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False
        )
        
        self.audit_logger.info({
            "event": "secure_engine_created",
            "pool_size": 10,
            "max_overflow": 20,
            "ssl_enabled": True,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def _parse_database_url(self, url: str) -> Dict[str, str]:
        """Parse database URL to extract components"""
        # Simple URL parsing - implement proper parsing
        return {
            "scheme": url.split("://")[0],
            "host": "localhost",
            "port": "5432",
            "database": "mommyshops"
        }
    
    @contextmanager
    def get_secure_session(self):
        """Get secure database session with proper error handling"""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.audit_logger.error({
                "event": "database_session_error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            raise
        finally:
            session.close()
    
    def test_connection_security(self) -> bool:
        """Test database connection security"""
        try:
            with self.get_secure_session() as session:
                # Test basic connectivity
                result = session.execute(text("SELECT 1"))
                assert result.fetchone()[0] == 1
                
                # Test SSL connection
                ssl_result = session.execute(text("SELECT ssl_is_used()"))
                ssl_enabled = ssl_result.fetchone()[0]
                
                self.audit_logger.info({
                    "event": "connection_security_test",
                    "ssl_enabled": ssl_enabled,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return ssl_enabled
                
        except Exception as e:
            self.audit_logger.error({
                "event": "connection_security_test_failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            return False

class DatabaseAuditLogger:
    """Database audit logging"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.audit_logger = db_security_logger
    
    def log_data_access(self, user_id: str, table: str, operation: str, 
                       record_id: str = None, changes: Dict[str, Any] = None):
        """Log data access for audit trail"""
        audit_entry = {
            "event": "data_access",
            "user_id": user_id,
            "table": table,
            "operation": operation,
            "record_id": record_id,
            "changes": changes,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.audit_logger.info(audit_entry)
    
    def log_sensitive_data_access(self, user_id: str, data_type: str, 
                                 record_id: str = None):
        """Log access to sensitive data"""
        audit_entry = {
            "event": "sensitive_data_access",
            "user_id": user_id,
            "data_type": data_type,
            "record_id": record_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.audit_logger.warning(audit_entry)
    
    def log_unauthorized_access(self, user_id: str, attempted_operation: str, 
                               table: str = None):
        """Log unauthorized access attempts"""
        audit_entry = {
            "event": "unauthorized_access",
            "user_id": user_id,
            "attempted_operation": attempted_operation,
            "table": table,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.audit_logger.error(audit_entry)

# Utility functions for secure database operations
def create_secure_database_session(database_url: str) -> DatabaseConnectionSecurity:
    """Create secure database session"""
    db_security = DatabaseConnectionSecurity(database_url)
    db_security.create_secure_engine()
    return db_security

def get_secure_query(db_session: Session) -> SecureQuery:
    """Get secure query instance"""
    return SecureQuery(db_session)

def get_database_access_control(db_session: Session) -> DatabaseAccessControl:
    """Get database access control instance"""
    return DatabaseAccessControl(db_session)

def get_database_encryption() -> DatabaseEncryption:
    """Get database encryption instance"""
    return DatabaseEncryption()

def get_database_audit_logger(db_session: Session) -> DatabaseAuditLogger:
    """Get database audit logger instance"""
    return DatabaseAuditLogger(db_session)
