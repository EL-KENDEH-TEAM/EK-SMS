/**
 * Environment Configuration
 *
 * Type-safe access to environment variables.
 */

const getEnvVar = (key: string, fallback?: string): string => {
  const value = process.env[key] ?? fallback;
  if (!value) {
    throw new Error(`Missing environment variable: ${key}`);
  }
  return value;
};

export const env = {
  // API Configuration
  apiUrl: getEnvVar("NEXT_PUBLIC_API_URL", "http://localhost:8002/api/v1"),
  appUrl: getEnvVar("NEXT_PUBLIC_APP_URL", "http://localhost:3000"),

  // Environment
  isDevelopment: process.env.NODE_ENV === "development",
  isProduction: process.env.NODE_ENV === "production",
} as const;
