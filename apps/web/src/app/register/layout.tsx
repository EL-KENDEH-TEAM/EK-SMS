'use client';

/**
 * Registration Layout
 * 
 * Wraps registration pages with header and context provider
 */

import { RegistrationProvider } from './context/RegistrationContext';
import { RegistrationHeader } from './components/RegistrationHeader';

export default function RegisterLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <RegistrationProvider>
            <div className="min-h-screen bg-[#f5f5f5]">
                <RegistrationHeader />
                {children}
            </div>
        </RegistrationProvider>
    );
}
