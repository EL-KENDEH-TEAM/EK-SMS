'use client';

/**
 * Step 3: Contact Information Form
 * 
 * School Contact Section (optional) + Principal Section (required)
 */

import { useState } from 'react';
import { useRegistration } from '../context/RegistrationContext';
import type { ContactData, FormErrors } from '../types/registration';

export function Step3Contact() {
    const { formData, updateFormData, nextStep, previousStep } = useRegistration();
    const [errors, setErrors] = useState<FormErrors>({});

    const currentData = formData.contact;

    const handleChange = (field: keyof ContactData, value: string) => {
        updateFormData('contact', { [field]: value });
        if (errors[field]) {
            setErrors(prev => ({ ...prev, [field]: '' }));
        }
    };

    const validate = (): boolean => {
        const newErrors: FormErrors = {};

        // Validation Rule: At least one of school_phone or school_email must be provided
        const hasSchoolContact = (currentData.schoolPhone?.trim() || currentData.schoolEmail?.trim());
        if (!hasSchoolContact) {
            newErrors.schoolContact = 'At least one of school phone or school email must be provided';
        }

        // School email validation if provided
        if (currentData.schoolEmail && !/\S+@\S+\.\S+/.test(currentData.schoolEmail)) {
            newErrors.schoolEmail = 'Please enter a valid email address';
        }

        // Principal Section - All Required
        if (!currentData.principalFullName.trim()) {
            newErrors.principalFullName = 'Principal full name is required';
        }

        if (!currentData.principalEmail.trim()) {
            newErrors.principalEmail = 'Principal email is required';
        } else if (!/\S+@\S+\.\S+/.test(currentData.principalEmail)) {
            newErrors.principalEmail = 'Please enter a valid email address';
        }

        if (!currentData.principalPhone.trim()) {
            newErrors.principalPhone = 'Principal phone is required';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleNext = () => {
        if (validate()) {
            nextStep();
        }
    };

    return (
        <div className="space-y-8">
            <div>
                <h2 className="text-2xl font-bold text-[#1a365d]">Contact Information</h2>
                <p className="text-[#4b5563] mt-2">How can we reach your school and principal?</p>
            </div>

            {/* Validation Rule Warning */}
            <div className="bg-[#f59e0b]/10 border border-[#f59e0b] rounded-lg p-4">
                <p className="text-[#92400e] text-sm">
                    <strong>Validation Rule:</strong> At least one of school_phone or school_email must be provided.
                </p>
            </div>

            {/* School Contact Section Error */}
            {errors.schoolContact && (
                <div className="bg-[#dc2626]/10 border border-[#dc2626] rounded-lg p-4">
                    <p className="text-[#dc2626] text-sm">{errors.schoolContact}</p>
                </div>
            )}

            {/* School Contact Section (Optional) */}
            <div className="bg-[#f5f5f5] rounded-lg p-6">
                <h3 className="text-lg font-semibold text-[#1a365d] mb-4">
                    School Contact <span className="text-[#6b7280] text-sm font-normal">(Optional)</span>
                </h3>

                <div className="space-y-4">
                    {/* School Phone */}
                    <div>
                        <label htmlFor="schoolPhone" className="block text-sm font-medium text-[#1f2937] mb-2">
                            School Phone
                        </label>
                        <input
                            id="schoolPhone"
                            type="tel"
                            value={currentData.schoolPhone || ''}
                            onChange={(e) => handleChange('schoolPhone', e.target.value)}
                            className="w-full px-4 py-3 rounded-lg border border-[#d1d5db] focus:outline-none focus:ring-2 focus:ring-[#3b82f6]"
                            placeholder="+232 XX XXX XXXX"
                        />
                    </div>

                    {/* School Email */}
                    <div>
                        <label htmlFor="schoolEmail" className="block text-sm font-medium text-[#1f2937] mb-2">
                            School Email
                        </label>
                        <input
                            id="schoolEmail"
                            type="email"
                            value={currentData.schoolEmail || ''}
                            onChange={(e) => handleChange('schoolEmail', e.target.value)}
                            className={`w-full px-4 py-3 rounded-lg border ${errors.schoolEmail ? 'border-[#dc2626]' : 'border-[#d1d5db]'} focus:outline-none focus:ring-2 focus:ring-[#3b82f6]`}
                            placeholder="school@example.com"
                        />
                        {errors.schoolEmail && <p className="text-[#dc2626] text-sm mt-1">{errors.schoolEmail}</p>}
                    </div>
                </div>
            </div>

            {/* Principal Section (Required) */}
            <div className="border-l-4 border-[#1a365d] pl-6">
                <h3 className="text-lg font-semibold text-[#1a365d] mb-4">
                    Principal Information <span className="text-[#dc2626]">*</span>
                </h3>

                <div className="space-y-4">
                    {/* Principal Full Name */}
                    <div>
                        <label htmlFor="principalFullName" className="block text-sm font-medium text-[#1f2937] mb-2">
                            Full Name <span className="text-[#dc2626]">*</span>
                        </label>
                        <input
                            id="principalFullName"
                            type="text"
                            value={currentData.principalFullName}
                            onChange={(e) => handleChange('principalFullName', e.target.value)}
                            className={`w-full px-4 py-3 rounded-lg border ${errors.principalFullName ? 'border-[#dc2626]' : 'border-[#d1d5db]'} focus:outline-none focus:ring-2 focus:ring-[#3b82f6]`}
                            placeholder="Principal's full name"
                        />
                        {errors.principalFullName && <p className="text-[#dc2626] text-sm mt-1">{errors.principalFullName}</p>}
                    </div>

                    {/* Principal Email */}
                    <div>
                        <label htmlFor="principalEmail" className="block text-sm font-medium text-[#1f2937] mb-2">
                            Email <span className="text-[#dc2626]">*</span>
                        </label>
                        <input
                            id="principalEmail"
                            type="email"
                            value={currentData.principalEmail}
                            onChange={(e) => handleChange('principalEmail', e.target.value)}
                            className={`w-full px-4 py-3 rounded-lg border ${errors.principalEmail ? 'border-[#dc2626]' : 'border-[#d1d5db]'} focus:outline-none focus:ring-2 focus:ring-[#3b82f6]`}
                            placeholder="principal@example.com"
                        />
                        {errors.principalEmail && <p className="text-[#dc2626] text-sm mt-1">{errors.principalEmail}</p>}
                    </div>

                    {/* Principal Phone */}
                    <div>
                        <label htmlFor="principalPhone" className="block text-sm font-medium text-[#1f2937] mb-2">
                            Phone <span className="text-[#dc2626]">*</span>
                        </label>
                        <input
                            id="principalPhone"
                            type="tel"
                            value={currentData.principalPhone}
                            onChange={(e) => handleChange('principalPhone', e.target.value)}
                            className={`w-full px-4 py-3 rounded-lg border ${errors.principalPhone ? 'border-[#dc2626]' : 'border-[#d1d5db]'} focus:outline-none focus:ring-2 focus:ring-[#3b82f6]`}
                            placeholder="+232 XX XXX XXXX"
                        />
                        {errors.principalPhone && <p className="text-[#dc2626] text-sm mt-1">{errors.principalPhone}</p>}
                    </div>
                </div>
            </div>

            {/* Navigation */}
            <div className="flex justify-between pt-4">
                <button
                    onClick={previousStep}
                    className="px-6 py-3 border border-[#d1d5db] text-[#4b5563] font-medium rounded-lg hover:bg-[#f5f5f5]"
                >
                    Previous
                </button>
                <button
                    onClick={handleNext}
                    className="px-6 py-3 bg-[#1a365d] text-white font-medium rounded-lg hover:bg-[#1e4976]"
                >
                    Continue
                </button>
            </div>
        </div>
    );
}
