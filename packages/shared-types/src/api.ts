/**
 * API request/response types
 */

import type { User, Student, CurrentGrade } from "./models";
import type { UserRole } from "./enums";

// Generic API response wrapper
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

export interface ApiErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, string[]>;
  };
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// Auth types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  user: User;
  accessToken: string;
  refreshToken: string;
  requiresTwoFactor: boolean;
}

export interface TwoFactorVerifyRequest {
  code: string;
  tempToken: string;
}

// User types
export interface CreateUserRequest {
  email: string;
  password: string;
  role: UserRole;
  phone?: string;
}

export interface UpdateUserRequest {
  email?: string;
  phone?: string;
  isActive?: boolean;
}

// Grade types
export interface SubmitGradeRequest {
  studentId: string;
  classSubjectId: string;
  termId: string;
  score: number;
  remarks?: string;
}

export interface GradeModificationRequest {
  gradeId: string;
  newScore: number;
  reason: string;
  supportingEvidence?: string;
}

// Dashboard types
export interface DashboardStats {
  totalStudents: number;
  totalTeachers: number;
  totalClasses: number;
  attendanceRate: number;
  gradesSubmitted: number;
  gradesPending: number;
}
