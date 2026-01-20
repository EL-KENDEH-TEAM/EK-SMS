'use client';

import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { useRouter, useSearchParams, usePathname } from 'next/navigation';
import Link from 'next/link';
import { getApplications } from '@/lib/api/admin-applications';
import type { ApplicationListItem, ApplicationStatus } from '@/app/admin/types/admin';

export default function ApplicationsListPage() {
    const router = useRouter();
    const pathname = usePathname();
    const searchParams = useSearchParams();

    // -- State --
    const [apps, setApps] = useState<ApplicationListItem[]>([]);
    const [totalCount, setTotalCount] = useState(0);
    const [isLoading, setIsLoading] = useState(true);

    // -- URL Filter Sync --
    const search = searchParams.get('search') || '';
    const status = searchParams.get('status') || '';
    const country_code = searchParams.get('country') || '';
    const sort = searchParams.get('sort') || 'desc';
    const page = parseInt(searchParams.get('page') || '1');
    const limit = 10;
    const skip = (page - 1) * limit;

    const updateFilters = useCallback((updates: Record<string, string | null>) => {
        const params = new URLSearchParams(searchParams.toString());
        Object.entries(updates).forEach(([key, value]) => {
            if (value === null || value === '') params.delete(key);
            else params.set(key, value);
        });
        if (!updates.page) params.set('page', '1'); // Reset to page 1 on filter change
        router.push(`${pathname}?${params.toString()}`);
    }, [pathname, router, searchParams]);

    useEffect(() => {
        async function fetchApps() {
            setIsLoading(true);
            try {
                const response = await getApplications({
                    search,
                    status: status as ApplicationStatus || undefined,
                    country_code: country_code || undefined,
                    sort_order: sort as 'asc' | 'desc',
                    skip,
                    limit
                });

                if (response.data && 'applications' in response.data) {
                    setApps(response.data.applications);
                    setTotalCount(response.data.total);
                }
            } catch (error) {
                console.error('Fetch failed:', error);
            } finally {
                setIsLoading(false);
            }
        }
        fetchApps();
    }, [search, status, country_code, sort, skip, limit]);

    // -- Debounced Search --
    const [searchTerm, setSearchTerm] = useState(search);
    useEffect(() => {
        const timer = setTimeout(() => {
            if (searchTerm !== search) updateFilters({ search: searchTerm });
        }, 500);
        return () => clearTimeout(timer);
    }, [searchTerm, search, updateFilters]);

    return (
        <div className="p-10 bg-slate-50 min-h-screen font-sans text-slate-900">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-slate-800 mb-2">All Applications</h1>
                <p className="text-slate-500 text-sm">Manage and review school registration applications</p>
            </div>

            {/* Filter Bar - Aligned with Wireframe */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row gap-4 mb-8">
                <div className="relative flex-1">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-blue-500">🔍</span>
                    <input
                        type="text"
                        placeholder="Search by school name or email..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-12 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:ring-2 focus:ring-blue-500/20 outline-none transition-all placeholder:text-slate-400"
                    />
                </div>
                <div className="flex gap-3">
                    <select
                        value={status}
                        onChange={(e) => updateFilters({ status: e.target.value })}
                        className="px-4 py-3 bg-white border border-slate-200 rounded-xl text-sm font-bold text-slate-700 outline-none hover:border-slate-300 transition-all cursor-pointer min-w-[150px]"
                    >
                        <option value="">All Statuses</option>
                        <option value="pending_review">Pending Review</option>
                        <option value="under_review">Under Review</option>
                        <option value="more_info_requested">More Info Requested</option>
                        <option value="approved">Approved</option>
                        <option value="rejected">Rejected</option>
                    </select>

                    <select
                        value={country_code}
                        onChange={(e) => updateFilters({ country: e.target.value })}
                        className="px-4 py-3 bg-white border border-slate-200 rounded-xl text-sm font-bold text-slate-700 outline-none hover:border-slate-300 transition-all cursor-pointer min-w-[150px]"
                    >
                        <option value="">All Countries</option>
                        <option value="LR">Liberia</option>
                        <option value="SL">Sierra Leone</option>
                    </select>

                    <select
                        value={sort}
                        onChange={(e) => updateFilters({ sort: e.target.value })}
                        className="px-4 py-3 bg-white border border-slate-200 rounded-xl text-sm font-bold text-slate-700 outline-none hover:border-slate-300 transition-all cursor-pointer min-w-[150px]"
                    >
                        <option value="desc">Newest First</option>
                        <option value="asc">Oldest First</option>
                    </select>
                </div>
            </div>

            {/* List Table Section */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="p-6 border-b border-slate-100 flex justify-between items-center">
                    <h2 className="text-lg font-bold text-slate-800">Applications ({totalCount} total)</h2>
                    <button className="px-6 py-2 border border-slate-200 rounded-lg text-sm font-bold text-slate-700 hover:bg-slate-50 transition-all">Export</button>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="bg-slate-50 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                                <th className="px-6 py-4">School Name ↓</th>
                                <th className="px-6 py-4">Location</th>
                                <th className="px-6 py-4">Type</th>
                                <th className="px-6 py-4">Students</th>
                                <th className="px-6 py-4">Submitted</th>
                                <th className="px-6 py-4">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {isLoading ? (
                                [1, 2, 3].map(i => (
                                    <tr key={i} className="animate-pulse">
                                        <td colSpan={6} className="px-6 py-5"><div className="h-4 bg-slate-100 rounded w-full"></div></td>
                                    </tr>
                                ))
                            ) : apps.length === 0 ? (
                                <tr><td colSpan={6} className="px-6 py-12 text-center text-slate-400 font-bold uppercase text-[10px] tracking-widest">No applications found matching filters</td></tr>
                            ) : apps.map((app) => (
                                <tr key={app.id} className="hover:bg-slate-50 transition-colors group">
                                    <td className="px-6 py-5">
                                        <Link href={`/admin/applications/${app.id}`} className="text-sm font-bold text-slate-900 hover:text-blue-600 transition-colors">
                                            {app.school_name}
                                        </Link>
                                    </td>
                                    <td className="px-6 py-5">
                                        <div className="text-sm text-slate-500 font-medium">{app.city}, {app.country_code}</div>
                                    </td>
                                    <td className="px-6 py-5">
                                        <div className="text-sm text-slate-500 font-medium">{app.school_type.charAt(0).toUpperCase() + app.school_type.slice(1)}</div>
                                    </td>
                                    <td className="px-6 py-5">
                                        <div className="text-sm text-slate-500 font-medium">{app.student_population}</div>
                                    </td>
                                    <td className="px-6 py-5">
                                        <div className="text-sm text-slate-500 font-medium">{new Date(app.submitted_at).toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' })}</div>
                                        <div className="text-[10px] text-slate-400">2 hours ago</div> {/* Static for wireframe feel or calc if needed */}
                                    </td>
                                    <td className="px-6 py-5">
                                        <span className={`inline-flex items-center px-4 py-1 rounded-full text-[10px] font-bold uppercase tracking-tight
                                            ${app.status === 'approved' ? 'bg-green-100 text-green-700' :
                                                app.status === 'rejected' ? 'bg-red-100 text-red-700' :
                                                    app.status === 'under_review' ? 'bg-blue-100 text-blue-700' :
                                                        app.status === 'pending_review' ? 'bg-yellow-100 text-yellow-800' :
                                                            app.status === 'expired' ? 'bg-slate-100 text-slate-500' :
                                                                app.status.startsWith('awaiting_') ? 'bg-slate-100 text-slate-600' :
                                                                    'bg-orange-100 text-orange-700'}`}>
                                            {app.status.replace('_', ' ')}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {/* Pagination */}
                <div className="p-6 border-t border-slate-100 flex justify-between items-center bg-slate-50/50">
                    <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Showing {(page - 1) * 10 + 1} to {Math.min(page * 10, totalCount)} of {totalCount} entries</p>
                    <div className="flex gap-2">
                        <button
                            disabled={page === 1 || isLoading}
                            onClick={() => updateFilters({ page: (page - 1).toString() })}
                            className="px-4 py-2 border border-slate-200 rounded-lg text-[10px] font-black uppercase tracking-widest text-slate-600 hover:bg-white disabled:opacity-50 transition-all"
                        >
                            Previous
                        </button>
                        <button
                            disabled={page * 10 >= totalCount || isLoading}
                            onClick={() => updateFilters({ page: (page + 1).toString() })}
                            className="px-4 py-2 border border-slate-200 rounded-lg text-[10px] font-black uppercase tracking-widest text-slate-600 hover:bg-white disabled:opacity-50 transition-all"
                        >
                            Next
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
