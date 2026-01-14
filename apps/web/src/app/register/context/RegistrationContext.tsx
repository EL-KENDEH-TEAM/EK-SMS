'use client';

/**
 * Registration Context
 * 
 * Manages form state across all 6 steps of the registration wizard
 */

import { createContext, useContext, useState, ReactNode } from 'react';
import type { RegistrationFormData, FormStep } from '../types/registration';
import { initialFormData } from '../types/registration';

interface RegistrationContextType {
    formData: RegistrationFormData;
    currentStep: FormStep;
    updateFormData: (step: keyof RegistrationFormData, data: any) => void;
    nextStep: () => void;
    previousStep: () => void;
    goToStep: (step: FormStep) => void;
    resetForm: () => void;
}

const RegistrationContext = createContext<RegistrationContextType | undefined>(undefined);

export function RegistrationProvider({ children }: { children: ReactNode }) {
    const [formData, setFormData] = useState<RegistrationFormData>(initialFormData);
    const [currentStep, setCurrentStep] = useState<FormStep>(1);

    const updateFormData = (step: keyof RegistrationFormData, data: any) => {
        setFormData(prev => ({
            ...prev,
            [step]: { ...prev[step], ...data }
        }));
    };

    const nextStep = () => {
        if (currentStep < 6) {
            setCurrentStep((currentStep + 1) as FormStep);
        }
    };

    const previousStep = () => {
        if (currentStep > 1) {
            setCurrentStep((currentStep - 1) as FormStep);
        }
    };

    const goToStep = (step: FormStep) => {
        setCurrentStep(step);
    };

    const resetForm = () => {
        setFormData(initialFormData);
        setCurrentStep(1);
    };

    return (
        <RegistrationContext.Provider
            value={{
                formData,
                currentStep,
                updateFormData,
                nextStep,
                previousStep,
                goToStep,
                resetForm,
            }}
        >
            {children}
        </RegistrationContext.Provider>
    );
}

export function useRegistration() {
    const context = useContext(RegistrationContext);
    if (context === undefined) {
        throw new Error('useRegistration must be used within a RegistrationProvider');
    }
    return context;
}
