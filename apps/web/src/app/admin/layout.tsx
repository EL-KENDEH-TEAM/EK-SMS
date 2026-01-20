'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

/**
 * Admin Shared Layout
 * 
 * Provides sidebar navigation and header for all /admin routes.
 */

export function AdminLayout({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();

    const navItems = [
        { name: 'Dashboard', href: '/admin/dashboard', icon: '📊' },
        { name: 'Applications', href: '/admin/applications', icon: '📋' },
    ];

    return (
        <div className="flex h-screen bg-[#f5f5f5]">
            {/* Sidebar */}
            <aside className="w-64 bg-[#1a365d] text-white flex flex-col shadow-lg">
                <div className="p-6 border-b border-[#2d4a77]">
                    <h1 className="text-2xl font-bold tracking-tight">EK-SMS</h1>
                    <p className="text-xs text-blue-300 mt-1 uppercase font-semibold">Admin Panel</p>
                </div>

                <nav className="flex-1 p-4 space-y-2 mt-4">
                    {navItems.map((item) => {
                        const isActive = pathname === item.href;
                        return (
                            <Link
                                key={item.href}
                                href={item.href}
                                className={`
                                    flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200
                                    ${isActive
                                        ? 'bg-white/10 text-white font-semibold'
                                        : 'text-blue-100 hover:bg-white/5 hover:text-white'}
                                `}
                            >
                                <span className="text-xl">{item.icon}</span>
                                <span>{item.name}</span>
                            </Link>
                        );
                    })}
                </nav>

                <div className="p-4 border-t border-[#2d4a77]">
                    <div className="flex items-center gap-3 px-4 py-2">
                        <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center font-bold">
                            A
                        </div>
                        <div className="overflow-hidden">
                            <p className="text-sm font-medium truncate">Platform Admin</p>
                            <Link href="/logout" className="text-xs text-blue-300 hover:text-white transition-colors">
                                Sign Out
                            </Link>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col overflow-hidden">
                {/* Header */}
                <header className="h-16 bg-white shadow-sm flex items-center justify-between px-8">
                    <div>
                        <h2 className="text-lg font-medium text-gray-700">
                            {navItems.find(item => pathname === item.href)?.name || 'Admin Panel'}
                        </h2>
                    </div>

                    <div className="flex items-center gap-4">
                        <button className="p-2 text-gray-400 hover:text-gray-600">
                            🔔
                        </button>
                        <div className="h-8 w-px bg-gray-200 mx-2"></div>
                        <span className="text-sm text-gray-600 font-medium">Alpha Version v0.1</span>
                    </div>
                </header>

                {/* Page Content */}
                <main className="flex-1 overflow-y-auto bg-[#f8fafc]">
                    {children}
                </main>
            </div>
        </div>
    );
}

export default AdminLayout;
