"""
Functional tests for user management
Tests user registration, authentication, and profile management
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch
import tempfile
import os

from app.main import app
from database import User

class TestUserManagement:
    """Test user management functionality"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_user_registration_flow(self, client):
        """Test complete user registration workflow"""
        # Test user data
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword123",
            "full_name": "New User"
        }
        
        # Register user
        response = client.post("/auth/register", json=user_data)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
    
    def test_user_registration_duplicate_email(self, client, db_session):
        """Test user registration with duplicate email"""
        # Create existing user
        existing_user = User(
            username="existing",
            email="existing@example.com",
            hashed_password="hashed_password",
            is_active=True
        )
        db_session.add(existing_user)
        db_session.commit()
        
        # Try to register with same email
        user_data = {
            "username": "newuser",
            "email": "existing@example.com",
            "password": "password123"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        # Should fail
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_user_registration_duplicate_username(self, client, db_session):
        """Test user registration with duplicate username"""
        # Create existing user
        existing_user = User(
            username="existing",
            email="existing@example.com",
            hashed_password="hashed_password",
            is_active=True
        )
        db_session.add(existing_user)
        db_session.commit()
        
        # Try to register with same username
        user_data = {
            "username": "existing",
            "email": "new@example.com",
            "password": "password123"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        # Should fail
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_user_login_flow(self, client, db_session):
        """Test complete user login workflow"""
        # Create test user
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=pwd_context.hash("password123"),
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        # Login
        response = client.post("/auth/login", data={
            "username": "testuser",
            "password": "password123"
        })
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
    
    def test_user_login_invalid_credentials(self, client, db_session):
        """Test login with invalid credentials"""
        # Create test user
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=pwd_context.hash("password123"),
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        # Try to login with wrong password
        response = client.post("/auth/login", data={
            "username": "testuser",
            "password": "wrongpassword"
        })
        
        # Should fail
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_user_login_inactive_user(self, client, db_session):
        """Test login with inactive user"""
        # Create inactive user
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        user = User(
            username="inactive",
            email="inactive@example.com",
            hashed_password=pwd_context.hash("password123"),
            is_active=False
        )
        db_session.add(user)
        db_session.commit()
        
        # Try to login
        response = client.post("/auth/login", data={
            "username": "inactive",
            "password": "password123"
        })
        
        # Should fail
        assert response.status_code == 401
        assert "Inactive user" in response.json()["detail"]
    
    def test_get_current_user_info(self, client, db_session):
        """Test getting current user information"""
        # Create test user
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=pwd_context.hash("password123"),
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        # Login to get token
        login_response = client.post("/auth/login", data={
            "username": "testuser",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        
        # Get user info
        response = client.get("/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
    
    def test_get_current_user_without_token(self, client):
        """Test getting user info without authentication"""
        response = client.get("/auth/me")
        
        # Should require authentication
        assert response.status_code == 401
    
    def test_get_current_user_invalid_token(self, client):
        """Test getting user info with invalid token"""
        response = client.get("/auth/me", headers={
            "Authorization": "Bearer invalid_token"
        })
        
        # Should fail
        assert response.status_code == 401
    
    def test_update_user_profile(self, client, db_session):
        """Test updating user profile"""
        # Create test user
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=pwd_context.hash("password123"),
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        # Login to get token
        login_response = client.post("/auth/login", data={
            "username": "testuser",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        
        # Update profile
        response = client.put("/auth/me", json={
            "full_name": "Updated Name"
        }, headers={
            "Authorization": f"Bearer {token}"
        })
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert data["full_name"] == "Updated Name"
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
    
    def test_user_registration_validation(self, client):
        """Test user registration input validation"""
        # Test with invalid email
        user_data = {
            "username": "testuser",
            "email": "invalid-email",
            "password": "password123"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        # Should fail validation
        assert response.status_code == 422
    
    def test_user_registration_weak_password(self, client):
        """Test user registration with weak password"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "123"  # Too short
        }
        
        response = client.post("/auth/register", json=user_data)
        
        # Should fail validation
        assert response.status_code == 422
    
    def test_user_registration_missing_fields(self, client):
        """Test user registration with missing required fields"""
        user_data = {
            "username": "testuser"
            # Missing email and password
        }
        
        response = client.post("/auth/register", json=user_data)
        
        # Should fail validation
        assert response.status_code == 422
    
    def test_user_authentication_flow(self, client, db_session):
        """Test complete authentication flow"""
        # Register user
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword123"
        }
        
        register_response = client.post("/auth/register", json=user_data)
        assert register_response.status_code == 200
        
        # Login
        login_response = client.post("/auth/login", data={
            "username": "newuser",
            "password": "securepassword123"
        })
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        
        # Access protected endpoint
        me_response = client.get("/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert me_response.status_code == 200
        
        # Update profile
        update_response = client.put("/auth/me", json={
            "full_name": "New User"
        }, headers={
            "Authorization": f"Bearer {token}"
        })
        assert update_response.status_code == 200
        
        # Verify update
        updated_user = update_response.json()
        assert updated_user["full_name"] == "New User"
