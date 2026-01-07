/**
 * Shared model interfaces
 */

import { UserRole, StudentStatus, GradeStatus, GradeEventType } from "./enums";

// Base interface for all models with common fields
export interface BaseModel {
  id: string;
  createdAt: string;
  updatedAt: string;
}

// User related types
export interface User extends BaseModel {
  email: string;
  phone?: string;
  role: UserRole;
  isActive: boolean;
  isTwoFactorEnabled: boolean;
}

export interface Student extends BaseModel {
  userId: string;
  studentNumber: string;
  firstName: string;
  lastName: string;
  dateOfBirth: string;
  gender: "male" | "female";
  status: StudentStatus;
  currentClassId?: string;
}

export interface Teacher extends BaseModel {
  userId: string;
  employeeNumber: string;
  firstName: string;
  lastName: string;
  specializations: string[];
}

// Academic types
export interface AcademicYear extends BaseModel {
  schoolId: string;
  name: string;
  startDate: string;
  endDate: string;
  isCurrent: boolean;
}

export interface Term extends BaseModel {
  academicYearId: string;
  name: string;
  startDate: string;
  endDate: string;
  isCurrent: boolean;
}

export interface Class extends BaseModel {
  schoolId: string;
  name: string;
  gradeLevel: number;
  academicYearId: string;
}

export interface Subject extends BaseModel {
  schoolId: string;
  name: string;
  code: string;
  category: "core" | "elective";
  creditHours: number;
}

// Grade types (event-sourced)
export interface GradeEvent extends BaseModel {
  studentId: string;
  classSubjectId: string;
  termId: string;
  eventType: GradeEventType;
  score: number;
  gradeLetter?: string;
  remarks?: string;
  recordedBy: string;
  recordedAt: string;
  modificationReason?: string;
  previousEventId?: string;
  hash: string;
}

export interface CurrentGrade {
  studentId: string;
  classSubjectId: string;
  termId: string;
  currentScore: number;
  currentGradeLetter?: string;
  status: GradeStatus;
  lastEventId: string;
}
