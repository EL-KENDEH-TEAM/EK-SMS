/**
 * Admin Dashboard Type Definitions
 * 
 * Aligned with the Admin Review API Contract
 */

export type ApplicationStatus =
    | 'awaiting_applicant_verification'
    | 'awaiting_principal_confirmation'
    | 'pending_review'
    | 'under_review'
    | 'more_info_requested'
    | 'approved'
    | 'rejected'
    | 'expired';

export interface DashboardStats {
    pending_review: number;
    under_review: number;
    more_info_requested: number;
    approved_this_week: number;
    total_this_month: number;
    avg_review_time_days: number;
}

export type SchoolType = 'public' | 'private' | 'mission' | 'university' | 'vocational';
export type StudentPopulation = 'under_100' | '100_to_300' | '300_to_500' | 'over_500';

export interface ApplicationListItem {
    id: string;
    school_name: string;
    school_type: SchoolType;
    city: string;
    country_code: string;
    student_population: StudentPopulation;
    applicant_name: string | null;
    status: ApplicationStatus;
    submitted_at: string;

    // Status timestamps from contract
    applicant_verified_at: string | null;
    principal_confirmed_at: string | null;
    reviewed_at: string | null;
    reviewed_by: string | null;
}

export interface InternalNote {
    note: string;
    created_by: string;
    created_at: string;
}

export interface TimelineEvent {
    id: string;
    event_type: 'submitted' | 'email_verified' | 'principal_confirmed' | 'moved_to_review' | 'review_started' | 'decision_made' | 'info_requested';
    label: string;
    timestamp: string;
    metadata?: Record<string, any>;
}

export interface OnlinePresence {
    type: string;
    url: string;
}

export interface ApplicationDetail extends Omit<ApplicationListItem, 'student_population' | 'applicant_verified_at' | 'principal_confirmed_at' | 'reviewed_at' | 'reviewed_by'> {
    year_established: number;
    student_population: StudentPopulation;

    // Contact Info
    school_email: string;
    school_phone: string;
    website?: string;

    // Detailed Contact
    principal_name: string;
    principal_email: string;
    principal_phone: string;

    // Applicant Info
    applicant_name: string | null;
    applicant_email: string | null;
    applicant_phone: string | null;
    applicant_role: string | null;
    applicant_is_principal: boolean;
    admin_choice: 'applicant' | 'principal';

    // Location Details
    address: string;

    // Verification & Review Dates
    applicant_verified_at: string | null;
    principal_confirmed_at: string | null;
    reviewed_at: string | null;
    reviewed_by: string | null;
    decision_reason: string | null;

    // Additional Details
    mission_statement: string;
    online_presence: OnlinePresence[];
    reasons: string[];
    other_reason?: string;

    // System Data
    timeline: TimelineEvent[];
    internal_notes: InternalNote[];
}

export interface PaginatedApplications {
    applications: ApplicationListItem[];
    total: number;
    skip: number;
    limit: number;
}

export interface AdminUser {
    id: string;
    name: string;
    email: string;
    role: 'platform_admin';
    avatar_url?: string;
}
