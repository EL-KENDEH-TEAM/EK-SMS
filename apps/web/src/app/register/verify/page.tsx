'use client';

/**
 * Email Verification Page
 *
 * Users land here when clicking verification link in email
 * Route: /register/verify?token=abc123xyz
 */

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { verifyApplicant } from '@/lib/api/registration';

type VerificationState = 'loading' | 'success' | 'error' | 'needs-principal';

function VerificationPageContent() {
    const searchParams = useSearchParams();
    const [state, setState] = useState<VerificationState>('loading');
    const [message, setMessage] = useState('');

    useEffect(() => {
        const verifyToken = async () => {
            const token = searchParams.get('token');

            if (!token) {
                setState('error');
                setMessage('Invalid verification link. No token provided.');
                return;
            }

            try {
                const response = await verifyApplicant(token);
                if (response.requires_principal_confirmation) {
                    setState('needs-principal');
                    setMessage(response.message || 'Verification successful! Waiting for principal confirmation.');
                } else {
                    setState('success');
                    setMessage(response.message || 'Your email has been verified successfully!');
                }
            } catch (error) {
                setState('error');
                setMessage(
                    error instanceof Error
                        ? error.message
                        : 'Verification failed. The link may be expired or invalid.'
                );
            }
        };

        verifyToken();
    }, [searchParams]);

    return (
        <div className="min-h-screen bg-[#f5f5f5] flex items-center justify-center px-4">
            <div className="max-w-2xl w-full bg-white rounded-xl shadow-md p-8 sm:p-12">
                {/* Loading State */}
                {state === 'loading' && (
                    <div className="text-center">
                        <div className="flex justify-center mb-6">
                            <svg
                                className="animate-spin h-16 w-16 text-[#3b82f6]"
                                fill="none"
                                viewBox="0 0 24 24"
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
                        <h1 className="text-2xl font-bold text-[#1a365d] mb-2">Verifying Your Email</h1>
                        <p className="text-[#6b7280]">Please wait while we verify your email address...</p>
                    </div>
                )}

                {/* Success State */}
                {state === 'success' && (
                    <div className="text-center">
                        <div className="flex justify-center mb-6">
                            <div className="w-20 h-20 bg-[#22c55e]/10 rounded-full flex items-center justify-center">
                                <svg
                                    className="w-10 h-10 text-[#22c55e]"
                                    fill="none"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth="2"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                >
                                    <path d="M5 13l4 4L19 7"></path>
                                </svg>
                            </div>
                        </div>
                        <h1 className="text-3xl font-bold text-[#1a365d] mb-4">Email Verified!</h1>
                        <p className="text-[#4b5563] mb-8">{message}</p>

                        <div className="bg-[#22c55e]/10 border border-[#22c55e] rounded-lg p-6 mb-8">
                            <h2 className="font-semibold text-[#166534] mb-2">What&apos;s Next?</h2>
                            <div className="text-[#166534] text-sm space-y-2">
                                <p>• Our team will review your application</p>
                                <p>• You&apos;ll receive an email notification within 3-5 business days</p>
                                <p>• Keep an eye on your inbox for updates</p>
                            </div>
                        </div>

                        <Link
                            href="/"
                            className="inline-block px-6 py-3 bg-[#1a365d] text-white font-medium rounded-lg hover:bg-[#1e4976]"
                        >
                            Back to Home
                        </Link>
                    </div>
                )}

                {/* Needs Principal Confirmation */}
                {state === 'needs-principal' && (
                    <div className="text-center">
                        <div className="flex justify-center mb-6">
                            <div className="w-20 h-20 bg-[#f59e0b]/10 rounded-full flex items-center justify-center">
                                <svg
                                    className="w-10 h-10 text-[#f59e0b]"
                                    fill="none"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth="2"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                >
                                    <path d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                </svg>
                            </div>
                        </div>
                        <h1 className="text-3xl font-bold text-[#1a365d] mb-4">Almost There!</h1>
                        <p className="text-[#4b5563] mb-8">{message}</p>

                        <div className="bg-[#f59e0b]/10 border border-[#f59e0b] rounded-lg p-6 mb-8">
                            <h2 className="font-semibold text-[#92400e] mb-2">Principal Confirmation Required</h2>
                            <p className="text-[#92400e] text-sm">
                                We&apos;ve sent a confirmation email to your principal. Your application will be processed once they confirm.
                            </p>
                        </div>

                        <Link
                            href="/"
                            className="inline-block px-6 py-3 bg-[#1a365d] text-white font-medium rounded-lg hover:bg-[#1e4976]"
                        >
                            Back to Home
                        </Link>
                    </div>
                )}

                {/* Error State */}
                {state === 'error' && (
                    <div className="text-center">
                        <div className="flex justify-center mb-6">
                            <div className="w-20 h-20 bg-[#dc2626]/10 rounded-full flex items-center justify-center">
                                <svg
                                    className="w-10 h-10 text-[#dc2626]"
                                    fill="none"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth="2"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                >
                                    <path d="M6 18L18 6M6 6l12 12"></path>
                                </svg>
                            </div>
                        </div>
                        <h1 className="text-3xl font-bold text-[#1a365d] mb-4">Verification Failed</h1>
                        <p className="text-[#4b5563] mb-8">{message}</p>

                        <div className="bg-[#dc2626]/10 border border-[#dc2626] rounded-lg p-6 mb-8">
                            <h2 className="font-semibold text-[#991b1b] mb-2">What can you do?</h2>
                            <div className="text-[#991b1b] text-sm space-y-2">
                                <p>• Check if the link was copied correctly</p>
                                <p>• Request a new verification link</p>
                                <p>• Contact support if the problem persists</p>
                            </div>
                        </div>

                        <div className="flex flex-col sm:flex-row gap-4 justify-center">
                            <Link
                                href="/register/success"
                                className="px-6 py-3 border border-[#d1d5db] text-[#4b5563] font-medium rounded-lg hover:bg-[#f5f5f5]"
                            >
                                Request New Link
                            </Link>
                            <Link
                                href="/"
                                className="px-6 py-3 bg-[#1a365d] text-white font-medium rounded-lg hover:bg-[#1e4976]"
                            >
                                Back to Home
                            </Link>
                        </div>
                    </div>
                )}
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

export function VerificationPage() {
    return (
        <Suspense fallback={<LoadingFallback />}>
            <VerificationPageContent />
        </Suspense>
    );
}

export default VerificationPage;
