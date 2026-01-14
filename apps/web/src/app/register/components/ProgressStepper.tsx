'use client';

/**
 * Progress Stepper Component
 * 
 * Shows 6-step progress with current step highlighted and completed steps with checkmark
 */

import { useRegistration } from '../context/RegistrationContext';

const steps = [
    { number: 1, name: 'Basic Info' },
    { number: 2, name: 'Location' },
    { number: 3, name: 'Contact' },
    { number: 4, name: 'About You' },
    { number: 5, name: 'Details' },
    { number: 6, name: 'Review' },
];

export function ProgressStepper() {
    const { currentStep } = useRegistration();

    return (
        <div className="w-full py-8">
            <div className="flex items-center justify-between max-w-4xl mx-auto px-4">
                {steps.map((step, index) => (
                    <div key={step.number} className="flex items-center flex-1">
                        {/* Step Circle */}
                        <div className="flex flex-col items-center relative">
                            <div
                                className={`
                  w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm
                  ${currentStep > step.number
                                        ? 'bg-[#22c55e] text-white'
                                        : currentStep === step.number
                                            ? 'bg-[#1a365d] text-white'
                                            : 'bg-gray-200 text-gray-500'
                                    }
                `}
                            >
                                {currentStep > step.number ? (
                                    <svg
                                        className="w-5 h-5"
                                        fill="none"
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth="2"
                                        viewBox="0 0 24 24"
                                        stroke="currentColor"
                                    >
                                        <path d="M5 13l4 4L19 7"></path>
                                    </svg>
                                ) : (
                                    step.number
                                )}
                            </div>
                            <span
                                className={`
                  mt-2 text-xs sm:text-sm font-medium whitespace-nowrap
                  ${currentStep >= step.number ? 'text-[#1a365d]' : 'text-gray-400'
                                    }
                `}
                            >
                                {step.name}
                            </span>
                        </div>

                        {/* Connector Line */}
                        {index < steps.length - 1 && (
                            <div
                                className={`
                  flex-1 h-1 mx-2 sm:mx-4
                  ${currentStep > step.number ? 'bg-[#22c55e]' : 'bg-gray-200'
                                    }
                `}
                            ></div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}
