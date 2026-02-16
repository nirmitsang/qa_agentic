# Codebase Map — Feature-Specific Context

**Purpose:** This file contains the ACTUAL CODE for the specific feature you're testing. It is updated for each feature and injected into Code Structure Planning and Scripting agents. This is where you provide the implementation details that help QA-GPT understand what utilities already exist and what the code structure looks like.

**CRITICAL:** Include ACTUAL CODE SNIPPETS, not just file names. The Code Structure Planner uses this to identify existing utilities and avoid creating duplicates.

**Instructions:** For each new feature you want to generate tests for, update this file with the relevant source code, existing test examples, and available helpers.

---

## 1. Feature Being Tested

**Feature Name:** User Login API Endpoint

**Feature Description:**
POST `/api/auth/login` endpoint that accepts username/password and returns a JWT token. Supports both regular users and admin users. Failed logins return 401. Account lockout after 5 failed attempts.

**Related Tickets/Issues:**
- JIRA-1234: Implement JWT authentication
- JIRA-1235: Add account lockout logic

---

## 2. Source Code Being Tested

**IMPORTANT:** Include the ACTUAL implementation code, not just file paths.

### File: `src/api/auth.py`
```python
from fastapi import APIRouter, HTTPException, Depends
from src.services.auth_service import AuthService
from src.models.user import User
from src.utils.jwt_helper import create_access_token

router = APIRouter()

@router.post("/login")
async def login(username: str, password: str, auth_service: AuthService = Depends()):
    """
    Authenticate user and return JWT token.
    
    Args:
        username: User's username
        password: User's password
        
    Returns:
        dict: {"access_token": str, "token_type": "bearer", "user": {...}}
        
    Raises:
        HTTPException 401: Invalid credentials
        HTTPException 403: Account locked
    """
    # Check if account is locked
    if auth_service.is_account_locked(username):
        raise HTTPException(status_code=403, detail="Account locked due to too many failed attempts")
    
    # Verify credentials
    user = await auth_service.authenticate(username, password)
    if not user:
        await auth_service.record_failed_attempt(username)
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Generate token
    token = create_access_token(user_id=user.id, username=user.username)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
    }
```

### File: `src/services/auth_service.py`
```python
class AuthService:
    """Handles authentication and authorization logic."""
    
    async def authenticate(self, username: str, password: str) -> User | None:
        """
        Verify username and password.
        Returns User object if valid, None otherwise.
        """
        user = await self.db.get_user_by_username(username)
        if not user:
            return None
        
        if not self.verify_password(password, user.hashed_password):
            return None
            
        return user
    
    async def is_account_locked(self, username: str) -> bool:
        """Check if account is locked due to failed login attempts."""
        failed_attempts = await self.redis.get(f"failed_attempts:{username}")
        return int(failed_attempts or 0) >= 5
    
    async def record_failed_attempt(self, username: str) -> None:
        """Increment failed login attempt counter."""
        key = f"failed_attempts:{username}"
        await self.redis.incr(key)
        await self.redis.expire(key, 3600)  # Reset after 1 hour
```

### File: `src/utils/jwt_helper.py`
```python
import jwt
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key"  # From environment in production

def create_access_token(user_id: int, username: str) -> str:
    """Generate JWT token valid for 30 minutes."""
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
```

---

## 3. Existing Related Test Files

**Purpose:** Show examples of your team's test style so generated tests match.

### File: `tests/integration/test_user_registration.py`
```python
import pytest
import httpx
from tests.fixtures.db_helpers import clean_database

BASE_URL = "http://localhost:8000"

@pytest.mark.asyncio
async def test_user_registration_success():
    """Test successful user registration with valid data."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "SecurePass123!"
            }
        )
    
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert "id" in data
    assert "password" not in data  # Password should not be in response

@pytest.mark.asyncio
async def test_user_registration_duplicate_username():
    """Test registration fails with duplicate username."""
    # Create first user
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{BASE_URL}/api/auth/register",
            json={"username": "testuser", "email": "test1@example.com", "password": "Pass123!"}
        )
        
        # Try to create duplicate
        response = await client.post(
            f"{BASE_URL}/api/auth/register",
            json={"username": "testuser", "email": "test2@example.com", "password": "Pass123!"}
        )
    
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"].lower()
```

