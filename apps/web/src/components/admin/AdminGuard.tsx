'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts';

/**
 * AdminGuard Component
 * 
 * Protects admin routes. Redirects to /login if not authenticated
 * or if the user doesn't have the 'platform_admin' role.
 */
export function AdminGuard({ children }: { children: React.ReactNode }) {
    const { user, isAuthenticated, isLoading } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (!isLoading) {
            if (!isAuthenticated) {
                router.push('/login');
            } else if (user?.role !== 'platform_admin') {
                router.push('/'); // Redirect unauthorized users to home
            }
        }
    }, [user, isAuthenticated, isLoading, router]);

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#1a365d]"></div>
            </div>
        );
    }

    if (!isAuthenticated || user?.role !== 'platform_admin') {
        return null; // Don't render anything while redirecting
    }

    return <>{children}</>;
}
