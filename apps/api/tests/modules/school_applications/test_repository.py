"""
Unit tests for school applications repository layer.

These tests focus on the state machine transitions and validation logic.
"""

from app.modules.school_applications.models import ApplicationStatus
from app.modules.school_applications.repository import (
    VALID_STATUS_TRANSITIONS,
    InvalidStatusTransitionError,
)


class TestStatusTransitions:
    """Tests for status transition state machine."""

    def test_valid_transitions_from_awaiting_applicant_verification(self):
        """Verify valid transitions from AWAITING_APPLICANT_VERIFICATION."""
        valid = VALID_STATUS_TRANSITIONS[ApplicationStatus.AWAITING_APPLICANT_VERIFICATION]
        assert ApplicationStatus.AWAITING_PRINCIPAL_CONFIRMATION in valid
        assert ApplicationStatus.PENDING_REVIEW in valid
        assert ApplicationStatus.EXPIRED in valid
        # Invalid transitions
        assert ApplicationStatus.APPROVED not in valid
        assert ApplicationStatus.REJECTED not in valid
        assert ApplicationStatus.UNDER_REVIEW not in valid

    def test_valid_transitions_from_awaiting_principal_confirmation(self):
        """Verify valid transitions from AWAITING_PRINCIPAL_CONFIRMATION."""
        valid = VALID_STATUS_TRANSITIONS[ApplicationStatus.AWAITING_PRINCIPAL_CONFIRMATION]
        assert ApplicationStatus.PENDING_REVIEW in valid
        assert ApplicationStatus.EXPIRED in valid
        # Invalid transitions
        assert ApplicationStatus.AWAITING_APPLICANT_VERIFICATION not in valid
        assert ApplicationStatus.APPROVED not in valid

    def test_valid_transitions_from_pending_review(self):
        """Verify valid transitions from PENDING_REVIEW."""
        valid = VALID_STATUS_TRANSITIONS[ApplicationStatus.PENDING_REVIEW]
        assert ApplicationStatus.UNDER_REVIEW in valid
        assert ApplicationStatus.APPROVED in valid
        assert ApplicationStatus.REJECTED in valid
        # Invalid transitions
        assert ApplicationStatus.AWAITING_APPLICANT_VERIFICATION not in valid
        assert ApplicationStatus.EXPIRED not in valid

    def test_valid_transitions_from_under_review(self):
        """Verify valid transitions from UNDER_REVIEW."""
        valid = VALID_STATUS_TRANSITIONS[ApplicationStatus.UNDER_REVIEW]
        assert ApplicationStatus.MORE_INFO_REQUESTED in valid
        assert ApplicationStatus.APPROVED in valid
        assert ApplicationStatus.REJECTED in valid
        # Invalid transitions
        assert ApplicationStatus.PENDING_REVIEW not in valid

    def test_valid_transitions_from_more_info_requested(self):
        """Verify valid transitions from MORE_INFO_REQUESTED."""
        valid = VALID_STATUS_TRANSITIONS[ApplicationStatus.MORE_INFO_REQUESTED]
        assert ApplicationStatus.UNDER_REVIEW in valid
        assert ApplicationStatus.EXPIRED in valid
        assert ApplicationStatus.REJECTED in valid
        # Invalid transitions
        assert ApplicationStatus.APPROVED not in valid

    def test_terminal_states_have_no_transitions(self):
        """Terminal states should have no valid transitions."""
        assert VALID_STATUS_TRANSITIONS[ApplicationStatus.APPROVED] == set()
        assert VALID_STATUS_TRANSITIONS[ApplicationStatus.REJECTED] == set()
        assert VALID_STATUS_TRANSITIONS[ApplicationStatus.EXPIRED] == set()

    def test_all_statuses_are_in_transition_map(self):
        """Every status should be a key in the transition map."""
        for status in ApplicationStatus:
            assert status in VALID_STATUS_TRANSITIONS


