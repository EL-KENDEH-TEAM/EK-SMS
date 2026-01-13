"""
Fixtures for school applications tests.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.modules.school_applications.models import (
    AdminChoice,
    ApplicationStatus,
    SchoolApplication,
    SchoolType,
    StudentPopulation,
    TokenType,
    VerificationToken,
)
from app.modules.school_applications.schemas import (
    ApplicantInfo,
    ContactInfo,
    DetailsInfo,
    LocationInfo,
    OnlinePresenceItem,
    SchoolApplicationCreate,
    SchoolInfo,
)


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.get = AsyncMock()
    db.execute = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.incr = AsyncMock()
    redis.expire = AsyncMock()
    redis.ttl = AsyncMock(return_value=3600)
    redis.pipeline = MagicMock()
    pipe = AsyncMock()
    pipe.incr = MagicMock()
    pipe.expire = MagicMock()
    pipe.execute = AsyncMock()
    redis.pipeline.return_value = pipe
    return redis


@pytest.fixture
def sample_application_create():
    """Create a sample application create request (applicant is principal)."""
    return SchoolApplicationCreate(
        school=SchoolInfo(
            name="Test School",
            year_established=2000,
            school_type=SchoolType.PUBLIC,
            student_population=StudentPopulation.FROM_100_TO_300,
        ),
        location=LocationInfo(
            country_code="GH",
            city="Accra",
            address="123 Test Street",
        ),
        contact=ContactInfo(
            school_phone="+233123456789",
            school_email="school@test.com",
            principal_name="John Principal",
            principal_email="principal@test.com",
            principal_phone="+233987654321",
        ),
        applicant=ApplicantInfo(
            is_principal=True,
        ),
        details=DetailsInfo(
            online_presence=[OnlinePresenceItem(type="website", url="https://test.com")],
            reasons=["digital_records", "transparency"],
            other_reason=None,
        ),
    )


@pytest.fixture
def sample_application_create_non_principal():
    """Create a sample application create request (applicant is NOT principal)."""
    return SchoolApplicationCreate(
        school=SchoolInfo(
            name="Test School",
            year_established=2000,
            school_type=SchoolType.PUBLIC,
            student_population=StudentPopulation.FROM_100_TO_300,
        ),
        location=LocationInfo(
            country_code="GH",
            city="Accra",
            address="123 Test Street",
        ),
        contact=ContactInfo(
            school_phone="+233123456789",
            school_email="school@test.com",
            principal_name="John Principal",
            principal_email="principal@test.com",
            principal_phone="+233987654321",
        ),
        applicant=ApplicantInfo(
            is_principal=False,
            name="Jane Applicant",
            email="applicant@test.com",
            phone="+233111222333",
            role="IT Administrator",
            admin_choice=AdminChoice.APPLICANT,
        ),
        details=DetailsInfo(
            online_presence=None,
            reasons=["digital_records"],
            other_reason=None,
        ),
    )


@pytest.fixture
def sample_application_model():
    """Create a sample application model (applicant is principal)."""
    app = MagicMock(spec=SchoolApplication)
    app.id = uuid4()
    app.school_name = "Test School"
    app.year_established = 2000
    app.school_type = SchoolType.PUBLIC
    app.student_population = StudentPopulation.FROM_100_TO_300
    app.country_code = "GH"
    app.city = "Accra"
    app.address = "123 Test Street"
    app.school_phone = "+233123456789"
    app.school_email = "school@test.com"
    app.principal_name = "John Principal"
    app.principal_email = "principal@test.com"
    app.principal_phone = "+233987654321"
    app.applicant_is_principal = True
    app.applicant_name = None
    app.applicant_email = None
    app.applicant_phone = None
    app.applicant_role = None
    app.admin_choice = None
    app.online_presence = [{"type": "website", "url": "https://test.com"}]
    app.reasons = ["digital_records", "transparency"]
    app.other_reason = None
    app.status = ApplicationStatus.AWAITING_APPLICANT_VERIFICATION
    app.submitted_at = datetime.now(UTC)
    app.applicant_verified_at = None
    app.principal_confirmed_at = None
    app.reviewed_at = None
    app.reviewed_by = None
    app.decision_reason = None
    app.reminder_sent_at = None
    return app


@pytest.fixture
def sample_application_model_non_principal():
    """Create a sample application model (applicant is NOT principal)."""
    app = MagicMock(spec=SchoolApplication)
    app.id = uuid4()
    app.school_name = "Test School"
    app.year_established = 2000
    app.school_type = SchoolType.PUBLIC
    app.student_population = StudentPopulation.FROM_100_TO_300
    app.country_code = "GH"
    app.city = "Accra"
    app.address = "123 Test Street"
    app.school_phone = "+233123456789"
    app.school_email = "school@test.com"
    app.principal_name = "John Principal"
    app.principal_email = "principal@test.com"
    app.principal_phone = "+233987654321"
    app.applicant_is_principal = False
    app.applicant_name = "Jane Applicant"
    app.applicant_email = "applicant@test.com"
    app.applicant_phone = "+233111222333"
    app.applicant_role = "IT Administrator"
    app.admin_choice = AdminChoice.APPLICANT
    app.online_presence = None
    app.reasons = ["digital_records"]
    app.other_reason = None
    app.status = ApplicationStatus.AWAITING_APPLICANT_VERIFICATION
    app.submitted_at = datetime.now(UTC)
    app.applicant_verified_at = None
    app.principal_confirmed_at = None
    app.reviewed_at = None
    app.reviewed_by = None
    app.decision_reason = None
    app.reminder_sent_at = None
    return app


@pytest.fixture
def sample_verification_token():
    """Create a sample verification token."""
    token = MagicMock(spec=VerificationToken)
    token.id = uuid4()
    token.application_id = uuid4()
    token.token = "hashed_token_value"
    token.token_type = TokenType.APPLICANT_VERIFICATION
    token.expires_at = datetime.now(UTC) + timedelta(hours=72)
    token.used_at = None
    token.created_at = datetime.now(UTC)
    return token


@pytest.fixture
def sample_principal_token():
    """Create a sample principal confirmation token."""
    token = MagicMock(spec=VerificationToken)
    token.id = uuid4()
    token.application_id = uuid4()
    token.token = "hashed_principal_token"
    token.token_type = TokenType.PRINCIPAL_CONFIRMATION
    token.expires_at = datetime.now(UTC) + timedelta(hours=72)
    token.used_at = None
    token.created_at = datetime.now(UTC)
    return token


@pytest.fixture
def expired_token():
    """Create an expired verification token."""
    token = MagicMock(spec=VerificationToken)
    token.id = uuid4()
    token.application_id = uuid4()
    token.token = "expired_token_hash"
    token.token_type = TokenType.APPLICANT_VERIFICATION
    token.expires_at = datetime.now(UTC) - timedelta(hours=1)  # Expired
    token.used_at = None
    token.created_at = datetime.now(UTC) - timedelta(hours=73)
    return token


@pytest.fixture
def used_token():
    """Create an already-used verification token."""
    token = MagicMock(spec=VerificationToken)
    token.id = uuid4()
    token.application_id = uuid4()
    token.token = "used_token_hash"
    token.token_type = TokenType.APPLICANT_VERIFICATION
    token.expires_at = datetime.now(UTC) + timedelta(hours=72)
    token.used_at = datetime.now(UTC) - timedelta(hours=1)  # Already used
    token.created_at = datetime.now(UTC) - timedelta(hours=2)
    return token
