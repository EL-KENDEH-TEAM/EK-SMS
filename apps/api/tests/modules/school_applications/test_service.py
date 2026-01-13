"""
Unit tests for school applications service layer.

These tests cover:
- Application submission
- Applicant verification
- Principal confirmation
- Resend verification (with rate limiting)
- Application status retrieval
- Error handling and edge cases
"""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.modules.school_applications.models import ApplicationStatus
from app.modules.school_applications.service import (
    AlreadyVerifiedError,
    ApplicationNotFoundError,
    ApplicationServiceError,
    DuplicateApplicationError,
    InvalidApplicationStateError,
    InvalidEmailError,
    InvalidTokenError,
    RateLimitExceededError,
    TokenAlreadyUsedError,
    TokenExpiredError,
    _hash_token,
    confirm_principal,
    get_application_status,
    resend_verification,
    submit_application,
    verify_applicant,
)


class TestHashToken:
    """Tests for token hashing function."""

    def test_hash_token_returns_hex_string(self):
        """Hash token should return a hex string."""
        result = _hash_token("test_token")
        assert isinstance(result, str)
        # SHA-256 produces 64 character hex string
        assert len(result) == 64

    def test_hash_token_is_deterministic(self):
        """Same input should produce same hash."""
        token = "my_secure_token"
        hash1 = _hash_token(token)
        hash2 = _hash_token(token)
        assert hash1 == hash2

    def test_hash_token_different_inputs_different_outputs(self):
        """Different tokens should produce different hashes."""
        hash1 = _hash_token("token1")
        hash2 = _hash_token("token2")
        assert hash1 != hash2


class TestSubmitApplication:
    """Tests for submit_application function."""

    @pytest.mark.asyncio
    async def test_submit_application_success_principal_applicant(
        self,
        mock_db,
        sample_application_create,
        sample_application_model,
    ):
        """Successfully submit application when applicant is principal."""
        with (
            patch("app.modules.school_applications.service.repository") as mock_repo,
            patch(
                "app.modules.school_applications.service.send_applicant_verification"
            ) as mock_email,
        ):
            # Setup mocks
            mock_repo.get_by_applicant_email = AsyncMock(return_value=[])
            mock_repo.get_pending_by_school_and_city = AsyncMock(return_value=None)
            mock_repo.create = AsyncMock(return_value=sample_application_model)
            mock_repo.create_token = AsyncMock()
            mock_email.return_value = True

            # Execute
            result = await submit_application(mock_db, sample_application_create)

            # Assert
            assert result.id == sample_application_model.id
            assert result.status == ApplicationStatus.AWAITING_APPLICANT_VERIFICATION
            assert result.applicant_email == "principal@test.com"
            assert "verify" in result.message.lower()

            # Verify repository calls
            mock_repo.create.assert_called_once()
            mock_repo.create_token.assert_called_once()
            mock_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_application_success_non_principal_applicant(
        self,
        mock_db,
        sample_application_create_non_principal,
        sample_application_model_non_principal,
    ):
        """Successfully submit application when applicant is not principal."""
        with (
            patch("app.modules.school_applications.service.repository") as mock_repo,
            patch(
                "app.modules.school_applications.service.send_applicant_verification"
            ) as mock_email,
        ):
            mock_repo.get_by_applicant_email = AsyncMock(return_value=[])
            mock_repo.get_pending_by_school_and_city = AsyncMock(return_value=None)
            mock_repo.create = AsyncMock(return_value=sample_application_model_non_principal)
            mock_repo.create_token = AsyncMock()
            mock_email.return_value = True

            result = await submit_application(mock_db, sample_application_create_non_principal)

            assert result.applicant_email == "applicant@test.com"
            mock_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_application_duplicate_by_email(
        self,
        mock_db,
        sample_application_create,
        sample_application_model,
    ):
        """Reject submission when duplicate application exists for email."""
        with patch("app.modules.school_applications.service.repository") as mock_repo:
            # Return existing pending application
            sample_application_model.status = ApplicationStatus.AWAITING_APPLICANT_VERIFICATION
            mock_repo.get_by_applicant_email = AsyncMock(return_value=[sample_application_model])

            with pytest.raises(DuplicateApplicationError) as exc_info:
                await submit_application(mock_db, sample_application_create)

            assert "pending application" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_submit_application_duplicate_by_school_city(
        self,
        mock_db,
        sample_application_create,
        sample_application_model,
    ):
        """Reject submission when duplicate application exists for school+city."""
        with patch("app.modules.school_applications.service.repository") as mock_repo:
            mock_repo.get_by_applicant_email = AsyncMock(return_value=[])
            mock_repo.get_pending_by_school_and_city = AsyncMock(
                return_value=sample_application_model
            )

            with pytest.raises(DuplicateApplicationError) as exc_info:
                await submit_application(mock_db, sample_application_create)

            assert "Test School" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_submit_application_email_failure_still_succeeds(
        self,
        mock_db,
        sample_application_create,
        sample_application_model,
    ):
        """Application submission succeeds even if email fails."""
        with (
            patch("app.modules.school_applications.service.repository") as mock_repo,
            patch(
                "app.modules.school_applications.service.send_applicant_verification"
            ) as mock_email,
        ):
            mock_repo.get_by_applicant_email = AsyncMock(return_value=[])
            mock_repo.get_pending_by_school_and_city = AsyncMock(return_value=None)
            mock_repo.create = AsyncMock(return_value=sample_application_model)
            mock_repo.create_token = AsyncMock()
            mock_email.return_value = False  # Email fails

            # Should not raise
            result = await submit_application(mock_db, sample_application_create)
            assert result.id == sample_application_model.id


