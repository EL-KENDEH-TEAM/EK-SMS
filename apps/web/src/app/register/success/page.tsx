'use client';

/**
 * Registration Success Page
 *
 * Shown after successful application submission
 * Route: /register/success
 */

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { resendVerification } from '@/lib/api/registration';

/**
 * Mask email address for privacy display
 * Handles edge cases like short usernames
 */
function maskEmail(email: string): string {
    if (!email) return '';
    const parts = email.split('@');
    if (parts.length !== 2) return email;

    const [user, domain] = parts;

    // For very short usernames, still mask but show first char
    if (user.length <= 2) {
        return `${user[0]}**@${domain}`;
    }
    if (user.length <= 4) {
        return `${user[0]}**${user[user.length - 1]}@${domain}`;
    }

    // Standard masking for longer usernames
    const maskedUser = user[0] + '***' + user[user.length - 1];
    return `${maskedUser}@${domain}`;
}

function SuccessPageContent() {
    const searchParams = useSearchParams();
    const [email, setEmail] = useState('');
    const [applicationId, setApplicationId] = useState('');
    const [isResending, setIsResending] = useState(false);
    const [resendMessage, setResendMessage] = useState('');

    useEffect(() => {
        // Get email and applicationId from URL params
        const emailParam = searchParams.get('email');
        const idParam = searchParams.get('id');

        if (emailParam) setEmail(emailParam);
        if (idParam) setApplicationId(idParam);

        // Fallback to sessionStorage if params not present (SSR-safe check)
        if ((!emailParam || !idParam) && typeof window !== 'undefined') {
            try {
                const storedEmail = sessionStorage.getItem('registrationEmail');
                const storedId = sessionStorage.getItem('applicationId');
                if (storedEmail && !emailParam) setEmail(storedEmail);
                if (storedId && !idParam) setApplicationId(storedId);
            } catch {
                // sessionStorage may not be available in some contexts
                console.warn('Unable to access sessionStorage');
            }
        }
    }, [searchParams]);

    const handleResend = async () => {
        if (!applicationId || !email) {
            setResendMessage('Missing application information. Please try registering again.');
            return;
        }

        setIsResending(true);
        setResendMessage('');

        try {
            await resendVerification(applicationId, email);
            setResendMessage('Verification email sent successfully! Please check your inbox.');
        } catch (error) {
            setResendMessage(error instanceof Error ? error.message : 'Failed to resend email. Please try again.');
        } finally {
            setIsResending(false);
        }
    };

    return (
      <div className="min-h-screen bg-[#f5f5f5] flex items-center justify-center px-4">
        <div className="max-w-2xl w-full bg-white rounded-xl shadow-md p-8 sm:p-12">
          {/* Email Icon */}
          <div className="flex justify-center mb-6">
            <div className="w-20 h-20 bg-[#3b82f6]/10 rounded-full flex items-center justify-center">
              <svg
                className="w-10 h-10 text-[#3b82f6]"
                fill="none"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                viewBox="0 0 24 24"
                stroke="currentColor"
                aria-hidden="true"
              >
                <path d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
              </svg>
            </div>
          </div>

          {/* Success Message */}
          <h1 className="text-3xl font-bold text-[#1a365d] text-center mb-4">Check Your Email!</h1>

          <p className="text-[#4b5563] text-center mb-6">
            We&apos;ve sent a verification email to:
          </p>

          <div className="bg-[#f5f5f5] rounded-lg p-4 mb-8">
            <p className="text-[#1a365d] font-semibold text-center">
              {email ? maskEmail(email) : "your email address"}
            </p>
          </div>

          {/* Next Steps */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-[#1a365d] mb-4">Next Steps:</h2>
            <ol className="space-y-4">
              <li className="flex items-start">
                <span className="flex-shrink-0 w-8 h-8 bg-[#1a365d] text-white rounded-full flex items-center justify-center font-semibold text-sm mr-3">
                  1
                </span>
                <div>
                  <p className="text-[#1f2937] font-medium">Check your inbox</p>
                  <p className="text-[#6b7280] text-sm">
                    Look for an email from EK-SMS with the subject &quot;Verify Your School
                    Registration&quot;
                  </p>
                </div>
              </li>
              <li className="flex items-start">
                <span className="flex-shrink-0 w-8 h-8 bg-[#1a365d] text-white rounded-full flex items-center justify-center font-semibold text-sm mr-3">
                  2
                </span>
                <div>
                  <p className="text-[#1f2937] font-medium">Click the verification link</p>
                  <p className="text-[#6b7280] text-sm">
                    This confirms your email address and activates your application
                  </p>
                </div>
              </li>
              <li className="flex items-start">
                <span className="flex-shrink-0 w-8 h-8 bg-[#1a365d] text-white rounded-full flex items-center justify-center font-semibold text-sm mr-3">
                  3
                </span>
                <div>
                  <p className="text-[#1f2937] font-medium">Wait for approval</p>
                  <p className="text-[#6b7280] text-sm">
                    Our team will review your application and get back to you within 3-5 business
                    days
                  </p>
                </div>
              </li>
            </ol>
          </div>

          {/* Resend Verification */}
          <div className="border-t border-[#e5e7eb] pt-6">
            <p className="text-[#6b7280] text-sm text-center mb-3">
              Didn&apos;t receive the email?
            </p>
            <div className="flex flex-col items-center gap-3">
              <button
                onClick={handleResend}
                disabled={isResending || !applicationId || !email}
                aria-label="Resend verification email"
                className={`text-[#3b82f6] hover:text-[#1e4976] font-medium text-sm underline ${
                  isResending || !applicationId || !email ? "opacity-50 cursor-not-allowed" : ""
                }`}
              >
                {isResending ? "Sending..." : "Resend verification email"}
              </button>
              {resendMessage && (
                <p
                  role="status"
                  aria-live="polite"
                  className={`text-sm ${resendMessage.includes("success") ? "text-[#22c55e]" : "text-[#dc2626]"}`}
                >
                  {resendMessage}
                </p>
              )}
            </div>
          </div>

          {/* Back to Home */}
          <div className="mt-8 text-center">
            <Link href="/" className="text-[#3b82f6] hover:text-[#1e4976] font-medium text-sm">
              ← Back to Home
            </Link>
          </div>
        </div>
      </div>
    );
}

function LoadingFallback() {
    return (
        <div className="min-h-screen bg-[#f5f5f5] flex items-center justify-center px-4">
            <div className="max-w-2xl w-full bg-white rounded-xl shadow-md p-8 sm:p-12">
                <div className="text-center">
                    <div className="flex justify-center mb-6">
                        <svg
                            className="animate-spin h-16 w-16 text-[#3b82f6]"
                            fill="none"
                            viewBox="0 0 24 24"
                            aria-hidden="true"
                        >
                            <circle
                                className="opacity-25"
                                cx="12"
                                cy="12"
                                r="10"
                                stroke="currentColor"
                                strokeWidth="4"
                            ></circle>
                            <path
                                className="opacity-75"
                                fill="currentColor"
                                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                            ></path>
                        </svg>
                    </div>
                    <h1 className="text-2xl font-bold text-[#1a365d] mb-2">Loading...</h1>
                    <p className="text-[#6b7280]">Please wait...</p>
                </div>
            </div>
        </div>
    );
}

export function SuccessPage() {
    return (
        <Suspense fallback={<LoadingFallback />}>
            <SuccessPageContent />
        </Suspense>
    );
}

export default SuccessPage;
