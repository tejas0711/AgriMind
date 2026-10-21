"""
Unit and integration tests for AgriMind Phase 8:
PostgreSQL persistence, user accounts, JWT authentication, and strict cross-user authorization.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.db.models import User, SavedReport
from app.core.security import verify_password, get_password_hash

# Set up an isolated in-memory SQLite database for test execution
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Create all tables before each test and drop them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Provide a TestClient with overridden get_db dependency."""
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# =========================================================================
# 1. Password Hashing and Security Utility Tests
# =========================================================================

def test_password_hashing():
    """Ensure passwords are cryptographically hashed and never stored in plain text."""
    plain = "KisanPassword123"
    hashed = get_password_hash(plain)

    assert hashed != plain
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


# =========================================================================
# 2. User Registration and Authentication Flow Tests
# =========================================================================

def test_user_registration(client):
    """Test user registration endpoint with valid data."""
    payload = {
        "email": "ram.patil@example.com",
        "full_name": "Ram Patil",
        "password": "SecretPassword123",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "ram.patil@example.com"
    assert data["user"]["full_name"] == "Ram Patil"
    assert "id" in data["user"]
    # Ensure hashed_password is NOT exposed in the API response
    assert "hashed_password" not in data["user"]


def test_user_registration_duplicate_email(client):
    """Ensure duplicate email registration is rejected with 409 Conflict."""
    payload = {
        "email": "sita.sharma@example.com",
        "full_name": "Sita Sharma",
        "password": "Password123",
    }
    res1 = client.post("/api/auth/register", json=payload)
    assert res1.status_code == 201

    payload_dup = {
        "email": "sita.sharma@example.com",
        "full_name": "Sita Sharma Duplicate",
        "password": "Password456",
    }
    res2 = client.post("/api/auth/register", json=payload_dup)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"].lower()


def test_user_login_success(client):
    """Test successful login returns a valid JWT bearer token."""
    # Register first
    client.post(
        "/api/auth/register",
        json={"email": "vikram@example.com", "full_name": "Vikram Singh", "password": "MySecurePassword"},
    )

    # Login
    login_res = client.post(
        "/api/auth/login",
        json={"email": "vikram@example.com", "password": "MySecurePassword"},
    )
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "vikram@example.com"


def test_user_login_invalid_password(client):
    """Test login failure with wrong password returns 401 Unauthorized."""
    client.post(
        "/api/auth/register",
        json={"email": "anita@example.com", "password": "CorrectPassword"},
    )

    login_res = client.post(
        "/api/auth/login",
        json={"email": "anita@example.com", "password": "WrongPassword"},
    )
    assert login_res.status_code == 401
    assert "incorrect email or password" in login_res.json()["detail"].lower()


def test_get_current_user_me(client):
    """Test /api/auth/me returns currently authenticated user details."""
    reg = client.post(
        "/api/auth/register",
        json={"email": "kavita@farm.in", "full_name": "Kavita", "password": "PassWord123"},
    )
    token = reg.json()["access_token"]

    # Valid token
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "kavita@farm.in"
    assert me_res.json()["full_name"] == "Kavita"

    # Missing token
    unauth_res = client.get("/api/auth/me")
    assert unauth_res.status_code == 401


# =========================================================================
# 3. Report Persistence, Retrieval, and Cross-User Authorization Tests
# =========================================================================

def test_save_report_unauthenticated_fails(client):
    """Ensure saving a report requires authentication."""
    report_data = {
        "title": "Field 1 Report",
        "soil_data": {"nitrogen": 210, "ph": 6.8},
        "deficiencies": [{"nutrient": "nitrogen", "status": "LOW"}],
    }
    res = client.post("/api/reports", json=report_data)
    assert res.status_code == 401


def test_save_and_retrieve_report(client):
    """Test saving and retrieving a soil report by owner."""
    reg = client.post(
        "/api/auth/register",
        json={"email": "user.one@example.com", "password": "PasswordOne123"},
    )
    token = reg.json()["access_token"]
    auth_header = {"Authorization": f"Bearer {token}"}

    report_payload = {
        "title": "North Plot - Kharif 2026",
        "farm_name": "Patil Family Farm",
        "location_name": "Nagpur, Maharashtra",
        "selected_crop": "Wheat",
        "soil_data": {
            "nitrogen": 210.0,
            "phosphorus": 14.5,
            "potassium": 290.0,
            "ph": 7.2,
            "organic_carbon": 0.45,
        },
        "deficiencies": [
            {"nutrient": "nitrogen", "value": 210.0, "status": "LOW", "unit": "kg/ha"},
            {"nutrient": "phosphorus", "value": 14.5, "status": "MEDIUM", "unit": "kg/ha"},
        ],
        "crop_scores": [
            {"crop": "Wheat", "score": 88, "suitability": "HIGH"},
        ],
        "fertilizer_options": [
            {"product": "Urea", "dosage": "110 kg/ha", "type": "chemical"},
        ],
        "application_window": {"apply_today": "GO", "reasoning": "Clear weather"},
        "notes": "Cotton post-harvest soil sample",
    }

    # Save report
    save_res = client.post("/api/reports", json=report_payload, headers=auth_header)
    assert save_res.status_code == 201
    saved = save_res.json()
    report_id = saved["id"]
    assert saved["title"] == "North Plot - Kharif 2026"
    assert saved["farm_name"] == "Patil Family Farm"
    assert saved["selected_crop"] == "Wheat"
    assert saved["soil_data"]["nitrogen"] == 210.0

    # List reports
    list_res = client.get("/api/reports", headers=auth_header)
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) == 1
    assert items[0]["id"] == report_id
    assert items[0]["title"] == "North Plot - Kharif 2026"
    assert items[0]["farm_name"] == "Patil Family Farm"

    # Get single report detail
    detail_res = client.get(f"/api/reports/{report_id}", headers=auth_header)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == report_id
    assert detail["notes"] == "Cotton post-harvest soil sample"
    assert len(detail["deficiencies"]) == 2
    assert detail["crop_scores"][0]["crop"] == "Wheat"