class TestVerifyApplicant:
    """Tests for verify_applicant function."""

    @pytest.mark.asyncio
    async def test_verify_applicant_principal_moves_to_pending_review(
        self,
        mock_db,
        sample_application_model,
        sample_verification_token,
    ):
        """When applicant is principal, verification moves to PENDING_REVIEW."""
        sample_application_model.applicant_is_principal = True
        sample_verification_token.application_id = sample_application_model.id

        with (
            patch("app.modules.school_applications.service.repository") as mock_repo,
            patch(
                "app.modules.school_applications.service.send_application_under_review"
            ) as mock_email,
        ):
            mock_repo.get_by_token = AsyncMock(return_value=sample_verification_token)
            mock_repo.get_by_id = AsyncMock(return_value=sample_application_model)
            mock_repo.mark_token_used = AsyncMock()
            mock_repo.update_status = AsyncMock()
            mock_email.return_value = True

            result = await verify_applicant(mock_db, "raw_token_value")

            assert result.status == ApplicationStatus.PENDING_REVIEW
            assert result.requires_principal_confirmation is False
            mock_repo.update_status.assert_called_once()
            # Verify principal_confirmed_at is set
            call_kwargs = mock_repo.update_status.call_args[1]
            assert "principal_confirmed_at" in call_kwargs

    @pytest.mark.asyncio
    async def test_verify_applicant_non_principal_needs_principal_confirmation(
        self,
        mock_db,
        sample_application_model_non_principal,
        sample_verification_token,
    ):
        """When applicant is not principal, moves to AWAITING_PRINCIPAL_CONFIRMATION."""
        sample_verification_token.application_id = sample_application_model_non_principal.id

        with (
            patch("app.modules.school_applications.service.repository") as mock_repo,
            patch(
                "app.modules.school_applications.service.send_principal_confirmation"
            ) as mock_email,
        ):
            mock_repo.get_by_token = AsyncMock(return_value=sample_verification_token)
            mock_repo.get_by_id = AsyncMock(return_value=sample_application_model_non_principal)
            mock_repo.mark_token_used = AsyncMock()
            mock_repo.update_status = AsyncMock()
            mock_repo.create_token = AsyncMock()
            mock_email.return_value = True

            result = await verify_applicant(mock_db, "raw_token_value")

            assert result.status == ApplicationStatus.AWAITING_PRINCIPAL_CONFIRMATION
            assert result.requires_principal_confirmation is True
            assert result.principal_email_hint is not None
            # Should create a new token for principal
            mock_repo.create_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_applicant_invalid_token(self, mock_db):
        """Raises InvalidTokenError when token not found."""
        with patch("app.modules.school_applications.service.repository") as mock_repo:
            mock_repo.get_by_token = AsyncMock(return_value=None)

            with pytest.raises(InvalidTokenError):
                await verify_applicant(mock_db, "invalid_token")

    @pytest.mark.asyncio
    async def test_verify_applicant_expired_token(
        self, mock_db, expired_token, sample_application_model
    ):
        """Raises TokenExpiredError when token is expired."""
        expired_token.application_id = sample_application_model.id

        with patch("app.modules.school_applications.service.repository") as mock_repo:
            mock_repo.get_by_token = AsyncMock(return_value=expired_token)

            with pytest.raises(TokenExpiredError):
                await verify_applicant(mock_db, "expired_token")

    @pytest.mark.asyncio
    async def test_verify_applicant_used_token(self, mock_db, used_token, sample_application_model):
        """Raises TokenAlreadyUsedError when token was already used."""
        used_token.application_id = sample_application_model.id

        with patch("app.modules.school_applications.service.repository") as mock_repo:
            mock_repo.get_by_token = AsyncMock(return_value=used_token)

            with pytest.raises(TokenAlreadyUsedError):
                await verify_applicant(mock_db, "used_token")

    @pytest.mark.asyncio
    async def test_verify_applicant_wrong_state(
        self, mock_db, sample_application_model, sample_verification_token
    ):
        """Raises InvalidApplicationStateError if not awaiting verification."""
        sample_application_model.status = ApplicationStatus.PENDING_REVIEW
        sample_verification_token.application_id = sample_application_model.id

        with patch("app.modules.school_applications.service.repository") as mock_repo:
            mock_repo.get_by_token = AsyncMock(return_value=sample_verification_token)
            mock_repo.get_by_id = AsyncMock(return_value=sample_application_model)

            with pytest.raises(InvalidApplicationStateError):
                await verify_applicant(mock_db, "token")


