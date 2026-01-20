/**
 * Admin Dashboard Type Definitions
 * 
 * Aligned with the Admin Review API Contract
 */

export type ApplicationStatus = 'pending' | 'under_review' | 'more_info_requested' | 'approved' | 'rejected';

export interface DashboardStats {
    pending_review: number;
    under_review: number;
    more_info_requested: number;
    approved_this_week: number;
    total_this_month: number;
    avg_review_time: string; // e.g., "2.4 days"
}

export interface ApplicationListItem {
    id: string;
    school_name: string;
    school_type: string;
    location: string;
    applicant_name: string;
    status: ApplicationStatus;
    submitted_at: string;
    assigned_to?: string;
}

export interface InternalNote {
    id: string;
    author: string;
    content: string;
    created_at: string;
    is_system?: boolean;
}

export interface ApplicationDetail extends ApplicationListItem {
    year_established: number;
    student_population: string;
    contact_email: string;
    contact_phone: string;
    mission_statement: string;
    website?: string;
    notes: InternalNote[];
}

export interface AdminUser {
    id: string;
    name: string;
    email: string;
    role: 'platform_admin';
    avatar_url?: string;
}