---

## 4. Shared Fixtures and Helpers (ACTUAL CODE)

**Purpose:** List existing test utilities that MUST BE REUSED (not recreated).

### File: `tests/fixtures/auth_helpers.py`
```python
import httpx
from typing import Dict

BASE_URL = "http://localhost:8000"

async def get_auth_token(username: str = "testuser", password: str = "testpass") -> str:
    """
    Get a valid JWT token for testing.
    Creates a test user if it doesn't exist.
    
    Returns:
        str: JWT access token
    """
    async with httpx.AsyncClient() as client:
        # Try to login
        response = await client.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": username, "password": password}
        )
        
        if response.status_code == 401:
            # User doesn't exist, create it
            await client.post(
                f"{BASE_URL}/api/auth/register",
                json={"username": username, "email": f"{username}@example.com", "password": password}
            )
            # Login again
            response = await client.post(
                f"{BASE_URL}/api/auth/login",
                json={"username": username, "password": password}
            )
        
        return response.json()["access_token"]

async def create_test_user(username: str, email: str, password: str = "TestPass123!") -> Dict:
    """
    Create a test user via the registration endpoint.
    
    Returns:
        dict: User data (id, username, email)
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/auth/register",
            json={"username": username, "email": email, "password": password}
        )
        return response.json()
```

### File: `tests/fixtures/conftest.py`
```python
import pytest
import asyncio

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def auth_client():
    """Provides an authenticated httpx client."""
    from tests.fixtures.auth_helpers import get_auth_token
    
    token = await get_auth_token()
    
    async with httpx.AsyncClient(
        headers={"Authorization": f"Bearer {token}"}
    ) as client:
        yield client
```

---

## 5. Known Edge Cases and Constraints

**Edge Cases Specific to This Feature:**
- Account lockout triggers after exactly 5 failed attempts within 1 hour
- Lockout automatically clears after 1 hour (Redis TTL)
- Admin users have same login endpoint, differentiated by `role` field in response
- Token expiration is 30 minutes (hardcoded in JWT helper)
- Passwords must be at least 8 characters (enforced at registration, not login)

**Database Constraints:**
- `username` is unique (enforced by DB unique constraint)
- `email` is unique (enforced by DB unique constraint)
- User records have soft-delete (deleted_at timestamp)

**API Behavior:**
- All error responses return JSON with `{"detail": "error message"}` structure
- Successful login returns 200 (not 201)
- Invalid credentials return generic "Invalid username or password" (no username enumeration)

---

## 6. Existing Utilities Summary (Quick Reference)

**DO REUSE THESE (already exist in codebase):**
- `tests/fixtures/auth_helpers.py::get_auth_token()` — Get JWT token
- `tests/fixtures/auth_helpers.py::create_test_user()` — Create test user
- `tests/fixtures/conftest.py::auth_client` — Authenticated HTTP client fixture
- `src/utils/jwt_helper.py::create_access_token()` — Generate JWT (source code, not test utility)

**DO NOT CREATE:**
- ❌ New login helper functions (use existing `get_auth_token()`)
- ❌ New user creation helpers (use existing `create_test_user()`)
- ❌ New JWT generation in tests (source code already has this)

---

## 7. File Naming Conventions

**For this feature, the test file should be named:**
- `tests/integration/test_auth_login.py` (API tests)

**Test function naming pattern:**
- `test_login_<scenario>` (e.g., `test_login_success`, `test_login_invalid_password`)

---

## 8. Additional Context

**Recent Changes:**
- 2025-02-10: Added account lockout feature (5 failed attempts)
- 2025-02-01: Migrated from session-based auth to JWT

**Known Issues:**
- None currently

**Performance Notes:**
- Login endpoint should respond within 200ms under normal load
- Redis check adds ~10ms latency

---

**Last Updated:** 2025-02-16
**Feature Owner:** Auth Team
**Reviewer:** QA Lead