class TestConfirmPrincipal:
    """Tests for confirm_principal function."""

    @pytest.mark.asyncio
    async def test_confirm_principal_success(
        self,
        mock_db,
        sample_application_model_non_principal,
        sample_principal_token,
    ):
        """Successfully confirm principal moves to PENDING_REVIEW."""
        sample_application_model_non_principal.status = (
            ApplicationStatus.AWAITING_PRINCIPAL_CONFIRMATION
        )
        sample_principal_token.application_id = sample_application_model_non_principal.id

        with (
            patch("app.modules.school_applications.service.repository") as mock_repo,
            patch(
                "app.modules.school_applications.service.send_application_under_review"
            ) as mock_email,
        ):
            mock_repo.get_by_token = AsyncMock(return_value=sample_principal_token)
            mock_repo.get_by_id = AsyncMock(return_value=sample_application_model_non_principal)
            mock_repo.mark_token_used = AsyncMock()
            mock_repo.update_status = AsyncMock()
            mock_email.return_value = True

            result = await confirm_principal(mock_db, "principal_token")

            assert result.status == ApplicationStatus.PENDING_REVIEW
            assert result.school_name == "Test School"
            mock_repo.update_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_confirm_principal_wrong_state(
        self,
        mock_db,
        sample_application_model_non_principal,
        sample_principal_token,
    ):
        """Raises error if application not awaiting principal confirmation."""
        sample_application_model_non_principal.status = (
            ApplicationStatus.AWAITING_APPLICANT_VERIFICATION
        )
        sample_principal_token.application_id = sample_application_model_non_principal.id

        with patch("app.modules.school_applications.service.repository") as mock_repo:
            mock_repo.get_by_token = AsyncMock(return_value=sample_principal_token)
            mock_repo.get_by_id = AsyncMock(return_value=sample_application_model_non_principal)

            with pytest.raises(InvalidApplicationStateError):
                await confirm_principal(mock_db, "token")


class TestResendVerification:
    """Tests for resend_verification function."""

    @pytest.mark.asyncio
    async def test_resend_verification_success(
        self,
        mock_db,
        mock_redis,
        sample_application_model,
    ):
        """Successfully resend verification email."""
        with (
            patch("app.modules.school_applications.service.repository") as mock_repo,
            patch(
                "app.modules.school_applications.service.send_applicant_verification"
            ) as mock_email,
        ):
            mock_repo.get_by_id = AsyncMock(return_value=sample_application_model)
            mock_repo.delete_tokens_for_application = AsyncMock()
            mock_repo.create_token = AsyncMock()
            mock_email.return_value = True

            result = await resend_verification(
                mock_db,
                sample_application_model.id,
                "principal@test.com",
                mock_redis,
            )

            assert "resent" in result.message.lower()
            assert result.expires_at is not None
            mock_repo.delete_tokens_for_application.assert_called_once()
            mock_repo.create_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_resend_verification_wrong_email(
        self,
        mock_db,
        mock_redis,
        sample_application_model,
    ):
        """Raises InvalidEmailError when email doesn't match."""
        with patch("app.modules.school_applications.service.repository") as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=sample_application_model)

            with pytest.raises(InvalidEmailError):
                await resend_verification(
                    mock_db,
                    sample_application_model.id,
                    "wrong@email.com",
                    mock_redis,
                )

    @pytest.mark.asyncio
    async def test_resend_verification_already_verified(
        self,
        mock_db,
        mock_redis,
        sample_application_model,
    ):
        """Raises AlreadyVerifiedError when application past verification stage."""
        sample_application_model.status = ApplicationStatus.PENDING_REVIEW

        with patch("app.modules.school_applications.service.repository") as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=sample_application_model)

            with pytest.raises(AlreadyVerifiedError):
                await resend_verification(
                    mock_db,
                    sample_application_model.id,
                    "principal@test.com",
                    mock_redis,
                )

    @pytest.mark.asyncio
    async def test_resend_verification_rate_limited(
        self,
        mock_db,
        sample_application_model,
    ):
        """Raises RateLimitExceededError when too many requests."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value="3")  # At limit
        mock_redis.ttl = AsyncMock(return_value=1800)

        with patch("app.modules.school_applications.service.repository") as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=sample_application_model)

            with pytest.raises(RateLimitExceededError) as exc_info:
                await resend_verification(
                    mock_db,
                    sample_application_model.id,
                    "principal@test.com",
                    mock_redis,
                )

            assert exc_info.value.retry_after_seconds > 0

    @pytest.mark.asyncio
    async def test_resend_verification_fails_when_redis_unavailable(
        self,
        mock_db,
        sample_application_model,
    ):
        """Raises ServiceUnavailable when Redis is None (fail-closed)."""
        with patch("app.modules.school_applications.service.repository") as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=sample_application_model)

            with pytest.raises(ApplicationServiceError) as exc_info:
                await resend_verification(
                    mock_db,
                    sample_application_model.id,
                    "principal@test.com",
                    redis_client=None,  # No Redis
                )

            assert exc_info.value.status_code == 503
            assert exc_info.value.error_code == "SERVICE_UNAVAILABLE"

    @pytest.mark.asyncio
    async def test_resend_verification_application_not_found(
        self,
        mock_db,
        mock_redis,
    ):
        """Raises ApplicationNotFoundError when application doesn't exist."""
        with patch("app.modules.school_applications.service.repository") as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=None)

            with pytest.raises(ApplicationNotFoundError):
                await resend_verification(
                    mock_db,
                    uuid4(),
                    "test@email.com",
                    mock_redis,
                )


