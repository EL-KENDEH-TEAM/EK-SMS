'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

import { AdminGuard } from '@/components/admin/AdminGuard';

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
        <AdminGuard>
            <div className="flex h-screen bg-slate-50 font-sans">
                {/* Sidebar - Dark Navy from Wireframe */}
                <aside className="w-64 bg-[#0f172a] text-white flex flex-col shadow-xl z-20">
                    <div className="p-8 border-b border-slate-800/50">
                        <h1 className="text-xl font-black tracking-tight text-white flex items-center gap-2">
                            EK-SMS Admin
                        </h1>
                    </div>

                    <nav className="flex-1 p-4 space-y-1 mt-6">
                        {navItems.map((item) => {
                            const isActive = pathname.startsWith(item.href);
                            return (
                                <Link
                                    key={item.href}
                                    href={item.href}
                                    className={`
                                    flex items-center gap-3 px-6 py-4 rounded-xl transition-all duration-200 group
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

                    <div className="p-6">
                        <div className="bg-slate-800/30 p-4 rounded-xl border border-slate-800/50">
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
                    {/* Header - White with Shadow as per wireframe */}
                    <header className="h-20 bg-[#1e293b] text-white border-b border-slate-800 flex items-center justify-between px-10 shadow-sm z-10">
                        <div>
                            <h2 className="text-lg font-black tracking-tight uppercase">
                                {navItems.find(item => pathname.startsWith(item.href))?.name || 'Admin Panel'}
                            </h2>
                        </div>

                        <div className="flex items-center gap-6">
                            <div className="flex items-center gap-3 hover:bg-slate-800 p-2 px-4 rounded-full transition-colors cursor-pointer group">
                                <div className="w-9 h-9 rounded-full bg-blue-600 flex items-center justify-center font-black text-sm border-2 border-slate-700 shadow-inner">
                                    JD
                                </div>
                                <div className="text-right">
                                    <p className="text-xs font-black text-white">John Doe (Admin)</p>
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
