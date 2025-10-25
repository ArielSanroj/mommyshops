"""
Locust performance tests for MommyShops API
"""

from locust import HttpUser, task, between
import random
import json

class MommyShopsUser(HttpUser):
    """Simulate user behavior for performance testing"""
    
    wait_time = between(1, 3)
    
    def on_start(self):
        """Setup for each user"""
        self.user_id = None
        self.auth_token = None
        self.products = [
            "Aqua, Glycerin, Hyaluronic Acid, Niacinamide",
            "Water, Glycerin, Retinol, Vitamin C, Peptides",
            "Aqua, Hyaluronic Acid, Ceramides, Squalane",
            "Water, Niacinamide, Salicylic Acid, Zinc",
            "Aqua, Vitamin C, E, Ferulic Acid, Hyaluronic Acid"
        ]
    
    @task(3)
    def health_check(self):
        """Test health check endpoint"""
        self.client.get("/health/")
    
    @task(2)
    def get_api_info(self):
        """Test API info endpoint"""
        self.client.get("/")
    
    @task(1)
    def register_user(self):
        """Test user registration"""
        if not self.auth_token:
            user_data = {
                "username": f"testuser{random.randint(1000, 9999)}",
                "email": f"test{random.randint(1000, 9999)}@example.com",
                "password": "testpassword123",
                "full_name": "Test User"
            }
            
            response = self.client.post("/auth/register", json=user_data)
            if response.status_code == 200:
                self.user_id = response.json()["id"]
    
    @task(1)
    def login_user(self):
        """Test user login"""
        if not self.auth_token:
            login_data = {
                "username": "testuser",
                "password": "testpassword123"
            }
            
            response = self.client.post("/auth/login", data=login_data)
            if response.status_code == 200:
                self.auth_token = response.json()["access_token"]
                self.client.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
    
    @task(5)
    def analyze_text(self):
        """Test text analysis endpoint"""
        if self.auth_token:
            product_text = random.choice(self.products)
            analysis_data = {
                "text": product_text,
                "user_need": random.choice(["anti-aging", "hydration", "acne", "sensitive skin"]),
                "notes": "Performance test analysis"
            }
            
            self.client.post("/analysis/text", json=analysis_data)
    
    @task(2)
    def analyze_ingredients(self):
        """Test ingredient analysis endpoint"""
        if self.auth_token:
            ingredients = random.sample([
                "Hyaluronic Acid", "Retinol", "Vitamin C", "Niacinamide", 
                "Salicylic Acid", "Ceramides", "Peptides", "Squalane"
            ], random.randint(2, 5))
            
            analysis_data = {
                "ingredients": ingredients,
                "user_concerns": random.sample([
                    "sensitive skin", "anti-aging", "acne", "dryness"
                ], random.randint(1, 2))
            }
            
            self.client.post("/analysis/ingredients", json=analysis_data)
    
    @task(1)
    def get_analysis_history(self):
        """Test analysis history endpoint"""
        if self.auth_token:
            self.client.get("/analysis/history")
    
    @task(1)
    def get_user_info(self):
        """Test user info endpoint"""
        if self.auth_token:
            self.client.get("/auth/me")
    
    @task(1)
    def update_user_profile(self):
        """Test user profile update"""
        if self.auth_token:
            update_data = {
                "full_name": f"Updated User {random.randint(1000, 9999)}"
            }
            self.client.put("/auth/me", json=update_data)

class AdminUser(HttpUser):
    """Simulate admin user behavior"""
    
    wait_time = between(2, 5)
    
    def on_start(self):
        """Setup for admin user"""
        self.auth_token = None
        # Login as admin (assuming admin user exists)
        login_data = {
            "username": "admin",
            "password": "adminpassword"
        }
        
        response = self.client.post("/auth/login", data=login_data)
        if response.status_code == 200:
            self.auth_token = response.json()["access_token"]
            self.client.headers.update({
                "Authorization": f"Bearer {self.auth_token}"
            })
    
    @task(3)
    def get_user_stats(self):
        """Test user statistics endpoint"""
        if self.auth_token:
            self.client.get("/admin/users/stats")
    
    @task(2)
    def get_system_stats(self):
        """Test system statistics endpoint"""
        if self.auth_token:
            self.client.get("/admin/system/stats")
    
    @task(1)
    def list_users(self):
        """Test list users endpoint"""
        if self.auth_token:
            self.client.get("/admin/users")
    
    @task(1)
    def health_check(self):
        """Test health check endpoint"""
        self.client.get("/health/detailed")
