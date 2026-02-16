# Tech Context — Team-Wide Technical Information

**Purpose:** This file contains team-wide technical standards, conventions, and infrastructure details. It is loaded ONCE per QA-GPT session and injected into multiple agents (QA Interaction, Requirements Spec, Strategy, Code Structure Planning, Scripting).

**Instructions:** Fill in the sections below with your team's actual technical stack and conventions. Be specific. The more detail you provide, the better the generated tests will match your team's style.

---

## 1. Language & Framework Versions

**Language:**
- Python 3.12.7

**Test Framework:**
- pytest 8.3.2
- pytest-asyncio 0.23.0 (if using async tests)

**Assertion Library:**
- Built-in Python `assert` statements
- pytest's assertion rewriting

**Framework Type:** (Choose ONE and delete the others)
- [ ] **UI/E2E Testing** — Playwright, Selenium, Cypress
- [x] **API Testing** — httpx, requests, FastAPI TestClient
- [ ] **Unit Testing** — pytest with mocks and fixtures

---

## 2. Project Folder Structure

**Relevant directories and their purpose:**
```
project_root/
├── src/                      # Application source code
│   ├── api/                  # FastAPI routes
│   ├── services/             # Business logic
│   └── models/               # Data models
├── tests/                    # All test code
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   ├── e2e/                  # End-to-end tests
│   └── fixtures/             # Shared test fixtures
└── utils/                    # Shared utilities
```

---

## 3. Coding Conventions

**Naming Conventions:**
- **Files:** `snake_case.py` (e.g., `test_user_login.py`)
- **Classes:** `PascalCase` (e.g., `UserLoginTest`)
- **Functions/Methods:** `snake_case` (e.g., `def test_valid_login()`)
- **Constants:** `UPPER_SNAKE_CASE` (e.g., `BASE_URL`)
- **Test Functions:** Must start with `test_` (pytest requirement)

**Import Style:**
```python
# Standard library first
import os
from datetime import datetime

# Third-party second
import pytest
import httpx

# Local imports third
from src.services.auth import AuthService
from tests.fixtures.user_factory import create_test_user
```

**Async Patterns:**
- Use `async/await` for all API calls
- Mark async test functions with `@pytest.mark.asyncio`

**Type Hints:**
- Use type hints for all function signatures
- Example: `def login(username: str, password: str) -> dict[str, Any]:`

---

## 4. Test Infrastructure

**Base URLs:**
- Local dev: `http://localhost:8000`
- Staging: `https://staging-api.example.com`
- Production: `https://api.example.com`

**Authentication Patterns:**
- JWT tokens stored in `Authorization: Bearer <token>` header
- Use `get_auth_token()` fixture to obtain valid tokens
- Test users created via `create_test_user()` fixture

**HTTP Client:**
- **DO USE:** `httpx.AsyncClient` for async API calls
- **DO NOT USE:** `requests` library (we've standardized on httpx)

**Fixture Organization:**
- Shared fixtures in `tests/fixtures/conftest.py`
- Test-specific fixtures in the test file itself
- Use `@pytest.fixture(scope="session")` for expensive setup (DB connections, etc.)

---

## 5. Existing Test Utilities

**Available Helper Functions:**
```python
# tests/fixtures/auth_helpers.py
async def get_auth_token(username: str = "testuser") -> str:
    """Returns a valid JWT token for testing."""
    
async def create_test_user(username: str, email: str) -> dict:
    """Creates a test user and returns user data."""

# tests/fixtures/api_helpers.py
async def make_api_request(
    method: str, 
    endpoint: str, 
    token: str | None = None,
    json: dict | None = None
) -> httpx.Response:
    """Wrapper around httpx.AsyncClient for API calls."""
```

**Available Fixtures:**
```python
@pytest.fixture
async def auth_client():
    """Authenticated httpx client with valid token."""
    
@pytest.fixture
async def test_db():
    """Fresh test database for each test."""
```

---

## 6. What NOT to Do

**Anti-Patterns to Avoid:**
- ❌ **DO NOT** use `requests` library — we use `httpx`
- ❌ **DO NOT** hardcode URLs — use `BASE_URL` constant
- ❌ **DO NOT** create auth logic in test files — use `get_auth_token()` fixture
- ❌ **DO NOT** use `time.sleep()` — use async `await` or `pytest-asyncio` timeouts
- ❌ **DO NOT** commit real credentials — use environment variables or test fixtures

---

## 7. Example Test Structure

**Typical API test structure:**
```python
import pytest
import httpx
from tests.fixtures.auth_helpers import get_auth_token, create_test_user

BASE_URL = "http://localhost:8000"

@pytest.mark.asyncio
async def test_user_login_success():
    """Test successful user login with valid credentials."""
    # Arrange
    user = await create_test_user(username="testuser", email="test@example.com")
    
    # Act
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "testuser", "password": "testpass123"}
        )
    
    # Assert
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"
```

---

## 8. Framework-Specific Notes

### For API Testing:
- All endpoints return JSON
- Standard status codes: 200 (OK), 201 (Created), 400 (Bad Request), 401 (Unauthorized), 404 (Not Found)
- Error responses have structure: `{"detail": "Error message"}`

### For UI/E2E Testing:
- (Fill in if applicable: browser config, page object patterns, wait strategies, etc.)

### For Unit Testing:
- (Fill in if applicable: mocking patterns, patch targets, fixture scope strategies, etc.)

---

## 9. Additional Notes

**Edge Cases to Consider:**
- Rate limiting kicks in after 100 requests/minute
- Session timeout is 30 minutes
- Max request payload size is 10MB

**Known Constraints:**
- Database uses PostgreSQL (be aware of case-sensitive string comparisons)
- Redis cache has 1-hour TTL
- Background jobs process every 5 minutes

---

**Last Updated:** [Fill in date when you last updated this file]
**Updated By:** [Your name/team name]