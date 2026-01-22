'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts';

/**
 * AdminGuard Component
 *
 * Protects admin routes. Redirects to /login if not authenticated
 * or if the user doesn't have the 'platform_admin' role.
 *
 * Development Mode: Set DEV_ADMIN_MODE=true in localStorage to bypass auth
 */
export function AdminGuard({ children }: { children: React.ReactNode }) {
    const { user, isAuthenticated, isLoading } = useAuth();
    const router = useRouter();
    // Initialize devMode state with lazy initializer to avoid effect setState issue
    const [devMode] = useState(() => {
        if (typeof window !== 'undefined') {
            return localStorage.getItem('DEV_ADMIN_MODE') === 'true';
        }
        return false;
    });

    useEffect(() => {
        if (!isLoading && !devMode) {
            if (!isAuthenticated) {
                router.push('/login');
            } else if (user?.role !== 'platform_admin') {
                router.push('/'); // Redirect unauthorized users to home
            }
        }
    }, [user, isAuthenticated, isLoading, router, devMode]);

    if (isLoading && !devMode) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#1a365d]"></div>
            </div>
        );
    }

    // Allow access in dev mode
    if (devMode) {
        return <>{children}</>;
    }

    if (!isAuthenticated || user?.role !== 'platform_admin') {
        return null; // Don't render anything while redirecting
    }

    return <>{children}</>;
}
