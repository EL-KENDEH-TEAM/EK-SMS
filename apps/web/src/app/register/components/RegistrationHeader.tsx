'use client';

/**
 * Registration Header Component
 * 
 * Displays EK-SMS logo and "Already registered? Login" link
 */

import Link from 'next/link';

export function RegistrationHeader() {
    return (
        <header className="w-full bg-white shadow-sm">
            <div className="max-w-6xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
                <div className="flex justify-between items-center">
                    <div className="flex items-center">
                        <h1 className="text-2xl font-bold text-[#1a365d]">EK-SMS</h1>
                    </div>
                    <div>
                        <span className="text-[#4b5563] text-sm mr-2">Already registered?</span>
                        <Link
                            href="/login"
                            className="text-[#1a365d] hover:text-[#1e4976] font-medium text-sm underline"
                        >
                            Login
                        </Link>
                    </div>
                </div>
            </div>
        </header>
    );
}
