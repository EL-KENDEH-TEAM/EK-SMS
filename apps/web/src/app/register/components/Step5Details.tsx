'use client';

/**
 * Step 5: Final Details Form
 * 
 * Online presence (optional) + Why EK-SMS (required)
 */

import { useState } from 'react';
import { useRegistration } from '../context/RegistrationContext';
import { type DetailsData, type FormErrors, type OnlinePresence } from '../types/registration';

export function Step5Details() {
    const { formData, updateFormData, nextStep, previousStep } = useRegistration();
    const [errors, setErrors] = useState<FormErrors>({});

    const currentData = formData.details;

    const handleCheckboxChange = (field: 'whyTransparency' | 'whyAutomation', value: boolean) => {
        updateFormData('details', { [field]: value });
        // Clear error when user selects a checkbox
        if (errors.whyEKSMS) {
            setErrors(prev => ({ ...prev, whyEKSMS: '' }));
        }
    };

    const handleTextChange = (field: keyof DetailsData, value: string) => {
        updateFormData('details', { [field]: value });
    };

    // Online Presence Management
    const addOnlinePresence = () => {
        const newEntry: OnlinePresence = { type: '', url: '' };
        updateFormData('details', {
            onlinePresence: [...currentData.onlinePresence, newEntry]
        });
    };

    const removeOnlinePresence = (index: number) => {
        const updated = currentData.onlinePresence.filter((_, i) => i !== index);
        updateFormData('details', { onlinePresence: updated });
    };

    const updateOnlinePresence = (index: number, field: keyof OnlinePresence, value: string) => {
        const updated = [...currentData.onlinePresence];
        updated[index] = { ...updated[index], [field]: value };
        updateFormData('details', { onlinePresence: updated });
    };

    const validate = (): boolean => {
        const newErrors: FormErrors = {};

        // At least one Why EK-SMS reason must be selected
        if (!currentData.whyTransparency && !currentData.whyAutomation) {
            newErrors.whyEKSMS = 'At least one reason must be selected';
        }

        // Validate online presence URLs if provided
        currentData.onlinePresence.forEach((entry, index) => {
            if (entry.url && !/^https?:\/\/.+/.test(entry.url)) {
                newErrors[`onlinePresence_${index}`] = 'Please enter a valid URL starting with http:// or https://';
            }
        });

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
                <h2 className="text-2xl font-bold text-[#1a365d]">Final Details</h2>
                <p className="text-[#4b5563] mt-2">Tell us about your online presence and why you want to use EK-SMS</p>
            </div>

            {/* Online Presence (Optional) */}
            <div>
                <h3 className="text-lg font-semibold text-[#1a365d] mb-4">
                    Online Presence <span className="text-[#6b7280] text-sm font-normal">(Optional)</span>
                </h3>

                <div className="space-y-4">
                    {currentData.onlinePresence.map((entry, index) => (
                        <div key={index} className="flex gap-3 items-start">
                            {/* Type Dropdown */}
                            <select
                                value={entry.type}
                                onChange={(e) => updateOnlinePresence(index, 'type', e.target.value)}
                                className="w-40 px-4 py-3 rounded-lg border border-[#d1d5db] focus:outline-none focus:ring-2 focus:ring-[#3b82f6]"
                            >
                                <option value="">Select type</option>
                                <option value="website">Website</option>
                                <option value="facebook">Facebook</option>
                                <option value="other">Other</option>
                            </select>

                            {/* URL Input */}
                            <div className="flex-1">
                                <input
                                    type="url"
                                    value={entry.url}
                                    onChange={(e) => updateOnlinePresence(index, 'url', e.target.value)}
                                    className={`w-full px-4 py-3 rounded-lg border ${errors[`onlinePresence_${index}`] ? 'border-[#dc2626]' : 'border-[#d1d5db]'} focus:outline-none focus:ring-2 focus:ring-[#3b82f6]`}
                                    placeholder="Enter URL"
                                />
                                {errors[`onlinePresence_${index}`] && (
                                    <p className="text-[#dc2626] text-sm mt-1">{errors[`onlinePresence_${index}`]}</p>
                                )}
                            </div>

                            {/* Remove Button */}
                            <button
                                onClick={() => removeOnlinePresence(index)}
                                aria-label={`Remove online presence entry ${index + 1}`}
                                className="px-4 py-3 border border-[#dc2626] text-[#dc2626] rounded-lg hover:bg-[#dc2626]/10"
                            >
                                Remove
                            </button>
                        </div>
                    ))}

                    {/* Add Another Link Button */}
                    <button
                        onClick={addOnlinePresence}
                        aria-label="Add another online presence link"
                        className="px-4 py-3 border border-[#3b82f6] text-[#3b82f6] rounded-lg hover:bg-[#3b82f6]/10"
                    >
                        + Add another link
                    </button>
                </div>
            </div>

            {/* Why EK-SMS (Required) */}
            <div className="border-l-4 border-[#1a365d] pl-6">
                <h3 className="text-lg font-semibold text-[#1a365d] mb-4">
                    Why EK-SMS? <span className="text-[#dc2626]">*</span>
                </h3>

                <div className="space-y-4">
                    {/* Transparency & Anti-corruption */}
                    <label className="flex items-start cursor-pointer">
                        <input
                            type="checkbox"
                            checked={currentData.whyTransparency}
                            onChange={(e) => handleCheckboxChange('whyTransparency', e.target.checked)}
                            className="w-5 h-5 mt-0.5 text-[#1a365d] rounded focus:ring-2 focus:ring-[#3b82f6]"
                        />
                        <span className="ml-3 text-sm text-[#1f2937]">Transparency & Anti-corruption</span>
                    </label>

                    {/* Automating School Processes */}
                    <label className="flex items-start cursor-pointer">
                        <input
                            type="checkbox"
                            checked={currentData.whyAutomation}
                            onChange={(e) => handleCheckboxChange('whyAutomation', e.target.checked)}
                            className="w-5 h-5 mt-0.5 text-[#1a365d] rounded focus:ring-2 focus:ring-[#3b82f6]"
                        />
                        <span className="ml-3 text-sm text-[#1f2937]">Automating School Processes</span>
                    </label>

                    {/* Error message */}
                    {errors.whyEKSMS && (
                        <p className="text-[#dc2626] text-sm" role="alert">{errors.whyEKSMS}</p>
                    )}

                    {/* Other Reasons (Optional Textarea) */}
                    <div className="mt-4">
                        <label htmlFor="whyOtherReason" className="block text-sm font-medium text-[#1f2937] mb-2">
                            Other reasons <span className="text-[#6b7280] text-xs">(Optional)</span>
                        </label>
                        <textarea
                            id="whyOtherReason"
                            value={currentData.whyOtherReason || ''}
                            onChange={(e) => handleTextChange('whyOtherReason', e.target.value)}
                            rows={4}
                            className="w-full px-4 py-3 rounded-lg border border-[#d1d5db] focus:outline-none focus:ring-2 focus:ring-[#3b82f6]"
                            placeholder="Tell us any other reasons..."
                        />
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