class TestInvalidStatusTransitionError:
    """Tests for InvalidStatusTransitionError."""

    def test_error_message_contains_both_statuses(self):
        """Error message should contain current and new status."""
        error = InvalidStatusTransitionError(
            ApplicationStatus.AWAITING_APPLICANT_VERIFICATION,
            ApplicationStatus.APPROVED,
        )
        message = str(error).lower()
        assert "awaiting_applicant_verification" in message
        assert "approved" in message

    def test_error_message_contains_valid_transitions(self):
        """Error message should list valid transitions."""
        error = InvalidStatusTransitionError(
            ApplicationStatus.AWAITING_APPLICANT_VERIFICATION,
            ApplicationStatus.APPROVED,
        )
        message = str(error)
        # Should mention what transitions ARE valid
        assert "Valid transitions" in message

    def test_error_stores_statuses(self):
        """Error should store the status values."""
        error = InvalidStatusTransitionError(
            ApplicationStatus.PENDING_REVIEW,
            ApplicationStatus.EXPIRED,
        )
        assert error.current_status == ApplicationStatus.PENDING_REVIEW
        assert error.new_status == ApplicationStatus.EXPIRED


class TestStatusTransitionPaths:
    """Tests for valid paths through the state machine."""

    def test_principal_applicant_happy_path(self):
        """Test valid path: submit -> verify -> review -> approve."""
        # Applicant IS principal, so skips principal confirmation
        path = [
            ApplicationStatus.AWAITING_APPLICANT_VERIFICATION,
            ApplicationStatus.PENDING_REVIEW,  # Direct because applicant is principal
            ApplicationStatus.UNDER_REVIEW,
            ApplicationStatus.APPROVED,
        ]
        for i in range(len(path) - 1):
            current = path[i]
            next_status = path[i + 1]
            assert next_status in VALID_STATUS_TRANSITIONS[current], (
                f"Invalid transition: {current} -> {next_status}"
            )

    def test_non_principal_applicant_happy_path(self):
        """Test valid path: submit -> verify -> principal confirm -> review -> approve."""
        path = [
            ApplicationStatus.AWAITING_APPLICANT_VERIFICATION,
            ApplicationStatus.AWAITING_PRINCIPAL_CONFIRMATION,
            ApplicationStatus.PENDING_REVIEW,
            ApplicationStatus.UNDER_REVIEW,
            ApplicationStatus.APPROVED,
        ]
        for i in range(len(path) - 1):
            current = path[i]
            next_status = path[i + 1]
            assert next_status in VALID_STATUS_TRANSITIONS[current], (
                f"Invalid transition: {current} -> {next_status}"
            )

    def test_rejection_path(self):
        """Test valid path to rejection."""
        path = [
            ApplicationStatus.AWAITING_APPLICANT_VERIFICATION,
            ApplicationStatus.PENDING_REVIEW,
            ApplicationStatus.UNDER_REVIEW,
            ApplicationStatus.REJECTED,
        ]
        for i in range(len(path) - 1):
            current = path[i]
            next_status = path[i + 1]
            assert next_status in VALID_STATUS_TRANSITIONS[current]

    def test_expiry_from_verification(self):
        """Test expiry path from verification states."""
        # Can expire from awaiting applicant verification
        assert (
            ApplicationStatus.EXPIRED
            in VALID_STATUS_TRANSITIONS[ApplicationStatus.AWAITING_APPLICANT_VERIFICATION]
        )
        # Can expire from awaiting principal confirmation
        assert (
            ApplicationStatus.EXPIRED
            in VALID_STATUS_TRANSITIONS[ApplicationStatus.AWAITING_PRINCIPAL_CONFIRMATION]
        )

    def test_more_info_requested_path(self):
        """Test path through MORE_INFO_REQUESTED state."""
        path = [
            ApplicationStatus.PENDING_REVIEW,
            ApplicationStatus.UNDER_REVIEW,
            ApplicationStatus.MORE_INFO_REQUESTED,
            ApplicationStatus.UNDER_REVIEW,  # Can go back after info provided
            ApplicationStatus.APPROVED,
        ]
        for i in range(len(path) - 1):
            current = path[i]
            next_status = path[i + 1]
            assert next_status in VALID_STATUS_TRANSITIONS[current]

    def test_cannot_skip_verification(self):
        """Cannot go directly from awaiting verification to approved."""
        assert (
            ApplicationStatus.APPROVED
            not in VALID_STATUS_TRANSITIONS[ApplicationStatus.AWAITING_APPLICANT_VERIFICATION]
        )

    def test_cannot_go_backwards_from_terminal(self):
        """Cannot transition from terminal states."""
        terminal_states = [
            ApplicationStatus.APPROVED,
            ApplicationStatus.REJECTED,
            ApplicationStatus.EXPIRED,
        ]
        for state in terminal_states:
            assert len(VALID_STATUS_TRANSITIONS[state]) == 0
