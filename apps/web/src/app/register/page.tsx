'use client';

/**
 * School Registration Page
 *
 * 6-step wizard for new schools to apply/register
 */

import { useRegistration } from './context/RegistrationContext';
import { ProgressStepper } from './components/ProgressStepper';
import { Step1BasicInfo } from './components/Step1BasicInfo';
import { Step2Location } from './components/Step2Location';
import { Step3Contact } from './components/Step3Contact';
import { Step4AboutYou } from './components/Step4AboutYou';
import { Step5Details } from './components/Step5Details';
import { Step6Review } from './components/Step6Review';

export function RegisterPage() {
  const { currentStep } = useRegistration();

  // Render current step component
  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return <Step1BasicInfo />;
      case 2:
        return <Step2Location />;
      case 3:
        return <Step3Contact />;
      case 4:
        return <Step4AboutYou />;
      case 5:
        return <Step5Details />;
      case 6:
        return <Step6Review />;
      default:
        return <Step1BasicInfo />;
    }
  };

  return (
    <div className="w-full">
      {/* Progress Stepper */}
      <ProgressStepper />

      {/* Form Container */}
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 pb-12">
        <div className="bg-white rounded-xl shadow-md p-8">
          {renderStep()}
        </div>
      </div>
    </div>
  );
}

export default RegisterPage;
