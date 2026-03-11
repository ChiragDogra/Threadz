"""
Authentication tests for Threadz backend
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User

@pytest.mark.unit
class TestAuthentication:
    """Test authentication endpoints and functionality"""
    
    async def test_user_registration_success(self, client: AsyncClient):
        """Test successful user registration."""
        user_data = {
            "email": "newuser@example.com",
            "password": "NewPassword123!",
            "full_name": "New User"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
        assert "password_hash" not in data  # Password should not be returned
    
    async def test_user_registration_duplicate_email(self, client: AsyncClient, test_user):
        """Test registration with duplicate email."""
        user_data = {
            "email": test_user.email,
            "password": "NewPassword123!",
            "full_name": "Duplicate User"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    async def test_user_registration_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email."""
        user_data = {
            "email": "invalid-email",
            "password": "NewPassword123!",
            "full_name": "Invalid Email User"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 422  # Validation error
    
    async def test_user_registration_weak_password(self, client: AsyncClient):
        """Test registration with weak password."""
        user_data = {
            "email": "weak@example.com",
            "password": "123",  # Too weak
            "full_name": "Weak Password User"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "password" in response.json()["detail"].lower()
    
    async def test_user_login_success(self, client: AsyncClient, test_user_data):
        """Test successful user login."""
        # First register the user
        await client.post("/api/v1/auth/register", json=test_user_data)
        
        # Then login
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        
        response = await client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 50  # JWT tokens are long
    
    async def test_user_login_invalid_credentials(self, client: AsyncClient, test_user):
        """Test login with invalid credentials."""
        login_data = {
            "email": test_user.email,
            "password": "wrongpassword"
        }
        
        response = await client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()
    
    async def test_user_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "SomePassword123!"
        }
        
        response = await client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()
    
    async def test_get_current_user_success(self, client: AsyncClient, auth_headers):
        """Test getting current user with valid token."""
        response = await client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "full_name" in data
        assert "password_hash" not in data
    
    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = await client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 401
    
    async def test_get_current_user_no_token(self, client: AsyncClient):
        """Test getting current user without token."""
        response = await client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
    
    async def test_protected_endpoint_with_valid_token(self, client: AsyncClient, auth_headers):
        """Test accessing protected endpoint with valid token."""
        response = await client.get("/api/v1/designs/my-designs", headers=auth_headers)
        
        assert response.status_code == 200
    
    async def test_protected_endpoint_without_token(self, client: AsyncClient):
        """Test accessing protected endpoint without token."""
        response = await client.get("/api/v1/designs/my-designs")
        
        assert response.status_code == 401
    
    async def test_token_expiry(self, client: AsyncClient, test_user_data):
        """Test token expiry functionality."""
        # Register and login
        await client.post("/api/v1/auth/register", json=test_user_data)
        
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        
        response = await client.post("/api/v1/auth/login", json=login_data)
        token = response.json()["access_token"]
        
        # Test with valid token
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        
        # Note: We can't easily test actual expiry without waiting
        # In a real test, you might mock time or use a very short expiry

@pytest.mark.integration
class TestAuthenticationIntegration:
    """Integration tests for authentication"""
    
    async def test_complete_user_flow(self, client: AsyncClient, db_session: AsyncSession):
        """Test complete user registration and authentication flow."""
        user_data = {
            "email": "flowtest@example.com",
            "password": "FlowTest123!",
            "full_name": "Flow Test User"
        }
        
        # 1. Register user
        response = await client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        
        # 2. Verify user exists in database
        from sqlalchemy import select
        result = await db_session.execute(
            select(User).where(User.email == user_data["email"])
        )
        user = result.scalars().first()
        assert user is not None
        assert user.email == user_data["email"]
        assert user.full_name == user_data["full_name"]
        assert user.password_hash is not None
        assert user.password_hash != user_data["password"]  # Should be hashed
        
        # 3. Login
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        response = await client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        
        token_data = response.json()
        assert "access_token" in token_data
        
        # 4. Use token to access protected endpoint
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        
        me_data = response.json()
        assert me_data["email"] == user_data["email"]
        assert me_data["full_name"] == user_data["full_name"]
    
    async def test_multiple_user_sessions(self, client: AsyncClient):
        """Test multiple users can be authenticated simultaneously."""
        users_data = [
            {
                "email": "user1@example.com",
                "password": "User1Pass123!",
                "full_name": "User One"
            },
            {
                "email": "user2@example.com",
                "password": "User2Pass123!",
                "full_name": "User Two"
            }
        ]
        
        tokens = []
        
        # Register and login both users
        for user_data in users_data:
            # Register
            response = await client.post("/api/v1/auth/register", json=user_data)
            assert response.status_code == 201
            
            # Login
            login_data = {
                "email": user_data["email"],
                "password": user_data["password"]
            }
            response = await client.post("/api/v1/auth/login", json=login_data)
            assert response.status_code == 200
            
            tokens.append(response.json()["access_token"])
        
        # Test both tokens work independently
        for i, token in enumerate(tokens):
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.get("/api/v1/auth/me", headers=headers)
            assert response.status_code == 200
            
            me_data = response.json()
            assert me_data["email"] == users_data[i]["email"]

@pytest.mark.slow
class TestAuthenticationPerformance:
    """Performance tests for authentication"""
    
    async def test_login_response_time(self, client: AsyncClient, test_user):
        """Test login response time is acceptable."""
        import time
        
        login_data = {
            "email": test_user.email,
            "password": "TestPassword123!"
        }
        
        start_time = time.time()
        response = await client.post("/api/v1/auth/login", json=login_data)
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = end_time - start_time
        
        # Should respond within 1 second
        assert response_time < 1.0, f"Login took {response_time:.2f} seconds"
    
    async def test_concurrent_logins(self, client: AsyncClient, test_user):
        """Test concurrent login requests."""
        import asyncio
        
        login_data = {
            "email": test_user.email,
            "password": "TestPassword123!"
        }
        
        async def make_login_request():
            return await client.post("/api/v1/auth/login", json=login_data)
        
        # Make 10 concurrent login requests
        responses = await asyncio.gather(
            *[make_login_request() for _ in range(10)],
            return_exceptions=True
        )
        
        # All should succeed
        for response in responses:
            if isinstance(response, Exception):
                pytest.fail(f"Concurrent login failed: {response}")
            else:
                assert response.status_code == 200
                assert "access_token" in response.json()
