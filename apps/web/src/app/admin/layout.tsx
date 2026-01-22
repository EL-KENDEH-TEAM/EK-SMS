'use client';

// Task 14: Final Verification and Cleanup - Mobile-first responsive

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

import { AdminGuard } from '@/components/admin/AdminGuard';
import { useAuth } from '@/contexts';

/**
 * Admin Shared Layout
 *
 * Provides sidebar navigation and header for all /admin routes.
 * Mobile-first responsive with collapsible sidebar.
 */

export function AdminLayout({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();
    const { user } = useAuth();
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);

    // Generate initials from user's name
    const userInitials = user
        ? `${user.first_name?.[0] || ''}${user.last_name?.[0] || ''}`.toUpperCase()
        : '??';
    const userName = user
        ? `${user.first_name} ${user.last_name}`
        : 'Loading...';

    const navItems = [
        { name: 'Dashboard', href: '/admin/dashboard', icon: '📊' },
        { name: 'Applications', href: '/admin/applications', icon: '📋' },
    ];

    const closeSidebar = () => setIsSidebarOpen(false);

    return (
        <AdminGuard>
            <div className="flex h-screen bg-slate-50 font-sans">
                {/* Mobile Overlay */}
                {isSidebarOpen && (
                    <div
                        className="fixed inset-0 bg-black/50 z-30 lg:hidden"
                        onClick={closeSidebar}
                    />
                )}

                {/* Sidebar - Dark Navy from Wireframe */}
                <aside className={`
                    fixed lg:static inset-y-0 left-0 z-40
                    w-64 bg-[#0f172a] text-white flex flex-col shadow-xl
                    transform transition-transform duration-300 ease-in-out
                    ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
                `}>
                    <div className="p-6 lg:p-8 border-b border-slate-800/50 flex items-center justify-between">
                        <h1 className="text-xl font-black tracking-tight text-white flex items-center gap-2">
                            EK-SMS Admin
                        </h1>
                        {/* Close button for mobile */}
                        <button
                            onClick={closeSidebar}
                            className="lg:hidden text-slate-400 hover:text-white p-1"
                        >
                            <span className="text-2xl">×</span>
                        </button>
                    </div>

                    <nav className="flex-1 p-4 space-y-1 mt-4 lg:mt-6">
                        {navItems.map((item) => {
                            const isActive = pathname.startsWith(item.href);
                            return (
                                <Link
                                    key={item.href}
                                    href={item.href}
                                    onClick={closeSidebar}
                                    className={`
                                    flex items-center gap-3 px-4 lg:px-6 py-3 lg:py-4 rounded-xl transition-all duration-200 group
                                    ${isActive
                                            ? 'bg-slate-800 text-white font-bold'
                                            : 'text-slate-400 hover:bg-slate-800/50 hover:text-white'}
                                `}
                                >
                                    <span className={`text-lg filter grayscale group-hover:grayscale-0 transition-all ${isActive ? 'grayscale-0' : ''}`}>{item.icon}</span>
                                    <span className="text-sm tracking-wide">{item.name}</span>
                                </Link>
                            );
                        })}
                    </nav>

                    <div className="p-4 lg:p-6">
                        <div className="bg-slate-800/30 p-3 lg:p-4 rounded-xl border border-slate-800/50">
                            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1">System Health</p>
                            <div className="flex items-center gap-2">
                                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                                <span className="text-[10px] font-bold text-slate-300">Operational</span>
                            </div>
                        </div>
                    </div>
                </aside>

                {/* Main Content Area */}
                <div className="flex-1 flex flex-col overflow-hidden">
                    {/* Header - Dark with Shadow as per wireframe */}
                    <header className="h-16 lg:h-20 bg-[#1e293b] text-white border-b border-slate-800 flex items-center justify-between px-4 lg:px-10 shadow-sm z-10">
                        <div className="flex items-center gap-4">
                            {/* Mobile menu toggle */}
                            <button
                                onClick={() => setIsSidebarOpen(true)}
                                className="lg:hidden text-white p-2 hover:bg-slate-700 rounded-lg"
                            >
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                                </svg>
                            </button>
                            <h2 className="text-base lg:text-lg font-black tracking-tight uppercase">
                                {navItems.find(item => pathname.startsWith(item.href))?.name || 'Admin Panel'}
                            </h2>
                        </div>

                        <div className="flex items-center gap-2 lg:gap-6">
                            <div className="flex items-center gap-2 lg:gap-3 hover:bg-slate-800 p-2 lg:px-4 rounded-full transition-colors cursor-pointer group">
                                <div className="w-8 lg:w-9 h-8 lg:h-9 rounded-full bg-blue-600 flex items-center justify-center font-black text-xs lg:text-sm border-2 border-slate-700 shadow-inner">
                                    {userInitials}
                                </div>
                                <div className="text-right hidden sm:block">
                                    <p className="text-xs font-black text-white">{userName} (Admin)</p>
                                    <p className="text-[9px] font-bold text-slate-500 uppercase tracking-tighter group-hover:text-blue-400">View Profile</p>
                                </div>
                            </div>
                        </div>
                    </header>

                    {/* Page Content */}
                    <main className="flex-1 overflow-y-auto bg-slate-50">
                        {children}
                    </main>
                </div>
            </div>
        </AdminGuard>
    );
}

export default AdminLayout;
