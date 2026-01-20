/**
 * Shared enumerations used across the application
 */

export enum UserRole {
  PLATFORM_ADMIN = "platform_admin",
  SUPER_ADMIN = "super_admin",
  SCHOOL_ADMIN = "school_admin",
  TEACHER = "teacher",
  STUDENT = "student",
  PARENT = "parent",
  EXAM_OFFICER = "exam_officer",
  FINANCE_OFFICER = "finance_officer",
}

export enum GradeStatus {
  DRAFT = "draft",
  SUBMITTED = "submitted",
  LOCKED = "locked",
}

export enum GradeEventType {
  DRAFT = "draft",
  SUBMIT = "submit",
  LOCK = "lock",
  MODIFY_REQUEST = "modify_request",
  MODIFY_APPROVED = "modify_approved",
  MODIFY_REJECTED = "modify_rejected",
}

export enum StudentStatus {
  ACTIVE = "active",
  GRADUATED = "graduated",
  TRANSFERRED = "transferred",
  WITHDRAWN = "withdrawn",
}

export enum NotificationType {
  GRADE_POSTED = "grade_posted",
  GRADE_LOCKED = "grade_locked",
  MODIFICATION_ATTEMPT = "modification_attempt",
  ATTENDANCE_ALERT = "attendance_alert",
  FEE_REMINDER = "fee_reminder",
  SYSTEM_ALERT = "system_alert",
}
