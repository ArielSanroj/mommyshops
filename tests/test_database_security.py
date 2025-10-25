"""
Database security tests for MommyShops backend.
Tests secure database operations and SQL injection prevention.
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set up environment
os.environ.setdefault("SKIP_MAIN_IMPORT_FOR_TESTS", "1")

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend-python"
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from database_security import (
    SecureQuery, DatabaseAccessControl, DatabaseEncryption,
    DatabaseConnectionSecurity, DatabaseAuditLogger,
    create_secure_database_session, get_secure_query,
    get_database_access_control, get_database_encryption,
    get_database_audit_logger
)

# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_security.db"

@pytest.fixture
def test_engine():
    """Create test database engine"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return engine

@pytest.fixture
def test_session(test_engine):
    """Create test database session"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture
def secure_query(test_session):
    """Create secure query instance"""
    return SecureQuery(test_session)

@pytest.fixture
def access_control(test_session):
    """Create database access control instance"""
    return DatabaseAccessControl(test_session)

@pytest.fixture
def encryption():
    """Create database encryption instance"""
    return DatabaseEncryption()

def test_secure_query_validation():
    """Test secure query validation"""
    mock_session = Mock()
    secure_query = SecureQuery(mock_session)
    
    # Test safe query
    safe_query = "SELECT * FROM users WHERE id = :user_id"
    is_safe = secure_query._validate_query_safety(safe_query)
    assert is_safe
    
    # Test dangerous queries
    dangerous_queries = [
        "SELECT * FROM users; DROP TABLE users; --",
        "SELECT * FROM users WHERE id = 1 OR 1=1",
        "SELECT * FROM users UNION SELECT * FROM passwords",
        "SELECT * FROM users; DELETE FROM users; --",
        "SELECT * FROM users; INSERT INTO users VALUES ('hacker', 'pass'); --"
    ]
    
    for query in dangerous_queries:
        is_safe = secure_query._validate_query_safety(query)
        assert not is_safe, f"Dangerous query should be rejected: {query}"

def test_secure_query_execution():
    """Test secure query execution"""
    mock_session = Mock()
    secure_query = SecureQuery(mock_session)
    
    # Test safe execution
    safe_query = "SELECT * FROM users WHERE id = :user_id"
    params = {"user_id": 123}
    
    with patch.object(secure_query, '_validate_query_safety', return_value=True):
        with patch.object(mock_session, 'execute') as mock_execute:
            mock_execute.return_value = Mock()
            result = secure_query.safe_execute(safe_query, params)
            mock_execute.assert_called_once()
            mock_session.commit.assert_called_once()
    
    # Test dangerous query rejection
    dangerous_query = "SELECT * FROM users; DROP TABLE users; --"
    
    with patch.object(secure_query, '_validate_query_safety', return_value=False):
        with pytest.raises(ValueError, match="Query contains potentially dangerous patterns"):
            secure_query.safe_execute(dangerous_query, {})

def test_secure_select():
    """Test secure SELECT operations"""
    mock_session = Mock()
    secure_query = SecureQuery(mock_session)
    
    # Test safe SELECT
    with patch.object(secure_query, 'safe_execute') as mock_execute:
        mock_execute.return_value = [Mock(id=1, name="test")]
        
        result = secure_query.safe_select(
            "users", 
            ["id", "name"], 
            "id = :user_id", 
            {"user_id": 123}
        )
        
        mock_execute.assert_called_once()
        assert len(result) == 1

def test_secure_insert():
    """Test secure INSERT operations"""
    mock_session = Mock()
    secure_query = SecureQuery(mock_session)
    
    # Test safe INSERT
    with patch.object(secure_query, 'safe_execute') as mock_execute:
        mock_execute.return_value = Mock(lastrowid=1)
        
        result = secure_query.safe_insert("users", {"name": "test", "email": "test@example.com"})
        
        mock_execute.assert_called_once()
        assert result == 1

def test_secure_update():
    """Test secure UPDATE operations"""
    mock_session = Mock()
    secure_query = SecureQuery(mock_session)
    
    # Test safe UPDATE
    with patch.object(secure_query, 'safe_execute') as mock_execute:
        mock_execute.return_value = Mock(rowcount=1)
        
        result = secure_query.safe_update(
            "users", 
            {"name": "updated"}, 
            "id = :user_id", 
            {"user_id": 123}
        )
        
        mock_execute.assert_called_once()
        assert result == 1

def test_secure_delete():
    """Test secure DELETE operations"""
    mock_session = Mock()
    secure_query = SecureQuery(mock_session)
    
    # Test safe DELETE
    with patch.object(secure_query, 'safe_execute') as mock_execute:
        mock_execute.return_value = Mock(rowcount=1)
        
        result = secure_query.safe_delete("users", "id = :user_id", {"user_id": 123})
        
        mock_execute.assert_called_once()
        assert result == 1

def test_database_access_control():
    """Test database access control"""
    mock_session = Mock()
    access_control = DatabaseAccessControl(mock_session)
    
    # Test valid permissions
    assert access_control.check_table_permission("user123", "users", "select")
    assert access_control.check_table_permission("user123", "product_analysis", "insert")
    
    # Test invalid permissions
    assert not access_control.check_table_permission("user123", "users", "delete")
    assert not access_control.check_table_permission("user123", "nonexistent_table", "select")
    
    # Test logging
    with patch.object(access_control.audit_logger, 'warning') as mock_warning:
        access_control.check_table_permission("user123", "users", "delete")
        mock_warning.assert_called_once()

def test_database_encryption():
    """Test database encryption"""
    encryption = DatabaseEncryption("test-secret-key")
    
    # Test password hashing
    password = "test-password"
    hashed = encryption.hash_password(password)
    assert hashed != password
    assert len(hashed) > 50  # Should be longer than original
    
    # Test password verification
    assert encryption.verify_password(password, hashed)
    assert not encryption.verify_password("wrong-password", hashed)
    
    # Test sensitive data encryption
    sensitive_data = "sensitive-information"
    encrypted = encryption.encrypt_sensitive_data(sensitive_data)
    assert encrypted != sensitive_data
    assert len(encrypted) == 64  # SHA256 hex length

def test_database_connection_security():
    """Test database connection security"""
    db_security = DatabaseConnectionSecurity(TEST_DATABASE_URL)
    
    # Test engine creation
    db_security.create_secure_engine()
    assert db_security.engine is not None
    assert db_security.session_factory is not None
    
    # Test secure session
    with db_security.get_secure_session() as session:
        assert session is not None
        # Session should be properly closed after context

def test_database_audit_logging():
    """Test database audit logging"""
    mock_session = Mock()
    audit_logger = DatabaseAuditLogger(mock_session)
    
    # Test data access logging
    with patch.object(audit_logger.audit_logger, 'info') as mock_info:
        audit_logger.log_data_access("user123", "users", "select", "record456")
        mock_info.assert_called_once()
        
        # Check logged data
        call_args = mock_info.call_args[0][0]
        assert call_args["event"] == "data_access"
        assert call_args["user_id"] == "user123"
        assert call_args["table"] == "users"
    
    # Test sensitive data access logging
    with patch.object(audit_logger.audit_logger, 'warning') as mock_warning:
        audit_logger.log_sensitive_data_access("user123", "password", "record456")
        mock_warning.assert_called_once()
        
        # Check logged data
        call_args = mock_warning.call_args[0][0]
        assert call_args["event"] == "sensitive_data_access"
        assert call_args["data_type"] == "password"
    
    # Test unauthorized access logging
    with patch.object(audit_logger.audit_logger, 'error') as mock_error:
        audit_logger.log_unauthorized_access("user123", "delete", "users")
        mock_error.assert_called_once()
        
        # Check logged data
        call_args = mock_error.call_args[0][0]
        assert call_args["event"] == "unauthorized_access"
        assert call_args["attempted_operation"] == "delete"

def test_sql_injection_prevention():
    """Test SQL injection prevention"""
    mock_session = Mock()
    secure_query = SecureQuery(mock_session)
    
    # Test various SQL injection patterns
    injection_patterns = [
        "'; DROP TABLE users; --",
        "1' OR '1'='1",
        "admin'--",
        "1' UNION SELECT * FROM users--",
        "'; INSERT INTO users VALUES ('hacker', 'password'); --",
        "1' OR 1=1 --",
        "admin' OR '1'='1",
        "1'; DELETE FROM users; --"
    ]
    
    for pattern in injection_patterns:
        is_safe = secure_query._validate_query_safety(pattern)
        assert not is_safe, f"SQL injection pattern should be detected: {pattern}"
    
    # Test safe queries
    safe_queries = [
        "SELECT * FROM users WHERE id = :user_id",
        "SELECT name, email FROM users WHERE active = :active",
        "INSERT INTO users (name, email) VALUES (:name, :email)",
        "UPDATE users SET name = :name WHERE id = :id"
    ]
    
    for query in safe_queries:
        is_safe = secure_query._validate_query_safety(query)
        assert is_safe, f"Safe query should be allowed: {query}"

def test_parameterized_queries():
    """Test parameterized query execution"""
    mock_session = Mock()
    secure_query = SecureQuery(mock_session)
    
    # Test parameterized SELECT
    with patch.object(secure_query, 'safe_execute') as mock_execute:
        secure_query.safe_select(
            "users", 
            ["id", "name"], 
            "id = :user_id AND active = :active",
            {"user_id": 123, "active": True}
        )
        
        # Verify parameters were passed correctly
        mock_execute.assert_called_once()
        call_args = mock_execute.call_args
        assert call_args[1]["user_id"] == 123
        assert call_args[1]["active"] is True

def test_database_security_integration():
    """Test database security integration"""
    # Test creating secure database session
    with patch('database_security.DatabaseConnectionSecurity') as mock_db_security:
        mock_instance = mock_db_security.return_value
        mock_instance.create_secure_engine.return_value = None
        
        db_security = create_secure_database_session(TEST_DATABASE_URL)
        assert db_security is not None
    
    # Test getting secure query
    mock_session = Mock()
    secure_query = get_secure_query(mock_session)
    assert isinstance(secure_query, SecureQuery)
    
    # Test getting access control
    access_control = get_database_access_control(mock_session)
    assert isinstance(access_control, DatabaseAccessControl)
    
    # Test getting encryption
    encryption = get_database_encryption()
    assert isinstance(encryption, DatabaseEncryption)
    
    # Test getting audit logger
    audit_logger = get_database_audit_logger(mock_session)
    assert isinstance(audit_logger, DatabaseAuditLogger)

def test_connection_security_test():
    """Test database connection security testing"""
    db_security = DatabaseConnectionSecurity(TEST_DATABASE_URL)
    db_security.create_secure_engine()
    
    # Test connection security
    with patch.object(db_security, 'get_secure_session') as mock_session:
        mock_session.return_value.__enter__.return_value.execute.return_value.fetchone.return_value = [1]
        
        # Mock SSL test
        with patch.object(db_security, 'get_secure_session') as mock_ssl_session:
            mock_ssl_session.return_value.__enter__.return_value.execute.return_value.fetchone.return_value = [True]
            
            is_secure = db_security.test_connection_security()
            assert is_secure

def test_audit_logging_comprehensive():
    """Test comprehensive audit logging"""
    mock_session = Mock()
    audit_logger = DatabaseAuditLogger(mock_session)
    
    # Test all logging methods
    with patch.object(audit_logger.audit_logger, 'info') as mock_info:
        audit_logger.log_data_access("user123", "users", "select", "record456", {"field": "value"})
        mock_info.assert_called_once()
    
    with patch.object(audit_logger.audit_logger, 'warning') as mock_warning:
        audit_logger.log_sensitive_data_access("user123", "password", "record456")
        mock_warning.assert_called_once()
    
    with patch.object(audit_logger.audit_logger, 'error') as mock_error:
        audit_logger.log_unauthorized_access("user123", "delete", "users")
        mock_error.assert_called_once()

def test_encryption_security():
    """Test encryption security features"""
    encryption = DatabaseEncryption("test-secret-key")
    
    # Test password hashing with different passwords
    passwords = ["password123", "admin", "user@example.com", "P@ssw0rd!"]
    
    for password in passwords:
        hashed = encryption.hash_password(password)
        assert hashed != password
        assert len(hashed) > 50
        assert encryption.verify_password(password, hashed)
        assert not encryption.verify_password("wrong", hashed)
    
    # Test that same password produces different hashes (due to salt)
    password = "test-password"
    hash1 = encryption.hash_password(password)
    hash2 = encryption.hash_password(password)
    assert hash1 != hash2  # Different salts should produce different hashes

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
