"""
Google OAuth2 Authentication Integration for MommyShops
Handles user registration and login using Google accounts
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import httpx

load_dotenv()
logger = logging.getLogger(__name__)

class GoogleAuthHandler:
    """Handles Google OAuth2 authentication for MommyShops"""
    
    def __init__(self):
        self.client_id = os.getenv('GOOGLE_CLIENT_ID')
        self.client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        # Determine redirect URI based on environment
        if os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('PRODUCTION'):
            # Production environment
            self.redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', 'https://web-production-f23a5.up.railway.app/auth/google/callback')
        else:
            # Development environment
            self.redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8000/auth/google/callback')
        
        # OAuth2 scopes
        self.scopes = [
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile',
            'openid'
        ]
        
        if not self.client_id or not self.client_secret:
            logger.warning("Google OAuth2 credentials not configured")
    
    def get_authorization_url(self) -> Optional[str]:
        """
        Generate Google OAuth2 authorization URL
        
        Returns:
            Authorization URL or None if not configured
        """
        if not self.client_id or not self.client_secret:
            logger.error("Google OAuth2 credentials not configured")
            return None
        
        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri]
                    }
                },
                scopes=self.scopes
            )
            flow.redirect_uri = self.redirect_uri
            
            authorization_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            logger.info("Generated Google OAuth2 authorization URL")
            return authorization_url
            
        except Exception as e:
            logger.error(f"Failed to generate authorization URL: {e}")
            return None
    
    async def handle_callback(self, authorization_code: str) -> Optional[Dict[str, Any]]:
        """
        Handle OAuth2 callback and exchange code for tokens
        
        Args:
            authorization_code: Authorization code from Google
            
        Returns:
            User information or None if failed
        """
        if not self.client_id or not self.client_secret:
            logger.error("Google OAuth2 credentials not configured")
            return None
        
        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri]
                    }
                },
                scopes=self.scopes
            )
            flow.redirect_uri = self.redirect_uri
            
            # Exchange authorization code for tokens
            flow.fetch_token(code=authorization_code)
            
            # Get user information
            credentials = flow.credentials
            user_info = await self._get_user_info(credentials)
            
            if user_info:
                logger.info(f"Google OAuth2 authentication successful for user: {user_info.get('email')}")
                return user_info
            else:
                logger.error("Failed to get user information from Google")
                return None
                
        except Exception as e:
            logger.error(f"Google OAuth2 callback failed: {e}")
            return None
    
    async def _get_user_info(self, credentials: Credentials) -> Optional[Dict[str, Any]]:
        """
        Get user information from Google using credentials
        
        Args:
            credentials: OAuth2 credentials
            
        Returns:
            User information dictionary
        """
        try:
            # Build the service
            service = build('oauth2', 'v2', credentials=credentials)
            
            # Get user info
            user_info = service.userinfo().get().execute()
            
            return {
                'google_id': user_info.get('id'),
                'email': user_info.get('email'),
                'name': user_info.get('name'),
                'given_name': user_info.get('given_name'),
                'family_name': user_info.get('family_name'),
                'picture': user_info.get('picture'),
                'verified_email': user_info.get('verified_email', False),
                'locale': user_info.get('locale', 'en')
            }
            
        except Exception as e:
            logger.error(f"Failed to get user info from Google: {e}")
            return None
    
    async def verify_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Verify Google access token and get user info
        
        Args:
            access_token: Google access token
            
        Returns:
            User information or None if invalid
        """
        try:
            url = f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={access_token}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    user_info = response.json()
                    return {
                        'google_id': user_info.get('id'),
                        'email': user_info.get('email'),
                        'name': user_info.get('name'),
                        'given_name': user_info.get('given_name'),
                        'family_name': user_info.get('family_name'),
                        'picture': user_info.get('picture'),
                        'verified_email': user_info.get('verified_email', False),
                        'locale': user_info.get('locale', 'en')
                    }
                else:
                    logger.error(f"Google token verification failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to verify Google token: {e}")
            return None

# Global instance
google_auth_handler = GoogleAuthHandler()

def get_google_auth_url() -> Optional[str]:
    """Get Google OAuth2 authorization URL"""
    return google_auth_handler.get_authorization_url()

async def handle_google_callback(authorization_code: str) -> Optional[Dict[str, Any]]:
    """Handle Google OAuth2 callback"""
    return await google_auth_handler.handle_callback(authorization_code)

async def verify_google_token(access_token: str) -> Optional[Dict[str, Any]]:
    """Verify Google access token"""
    return await google_auth_handler.verify_token(access_token)