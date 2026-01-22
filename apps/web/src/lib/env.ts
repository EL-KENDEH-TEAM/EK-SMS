/**
 * Environment Configuration
 *
 * Type-safe access to environment variables.
 * Note: Next.js requires static access to process.env.NEXT_PUBLIC_* variables.
 */

export const env = {
  // API Configuration
  // Must use static access for Next.js to replace at build time
  apiUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8002/api/v1",
  appUrl: process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000",

  // Environment
  isDevelopment: process.env.NODE_ENV === "development",
  isProduction: process.env.NODE_ENV === "production",
} as const;
