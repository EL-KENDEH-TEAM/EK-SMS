'use client';

// Task 4: Metric Dashboard UI Alignment Completed
// Task 13: Migrate UI Components Completed

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { getApplications, getDashboardStats } from '@/lib/api/admin-applications';
import type { ApplicationListItem, DashboardStats } from '@/app/admin/types/admin';

export default function AdminDashboard() {
    const [recentApps, setRecentApps] = useState<ApplicationListItem[]>([]);
    const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        async function fetchDashboardData() {
            try {
                // Get 5 most recent applications and dashboard stats
                const [appsRes, statsRes] = await Promise.all([
                    getApplications({ limit: 5, sort_order: 'desc' }),
                    getDashboardStats()
                ]);

                if (appsRes.data && 'applications' in appsRes.data) {
                    setRecentApps(appsRes.data.applications);
                }
                if (statsRes.data) {
                    setDashboardStats(statsRes.data);
                }
            } catch (error) {
                console.error('Failed to fetch dashboard data:', error);
            } finally {
                setIsLoading(false);
            }
        }
        fetchDashboardData();
    }, []);

    const stats = dashboardStats ? [
        { label: 'PENDING REVIEW', value: String(dashboardStats.pending_review ?? 0), change: '+3 from last week', color: 'text-blue-600', trend: 'up' },
        { label: 'UNDER REVIEW', value: String(dashboardStats.under_review ?? 0), change: '-2 from last week', color: 'text-slate-900', trend: 'down' },
        { label: 'MORE INFO REQUESTED', value: String(dashboardStats.more_info_requested ?? 0), change: '+1 from last week', color: 'text-slate-900', trend: 'up' },
        { label: 'THIS MONTH', value: String(dashboardStats.total_this_month ?? 0), change: 'Applications received', color: 'text-slate-900' },
        { label: 'APPROVED (THIS WEEK)', value: String(dashboardStats.approved_this_week ?? 0), change: '✓ On target', color: 'text-slate-900', trend: 'positive' },
        { label: 'AVG. REVIEW TIME', value: (dashboardStats.avg_review_time_days ?? 0).toFixed(1), change: 'days', color: 'text-slate-900' },
    ] : [];

    if (isLoading) {
        return (
            <div className="p-8 bg-slate-50 min-h-screen animate-pulse">
                <div className="h-8 w-48 bg-slate-200 rounded mb-8"></div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
                    {[1, 2, 3, 4].map(i => <div key={i} className="h-32 bg-white rounded-xl border border-slate-200"></div>)}
                </div>
            </div>
        );
    }

    return (
        <div className="p-10 bg-slate-50 min-h-screen font-sans text-slate-900">
            <div className="mb-10">
                <h1 className="text-3xl font-bold text-slate-800 mb-2">Dashboard</h1>
                <p className="text-slate-500 text-sm">Overview of school registration applications</p>
            </div>

            {/* Stats Grid - 4x1 then 2x1 as per wireframe */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
                {stats.slice(0, 4).map((stat) => (
                    <div key={stat.label} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm transition-shadow hover:shadow-md">
                        <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-4">{stat.label}</p>
                        <p className={`text-4xl font-bold mb-2 ${stat.color}`}>{stat.value}</p>
                        <p className={`text-xs font-medium ${stat.trend === 'up' ? 'text-green-600' : stat.trend === 'down' ? 'text-blue-500' : stat.trend === 'positive' ? 'text-green-600' : 'text-slate-400'}`}>
                            {stat.change}
                        </p>
                    </div>
                ))}
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
                {stats.slice(4).map((stat) => (
                    <div key={stat.label} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm transition-shadow hover:shadow-md">
                        <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-4">{stat.label}</p>
                        <p className="text-4xl font-bold mb-2 text-slate-900">{stat.value}</p>
                        <p className={`text-xs font-medium ${stat.change.includes('target') ? 'text-green-600' : 'text-slate-400'}`}>
                            {stat.change}
                        </p>
                    </div>
                ))}
            </div>

            {/* Recent Applications Section */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden mb-12">
                <div className="p-6 border-b border-slate-100 flex justify-between items-center">
                    <h2 className="text-lg font-bold text-slate-800">Recent Applications</h2>
                    <Link href="/admin/applications" className="text-blue-600 text-sm font-bold hover:underline">View All</Link>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="bg-slate-50 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                                <th className="px-6 py-4">School Name</th>
                                <th className="px-6 py-4">Location</th>
                                <th className="px-6 py-4">Status</th>
                                <th className="px-6 py-4 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {recentApps.map((app) => (
                                <tr key={app.id} className="hover:bg-slate-50 transition-colors">
                                    <td className="px-6 py-4">
                                        <div className="text-sm font-bold text-slate-900">{app.school_name}</div>
                                        <div className="text-[10px] text-slate-400 font-medium">Applied {new Date(app.submitted_at).toLocaleDateString()}</div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="text-sm text-slate-600 font-medium">{app.city}, {app.country_code}</div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-tight
                                            ${app.status === 'approved' ? 'bg-green-100 text-green-700' :
                                                app.status === 'rejected' ? 'bg-red-100 text-red-700' :
                                                    app.status === 'under_review' ? 'bg-blue-100 text-blue-700' :
                                                        app.status.startsWith('awaiting_') ? 'bg-slate-100 text-slate-600' :
                                                            'bg-yellow-100 text-yellow-700'}`}>
                                            {app.status.replace('_', ' ')}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <Link href={`/admin/applications/${app.id}`} className="inline-flex items-center justify-center h-8 w-8 rounded-lg border border-slate-200 text-slate-400 hover:text-blue-600 hover:border-blue-200 transition-all">
                                            <span className="text-xs">→</span>
                                        </Link>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
