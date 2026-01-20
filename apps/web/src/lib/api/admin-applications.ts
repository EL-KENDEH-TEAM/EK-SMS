import { api } from './client';
import type {
    ApplicationListItem,
    ApplicationDetail,
    DashboardStats,
    ApplicationStatus,
    PaginatedApplications
} from '@/app/admin/types/admin';

/**
 * Admin API Client Functions
 * 
 * Centralized functions for all admin review operations.
 */

/**
 * Fetches list of all school applications with optional filtering, sorting, and pagination
 */
export async function getApplications(params?: {
    status?: ApplicationStatus;
    skip?: number;
    limit?: number;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
    country_code?: string;
    search?: string;
}) {
    const query = new URLSearchParams();
    if (params?.status) query.append('status', params.status);
    if (params?.skip !== undefined) query.append('skip', params.skip.toString());
    if (params?.limit !== undefined) query.append('limit', params.limit.toString());
    if (params?.sort_by) query.append('sort_by', params.sort_by);
    if (params?.sort_order) query.append('sort_order', params.sort_order);
    if (params?.country_code) query.append('country_code', params.country_code);
    if (params?.search) query.append('search', params.search);

    const queryString = query.toString();
    const endpoint = queryString ? `/admin/applications?${queryString}` : '/admin/applications';

    return api.get<PaginatedApplications>(endpoint);
}

/**
 * Fetches summary statistics for the admin dashboard
 */
export async function getDashboardStats() {
    return api.get<DashboardStats>('/admin/applications/stats');
}

/**
 * Fetches full details for a specific application
 */
export async function getApplicationDetail(id: string) {
    return api.get<ApplicationDetail>(`/admin/applications/${id}`);
}

/**
 * Transition an application to 'under_review' status
 */
export async function startReview(id: string) {
    return api.post<null>(`/admin/applications/${id}/review`);
}

/**
 * Requests more information from the applicant
 */
export async function requestMoreInfo(id: string, message: string) {
    return api.post<null>(`/admin/applications/${id}/request-info`, { message });
}

/**
 * Approves a school application
 */
export async function approveApplication(id: string) {
    return api.post<null>(`/admin/applications/${id}/approve`);
}

/**
 * Rejects a school application
 */
export async function rejectApplication(id: string, reason: string) {
    return api.post<null>(`/admin/applications/${id}/reject`, { reason });
}

/**
 * Adds an internal note to an application
 */
export async function addInternalNote(id: string, note: string) {
    return api.post<null>(`/admin/applications/${id}/notes`, { note });
}
