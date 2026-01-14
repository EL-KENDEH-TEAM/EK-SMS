/**
 * Registration API Client
 *
 * API functions for school registration flow
 */

import type {
    RegistrationFormData,
    RegistrationRequest,
    SubmissionResponse,
    VerificationResponse,
    PrincipalApplicationResponse,
    PrincipalConfirmationResponse,
    ApplicationStatusResponse,
    Country
} from '@/app/register/types/registration';

// API URL configuration
// In production, NEXT_PUBLIC_API_URL should be set via environment variables
// Falls back to localhost for development
const API_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002') + '/api/v1';

/**
 * Sanitize string input - trim whitespace
 */
function sanitizeString(value: string | undefined | null): string | null {
    if (!value) return null;
    const trimmed = value.trim();
    return trimmed || null;
}

/**
 * Sanitize and lowercase email
 */
function sanitizeEmail(email: string | undefined | null): string | null {
    const sanitized = sanitizeString(email);
    return sanitized ? sanitized.toLowerCase() : null;
}

/**
 * Transform frontend student population values to backend enum format
 */
function transformStudentPopulation(value: string): string {
    const mapping: Record<string, string> = {
        'under100': 'under_100',
        '100-300': 'from_100_to_300',
        '300-500': 'from_300_to_500',
        '500+': 'over_500',
    };
    return mapping[value] || value;
}

/**
 * Transformer: frontend formData -> official API RegistrationRequest
 * Includes input sanitization for all text fields
 */
function transformFormData(data: RegistrationFormData): RegistrationRequest {
    return {
        school: {
            name: sanitizeString(data.basicInfo.schoolName) || '',
            year_established: parseInt(data.basicInfo.yearEstablished, 10),
            school_type: data.basicInfo.schoolType.toLowerCase(),
            student_population: transformStudentPopulation(data.basicInfo.studentPopulation),
        },
        location: {
            country_code: data.location.country,
            city: sanitizeString(data.location.cityTown) || '',
            address: sanitizeString(data.location.physicalAddress) || '',
        },
        contact: {
            school_phone: sanitizeString(data.contact.schoolPhone),
            school_email: sanitizeEmail(data.contact.schoolEmail),
            principal_name: sanitizeString(data.contact.principalFullName) || '',
            principal_email: sanitizeEmail(data.contact.principalEmail) || '',
            principal_phone: sanitizeString(data.contact.principalPhone) || '',
        },
        applicant: {
            is_principal: data.aboutYou.iAmPrincipal,
            name: data.aboutYou.iAmPrincipal ? null : sanitizeString(data.aboutYou.yourFullName),
            email: data.aboutYou.iAmPrincipal ? null : sanitizeEmail(data.aboutYou.yourEmail),
            phone: data.aboutYou.iAmPrincipal ? null : sanitizeString(data.aboutYou.yourPhone),
            role: data.aboutYou.iAmPrincipal ? null : sanitizeString(data.aboutYou.yourRole),
            admin_choice: data.aboutYou.iAmPrincipal ? null : (data.aboutYou.whoManagesSystem === 'me' ? 'applicant' : 'principal'),
        },
        details: {
            online_presence: data.details.onlinePresence
                .filter(op => op.url?.trim()) // Only include entries with URLs
                .map(op => ({
                    type: op.type,
                    url: op.url.trim()
                })),
            reasons: [
                ...(data.details.whyTransparency ? ['transparency'] : []),
                ...(data.details.whyAutomation ? ['automation'] : [])
            ],
            other_reason: sanitizeString(data.details.whyOtherReason),
        }
    };
}

/**
 * Get list of countries
 * GET /school-applications/countries
 */
export async function getCountries(): Promise<Country[]> {
    try {
        const response = await fetch(`${API_URL}/school-applications/countries`);

        if (!response.ok) {
            throw new Error(`Failed to fetch countries: ${response.statusText}`);
        }

        const data = await response.json();
        return data.countries;
    } catch (error) {
        console.error('Error fetching countries:', error);
        throw error;
    }
}

/**
 * Submit school application
 * POST /school-applications
 */
export async function submitApplication(
    data: RegistrationFormData
): Promise<SubmissionResponse> {
    const payload = transformFormData(data);

    try {
        const response = await fetch(`${API_URL}/school-applications`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        });

        const responseData = await response.json();

        // Handle different status codes
        if (response.status === 201) {
            return responseData;
        }

        if (response.status === 400) {
            throw new Error(responseData.message || 'Validation error. Please check your data.');
        }

        if (response.status === 409) {
            throw new Error(responseData.message || 'An application with this email already exists.');
        }

        if (!response.ok) {
            throw new Error(responseData.message || 'Failed to submit application');
        }

        return responseData;
    } catch (error) {
        console.error('Error submitting application:', error);
        throw error;
    }
}

/**
 * Verify applicant with token
 * POST /school-applications/verify-applicant
 */
export async function verifyApplicant(token: string): Promise<VerificationResponse> {
    try {
        const response = await fetch(`${API_URL}/school-applications/verify-applicant`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ token }),
        });

        const data = await response.json();

        if (!response.ok) {
            if (response.status === 400) {
                throw new Error(data.message || 'Invalid or expired verification token');
            }
            if (response.status === 404) {
                throw new Error(data.message || 'Application not found');
            }
            if (response.status === 409) {
                throw new Error(data.message || 'Email already verified');
            }
            throw new Error(data.message || 'Verification failed');
        }

        return data;
    } catch (error) {
        console.error('Error verifying applicant:', error);
        throw error;
    }
}

/**
 * Resend verification email
 * POST /school-applications/resend-verification
 */
export async function resendVerification(
    applicationId: string,
    email: string
): Promise<{ message: string; expires_at: string }> {
    try {
        const response = await fetch(`${API_URL}/school-applications/resend-verification`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ application_id: applicationId, email }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || 'Failed to resend verification email');
        }

        return data;
    } catch (error) {
        console.error('Error resending verification:', error);
        throw error;
    }
}

/**
 * Get application status
 * GET /school-applications/{id}/status
 */
export async function getApplicationStatus(
    id: string,
    email: string
): Promise<ApplicationStatusResponse> {
    try {
        const response = await fetch(
            `${API_URL}/school-applications/${id}/status?email=${encodeURIComponent(email)}`,
            {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || 'Failed to fetch application status');
        }

        return data;
    } catch (error) {
        console.error('Error fetching application status:', error);
        throw error;
    }
}

/**
 * Get principal application details by token
 * GET /school-applications/principal-view?token={token}
 */
export async function getPrincipalApplication(token: string): Promise<PrincipalApplicationResponse> {
    try {
        const response = await fetch(
            `${API_URL}/school-applications/principal-view?token=${encodeURIComponent(token)}`,
            {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            }
        );

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.message || 'Failed to fetch application details');
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching principal application:', error);
        throw error;
    }
}

/**
 * Confirm principal application
 * POST /school-applications/confirm-principal
 */
export async function confirmPrincipal(token: string): Promise<PrincipalConfirmationResponse> {
    try {
        const response = await fetch(`${API_URL}/school-applications/confirm-principal`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ token }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || 'Confirmation failed');
        }

        return data;
    } catch (error) {
        console.error('Error confirming principal:', error);
        throw error;
    }
}