def test_cross_user_access_denial(client):
    """
    CRITICAL SECURITY TEST:
    Verify that User B CANNOT read, modify, or delete a report saved by User A.
    Must return 403 Forbidden.
    """
    # 1. Create User A and save a report
    user_a = client.post(
        "/api/auth/register",
        json={"email": "farmer.a@example.com", "password": "PasswordA123"},
    ).json()
    token_a = user_a["access_token"]

    report_a = client.post(
        "/api/reports",
        json={
            "title": "Private Farm A",
            "soil_data": {"nitrogen": 180, "ph": 6.5},
            "notes": "Secret farm notes",
        },
        headers={"Authorization": f"Bearer {token_a}"},
    ).json()
    report_id_a = report_a["id"]

    # 2. Create User B
    user_b = client.post(
        "/api/auth/register",
        json={"email": "farmer.b@example.com", "password": "PasswordB123"},
    ).json()
    token_b = user_b["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. User B lists reports -> should NOT see User A's report
    list_b = client.get("/api/reports", headers=headers_b).json()
    assert len(list_b) == 0

    # 4. User B attempts to access User A's report directly -> 403 Forbidden
    cross_read_res = client.get(f"/api/reports/{report_id_a}", headers=headers_b)
    assert cross_read_res.status_code == 403
    assert "not authorized" in cross_read_res.json()["detail"].lower()

    # 5. User B attempts to delete User A's report -> 403 Forbidden
    cross_delete_res = client.delete(f"/api/reports/{report_id_a}", headers=headers_b)
    assert cross_delete_res.status_code == 403
    assert "not authorized" in cross_delete_res.json()["detail"].lower()

    # 6. Verify User A's report still exists untouched
    verify_a = client.get(f"/api/reports/{report_id_a}", headers={"Authorization": f"Bearer {token_a}"})
    assert verify_a.status_code == 200
    assert verify_a.json()["title"] == "Private Farm A"


def test_delete_report_by_owner(client):
    """Test owner can delete their own report and subsequent gets return 404."""
    user = client.post(
        "/api/auth/register",
        json={"email": "farmer.c@example.com", "password": "PasswordC123"},
    ).json()
    token = user["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    report = client.post(
        "/api/reports",
        json={
            "title": "Report to be deleted",
            "soil_data": {"ph": 7.0},
        },
        headers=headers,
    ).json()
    report_id = report["id"]

    # Delete
    del_res = client.delete(f"/api/reports/{report_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"

    # Subsequent GET should return 404
    get_res = client.get(f"/api/reports/{report_id}", headers=headers)
    assert get_res.status_code == 404
