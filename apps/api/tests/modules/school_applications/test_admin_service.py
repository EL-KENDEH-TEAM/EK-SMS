"""
Tests for admin service functions.

These tests verify the business logic for admin operations including:
- Listing applications with filters
- Getting dashboard statistics
- Starting reviews
- Requesting more information
- Adding internal notes
- Approving applications
- Rejecting applications
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.modules.school_applications.models import (
    AdminChoice,
    ApplicationStatus,
    SchoolApplication,
    SchoolType,
    StudentPopulation,
)
from app.modules.school_applications.service import (
    ApplicationNotFoundError,
    CannotDecideApplicationError,
    CannotReviewApplicationError,
    admin_add_internal_note,
    admin_approve_application,
    admin_get_application_detail,
    admin_get_applications_list,
    admin_get_dashboard_stats,
    admin_reject_application,
    admin_request_more_info,
    admin_start_review,
)

# ============================================
# Fixtures
# ============================================


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def admin_id():
    """Return a consistent admin UUID for testing."""
    return UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def application_id():
    """Return a consistent application UUID for testing."""
    return uuid4()


@pytest.fixture
def sample_pending_application(application_id):
    """Create a sample pending_review application."""
    app = MagicMock(spec=SchoolApplication)
    app.id = application_id
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
    app.status = ApplicationStatus.PENDING_REVIEW
    app.submitted_at = datetime.now(UTC) - timedelta(days=1)
    app.applicant_verified_at = datetime.now(UTC) - timedelta(hours=12)
    app.principal_confirmed_at = None
    app.reviewed_at = None
    app.reviewed_by = None
    app.decision_reason = None
    app.internal_notes = None
    return app


@pytest.fixture
def sample_under_review_application(application_id, admin_id):
    """Create a sample under_review application."""
    app = MagicMock(spec=SchoolApplication)
    app.id = application_id
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
    app.status = ApplicationStatus.UNDER_REVIEW
    app.submitted_at = datetime.now(UTC) - timedelta(days=1)
    app.applicant_verified_at = datetime.now(UTC) - timedelta(hours=12)
    app.principal_confirmed_at = None
    app.reviewed_at = datetime.now(UTC) - timedelta(hours=1)
    app.reviewed_by = admin_id
    app.decision_reason = None
    app.internal_notes = None
    return app


# ============================================
# Test admin_get_applications_list
# ============================================


@pytest.mark.asyncio
async def test_admin_get_applications_list_success(mock_db, sample_pending_application):
    """Test successful listing of applications."""
    with patch("app.modules.school_applications.service.repository") as mock_repo:
        mock_repo.get_applications_for_admin = AsyncMock(
            return_value=([sample_pending_application], 1)
        )

        result = await admin_get_applications_list(
            mock_db,
            status=ApplicationStatus.PENDING_REVIEW,
            skip=0,
            limit=20,
        )

        assert result["total"] == 1
        assert len(result["applications"]) == 1
        assert result["skip"] == 0
        assert result["limit"] == 20
        mock_repo.get_applications_for_admin.assert_called_once()


@pytest.mark.asyncio
async def test_admin_get_applications_list_with_filters(mock_db):
    """Test listing with various filters."""
    with patch("app.modules.school_applications.service.repository") as mock_repo:
        mock_repo.get_applications_for_admin = AsyncMock(return_value=([], 0))

        result = await admin_get_applications_list(
            mock_db,
            status=ApplicationStatus.PENDING_REVIEW,
            country_code="GH",
            search="Test School",
            sort_by="school_name",
            sort_order="desc",
            skip=10,
            limit=50,
        )

        assert result["total"] == 0
        assert result["applications"] == []
        mock_repo.get_applications_for_admin.assert_called_once_with(
            mock_db,
            status=ApplicationStatus.PENDING_REVIEW,
            country_code="GH",
            search="Test School",
            sort_by="school_name",
            sort_order="desc",
            skip=10,
            limit=50,
        )


@pytest.mark.asyncio
async def test_admin_get_applications_list_limit_cap(mock_db):
    """Test that limit is capped at 100."""
    with patch("app.modules.school_applications.service.repository") as mock_repo:
        mock_repo.get_applications_for_admin = AsyncMock(return_value=([], 0))

        result = await admin_get_applications_list(mock_db, limit=200)

        # Limit should be capped at 100
        assert result["limit"] == 100


# ============================================
# Test admin_get_dashboard_stats
# ============================================


@pytest.mark.asyncio
async def test_admin_get_dashboard_stats_success(mock_db):
    """Test successful retrieval of dashboard statistics."""
    expected_stats = {
        "pending_review": 5,
        "under_review": 2,
        "more_info_requested": 1,
        "approved_this_week": 3,
        "total_this_month": 10,
        "avg_review_time_days": 2.5,
    }

    with patch("app.modules.school_applications.service.repository") as mock_repo:
        mock_repo.get_dashboard_stats = AsyncMock(return_value=expected_stats)

        result = await admin_get_dashboard_stats(mock_db)

        assert result == expected_stats
        mock_repo.get_dashboard_stats.assert_called_once_with(mock_db)


# ============================================
# Test admin_get_application_detail
# ============================================


@pytest.mark.asyncio
async def test_admin_get_application_detail_success(
    mock_db, application_id, sample_pending_application
):
    """Test successful retrieval of application details."""
    with patch("app.modules.school_applications.service.repository") as mock_repo:
        mock_repo.get_by_id = AsyncMock(return_value=sample_pending_application)

        result = await admin_get_application_detail(mock_db, application_id)

        assert result == sample_pending_application
        mock_repo.get_by_id.assert_called_once_with(mock_db, application_id)


@pytest.mark.asyncio
async def test_admin_get_application_detail_not_found(mock_db, application_id):
    """Test error when application doesn't exist."""
    with patch("app.modules.school_applications.service.repository") as mock_repo:
        mock_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(ApplicationNotFoundError):
            await admin_get_application_detail(mock_db, application_id)


