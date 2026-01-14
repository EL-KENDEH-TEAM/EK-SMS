'use client';

/**
 * Step 6: Review & Submit
 *
 * Displays all form data for review before submission
 */

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useRegistration } from '../context/RegistrationContext';
import { submitApplication } from '@/lib/api/registration';
import type { FormStep, BasicInfoData, LocationData, ContactData, AboutYouData, DetailsData } from '../types/registration';

// Union type for all section data types
type SectionData = BasicInfoData | LocationData | ContactData | AboutYouData | DetailsData;

export function Step6Review() {
    const router = useRouter();
    const { formData, previousStep, goToStep } = useRegistration();
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [submitError, setSubmitError] = useState('');
    const [acceptedTerms, setAcceptedTerms] = useState(false);

    const handleSubmit = async () => {
        if (!acceptedTerms) {
            setSubmitError('You must accept the terms & conditions to continue');
            return;
        }

        setIsSubmitting(true);
        setSubmitError('');

        try {
            // Submit application to API
            const response = await submitApplication(formData);

            // Store application data for success page
            if (typeof window !== 'undefined') {
                sessionStorage.setItem('applicationId', response.id);
                sessionStorage.setItem('registrationEmail', response.applicant_email);
            }

            // Redirect to success page
            router.push(`/register/success?id=${response.id}&email=${encodeURIComponent(response.applicant_email)}`);

        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to submit registration. Please try again.';
            setSubmitError(errorMessage);
            console.error('Registration error:', error);
        } finally {
            setIsSubmitting(false);
        }
    };

    const SectionCard = ({ title, data, stepNumber }: { title: string; data: SectionData; stepNumber: FormStep }) => (
        <div className="bg-white rounded-lg border border-[#e5e7eb] p-6">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-[#1a365d]">{title}</h3>
                <button
                    onClick={() => goToStep(stepNumber)}
                    aria-label={`Edit ${title}`}
                    className="text-sm text-[#3b82f6] hover:text-[#1e4976] underline"
                >
                    Edit
                </button>
            </div>
            <div className="space-y-2">
                {Object.entries(data).map(([key, value]) => {
                    if (value === '' || value === false || value === undefined) return null;

                    // Format field names
                    const fieldName = key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase());

                    let displayValue: string = '';
                    if (typeof value === 'boolean') {
                        displayValue = value ? 'Yes' : 'No';
                    } else if (Array.isArray(value)) {
                        displayValue = `${value.length} items`;
                    } else {
                        displayValue = String(value);
                    }

                    return (
                        <div key={key} className="flex justify-between py-2 border-b border-[#f5f5f5] last:border-0">
                            <span className="text-sm text-[#6b7280]">{fieldName}:</span>
                            <span className="text-sm text-[#1f2937] font-medium">
                                {displayValue}
                            </span>
                        </div>
                    );
                })}
            </div>
        </div>
    );

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold text-[#1a365d]">Review Your Information</h2>
                <p className="text-[#4b5563] mt-2">Please review all details before submitting</p>
            </div>

            {/* Review Sections */}
            <div className="space-y-4">
                <SectionCard title="Basic Information" data={formData.basicInfo} stepNumber={1} />
                <SectionCard title="Location" data={formData.location} stepNumber={2} />
                <SectionCard title="Contact Information" data={formData.contact} stepNumber={3} />
                <SectionCard title="About You" data={formData.aboutYou} stepNumber={4} />
                <SectionCard title="School Details" data={formData.details} stepNumber={5} />
            </div>

            {/* Error Message */}
            {submitError && (
                <div className="bg-[#dc2626]/10 border border-[#dc2626] rounded-lg p-4" role="alert">
                    <p className="text-[#dc2626] text-sm">{submitError}</p>
                </div>
            )}

            {/* Info Box */}
            <div className="bg-[#3b82f6]/10 border border-[#3b82f6] rounded-lg p-4">
                <p className="text-[#1a365d] text-sm">
                    <strong>Next Steps:</strong> After submission, you will receive a verification email.
                    Please check your inbox and follow the instructions to complete your registration.
                </p>
            </div>

            {/* Terms & Conditions (Required) */}
            <div className="border-l-4 border-[#1a365d] pl-6">
                <label className="flex items-start cursor-pointer">
                    <input
                        type="checkbox"
                        checked={acceptedTerms}
                        onChange={(e) => setAcceptedTerms(e.target.checked)}
                        aria-required="true"
                        aria-describedby="terms-error"
                        className="w-5 h-5 mt-0.5 text-[#1a365d] rounded focus:ring-2 focus:ring-[#3b82f6]"
                    />
                    <span className="ml-3 text-sm text-[#1f2937]">
                        I accept the <a href="/terms" className="text-[#3b82f6] hover:underline" target="_blank" rel="noopener noreferrer">Terms & Conditions</a> <span className="text-[#dc2626]">*</span>
                    </span>
                </label>
                {!acceptedTerms && submitError && (
                    <p id="terms-error" className="text-[#dc2626] text-sm mt-2" role="alert">You must accept the terms & conditions to submit</p>
                )}
            </div>

            {/* Navigation */}
            <div className="flex justify-between pt-4">
                <button
                    onClick={previousStep}
                    disabled={isSubmitting}
                    className="px-6 py-3 border border-[#d1d5db] text-[#4b5563] font-medium rounded-lg hover:bg-[#f5f5f5] disabled:opacity-50"
                >
                    Previous
                </button>
                <button
                    onClick={handleSubmit}
                    disabled={isSubmitting || !acceptedTerms}
                    className={`px-8 py-3 font-medium rounded-lg flex items-center ${!acceptedTerms || isSubmitting
                        ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                        : 'bg-[#22c55e] text-white hover:bg-[#16a34a]'
                        }`}
                >
                    {isSubmitting ? (
                        <>
                            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            Submitting...
                        </>
                    ) : (
                        'Submit Registration'
                    )}
                </button>
            </div>
        </div>
    );
}