class TestGetApplicationStatus:
    """Tests for get_application_status function."""

    @pytest.mark.asyncio
    async def test_get_status_success(
        self,
        mock_db,
        sample_application_model,
    ):
        """Successfully retrieve application status."""
        with patch("app.modules.school_applications.service.repository") as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=sample_application_model)

            result = await get_application_status(
                mock_db,
                sample_application_model.id,
                "principal@test.com",
            )

            assert result.id == sample_application_model.id
            assert result.status == ApplicationStatus.AWAITING_APPLICANT_VERIFICATION
            assert result.school_name == "Test School"
            assert len(result.steps) > 0

    @pytest.mark.asyncio
    async def test_get_status_case_insensitive_email(
        self,
        mock_db,
        sample_application_model,
    ):
        """Email comparison should be case-insensitive."""
        with patch("app.modules.school_applications.service.repository") as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=sample_application_model)

            # Use different case
            result = await get_application_status(
                mock_db,
                sample_application_model.id,
                "PRINCIPAL@TEST.COM",
            )

            assert result.id == sample_application_model.id

    @pytest.mark.asyncio
    async def test_get_status_wrong_email(
        self,
        mock_db,
        sample_application_model,
    ):
        """Raises InvalidEmailError for security when email doesn't match."""
        with patch("app.modules.school_applications.service.repository") as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=sample_application_model)

            with pytest.raises(InvalidEmailError):
                await get_application_status(
                    mock_db,
                    sample_application_model.id,
                    "hacker@evil.com",
                )

    @pytest.mark.asyncio
    async def test_get_status_not_found(
        self,
        mock_db,
    ):
        """Raises ApplicationNotFoundError when application doesn't exist."""
        with patch("app.modules.school_applications.service.repository") as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=None)

            with pytest.raises(ApplicationNotFoundError):
                await get_application_status(
                    mock_db,
                    uuid4(),
                    "test@email.com",
                )

    @pytest.mark.asyncio
    async def test_get_status_steps_for_principal_applicant(
        self,
        mock_db,
        sample_application_model,
    ):
        """Status steps should not include principal confirmation for principal applicants."""
        sample_application_model.applicant_is_principal = True

        with patch("app.modules.school_applications.service.repository") as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=sample_application_model)

            result = await get_application_status(
                mock_db,
                sample_application_model.id,
                "principal@test.com",
            )

            step_names = [step.name for step in result.steps]
            assert "Principal Confirmed" not in step_names

    @pytest.mark.asyncio
    async def test_get_status_steps_for_non_principal_applicant(
        self,
        mock_db,
        sample_application_model_non_principal,
    ):
        """Status steps should include principal confirmation for non-principal applicants."""
        with patch("app.modules.school_applications.service.repository") as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=sample_application_model_non_principal)

            result = await get_application_status(
                mock_db,
                sample_application_model_non_principal.id,
                "applicant@test.com",
            )

            step_names = [step.name for step in result.steps]
            assert "Principal Confirmed" in step_names