# ============================================
# Test admin_start_review
# ============================================


@pytest.mark.asyncio
async def test_admin_start_review_success(
    mock_db, application_id, admin_id, sample_pending_application
):
    """Test successful start of review."""
    updated_app = MagicMock(spec=SchoolApplication)
    updated_app.id = application_id
    updated_app.status = ApplicationStatus.UNDER_REVIEW
    updated_app.reviewed_by = admin_id
    updated_app.reviewed_at = datetime.now(UTC)

    with patch("app.modules.school_applications.service.repository") as mock_repo:
        mock_repo.get_by_id = AsyncMock(return_value=sample_pending_application)
        mock_repo.update_application_for_review = AsyncMock(return_value=updated_app)

        result = await admin_start_review(mock_db, application_id, admin_id)

        assert result.status == ApplicationStatus.UNDER_REVIEW
        assert result.reviewed_by == admin_id
        mock_repo.update_application_for_review.assert_called_once()


@pytest.mark.asyncio
async def test_admin_start_review_wrong_status(
    mock_db, application_id, admin_id, sample_under_review_application
):
    """Test error when application is not in pending_review status."""
    with patch("app.modules.school_applications.service.repository") as mock_repo:
        mock_repo.get_by_id = AsyncMock(return_value=sample_under_review_application)

        with pytest.raises(CannotReviewApplicationError):
            await admin_start_review(mock_db, application_id, admin_id)


@pytest.mark.asyncio
async def test_admin_start_review_not_found(mock_db, application_id, admin_id):
    """Test error when application doesn't exist."""
    with patch("app.modules.school_applications.service.repository") as mock_repo:
        mock_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(ApplicationNotFoundError):
            await admin_start_review(mock_db, application_id, admin_id)


# ============================================
# Test admin_request_more_info
# ============================================


@pytest.mark.asyncio
async def test_admin_request_more_info_success(
    mock_db, application_id, admin_id, sample_under_review_application
):
    """Test successful request for more information."""
    updated_app = MagicMock(spec=SchoolApplication)
    updated_app.id = application_id
    updated_app.status = ApplicationStatus.MORE_INFO_REQUESTED
    updated_app.decision_reason = "Please provide documentation"

    with (
        patch("app.modules.school_applications.service.repository") as mock_repo,
        patch(
            "app.core.email.send_more_info_requested",
            new_callable=AsyncMock,
        ) as mock_email,
    ):
        mock_repo.get_by_id = AsyncMock(return_value=sample_under_review_application)
        mock_repo.update_application_decision = AsyncMock(return_value=updated_app)
        mock_email.return_value = True

        result = await admin_request_more_info(
            mock_db,
            application_id,
            admin_id,
            "Please provide documentation",
        )

        assert result.status == ApplicationStatus.MORE_INFO_REQUESTED
        mock_repo.update_application_decision.assert_called_once()


