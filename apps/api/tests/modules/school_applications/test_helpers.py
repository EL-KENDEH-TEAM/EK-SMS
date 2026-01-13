"""
Unit tests for school applications helpers module.
"""

from unittest.mock import MagicMock

from app.modules.school_applications.helpers import (
    get_effective_applicant_email_from_model,
    get_effective_applicant_email_from_schema,
    get_effective_applicant_name_from_model,
    get_effective_applicant_name_from_schema,
)
from app.modules.school_applications.models import AdminChoice, SchoolType, StudentPopulation
from app.modules.school_applications.schemas import (
    ApplicantInfo,
    ContactInfo,
    DetailsInfo,
    LocationInfo,
    SchoolApplicationCreate,
    SchoolInfo,
)


class TestGetEffectiveApplicantEmailFromModel:
    """Tests for get_effective_applicant_email_from_model."""

    def test_returns_principal_email_when_applicant_is_principal(self):
        """When applicant is principal, return principal email."""
        app = MagicMock()
        app.applicant_is_principal = True
        app.principal_email = "principal@test.com"
        app.applicant_email = "applicant@test.com"

        result = get_effective_applicant_email_from_model(app)
        assert result == "principal@test.com"

    def test_returns_applicant_email_when_not_principal(self):
        """When applicant is not principal, return applicant email."""
        app = MagicMock()
        app.applicant_is_principal = False
        app.principal_email = "principal@test.com"
        app.applicant_email = "applicant@test.com"

        result = get_effective_applicant_email_from_model(app)
        assert result == "applicant@test.com"

    def test_fallback_to_principal_email_when_applicant_email_none(self):
        """When applicant email is None, fallback to principal email."""
        app = MagicMock()
        app.applicant_is_principal = False
        app.principal_email = "principal@test.com"
        app.applicant_email = None

        result = get_effective_applicant_email_from_model(app)
        assert result == "principal@test.com"


class TestGetEffectiveApplicantNameFromModel:
    """Tests for get_effective_applicant_name_from_model."""

    def test_returns_principal_name_when_applicant_is_principal(self):
        """When applicant is principal, return principal name."""
        app = MagicMock()
        app.applicant_is_principal = True
        app.principal_name = "Principal Name"
        app.applicant_name = "Applicant Name"

        result = get_effective_applicant_name_from_model(app)
        assert result == "Principal Name"

    def test_returns_applicant_name_when_not_principal(self):
        """When applicant is not principal, return applicant name."""
        app = MagicMock()
        app.applicant_is_principal = False
        app.principal_name = "Principal Name"
        app.applicant_name = "Applicant Name"

        result = get_effective_applicant_name_from_model(app)
        assert result == "Applicant Name"

    def test_fallback_to_principal_name_when_applicant_name_none(self):
        """When applicant name is None, fallback to principal name."""
        app = MagicMock()
        app.applicant_is_principal = False
        app.principal_name = "Principal Name"
        app.applicant_name = None

        result = get_effective_applicant_name_from_model(app)
        assert result == "Principal Name"


class TestGetEffectiveApplicantEmailFromSchema:
    """Tests for get_effective_applicant_email_from_schema."""

    def test_returns_principal_email_when_applicant_is_principal(self):
        """When applicant is principal, return principal email from contact."""
        data = SchoolApplicationCreate(
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
                school_phone="+233999888777",
                principal_name="Principal",
                principal_email="principal@test.com",
                principal_phone="+233123456789",
            ),
            applicant=ApplicantInfo(is_principal=True),
            details=DetailsInfo(reasons=["digital_records"]),
        )

        result = get_effective_applicant_email_from_schema(data)
        assert result == "principal@test.com"

    def test_returns_applicant_email_when_not_principal(self):
        """When applicant is not principal, return applicant email."""
        data = SchoolApplicationCreate(
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
                school_phone="+233999888777",
                principal_name="Principal",
                principal_email="principal@test.com",
                principal_phone="+233123456789",
            ),
            applicant=ApplicantInfo(
                is_principal=False,
                name="Applicant",
                email="applicant@test.com",
                phone="+233111222333",
                role="Staff",
                admin_choice=AdminChoice.APPLICANT,
            ),
            details=DetailsInfo(reasons=["digital_records"]),
        )

        result = get_effective_applicant_email_from_schema(data)
        assert result == "applicant@test.com"


class TestGetEffectiveApplicantNameFromSchema:
    """Tests for get_effective_applicant_name_from_schema."""

    def test_returns_principal_name_when_applicant_is_principal(self):
        """When applicant is principal, return principal name from contact."""
        data = SchoolApplicationCreate(
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
                school_phone="+233999888777",
                principal_name="Principal Name",
                principal_email="principal@test.com",
                principal_phone="+233123456789",
            ),
            applicant=ApplicantInfo(is_principal=True),
            details=DetailsInfo(reasons=["digital_records"]),
        )

        result = get_effective_applicant_name_from_schema(data)
        assert result == "Principal Name"

    def test_returns_applicant_name_when_not_principal(self):
        """When applicant is not principal, return applicant name."""
        data = SchoolApplicationCreate(
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
                school_phone="+233999888777",
                principal_name="Principal Name",
                principal_email="principal@test.com",
                principal_phone="+233123456789",
            ),
            applicant=ApplicantInfo(
                is_principal=False,
                name="Applicant Name",
                email="applicant@test.com",
                phone="+233111222333",
                role="Staff",
                admin_choice=AdminChoice.APPLICANT,
            ),
            details=DetailsInfo(reasons=["digital_records"]),
        )

        result = get_effective_applicant_name_from_schema(data)
        assert result == "Applicant Name"
