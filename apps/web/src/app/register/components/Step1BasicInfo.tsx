'use client';

/**
 * Step 1: Basic Information Form
 * 
 * Collects: School name, year established, school type, student population
 */

import { useState } from 'react';
import { useRegistration } from '../context/RegistrationContext';
import type { BasicInfoData, FormErrors } from '../types/registration';

export function Step1BasicInfo() {
    const { formData, updateFormData, nextStep } = useRegistration();
    const [errors, setErrors] = useState<FormErrors>({});

    const currentData = formData.basicInfo;

    const handleChange = (field: keyof BasicInfoData, value: string) => {
        updateFormData('basicInfo', { [field]: value });
        // Clear error when user types
        if (errors[field]) {
            setErrors(prev => ({ ...prev, [field]: '' }));
        }
    };

    const validate = (): boolean => {
        const newErrors: FormErrors = {};

        if (!currentData.schoolName.trim()) {
            newErrors.schoolName = 'School name is required';
        } else if (currentData.schoolName.length > 200) {
            newErrors.schoolName = 'School name must not exceed 200 characters';
        }

        if (!currentData.yearEstablished) {
            newErrors.yearEstablished = 'Year established is required';
        } else {
            const year = parseInt(currentData.yearEstablished);
            const currentYear = new Date().getFullYear();
            if (year < 1800 || year > currentYear) {
                newErrors.yearEstablished = `Year must be between 1800 and ${currentYear}`;
            }
        }

        if (!currentData.schoolType) {
            newErrors.schoolType = 'School type is required';
        }

        if (!currentData.studentPopulation) {
            newErrors.studentPopulation = 'Student population is required';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleNext = () => {
        if (validate()) {
            nextStep();
        }
    };

    const isFormValid = currentData.schoolName.trim() &&
        currentData.yearEstablished &&
        currentData.schoolType &&
        currentData.studentPopulation;

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold text-[#1a365d]">Basic Information</h2>
                <p className="text-[#4b5563] mt-2">Tell us about your school</p>
            </div>

            {/* School Name */}
            <div>
                <label htmlFor="schoolName" className="block text-sm font-medium text-[#1f2937] mb-2">
                    School Name <span className="text-[#dc2626]">*</span>
                </label>
                <input
                    id="schoolName"
                    type="text"
                    value={currentData.schoolName}
                    onChange={(e) => handleChange('schoolName', e.target.value)}
                    maxLength={200}
                    className={`
            w-full px-4 py-3 rounded-lg border
            ${errors.schoolName ? 'border-[#dc2626]' : 'border-[#d1d5db]'}
            focus:outline-none focus:ring-2 focus:ring-[#3b82f6] focus:border-transparent
          `}
                    placeholder="Enter school name"
                />
                {errors.schoolName && (
                    <p className="text-[#dc2626] text-sm mt-1">{errors.schoolName}</p>
                )}
            </div>

            {/* Year Established */}
            <div>
                <label htmlFor="yearEstablished" className="block text-sm font-medium text-[#1f2937] mb-2">
                    Year Established <span className="text-[#dc2626]">*</span>
                </label>
                <input
                    id="yearEstablished"
                    type="number"
                    value={currentData.yearEstablished}
                    onChange={(e) => handleChange('yearEstablished', e.target.value)}
                    className={`
            w-full px-4 py-3 rounded-lg border
            ${errors.yearEstablished ? 'border-[#dc2626]' : 'border-[#d1d5db]'}
            focus:outline-none focus:ring-2 focus:ring-[#3b82f6] focus:border-transparent
          `}
                    placeholder="e.g., 2010"
                    min="1800"
                    max={new Date().getFullYear()}
                />
                {errors.yearEstablished && (
                    <p className="text-[#dc2626] text-sm mt-1">{errors.yearEstablished}</p>
                )}
            </div>

            {/* School Type */}
            <div>
                <label htmlFor="schoolType" className="block text-sm font-medium text-[#1f2937] mb-2">
                    School Type <span className="text-[#dc2626]">*</span>
                </label>
                <select
                    id="schoolType"
                    value={currentData.schoolType}
                    onChange={(e) => handleChange('schoolType', e.target.value)}
                    className={`
            w-full px-4 py-3 rounded-lg border
            ${errors.schoolType ? 'border-[#dc2626]' : 'border-[#d1d5db]'}
            focus:outline-none focus:ring-2 focus:ring-[#3b82f6] focus:border-transparent
          `}
                >
                    <option value="">Select school type</option>
                    <option value="public">Public</option>
                    <option value="private">Private</option>
                    <option value="mission">Mission</option>
                    <option value="vocational">Vocational</option>
                    <option value="university">University</option>
                </select>
                {errors.schoolType && (
                    <p className="text-[#dc2626] text-sm mt-1">{errors.schoolType}</p>
                )}
            </div>

            {/* Student Population */}
            <div>
                <label htmlFor="studentPopulation" className="block text-sm font-medium text-[#1f2937] mb-2">
                    Student Population <span className="text-[#dc2626]">*</span>
                </label>
                <select
                    id="studentPopulation"
                    value={currentData.studentPopulation}
                    onChange={(e) => handleChange('studentPopulation', e.target.value)}
                    className={`
            w-full px-4 py-3 rounded-lg border
            ${errors.studentPopulation ? 'border-[#dc2626]' : 'border-[#d1d5db]'}
            focus:outline-none focus:ring-2 focus:ring-[#3b82f6] focus:border-transparent
          `}
                >
                    <option value="">Select student population</option>
                    <option value="under100">Under 100</option>
                    <option value="100-300">100-300</option>
                    <option value="300-500">300-500</option>
                    <option value="500+">500+</option>
                </select>
                {errors.studentPopulation && (
                    <p className="text-[#dc2626] text-sm mt-1">{errors.studentPopulation}</p>
                )}
            </div>

            {/* Navigation Button */}
            <div className="flex justify-end pt-4">
                <button
                    onClick={handleNext}
                    disabled={!isFormValid}
                    className={`
            px-6 py-3 font-medium rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1a365d] focus:ring-offset-2
            ${isFormValid
                            ? 'bg-[#1a365d] text-white hover:bg-[#1e4976]'
                            : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                        }
          `}
                >
                    Continue
                </button>
            </div>
        </div>
    );
}
