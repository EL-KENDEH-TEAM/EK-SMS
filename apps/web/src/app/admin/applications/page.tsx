'use client';

// Task 5: Advanced Applications List - Updated per wireframe
// Task 6: Data Table & Pagination - Page numbers added

import React, { useEffect, useState, useCallback } from 'react';
import { useRouter, useSearchParams, usePathname } from 'next/navigation';
import Link from 'next/link';
import { getApplications } from '@/lib/api/admin-applications';
import type { ApplicationListItem, ApplicationStatus } from '@/app/admin/types/admin';

// Helper function for relative time
function getRelativeTime(dateString: string): string {
    const now = new Date();
    const date = new Date(dateString);
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return `${diffMins} minutes ago`;
    if (diffHours < 24) return `${diffHours} hours ago`;
    if (diffDays === 1) return '1 day ago';
    return `${diffDays} days ago`;
}

// Helper to get action button text based on status
function getActionButtonText(status: string): string {
    switch (status) {
        case 'pending_review':
            return 'Review';
        case 'under_review':
            return 'Continue';
        case 'approved':
        case 'rejected':
            return 'Details';
        default:
            return 'View';
    }
}

// Helper to get action button style based on status
function getActionButtonStyle(status: string): string {
    if (status === 'pending_review' || status === 'under_review') {
        return 'bg-[#1a365d] text-white hover:bg-[#1e4976]';
    }
    return 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50';
}

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
    const sort = searchParams.get('sort') || 'date_desc';
    const page = parseInt(searchParams.get('page') || '1');
    const limit = 10;
    const skip = (page - 1) * limit;

    // Parse sort parameter into field and order
    const getSortParams = (sortValue: string) => {
        if (sortValue === 'name_asc') return { sort_by: 'school_name', sort_order: 'asc' as const };
        if (sortValue === 'name_desc') return { sort_by: 'school_name', sort_order: 'desc' as const };
        if (sortValue === 'date_asc') return { sort_by: 'submitted_at', sort_order: 'asc' as const };
        return { sort_by: 'submitted_at', sort_order: 'desc' as const }; // date_desc default
    };

    // Calculate total pages for pagination
    const totalPages = Math.ceil(totalCount / limit);

    // Generate page numbers to display (show 5 at a time)
    const getPageNumbers = (): number[] => {
        const pages: number[] = [];
        let start = Math.max(1, page - 2);
        const end = Math.min(totalPages, start + 4);

        // Adjust start if we're near the end
        if (end - start < 4) {
            start = Math.max(1, end - 4);
        }

        for (let i = start; i <= end; i++) {
            pages.push(i);
        }
        return pages;
    };

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
                const sortParams = getSortParams(sort);
                const response = await getApplications({
                    search,
                    status: status as ApplicationStatus || undefined,
                    country_code: country_code || undefined,
                    sort_order: sortParams.sort_order,
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
        <div className="p-4 sm:p-6 lg:p-10 bg-slate-50 min-h-screen font-sans text-slate-900">
            <div className="mb-6 lg:mb-8">
                <h1 className="text-2xl sm:text-3xl font-bold text-slate-800 mb-2">All Applications</h1>
                <p className="text-slate-500 text-sm">Manage and review school registration applications</p>
            </div>

            {/* Filter Bar - Mobile-first responsive */}
            <div className="bg-white p-4 lg:p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col gap-4 mb-6 lg:mb-8">
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
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <select
                        value={status}
                        onChange={(e) => updateFilters({ status: e.target.value })}
                        className="px-4 py-3 bg-white border border-slate-200 rounded-xl text-sm font-bold text-slate-700 outline-none hover:border-slate-300 transition-all cursor-pointer w-full"
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
                        className="px-4 py-3 bg-white border border-slate-200 rounded-xl text-sm font-bold text-slate-700 outline-none hover:border-slate-300 transition-all cursor-pointer w-full"
                    >
                        <option value="">All Countries</option>
                        <option value="LR">Liberia</option>
                        <option value="SL">Sierra Leone</option>
                        <option value="GH">Ghana</option>
                        <option value="NG">Nigeria</option>
                        <option value="CI">Cote d&apos;Ivoire</option>
                        <option value="SN">Senegal</option>
                        <option value="GM">Gambia</option>
                        <option value="GN">Guinea</option>
                    </select>

                    <select
                        value={sort}
                        onChange={(e) => updateFilters({ sort: e.target.value })}
                        className="px-4 py-3 bg-white border border-slate-200 rounded-xl text-sm font-bold text-slate-700 outline-none hover:border-slate-300 transition-all cursor-pointer w-full"
                    >
                        <option value="date_desc">Newest First</option>
                        <option value="date_asc">Oldest First</option>
                        <option value="name_asc">Name (A-Z)</option>
                        <option value="name_desc">Name (Z-A)</option>
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
                                <th className="px-6 py-4 cursor-pointer hover:text-slate-600" onClick={() => updateFilters({ sort: sort === 'name_asc' ? 'name_desc' : 'name_asc' })}>
                                    School Name {sort.startsWith('name') ? (sort === 'name_asc' ? '↑' : '↓') : ''}
                                </th>
                                <th className="px-6 py-4">Location</th>
                                <th className="px-6 py-4">Type</th>
                                <th className="px-6 py-4">Students</th>
                                <th className="px-6 py-4 cursor-pointer hover:text-slate-600" onClick={() => updateFilters({ sort: sort === 'date_asc' ? 'date_desc' : 'date_asc' })}>
                                    Submitted {sort.startsWith('date') ? (sort === 'date_asc' ? '↑' : '↓') : ''}
                                </th>
                                <th className="px-6 py-4">Status</th>
                                <th className="px-6 py-4">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {isLoading ? (
                                [1, 2, 3].map(i => (
                                    <tr key={i} className="animate-pulse">
                                        <td colSpan={7} className="px-6 py-5"><div className="h-4 bg-slate-100 rounded w-full"></div></td>
                                    </tr>
                                ))
                            ) : apps.length === 0 ? (
                                <tr><td colSpan={7} className="px-6 py-12 text-center text-slate-400 font-bold uppercase text-[10px] tracking-widest">No applications found matching filters</td></tr>
                            ) : apps.map((app) => (
                                <tr key={app.id} className="hover:bg-slate-50 transition-colors group cursor-pointer" onClick={() => router.push(`/admin/applications/${app.id}`)}>
                                    <td className="px-6 py-5">
                                        <span className="text-sm font-bold text-slate-900 group-hover:text-blue-600 transition-colors">
                                            {app.school_name}
                                        </span>
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
                                        <div className="text-[10px] text-slate-400">{getRelativeTime(app.submitted_at)}</div>
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
                                    <td className="px-6 py-5" onClick={(e) => e.stopPropagation()}>
                                        <Link
                                            href={`/admin/applications/${app.id}`}
                                            className={`inline-flex items-center px-4 py-2 rounded-lg text-sm font-bold transition-all ${getActionButtonStyle(app.status)}`}
                                        >
                                            {getActionButtonText(app.status)}
                                        </Link>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {/* Pagination */}
                <div className="p-6 border-t border-slate-100 flex flex-col sm:flex-row justify-between items-center gap-4 bg-slate-50/50">
                    <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                        Showing {totalCount === 0 ? 0 : (page - 1) * limit + 1} to {Math.min(page * limit, totalCount)} of {totalCount} entries
                    </p>
                    <div className="flex gap-2">
                        <button
                            disabled={page === 1 || isLoading}
                            onClick={() => updateFilters({ page: (page - 1).toString() })}
                            className="px-4 py-2 border border-slate-200 rounded-lg text-sm font-medium text-slate-600 hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                        >
                            ← Previous
                        </button>
                        {/* Page number buttons */}
                        {getPageNumbers().map((pageNum) => (
                            <button
                                key={pageNum}
                                disabled={isLoading}
                                onClick={() => updateFilters({ page: pageNum.toString() })}
                                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all
                                    ${pageNum === page
                                        ? 'bg-[#1a365d] text-white border border-[#1a365d]'
                                        : 'border border-slate-200 text-slate-600 hover:bg-white'
                                    }`}
                            >
                                {pageNum}
                            </button>
                        ))}
                        <button
                            disabled={page >= totalPages || isLoading}
                            onClick={() => updateFilters({ page: (page + 1).toString() })}
                            className="px-4 py-2 border border-slate-200 rounded-lg text-sm font-medium text-slate-600 hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                        >
                            Next →
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
