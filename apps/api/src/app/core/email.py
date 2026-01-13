"""
Email Service using Resend

Handles sending emails for the school registration flow.
"""

import asyncio
import logging
import os
from html import escape

import resend

logger = logging.getLogger(__name__)

# Initialize Resend with API key
resend.api_key = os.getenv("RESEND_API_KEY")

# Configurations
EMAIL_FROM = os.getenv("EMAIL_FROM", "EK-SMS <noreply@eksms.dev>")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
) -> bool:
    """
    Send an email using Resend.

    Args:
        to_email: Recipient email address
        subject: Email subject line
        html_content: HTML content of the email

    Returns:
        True if email was sent successfully
    """
    if not resend.api_key:
        logger.warning("RESEND_API_KEY not set - logging email instead of sending")
        logger.info(f"EMAIL TO: {to_email} | SUBJECT: {subject}")
        return True

    try:
        params: resend.Emails.SendParams = {
            "from": EMAIL_FROM,
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }

        # Run sync Resend call in thread pool to avoid blocking event loop
        email = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Email sent successfully to {to_email}, id: {email['id']}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


async def send_applicant_verification(
    to_email: str,
    applicant_name: str,
    school_name: str,
    token: str,
) -> bool:
    """Send verification email to applicant."""
    # Escape user inputs to prevent XSS
    safe_applicant_name = escape(applicant_name)
    safe_school_name = escape(school_name)

    verification_url = f"{FRONTEND_URL}/register/verify?token={token}"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: system-ui, -apple-system, sans-serif; line-height: 1.6; color: #1f2937; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
            .header {{ color: #1a365d; margin-bottom: 24px; }}
            .button {{ display: inline-block; background-color: #1a365d; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; margin: 24px 0; }}
            .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="header">Verify Your Email</h1>

            <p>Hello {safe_applicant_name},</p>

            <p>Thank you for submitting a registration application for <strong>{safe_school_name}</strong> on EK-SMS.</p>

            <p>Please verify your email address by clicking the button below:</p>

            <a href="{verification_url}" class="button">Verify Email</a>

            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #3b82f6;">{verification_url}</p>

            <p><strong>This link expires in 72 hours.</strong></p>

            <div class="footer">
                <p>If you didn't submit this application, you can safely ignore this email.</p>
                <p>EK-SMS - School Management System</p>
            </div>
        </div>
    </body>
    </html>
    """
    return await send_email(
        to_email=to_email,
        subject=f"Verify your EK-SMS application for {safe_school_name}",
        html_content=html_content,
    )


async def send_principal_confirmation(
    to_email: str,
    principal_name: str,
    school_name: str,
    applicant_name: str,
    applicant_role: str,
    city: str,
    country: str,
    designated_admin: str,
    token: str,
) -> bool:
    """Send confirmation email to principal."""
    # Escape user inputs to prevent XSS
    safe_principal_name = escape(principal_name)
    safe_school_name = escape(school_name)
    safe_applicant_name = escape(applicant_name)
    safe_applicant_role = escape(applicant_role)
    safe_city = escape(city)
    safe_country = escape(country)
    safe_designated_admin = escape(designated_admin)

    confirmation_url = f"{FRONTEND_URL}/register/confirm-principal?token={token}"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: system-ui, -apple-system, sans-serif; line-height: 1.6; color: #1f2937; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
            .header {{ color: #1a365d; margin-bottom: 24px; }}
            .button {{ display: inline-block; background-color: #1a365d; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; margin: 24px 0; }}
            .info-box {{ background-color: #f3f4f6; padding: 16px; border-radius: 8px; margin: 16px 0; }}
            .summary-box {{ background-color: #f9fafb; border: 1px solid #e5e7eb; padding: 16px; border-radius: 8px; margin: 16px 0; }}
            .summary-box ul {{ margin: 8px 0 0 0; padding-left: 20px; }}
            .summary-box li {{ margin-bottom: 4px; }}
            .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="header">Principal Confirmation Required</h1>

            <p>Dear {safe_principal_name},</p>

            <p><strong>{safe_applicant_name}</strong> has submitted a registration application for <strong>{safe_school_name}</strong> on EK-SMS, a school management platform.</p>

            <p>As the Principal/Head Teacher, your confirmation is required to proceed.</p>

            <div class="summary-box">
                <p><strong>Application Summary:</strong></p>
                <ul>
                    <li><strong>School:</strong> {safe_school_name}</li>
                    <li><strong>Location:</strong> {safe_city}, {safe_country}</li>
                    <li><strong>Submitted by:</strong> {safe_applicant_name} ({safe_applicant_role})</li>
                    <li><strong>Designated Admin:</strong> {safe_designated_admin}</li>
                </ul>
            </div>

            <div class="info-box">
                <p><strong>What is EK-SMS?</strong></p>
                <p>EK-SMS is a school management system designed to bring transparency and efficiency to school administration, with a focus on grade management and anti-corruption measures.</p>
            </div>

            <p>If you authorize this registration, please click below:</p>

            <a href="{confirmation_url}" class="button">Confirm Application</a>

            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #3b82f6;">{confirmation_url}</p>

            <p><strong>This link expires in 72 hours.</strong></p>

            <div class="footer">
                <p>If you did not authorize this application or have concerns, please ignore this email or contact us at support@eksms.dev.</p>
                <p>EK-SMS - School Management System</p>
            </div>
        </div>
    </body>
    </html>
    """

    return await send_email(
        to_email=to_email,
        subject=f"Please confirm EK-SMS registration for {safe_school_name}",
        html_content=html_content,
    )


async def send_verification_reminder(
    to_email: str,
    applicant_name: str,
    school_name: str,
    token: str,
    hours_remaining: int,
) -> bool:
    """Send reminder email for pending verification."""
    # Escape user inputs to prevent XSS
    safe_applicant_name = escape(applicant_name)
    safe_school_name = escape(school_name)

    verification_url = f"{FRONTEND_URL}/register/verify?token={token}"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: system-ui, -apple-system, sans-serif; line-height: 1.6; color: #1f2937; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
            .header {{ color: #1a365d; margin-bottom: 24px; }}
            .warning {{ background-color: #fef3c7; border: 1px solid #f59e0b; padding: 16px; border-radius: 8px; margin: 16px 0; }}
            .button {{ display: inline-block; background-color: #1a365d; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; margin: 24px 0; }}
            .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="header">Reminder: Verify Your Email</h1>

            <p>Hello {safe_applicant_name},</p>

            <div class="warning">
                <strong>Your verification link expires in {hours_remaining} hours!</strong>
            </div>

            <p>You submitted a registration application for <strong>{safe_school_name}</strong> but haven't verified your email yet.</p>

            <p>Please verify now to continue with your application:</p>

            <a href="{verification_url}" class="button">Verify Email</a>

            <div class="footer">
                <p>If you no longer wish to register, you can ignore this email.</p>
                <p>EK-SMS - School Management System</p>
            </div>
        </div>
    </body>
    </html>
    """
    return await send_email(
        to_email=to_email,
        subject=f"Reminder: Verify your EK-SMS application for {safe_school_name}",
        html_content=html_content,
    )


async def send_application_expired(
    to_email: str,
    applicant_name: str,
    school_name: str,
) -> bool:
    """Send notification that application has expired."""
    # Escape user inputs to prevent XSS
    safe_applicant_name = escape(applicant_name)
    safe_school_name = escape(school_name)

    register_url = f"{FRONTEND_URL}/register"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: system-ui, -apple-system, sans-serif; line-height: 1.6; color: #1f2937; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
            .header {{ color: #1a365d; margin-bottom: 24px; }}
            .button {{ display: inline-block; background-color: #1a365d; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; margin: 24px 0; }}
            .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="header">Application Expired</h1>

            <p>Hello {safe_applicant_name},</p>

            <p>Your registration application for <strong>{safe_school_name}</strong> has expired because the email was not verified within 72 hours.</p>

            <p>If you still wish to register your school on EK-SMS, you can submit a new application:</p>

            <a href="{register_url}" class="button">Start New Application</a>

            <div class="footer">
                <p>EK-SMS - School Management System</p>
            </div>
        </div>
    </body>
    </html>
    """

    return await send_email(
        to_email=to_email,
        subject=f"Your EK-SMS application for {safe_school_name} has expired",
        html_content=html_content,
    )


async def send_application_under_review(
    to_email: str,
    applicant_name: str,
    school_name: str,
    application_id: str,
) -> bool:
    """Send notification that application is now under review."""
    # Escape user inputs to prevent XSS
    safe_applicant_name = escape(applicant_name)
    safe_school_name = escape(school_name)

    status_url = f"{FRONTEND_URL}/register/status?id={application_id}"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: system-ui, -apple-system, sans-serif; line-height: 1.6; color: #1f2937; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
            .header {{ color: #1a365d; margin-bottom: 24px; }}
            .success {{ background-color: #d1fae5; border: 1px solid #22c55e; padding: 16px; border-radius: 8px; margin: 16px 0; }}
            .button {{ display: inline-block; background-color: #1a365d; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; margin: 24px 0; }}
            .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="header">Application Under Review</h1>

            <p>Hello {safe_applicant_name},</p>

            <div class="success">
                <strong>Great news!</strong> Your application for <strong>{safe_school_name}</strong> has been verified and is now under review by our team.
            </div>

            <p>We will review your application and get back to you within 2-3 business days.</p>

            <p>You can check your application status at any time:</p>

            <a href="{status_url}" class="button">Check Status</a>

            <div class="footer">
                <p>Thank you for choosing EK-SMS!</p>
                <p>EK-SMS - School Management System</p>
            </div>
        </div>
    </body>
    </html>
    """

    return await send_email(
        to_email=to_email,
        subject=f"Your EK-SMS application for {safe_school_name} is under review",
        html_content=html_content,
    )


async def send_more_info_requested(
    to_email: str,
    applicant_name: str,
    school_name: str,
    admin_message: str,
    application_id: str,
) -> bool:
    """Send notification that admin requested more information."""
    # Escape user inputs to prevent XSS
    safe_applicant_name = escape(applicant_name)
    safe_school_name = escape(school_name)
    safe_admin_message = escape(admin_message)

    respond_url = f"{FRONTEND_URL}/register/respond?id={application_id}"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: system-ui, -apple-system, sans-serif; line-height: 1.6; color: #1f2937; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
            .header {{ color: #1a365d; margin-bottom: 24px; }}
            .message-box {{ background-color: #eff6ff; border: 1px solid #bfdbfe; padding: 16px; border-radius: 8px; margin: 16px 0; }}
            .button {{ display: inline-block; background-color: #1a365d; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; margin: 24px 0; }}
            .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="header">Additional Information Needed</h1>

            <p>Hello {safe_applicant_name},</p>

            <p>Thank you for your application to register <strong>{safe_school_name}</strong> on EK-SMS.</p>

            <p>Our team needs some additional information to process your application:</p>

            <div class="message-box">
                {safe_admin_message}
            </div>

            <p>Please reply to this email or click below to provide the requested information:</p>

            <a href="{respond_url}" class="button">Respond to Request</a>

            <div class="footer">
                <p>If you have questions, please contact us at support@eksms.dev.</p>
                <p>EK-SMS - School Management System</p>
            </div>
        </div>
    </body>
    </html>
    """

    return await send_email(
        to_email=to_email,
        subject="Additional information needed for your EK-SMS application",
        html_content=html_content,
    )


async def send_application_approved(
    to_email: str,
    admin_name: str,
    school_name: str,
    admin_email: str,
    temp_password: str,
) -> bool:
    """Send notification that application was approved with login credentials."""
    # Escape user inputs to prevent XSS
    safe_admin_name = escape(admin_name)
    safe_school_name = escape(school_name)
    safe_admin_email = escape(admin_email)

    login_url = f"{FRONTEND_URL}/login"
    docs_url = "https://docs.eksms.dev"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: system-ui, -apple-system, sans-serif; line-height: 1.6; color: #1f2937; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
            .header {{ color: #1a365d; margin-bottom: 24px; }}
            .success-banner {{ background-color: #d1fae5; border: 1px solid #22c55e; padding: 16px; border-radius: 8px; margin: 16px 0; text-align: center; }}
            .credentials-box {{ background-color: #f9fafb; border: 1px solid #e5e7eb; padding: 16px; border-radius: 8px; margin: 16px 0; }}
            .credentials-box p {{ margin: 8px 0; }}
            .warning {{ background-color: #fef3c7; border: 1px solid #f59e0b; padding: 12px 16px; border-radius: 8px; margin: 16px 0; font-size: 14px; }}
            .button {{ display: inline-block; background-color: #1a365d; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; margin: 24px 0; }}
            .steps {{ background-color: #f9fafb; padding: 16px; border-radius: 8px; margin: 16px 0; }}
            .steps ol {{ margin: 8px 0 0 0; padding-left: 20px; }}
            .steps li {{ margin-bottom: 8px; }}
            .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="header">Welcome to EK-SMS!</h1>

            <div class="success-banner">
                <strong>Congratulations!</strong> Your application for <strong>{safe_school_name}</strong> has been approved.
            </div>

            <p>Dear {safe_admin_name},</p>

            <p>Your school is now registered on EK-SMS. Here are your login credentials:</p>

            <div class="credentials-box">
                <p><strong>Login URL:</strong> <a href="{login_url}">{login_url}</a></p>
                <p><strong>Email:</strong> {safe_admin_email}</p>
                <p><strong>Temporary Password:</strong> <code>{temp_password}</code></p>
            </div>

            <div class="warning">
                <strong>Important:</strong> You will be required to change your password on first login.
            </div>

            <div class="steps">
                <p><strong>Getting Started:</strong></p>
                <ol>
                    <li>Log in with the credentials above</li>
                    <li>Change your password</li>
                    <li>Set up two-factor authentication (required for admin accounts)</li>
                    <li>Configure your school settings</li>
                    <li>Start adding teachers and students</li>
                </ol>
            </div>

            <a href="{login_url}" class="button">Log In Now</a>

            <p>If you need help getting started, check out our guide at <a href="{docs_url}">{docs_url}</a> or contact support@eksms.dev.</p>

            <div class="footer">
                <p>Welcome aboard!</p>
                <p>EK-SMS - School Management System</p>
            </div>
        </div>
    </body>
    </html>
    """

    return await send_email(
        to_email=to_email,
        subject="Welcome to EK-SMS! Your school is approved",
        html_content=html_content,
    )


async def send_application_rejected(
    to_email: str,
    applicant_name: str,
    school_name: str,
    rejection_reason: str,
) -> bool:
    """Send notification that application was rejected."""
    # Escape user inputs to prevent XSS
    safe_applicant_name = escape(applicant_name)
    safe_school_name = escape(school_name)
    safe_rejection_reason = escape(rejection_reason)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: system-ui, -apple-system, sans-serif; line-height: 1.6; color: #1f2937; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
            .header {{ color: #1a365d; margin-bottom: 24px; }}
            .reason-box {{ background-color: #fef2f2; border: 1px solid #fecaca; padding: 16px; border-radius: 8px; margin: 16px 0; }}
            .reason-box p {{ margin: 0; }}
            .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="header">Update on Your EK-SMS Application</h1>

            <p>Hello {safe_applicant_name},</p>

            <p>Thank you for your interest in EK-SMS. After reviewing your application for <strong>{safe_school_name}</strong>, we're unable to approve it at this time.</p>

            <div class="reason-box">
                <p><strong>Reason:</strong></p>
                <p>{safe_rejection_reason}</p>
            </div>

            <p>If you believe this decision was made in error or if you can address the above concerns, you may submit a new application after 30 days.</p>

            <p>If you have questions, please contact us at support@eksms.dev.</p>

            <div class="footer">
                <p>Best regards,</p>
                <p>The EK-SMS Team</p>
            </div>
        </div>
    </body>
    </html>
    """

    return await send_email(
        to_email=to_email,
        subject="Update on your EK-SMS application",
        html_content=html_content,
    )
