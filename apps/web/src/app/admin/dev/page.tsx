'use client';

import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

/**
 * Development Admin Access Page
 * 
 * This page enables development mode to bypass authentication.
 * Navigate to /admin/dev to enable dev mode and access the admin dashboard.
 */
export default function DevAdminPage() {
    const router = useRouter();

    useEffect(() => {
        // Enable development mode
        localStorage.setItem('DEV_ADMIN_MODE', 'true');

        console.log('✅ Development mode enabled for admin access');

        // Redirect to admin dashboard
        setTimeout(() => {
            router.push('/admin/dashboard');
        }, 1000);
    }, [router]);

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
            <div className="text-center max-w-md">
                <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-6"></div>
                <h2 className="text-3xl font-bold text-slate-800 mb-3">Development Mode</h2>
                <p className="text-slate-600 mb-4">Enabling admin access without authentication...</p>
                <div className="bg-white rounded-xl p-6 shadow-lg border border-blue-200">
                    <p className="text-sm text-slate-700 mb-2">
                        <strong>Development Mode Activated</strong>
                    </p>
                    <p className="text-xs text-slate-500">
                        You can now access the admin dashboard without logging in.
                    </p>
                </div>
                <p className="text-sm text-slate-500 mt-4">Redirecting to dashboard...</p>
            </div>
        </div>
    );
}
