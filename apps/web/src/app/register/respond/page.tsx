'use client';

/**
 * Respond to Info Request Page
 *
 * Users land here when clicking "Respond to Request" link in the
 * "More Information Requested" email.
 *
 * Route: /register/respond?id=application-uuid
 *
 * Since the backend doesn't have a dedicated submit-response endpoint,
 * this page provides instructions for responding via email.
 */

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { getApplicationStatus } from '@/lib/api/registration';
import type { ApplicationStatusResponse } from '@/app/register/types/registration';

type PageState = 'form' | 'loading' | 'success' | 'error';

function RespondPageContent() {
    const searchParams = useSearchParams();
    const applicationId = searchParams.get('id');

    const [state, setState] = useState<PageState>('form');
    const [email, setEmail] = useState('');
    const [emailError, setEmailError] = useState('');
    const [errorMessage, setErrorMessage] = useState('');
    const [statusData, setStatusData] = useState<ApplicationStatusResponse | null>(null);

    const validateEmail = (email: string): boolean => {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setEmailError('');

        if (!email.trim()) {
            setEmailError('Email is required');
            return;
        }

        if (!validateEmail(email)) {
            setEmailError('Please enter a valid email address');
            return;
        }

        if (!applicationId) {
            setState('error');
            setErrorMessage('Invalid application ID. Please use the link from your email.');
            return;
        }

        setState('loading');

        try {
            const response = await getApplicationStatus(applicationId, email.trim().toLowerCase());
            setStatusData(response);
            setState('success');
        } catch (error) {
            setState('error');
            setErrorMessage(
                error instanceof Error
                    ? error.message
                    : 'Failed to retrieve application. Please check your email and try again.'
            );
        }
    };

    // No application ID provided
    if (!applicationId) {
        return (
            <div className="min-h-screen bg-[#f5f5f5] flex items-center justify-center px-4">
                <div className="max-w-2xl w-full bg-white rounded-xl shadow-md p-8 sm:p-12">
                    <div className="text-center">
                        <div className="flex justify-center mb-6">
                            <div className="w-20 h-20 bg-[#dc2626]/10 rounded-full flex items-center justify-center">
                                <svg className="w-10 h-10 text-[#dc2626]" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
                                    <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                                </svg>
                            </div>
                        </div>
                        <h1 className="text-3xl font-bold text-[#1a365d] mb-4">Invalid Link</h1>
                        <p className="text-[#4b5563] mb-8">
                            No application ID was provided. Please use the link from your email.
                        </p>
                        <Link
                            href="/"
                            className="inline-block px-6 py-3 bg-[#1a365d] text-white font-medium rounded-lg hover:bg-[#1e4976]"
                        >
                            Back to Home
                        </Link>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#f5f5f5] flex items-center justify-center px-4">
            <div className="max-w-2xl w-full bg-white rounded-xl shadow-md p-8 sm:p-12">
                {/* Email Form State */}
                {state === 'form' && (
                    <div>
                        <div className="text-center mb-8">
                            <div className="flex justify-center mb-6">
                                <div className="w-20 h-20 bg-[#f59e0b]/10 rounded-full flex items-center justify-center">
                                    <svg className="w-10 h-10 text-[#f59e0b]" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
                                        <path d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                    </svg>
                                </div>
                            </div>
                            <h1 className="text-3xl font-bold text-[#1a365d] mb-2">Respond to Information Request</h1>
                            <p className="text-[#4b5563]">
                                Enter your email to view what information is needed for your application.
                            </p>
                        </div>

                        <form onSubmit={handleSubmit} className="space-y-6">
                            <div>
                                <label htmlFor="email" className="block text-sm font-medium text-[#1f2937] mb-2">
                                    Email Address
                                </label>
                                <input
                                    type="email"
                                    id="email"
                                    value={email}
                                    onChange={(e) => {
                                        setEmail(e.target.value);
                                        setEmailError('');
                                    }}
                                    placeholder="Enter your email"
                                    className={`w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3b82f6]/50 ${
                                        emailError
                                            ? 'border-[#dc2626] focus:border-[#dc2626]'
                                            : 'border-[#d1d5db] focus:border-[#3b82f6]'
                                    }`}
                                />
                                {emailError && (
                                    <p className="mt-2 text-sm text-[#dc2626]">{emailError}</p>
                                )}
                            </div>

                            <button
                                type="submit"
                                className="w-full px-6 py-3 bg-[#1a365d] text-white font-medium rounded-lg hover:bg-[#1e4976] transition-colors"
                            >
                                View Request
                            </button>
                        </form>

                        <div className="mt-8 text-center">
                            <Link href="/" className="text-[#3b82f6] hover:underline">
                                Back to Home
                            </Link>
                        </div>
                    </div>
                )}

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
                        <h1 className="text-2xl font-bold text-[#1a365d] mb-2">Loading...</h1>
                        <p className="text-[#6b7280]">Please wait while we retrieve your application...</p>
                    </div>
                )}

                {/* Success State */}
                {state === 'success' && statusData && (
                    <div>
                        <div className="text-center mb-8">
                            <div className="flex justify-center mb-6">
                                <div className="w-20 h-20 bg-[#f59e0b]/10 rounded-full flex items-center justify-center">
                                    <svg className="w-10 h-10 text-[#f59e0b]" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
                                        <path d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
                                    </svg>
                                </div>
                            </div>
                            <h1 className="text-3xl font-bold text-[#1a365d] mb-2">{statusData.school_name}</h1>
                            <p className="text-[#6b7280]">
                                {statusData.status === 'more_info_requested'
                                    ? 'Additional information has been requested for your application.'
                                    : statusData.status_description
                                }
                            </p>
                        </div>

                        {statusData.status === 'more_info_requested' && (
                            <>
                                <div className="bg-[#f59e0b]/10 border border-[#f59e0b] rounded-lg p-6 mb-6">
                                    <h2 className="font-semibold text-[#92400e] mb-2">How to Respond</h2>
                                    <p className="text-[#92400e] text-sm mb-4">
                                        Our team has requested additional information for your application.
                                        Please reply directly to the email you received with the requested information.
                                    </p>
                                    <p className="text-[#92400e] text-sm">
                                        If you didn&apos;t receive the email, check your spam folder or contact us at{' '}
                                        <a href="mailto:support@eksms.dev" className="underline">support@eksms.dev</a>
                                    </p>
                                </div>

                                <div className="bg-[#eff6ff] border border-[#bfdbfe] rounded-lg p-6 mb-8">
                                    <h2 className="font-semibold text-[#1e40af] mb-2">What to Include in Your Response</h2>
                                    <ul className="text-[#1e40af] text-sm space-y-2">
                                        <li>• Reference your application ID: <strong className="font-mono">{statusData.id}</strong></li>
                                        <li>• Include your school name: <strong>{statusData.school_name}</strong></li>
                                        <li>• Provide all the information that was requested</li>
                                        <li>• Attach any relevant documents if needed</li>
                                    </ul>
                                </div>
                            </>
                        )}

                        {statusData.status !== 'more_info_requested' && (
                            <div className="bg-[#3b82f6]/10 border border-[#3b82f6] rounded-lg p-6 mb-8">
                                <h2 className="font-semibold text-[#1e40af] mb-2">Application Status</h2>
                                <p className="text-[#1e40af] text-sm">
                                    Your application is currently: <strong>{statusData.status_label}</strong>
                                </p>
                                <p className="text-[#1e40af] text-sm mt-2">
                                    {statusData.status_description}
                                </p>
                            </div>
                        )}

                        <div className="text-center">
                            <Link
                                href={`/register/status?id=${applicationId}`}
                                className="inline-block px-6 py-3 border border-[#d1d5db] text-[#4b5563] font-medium rounded-lg hover:bg-[#f5f5f5] mr-4"
                            >
                                View Full Status
                            </Link>
                            <Link
                                href="/"
                                className="inline-block px-6 py-3 bg-[#1a365d] text-white font-medium rounded-lg hover:bg-[#1e4976]"
                            >
                                Back to Home
                            </Link>
                        </div>
                    </div>
                )}

                {/* Error State */}
                {state === 'error' && (
                    <div className="text-center">
                        <div className="flex justify-center mb-6">
                            <div className="w-20 h-20 bg-[#dc2626]/10 rounded-full flex items-center justify-center">
                                <svg className="w-10 h-10 text-[#dc2626]" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
                                    <path d="M6 18L18 6M6 6l12 12"></path>
                                </svg>
                            </div>
                        </div>
                        <h1 className="text-3xl font-bold text-[#1a365d] mb-4">Unable to Load Application</h1>
                        <p className="text-[#4b5563] mb-8">{errorMessage}</p>

                        <div className="flex flex-col sm:flex-row gap-4 justify-center">
                            <button
                                onClick={() => {
                                    setState('form');
                                    setErrorMessage('');
                                }}
                                className="px-6 py-3 border border-[#d1d5db] text-[#4b5563] font-medium rounded-lg hover:bg-[#f5f5f5]"
                            >
                                Try Again
                            </button>
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

export function RespondPage() {
    return (
        <Suspense fallback={<LoadingFallback />}>
            <RespondPageContent />
        </Suspense>
    );
}

export default RespondPage;
