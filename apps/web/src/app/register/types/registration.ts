/**
 * Registration Form Types
 * 
 * TypeScript interfaces for the 6-step school registration wizard
 */

// Step 1: Basic Information
export interface BasicInfoData {
  schoolName: string;
  yearEstablished: string;
  schoolType: 'public' | 'private' | 'mission' | 'vocational' | 'university' | '';
  studentPopulation: 'under100' | '100-300' | '300-500' | '500+' | '';
}

// Step 2: Location
export interface LocationData {
  country: string;
  cityTown: string;
  physicalAddress: string;
}

// Step 3: Contact Information
export interface ContactData {
  // School Contact Section (conditional/optional)
  schoolPhone?: string;
  schoolEmail?: string;

  // Principal Section (required)
  principalFullName: string;
  principalEmail: string;
  principalPhone: string;
}

// Step 4: About You (Applicant Information)
export interface AboutYouData {
  iAmPrincipal: boolean;
  // If NOT principal, these fields are required:
  yourFullName?: string;
  yourEmail?: string;
  yourPhone?: string;
  yourRole?: string;
  whoManagesSystem?: 'me' | 'principal' | '';
}

// Online presence entry
export interface OnlinePresence {
  type: 'website' | 'facebook' | 'other' | '';
  url: string;
}

// Step 5: Final Details
export interface DetailsData {
  // Online Presence (optional)
  onlinePresence: OnlinePresence[];

  // Why EK-SMS (required - at least one)
  whyTransparency: boolean;
  whyAutomation: boolean;
  whyOtherReason?: string;
}

// Complete registration data (Internal Frontend State)
export interface RegistrationFormData {
  basicInfo: BasicInfoData;
  location: LocationData;
  contact: ContactData;
  aboutYou: AboutYouData;
  details: DetailsData;
}

// Official API Request Payload (Nested Structure)
export interface RegistrationRequest {
  school: {
    name: string;
    year_established: number;
    school_type: string;
    student_population: string;
  };
  location: {
    country_code: string;
    city: string;
    address: string;
  };
  contact: {
    school_phone: string | null;
    school_email: string | null;
    principal_name: string;
    principal_email: string;
    principal_phone: string;
  };
  applicant: {
    is_principal: boolean;
    name: string | null;
    email: string | null;
    phone: string | null;
    role: string | null;
    admin_choice: 'applicant' | 'principal' | null;
  };
  details: {
    online_presence: Array<{ type: string; url: string }>;
    reasons: string[];
    other_reason: string | null;
  };
}

// API Success Response for Submission
export interface SubmissionResponse {
  id: string;
  status: string;
  applicant_email: string;
  message: string;
  verification_expires_at: string;
}

// API Response for Verification
export interface VerificationResponse {
  id: string;
  status: string;
  message: string;
  requires_principal_confirmation: boolean;
  principal_email_hint?: string;
}

// API Response for Principal Application Summary (confirm-principal success)
export interface PrincipalConfirmationResponse {
  id: string;
  status: string;
  message: string;
  school_name: string;
}

// API Response for Principal View (summary before confirmation)
export interface PrincipalApplicationResponse {
  id: string;
  school_name: string;
  applicant_name: string;
  admin_choice: 'applicant' | 'principal';
}

// API Response for Application Status progress step
export interface StatusStep {
  name: string;
  completed: boolean;
  completed_at: string | null;
}

// API Response for Application Status (Image 0)
export interface ApplicationStatusResponse {
  id: string;
  school_name: string;
  status: 'awaiting_applicant_verification' | 'awaiting_principal_confirmation' | 'pending_review' | 'under_review' | 'more_info_requested' | 'approved' | 'rejected' | 'expired';
  status_label: string;
  status_description: string;
  submitted_at: string;
  applicant_verified_at: string | null;
  principal_confirmed_at: string | null;
  steps: StatusStep[];
}

// Form step type
export type FormStep = 1 | 2 | 3 | 4 | 5 | 6;

// Initial form state
export const initialFormData: RegistrationFormData = {
  basicInfo: {
    schoolName: '',
    yearEstablished: '',
    schoolType: '',
    studentPopulation: '',
  },
  location: {
    country: '',
    cityTown: '',
    physicalAddress: '',
  },
  contact: {
    schoolPhone: '',
    schoolEmail: '',
    principalFullName: '',
    principalEmail: '',
    principalPhone: '',
  },
  aboutYou: {
    iAmPrincipal: true,
    yourFullName: '',
    yourEmail: '',
    yourPhone: '',
    yourRole: '',
    whoManagesSystem: '',
  },
  details: {
    onlinePresence: [],
    whyTransparency: false,
    whyAutomation: false,
    whyOtherReason: '',
  },
};

// Validation errors type
export interface FormErrors {
  [key: string]: string;
}

// Country type for API response
export interface Country {
  code: string;
  name: string;
}