@pytest.mark.asyncio
async def test_admin_request_more_info_wrong_status(mock_db, application_id, admin_id):
    """Test error when application is in wrong status."""
    approved_app = MagicMock(spec=SchoolApplication)
    approved_app.id = application_id
    approved_app.status = ApplicationStatus.APPROVED
    approved_app.applicant_is_principal = True
    approved_app.principal_email = "principal@test.com"
    approved_app.principal_name = "John Principal"

    with patch("app.modules.school_applications.service.repository") as mock_repo:
        mock_repo.get_by_id = AsyncMock(return_value=approved_app)

        with pytest.raises(CannotDecideApplicationError):
            await admin_request_more_info(
                mock_db,
                application_id,
                admin_id,
                "Please provide documentation",
            )


# ============================================
# Test admin_add_internal_note
# ============================================


@pytest.mark.asyncio
async def test_admin_add_internal_note_success(
    mock_db, application_id, admin_id, sample_pending_application
):
    """Test successful addition of internal note."""
    expected_note = {
        "note": "Verified school registration",
        "created_by": str(admin_id),
        "created_at": datetime.now(UTC).isoformat(),
    }

    with patch("app.modules.school_applications.service.repository") as mock_repo:
        mock_repo.get_by_id = AsyncMock(return_value=sample_pending_application)
        mock_repo.add_internal_note = AsyncMock(return_value=expected_note)

        result = await admin_add_internal_note(
            mock_db,
            application_id,
            admin_id,
            "Verified school registration",
        )

        assert result["note"] == "Verified school registration"
        assert result["created_by"] == str(admin_id)
        mock_repo.add_internal_note.assert_called_once()


@pytest.mark.asyncio
async def test_admin_add_internal_note_not_found(mock_db, application_id, admin_id):
    """Test error when application doesn't exist."""
    with patch("app.modules.school_applications.service.repository") as mock_repo:
        mock_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(ApplicationNotFoundError):
            await admin_add_internal_note(
                mock_db,
                application_id,
                admin_id,
                "Test note",
            )


# ============================================
# Test admin_reject_application
# ============================================


@pytest.mark.asyncio
async def test_admin_reject_application_success(
    mock_db, application_id, admin_id, sample_under_review_application
):
    """Test successful rejection of application."""
    rejected_app = MagicMock(spec=SchoolApplication)
    rejected_app.id = application_id
    rejected_app.status = ApplicationStatus.REJECTED
    rejected_app.decision_reason = "Unable to verify school"

    with (
        patch("app.modules.school_applications.service.repository") as mock_repo,
        patch(
            "app.core.email.send_application_rejected",
            new_callable=AsyncMock,
        ) as mock_email,
    ):
        mock_repo.get_by_id = AsyncMock(return_value=sample_under_review_application)
        mock_repo.update_application_decision = AsyncMock(return_value=rejected_app)
        mock_email.return_value = True

        result = await admin_reject_application(
            mock_db,
            application_id,
            admin_id,
            "Unable to verify school registration with Ministry of Education.",
        )

        assert result.status == ApplicationStatus.REJECTED
        mock_email.assert_called_once()


@pytest.mark.asyncio
async def test_admin_reject_application_not_found(mock_db, application_id, admin_id):
    """Test error when application doesn't exist."""
    with patch("app.modules.school_applications.service.repository") as mock_repo:
        mock_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(ApplicationNotFoundError):
            await admin_reject_application(
                mock_db,
                application_id,
                admin_id,
                "Rejection reason",
            )


# ============================================
# Test admin_approve_application
# ============================================


@pytest.mark.asyncio
async def test_admin_approve_application_success(
    mock_db, application_id, admin_id, sample_under_review_application
):
    """Test successful approval of application."""
    approved_app = MagicMock(spec=SchoolApplication)
    approved_app.id = application_id
    approved_app.status = ApplicationStatus.APPROVED

    # Mock school and user for provisioning
    mock_school = MagicMock()
    mock_school.id = str(uuid4())
    mock_school.name = "Test School"

    mock_user = MagicMock()
    mock_user.id = str(uuid4())
    mock_user.email = "principal@test.com"

    with (
        patch("app.modules.school_applications.service.repository") as mock_repo,
        patch(
            "app.core.email.send_application_approved",
            new_callable=AsyncMock,
        ) as mock_email,
        patch("app.modules.users.repository.UserRepository") as mock_user_repo,
        patch("app.modules.schools.repository.SchoolRepository") as mock_school_repo,
        patch("app.core.security.hash_password") as mock_hash,
    ):
        mock_repo.get_by_id = AsyncMock(return_value=sample_under_review_application)
        mock_repo.update_application_decision = AsyncMock(return_value=approved_app)
        mock_email.return_value = True

        # Mock user/school provisioning
        mock_user_repo.get_by_email = AsyncMock(return_value=None)  # No existing user
        mock_user_repo.create = AsyncMock(return_value=mock_user)
        mock_school_repo.create = AsyncMock(return_value=mock_school)
        mock_hash.return_value = "hashed_password"

        result = await admin_approve_application(
            mock_db,
            application_id,
            admin_id,
        )

        assert result["id"] == application_id
        assert "school_id" in result
        assert "admin_user_id" in result
        assert "message" in result
        mock_email.assert_called_once()
        mock_school_repo.create.assert_called_once()
        mock_user_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_admin_approve_application_not_found(mock_db, application_id, admin_id):
    """Test error when application doesn't exist."""
    with patch("app.modules.school_applications.service.repository") as mock_repo:
        mock_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(ApplicationNotFoundError):
            await admin_approve_application(
                mock_db,
                application_id,
                admin_id,
            )


