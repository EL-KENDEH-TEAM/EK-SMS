"""
School Applications Module

Handles the school registration application workflow:
1. Application submission with duplicate detection
2. Applicant email verification (72-hour expiry)
3. Principal confirmation (when applicant != principal)
4. Background jobs for reminders and expiration

API Endpoints:
- POST /school-applications - Submit new application
- POST /school-applications/verify-applicant - Verify applicant email
- POST /school-applications/confirm-principal - Principal confirms application
- POST /school-applications/resend-verification - Resend verification email
- GET /school-applications/{id}/status - Get application status
- GET /school-applications/countries - List supported countries

Security Features:
- SHA-256 token hashing (tokens never stored in plain text)
- Rate limiting with fail-closed behavior (requires Redis)
- State machine validation for status transitions
- Case-insensitive email validation
- No sensitive data in logs

Background Jobs (via APScheduler):
- send_verification_reminders: Runs hourly, sends reminders at 48 hours
- expire_unverified_applications: Runs hourly, expires at 72 hours
"""

from .jobs import register_school_application_jobs
from .router import router

__all__ = ["router", "register_school_application_jobs"]
