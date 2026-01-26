'use client';

/**
 * Application Status Page
 *
 * Users land here when clicking "Check Status" link in emails
 * Route: /register/status?id=application-uuid
 *
 * Flow:
 * 1. Get application ID from URL
 * 2. Prompt user for email (security verification)
 * 3. Fetch and display application status with progress
 */

import { useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { getApplicationStatus } from '@/lib/api/registration';
import type { ApplicationStatusResponse, StatusStep } from '@/app/register/types/registration';

type PageState = 'form' | 'loading' | 'success' | 'error';

/**
 * Get status color based on application status
 */
function getStatusColor(status: ApplicationStatusResponse['status']): {
    bg: string;
    border: string;
    text: string;
    icon: string;
} {
    switch (status) {
        case 'approved':
            return { bg: 'bg-[#22c55e]/10', border: 'border-[#22c55e]', text: 'text-[#166534]', icon: '#22c55e' };
        case 'rejected':
        case 'expired':
            return { bg: 'bg-[#dc2626]/10', border: 'border-[#dc2626]', text: 'text-[#991b1b]', icon: '#dc2626' };
        case 'more_info_requested':
            return { bg: 'bg-[#f59e0b]/10', border: 'border-[#f59e0b]', text: 'text-[#92400e]', icon: '#f59e0b' };
        default:
            return { bg: 'bg-[#3b82f6]/10', border: 'border-[#3b82f6]', text: 'text-[#1e40af]', icon: '#3b82f6' };
    }
}

/**
 * Get icon based on application status
 */
function StatusIcon({ status }: { status: ApplicationStatusResponse['status'] }) {
    const colors = getStatusColor(status);

    if (status === 'approved') {
        return (
            <div className={`w-20 h-20 ${colors.bg} rounded-full flex items-center justify-center`}>
                <svg className="w-10 h-10" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke={colors.icon}>
                    <path d="M5 13l4 4L19 7"></path>
                </svg>
            </div>
        );
    }

    if (status === 'rejected' || status === 'expired') {
        return (
            <div className={`w-20 h-20 ${colors.bg} rounded-full flex items-center justify-center`}>
                <svg className="w-10 h-10" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke={colors.icon}>
                    <path d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </div>
        );
    }

    // Default: in progress / pending states
    return (
        <div className={`w-20 h-20 ${colors.bg} rounded-full flex items-center justify-center`}>
            <svg className="w-10 h-10" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke={colors.icon}>
                <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
        </div>
    );
}

/**
 * Progress Stepper Component
 */
function ProgressStepper({ steps }: { steps: StatusStep[] }) {
    return (
        <div className="w-full max-w-md mx-auto">
            {steps.map((step, index) => (
                <div key={step.name} className="flex items-start">
                    <div className="flex flex-col items-center mr-4">
                        {/* Step circle */}
                        <div
                            className={`w-8 h-8 rounded-full flex items-center justify-center ${
                                step.completed
                                    ? 'bg-[#22c55e] text-white'
                                    : 'bg-[#e5e7eb] text-[#9ca3af]'
                            }`}
                        >
                            {step.completed ? (
                                <svg className="w-4 h-4" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
                                    <path d="M5 13l4 4L19 7"></path>
                                </svg>
                            ) : (
                                <span className="text-sm font-medium">{index + 1}</span>
                            )}
                        </div>
                        {/* Connecting line (except for last item) */}
                        {index < steps.length - 1 && (
                            <div
                                className={`w-0.5 h-8 ${
                                    step.completed ? 'bg-[#22c55e]' : 'bg-[#e5e7eb]'
                                }`}
                            ></div>
                        )}
                    </div>
                    <div className="flex-1 pb-8">
                        <p
                            className={`font-medium ${
                                step.completed ? 'text-[#1f2937]' : 'text-[#9ca3af]'
                            }`}
                        >
                            {step.name}
                        </p>
                        {step.completed && step.completed_at && (
                            <p className="text-xs text-[#6b7280] mt-1">
                                {new Date(step.completed_at).toLocaleDateString('en-US', {
                                    month: 'short',
                                    day: 'numeric',
                                    year: 'numeric',
                                    hour: '2-digit',
                                    minute: '2-digit',
                                })}
                            </p>
                        )}
                    </div>
                </div>
            ))}
        </div>
    );
}

function StatusPageContent() {
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
                    : 'Failed to retrieve application status. Please check your email and try again.'
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
                            No application ID was provided. Please use the link from your email to check your application status.
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
                                <div className="w-20 h-20 bg-[#3b82f6]/10 rounded-full flex items-center justify-center">
                                    <svg className="w-10 h-10 text-[#3b82f6]" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
                                        <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                                    </svg>
                                </div>
                            </div>
                            <h1 className="text-3xl font-bold text-[#1a365d] mb-2">Check Application Status</h1>
                            <p className="text-[#4b5563]">
                                Enter the email address you used to register to view your application status.
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
                                Check Status
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
                        <h1 className="text-2xl font-bold text-[#1a365d] mb-2">Loading Status</h1>
                        <p className="text-[#6b7280]">Please wait while we retrieve your application status...</p>
                    </div>
                )}

                {/* Success State */}
                {state === 'success' && statusData && (
                    <div>
                        <div className="text-center mb-8">
                            <div className="flex justify-center mb-6">
                                <StatusIcon status={statusData.status} />
                            </div>
                            <h1 className="text-3xl font-bold text-[#1a365d] mb-2">{statusData.school_name}</h1>
                            <p className="text-[#6b7280] text-sm">
                                Submitted on {new Date(statusData.submitted_at).toLocaleDateString('en-US', {
                                    month: 'long',
                                    day: 'numeric',
                                    year: 'numeric',
                                })}
                            </p>
                        </div>

                        {/* Status Badge */}
                        {(() => {
                            const colors = getStatusColor(statusData.status);
                            return (
                                <div className={`${colors.bg} ${colors.border} border rounded-lg p-6 mb-8`}>
                                    <div className="text-center">
                                        <span className={`inline-block px-4 py-1 rounded-full text-sm font-semibold ${colors.bg} ${colors.text} border ${colors.border}`}>
                                            {statusData.status_label}
                                        </span>
                                        <p className={`mt-3 ${colors.text}`}>
                                            {statusData.status_description}
                                        </p>
                                    </div>
                                </div>
                            );
                        })()}

                        {/* Progress Steps */}
                        <div className="mb-8">
                            <h2 className="text-lg font-semibold text-[#1f2937] mb-4 text-center">Application Progress</h2>
                            <ProgressStepper steps={statusData.steps} />
                        </div>

                        <div className="text-center">
                            <button
                                onClick={() => {
                                    setState('form');
                                    setEmail('');
                                    setStatusData(null);
                                }}
                                className="px-6 py-3 border border-[#d1d5db] text-[#4b5563] font-medium rounded-lg hover:bg-[#f5f5f5] mr-4"
                            >
                                Check Another
                            </button>
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
                        <h1 className="text-3xl font-bold text-[#1a365d] mb-4">Unable to Retrieve Status</h1>
                        <p className="text-[#4b5563] mb-8">{errorMessage}</p>

                        <div className="bg-[#dc2626]/10 border border-[#dc2626] rounded-lg p-6 mb-8">
                            <h2 className="font-semibold text-[#991b1b] mb-2">What can you do?</h2>
                            <div className="text-[#991b1b] text-sm space-y-2">
                                <p>• Make sure you entered the correct email address</p>
                                <p>• Use the email you used when registering</p>
                                <p>• Contact support if the problem persists</p>
                            </div>
                        </div>

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

export function StatusPage() {
    return (
        <Suspense fallback={<LoadingFallback />}>
            <StatusPageContent />
        </Suspense>
    );
}

export default StatusPage;