@pytest.mark.asyncio
async def test_admin_approve_application_wrong_status(mock_db, application_id, admin_id):
    """Test error when application is in wrong status."""
    approved_app = MagicMock(spec=SchoolApplication)
    approved_app.id = application_id
    approved_app.status = ApplicationStatus.APPROVED
    approved_app.applicant_is_principal = True
    approved_app.admin_choice = None

    with patch("app.modules.school_applications.service.repository") as mock_repo:
        mock_repo.get_by_id = AsyncMock(return_value=approved_app)

        with pytest.raises(CannotDecideApplicationError):
            await admin_approve_application(
                mock_db,
                application_id,
                admin_id,
            )


@pytest.mark.asyncio
async def test_admin_approve_non_principal_applicant(mock_db, application_id, admin_id):
    """Test approval where applicant is not principal but will be admin."""
    app = MagicMock(spec=SchoolApplication)
    app.id = application_id
    app.school_name = "Test School"
    app.year_established = 2000
    app.school_type = SchoolType.PUBLIC
    app.student_population = StudentPopulation.FROM_100_TO_300
    app.country_code = "GH"
    app.city = "Accra"
    app.address = "123 Test Street"
    app.school_phone = "+233123456789"
    app.school_email = "school@test.com"
    app.online_presence = None
    app.status = ApplicationStatus.UNDER_REVIEW
    app.applicant_is_principal = False
    app.admin_choice = AdminChoice.APPLICANT
    app.applicant_name = "Jane Applicant"
    app.applicant_email = "applicant@test.com"
    app.principal_name = "John Principal"
    app.principal_email = "principal@test.com"
    app.principal_phone = "+233987654321"

    approved_app = MagicMock(spec=SchoolApplication)
    approved_app.id = application_id
    approved_app.status = ApplicationStatus.APPROVED

    # Mock school and user for provisioning
    mock_school = MagicMock()
    mock_school.id = str(uuid4())
    mock_school.name = "Test School"

    mock_user = MagicMock()
    mock_user.id = str(uuid4())
    mock_user.email = "applicant@test.com"

    with (
        patch("app.modules.school_applications.service.repository") as mock_repo,
        patch(
            "app.core.email.send_application_approved",
            new_callable=AsyncMock,
        ) as mock_email,
        patch("app.modules.users.repository.UserRepository") as mock_user_repo,
        patch("app.modules.schools.repository.SchoolRepository") as mock_school_repo,
        patch("app.core.security.hash_password") as mock_hash,
    ):
        mock_repo.get_by_id = AsyncMock(return_value=app)
        mock_repo.update_application_decision = AsyncMock(return_value=approved_app)
        mock_email.return_value = True

        # Mock user/school provisioning
        mock_user_repo.get_by_email = AsyncMock(return_value=None)  # No existing user
        mock_user_repo.create = AsyncMock(return_value=mock_user)
        mock_school_repo.create = AsyncMock(return_value=mock_school)
        mock_hash.return_value = "hashed_password"

        result = await admin_approve_application(
            mock_db,
            application_id,
            admin_id,
        )

        # Verify result contains expected keys
        assert "id" in result
        assert "school_id" in result
        assert "admin_user_id" in result

        # Email should be sent to the applicant (designated admin)
        mock_email.assert_called_once()
        call_args = mock_email.call_args
        assert call_args[1]["to_email"] == "applicant@test.com"
        assert call_args[1]["admin_name"] == "Jane Applicant"
