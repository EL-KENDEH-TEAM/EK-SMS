'use client';

/**
 * Step 4: About You Form
 * 
 * Applicant information with conditional fields
 */

import { useState } from 'react';
import { useRegistration } from '../context/RegistrationContext';
import type { AboutYouData, FormErrors } from '../types/registration';

export function Step4AboutYou() {
    const { formData, updateFormData, nextStep, previousStep } = useRegistration();
    const [errors, setErrors] = useState<FormErrors>({});

    const currentData = formData.aboutYou;

    const handleChange = (field: keyof AboutYouData, value: string | boolean) => {
        updateFormData('aboutYou', { [field]: value });
        if (errors[field as string]) {
            setErrors(prev => ({ ...prev, [field as string]: '' }));
        }
    };

    const validate = (): boolean => {
        const newErrors: FormErrors = {};

        // If NOT principal, all fields are required
        if (!currentData.iAmPrincipal) {
            if (!currentData.yourFullName?.trim()) {
                newErrors.yourFullName = 'Your full name is required';
            }
            if (!currentData.yourEmail?.trim()) {
                newErrors.yourEmail = 'Your email is required';
            } else if (!/\S+@\S+\.\S+/.test(currentData.yourEmail)) {
                newErrors.yourEmail = 'Please enter a valid email address';
            }
            if (!currentData.yourPhone?.trim()) {
                newErrors.yourPhone = 'Your phone is required';
            }
            if (!currentData.yourRole?.trim()) {
                newErrors.yourRole = 'Your role is required';
            }
            if (!currentData.whoManagesSystem) {
                newErrors.whoManagesSystem = 'Please select who should manage the system';
            }
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
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold text-[#1a365d]">About You</h2>
                <p className="text-[#4b5563] mt-2">Tell us about yourself</p>
            </div>

            {/* I am the Principal Checkbox */}
            <div className="bg-[#f5f5f5] p-4 rounded-lg">
                <label className="flex items-center cursor-pointer">
                    <input
                        type="checkbox"
                        checked={currentData.iAmPrincipal}
                        onChange={(e) => handleChange('iAmPrincipal', e.target.checked)}
                        className="w-5 h-5 text-[#1a365d] rounded focus:ring-2 focus:ring-[#3b82f6]"
                    />
                    <span className="ml-3 text-sm font-medium text-[#1f2937]">
                        I am the Principal
                    </span>
                </label>
            </div>

            {/* Show info message if principal */}
            {currentData.iAmPrincipal && (
                <div className="bg-[#3b82f6]/10 border border-[#3b82f6] rounded-lg p-4" role="status">
                    <p className="text-[#1a365d] text-sm">
                        <strong>Note:</strong> As the principal, you will automatically become the system administrator for your school.
                    </p>
                </div>
            )}

            {/* Conditional Fields - Show if NOT principal */}
            {!currentData.iAmPrincipal && (
                <div className="border-l-4 border-[#3b82f6] pl-6 space-y-4">
                    {/* Your Full Name */}
                    <div>
                        <label htmlFor="yourFullName" className="block text-sm font-medium text-[#1f2937] mb-2">
                            Your Full Name <span className="text-[#dc2626]">*</span>
                        </label>
                        <input
                            id="yourFullName"
                            type="text"
                            value={currentData.yourFullName || ''}
                            onChange={(e) => handleChange('yourFullName', e.target.value)}
                            className={`w-full px-4 py-3 rounded-lg border ${errors.yourFullName ? 'border-[#dc2626]' : 'border-[#d1d5db]'} focus:outline-none focus:ring-2 focus:ring-[#3b82f6]`}
                            placeholder="Your full name"
                        />
                        {errors.yourFullName && <p className="text-[#dc2626] text-sm mt-1">{errors.yourFullName}</p>}
                    </div>

                    {/* Your Email */}
                    <div>
                        <label htmlFor="yourEmail" className="block text-sm font-medium text-[#1f2937] mb-2">
                            Your Email <span className="text-[#dc2626]">*</span>
                        </label>
                        <input
                            id="yourEmail"
                            type="email"
                            value={currentData.yourEmail || ''}
                            onChange={(e) => handleChange('yourEmail', e.target.value)}
                            className={`w-full px-4 py-3 rounded-lg border ${errors.yourEmail ? 'border-[#dc2626]' : 'border-[#d1d5db]'} focus:outline-none focus:ring-2 focus:ring-[#3b82f6]`}
                            placeholder="your@example.com"
                        />
                        {errors.yourEmail && <p className="text-[#dc2626] text-sm mt-1">{errors.yourEmail}</p>}
                    </div>

                    {/* Your Phone */}
                    <div>
                        <label htmlFor="yourPhone" className="block text-sm font-medium text-[#1f2937] mb-2">
                            Your Phone <span className="text-[#dc2626]">*</span>
                        </label>
                        <input
                            id="yourPhone"
                            type="tel"
                            value={currentData.yourPhone || ''}
                            onChange={(e) => handleChange('yourPhone', e.target.value)}
                            className={`w-full px-4 py-3 rounded-lg border ${errors.yourPhone ? 'border-[#dc2626]' : 'border-[#d1d5db]'} focus:outline-none focus:ring-2 focus:ring-[#3b82f6]`}
                            placeholder="+232 XX XXX XXXX"
                        />
                        {errors.yourPhone && <p className="text-[#dc2626] text-sm mt-1">{errors.yourPhone}</p>}
                    </div>

                    {/* Your Role */}
                    <div>
                        <label htmlFor="yourRole" className="block text-sm font-medium text-[#1f2937] mb-2">
                            Your Role <span className="text-[#dc2626]">*</span>
                        </label>
                        <input
                            id="yourRole"
                            type="text"
                            value={currentData.yourRole || ''}
                            onChange={(e) => handleChange('yourRole', e.target.value)}
                            className={`w-full px-4 py-3 rounded-lg border ${errors.yourRole ? 'border-[#dc2626]' : 'border-[#d1d5db]'} focus:outline-none focus:ring-2 focus:ring-[#3b82f6]`}
                            placeholder="e.g., Vice Principal, Administrator"
                        />
                        {errors.yourRole && <p className="text-[#dc2626] text-sm mt-1">{errors.yourRole}</p>}
                    </div>

                    {/* Who should manage system - Radio buttons */}
                    <div>
                        <label className="block text-sm font-medium text-[#1f2937] mb-2">
                            Who should manage system? <span className="text-[#dc2626]">*</span>
                        </label>
                        <div className="space-y-3">
                            <label className="flex items-center cursor-pointer">
                                <input
                                    type="radio"
                                    name="whoManagesSystem"
                                    value="me"
                                    checked={currentData.whoManagesSystem === 'me'}
                                    onChange={(e) => handleChange('whoManagesSystem', e.target.value)}
                                    className="w-4 h-4 text-[#1a365d]"
                                />
                                <span className="ml-3 text-sm text-[#1f2937]">Me</span>
                            </label>
                            <label className="flex items-center cursor-pointer">
                                <input
                                    type="radio"
                                    name="whoManagesSystem"
                                    value="principal"
                                    checked={currentData.whoManagesSystem === 'principal'}
                                    onChange={(e) => handleChange('whoManagesSystem', e.target.value)}
                                    className="w-4 h-4 text-[#1a365d]"
                                />
                                <span className="ml-3 text-sm text-[#1f2937]">The Principal</span>
                            </label>
                        </div>
                        {errors.whoManagesSystem && <p className="text-[#dc2626] text-sm mt-1">{errors.whoManagesSystem}</p>}
                    </div>
                </div>
            )}

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
