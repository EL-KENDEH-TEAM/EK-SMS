"""
School Applications Shared Helpers

Common utility functions used across the school applications module.
These helpers are extracted to avoid code duplication between service.py and jobs.py.
"""

from app.modules.school_applications.models import SchoolApplication
from app.modules.school_applications.schemas import SchoolApplicationCreate


def get_effective_applicant_email_from_model(application: SchoolApplication) -> str:
    """
    Get the effective applicant email from an application model.

    If the applicant is the principal, use the principal's email.
    Otherwise, use the applicant's email.

    Args:
        application: The school application model

    Returns:
        The email address to use for the applicant
    """
    if application.applicant_is_principal:
        return application.principal_email
    return application.applicant_email or application.principal_email


def get_effective_applicant_name_from_model(application: SchoolApplication) -> str:
    """
    Get the effective applicant name from an application model.

    If the applicant is the principal, use the principal's name.
    Otherwise, use the applicant's name.

    Args:
        application: The school application model

    Returns:
        The name to use for the applicant
    """
    if application.applicant_is_principal:
        return application.principal_name
    return application.applicant_name or application.principal_name


def get_effective_applicant_email_from_schema(data: SchoolApplicationCreate) -> str:
    """
    Get the effective applicant email from a create schema.

    If the applicant is the principal, use the principal's email.
    Otherwise, use the applicant's email.

    Args:
        data: The application create request data

    Returns:
        The email address to use for the applicant
    """
    if data.applicant.is_principal:
        return data.contact.principal_email
    return data.applicant.email  # type: ignore - validated in schema


def get_effective_applicant_name_from_schema(data: SchoolApplicationCreate) -> str:
    """
    Get the effective applicant name from a create schema.

    If the applicant is the principal, use the principal's name.
    Otherwise, use the applicant's name.

    Args:
        data: The application create request data

    Returns:
        The name to use for the applicant
    """
    if data.applicant.is_principal:
        return data.contact.principal_name
    return data.applicant.name  # type: ignore - validated in schema
