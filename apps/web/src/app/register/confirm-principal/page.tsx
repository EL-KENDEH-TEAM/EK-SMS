'use client';

/**
 * Principal Confirmation Page
 * 
 * Principals land here when clicking confirmation link in their email
 * Route: /register/confirm-principal?token=xyz
 */

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { getPrincipalApplication, confirmPrincipal } from '@/lib/api/registration';
import type { PrincipalApplicationResponse } from '../types/registration';

type ConfirmationState = 'loading' | 'fetched' | 'success' | 'error';

function PrincipalConfirmationContent() {
    const searchParams = useSearchParams();
    const [state, setState] = useState<ConfirmationState>('loading');
    const [message, setMessage] = useState('');
    const [application, setApplication] = useState<PrincipalApplicationResponse | null>(null);
    const [isConfirming, setIsConfirming] = useState(false);
    const [token, setToken] = useState<string | null>(null);

    useEffect(() => {
        const tokenParam = searchParams.get('token');
        setToken(tokenParam);

        if (!tokenParam) {
            setState('error');
            setMessage('Invalid confirmation link. No token provided.');
            return;
        }

        // Fetch application summary
        getPrincipalApplication(tokenParam)
            .then((data) => {
                setApplication(data);
                setState('fetched');
            })
            .catch((error) => {
                setState('error');
                setMessage(
                    error instanceof Error
                        ? error.message
                        : 'Failed to fetch application details. The link may be expired.'
                );
            });
    }, [searchParams]);

    const handleConfirm = async () => {
        if (!token) return;

        setIsConfirming(true);
        try {
            const response = await confirmPrincipal(token);
            setState('success');
            setMessage(response.message || 'Thank you! The school application has been confirmed.');
        } catch (error) {
            setState('error');
            setMessage(
                error instanceof Error
                    ? error.message
                    : 'Confirmation failed. Please try again later.'
            );
        } finally {
            setIsConfirming(false);
        }
    };

    return (
        <div className="min-h-screen bg-[#f5f5f5] flex items-center justify-center px-4 py-12">
            <div className="max-w-2xl w-full bg-white rounded-xl shadow-md p-8 sm:p-12">
                {/* Loading State */}
                {state === 'loading' && (
                    <div className="text-center py-8">
                        <div className="flex justify-center mb-6">
                            <svg className="animate-spin h-16 w-16 text-[#3b82f6]" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                        </div>
                        <h1 className="text-2xl font-bold text-[#1a365d] mb-2">Loading Application...</h1>
                        <p className="text-[#6b7280]">Please wait while we retrieve the details...</p>
                    </div>
                )}

                {/* Fetched State (Summary & Confirm) */}
                {state === 'fetched' && application && (
                    <div>
                        <div className="mb-8 text-center">
                            <h1 className="text-3xl font-bold text-[#1a365d] mb-2">School Registration Confirmation</h1>
                            <p className="text-[#4b5563]">An application has been submitted for your school. Please review the details below to confirm.</p>
                        </div>

                        <div className="bg-[#f8fafc] border border-[#e2e8f0] rounded-xl p-6 mb-8 space-y-6">
                            <h2 className="text-lg font-semibold text-[#1a365d] border-b border-[#e2e8f0] pb-3 mb-4">Application Summary</h2>

                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <div>
                                    <p className="text-sm text-[#64748b] font-medium uppercase tracking-wider">School Name</p>
                                    <p className="text-[#1e293b] font-semibold">{application.school_name}</p>
                                </div>
                                <div>
                                    <p className="text-sm text-[#64748b] font-medium uppercase tracking-wider">Submitted By</p>
                                    <p className="text-[#1e293b] font-semibold">{application.applicant_name}</p>
                                </div>
                                <div className="sm:col-span-2">
                                    <p className="text-sm text-[#64748b] font-medium uppercase tracking-wider">Initial System Administrator</p>
                                    <p className="text-[#1e293b] font-semibold">
                                        {application.admin_choice === 'applicant'
                                            ? `${application.applicant_name} (Applicant)`
                                            : 'The Principal (You)'}
                                    </p>
                                    <p className="text-xs text-[#64748b] mt-1 italic">
                                        Note: This person will have full access to set up the system. You can change this later.
                                    </p>
                                </div>
                            </div>
                        </div>

                        <div className="bg-[#3b82f6]/5 border border-[#3b82f6]/20 rounded-lg p-4 mb-8">
                            <p className="text-sm text-[#1e40af]">
                                By clicking <strong>Confirm</strong>, you authorize the registration of this school on the EK-SMS platform.
                            </p>
                        </div>

                        <div className="flex flex-col sm:flex-row gap-4 justify-center">
                            <button
                                onClick={handleConfirm}
                                disabled={isConfirming}
                                className="px-8 py-3 bg-[#1a365d] text-white font-semibold rounded-lg hover:bg-[#1e4976] disabled:opacity-50 transition-colors flex items-center justify-center min-w-[160px]"
                            >
                                {isConfirming ? (
                                    <>
                                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                        </svg>
                                        Confirming...
                                    </>
                                ) : (
                                    'Confirm Registration'
                                )}
                            </button>
                            <Link
                                href="/"
                                className="px-8 py-3 border border-[#d1d5db] text-[#475569] font-semibold rounded-lg hover:bg-[#f8fafc] text-center"
                            >
                                Cancel
                            </Link>
                        </div>
                    </div>
                )}

                {/* Success State */}
                {state === 'success' && (
                    <div className="text-center py-4">
                        <div className="flex justify-center mb-6">
                            <div className="w-20 h-20 bg-[#22c55e]/10 rounded-full flex items-center justify-center">
                                <svg className="w-12 h-12 text-[#22c55e]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                                </svg>
                            </div>
                        </div>
                        <h1 className="text-3xl font-bold text-[#1a365d] mb-4">Confirmation Complete!</h1>
                        <p className="text-[#4b5563] mb-8">{message}</p>

                        <div className="bg-[#22c55e]/5 border border-[#22c55e]/20 rounded-xl p-6 mb-8 text-left">
                            <h2 className="font-semibold text-[#166534] mb-3 flex items-center">
                                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1-1 0 00-1.414-1.414L9 10.586 7.707 9.293a1-1 0 00-1.414 1.414l2 2a1-1 0 001.414 0l4-4z" clipRule="evenodd"></path>
                                </svg>
                                What happens next?
                            </h2>
                            <ul className="text-[#166534] text-sm space-y-3">
                                <li className="flex items-start">
                                    <span className="mr-2 mt-1">•</span>
                                    <span>The application is now fully verified and will be reviewed by our administration team.</span>
                                </li>
                                <li className="flex items-start">
                                    <span className="mr-2 mt-1">•</span>
                                    <span>You will receive an email notification once the school setup is approved.</span>
                                </li>
                                <li className="flex items-start">
                                    <span className="mr-2 mt-1">•</span>
                                    <span>This process typically takes 3-5 business days.</span>
                                </li>
                            </ul>
                        </div>

                        <Link
                            href="/"
                            className="inline-block px-8 py-3 bg-[#1a365d] text-white font-semibold rounded-lg hover:bg-[#1e4976]"
                        >
                            Back to Home
                        </Link>
                    </div>
                )}

                {/* Error State */}
                {state === 'error' && (
                    <div className="text-center py-4">
                        <div className="flex justify-center mb-6">
                            <div className="w-20 h-20 bg-[#dc2626]/10 rounded-full flex items-center justify-center">
                                <svg className="w-12 h-12 text-[#dc2626]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                                </svg>
                            </div>
                        </div>
                        <h1 className="text-3xl font-bold text-[#1a365d] mb-4">Confirmation Failed</h1>
                        <div className="bg-[#dc2626]/5 border border-[#dc2626]/20 rounded-lg p-4 mb-8">
                            <p className="text-[#dc2626]">{message}</p>
                        </div>

                        <p className="text-[#4b5563] mb-8 text-sm">
                            If you believe this is an error, please contact the person who submitted the application or reach out to our support team.
                        </p>

                        <div className="flex flex-col sm:flex-row gap-4 justify-center">
                            <Link
                                href="/contact"
                                className="px-8 py-3 border border-[#d1d5db] text-[#475569] font-semibold rounded-lg hover:bg-[#f8fafc]"
                            >
                                Contact Support
                            </Link>
                            <Link
                                href="/"
                                className="px-8 py-3 bg-[#1a365d] text-white font-semibold rounded-lg hover:bg-[#1e4976]"
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

export default function PrincipalConfirmationPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-[#f5f5f5] flex items-center justify-center">
                <div className="animate-spin h-16 w-16 text-[#3b82f6]"></div>
            </div>
        }>
            <PrincipalConfirmationContent />
        </Suspense>
    );
}
