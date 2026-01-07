/**
 * Home Page
 *
 * Landing page / entry point.
 */

import Link from "next/link";

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900">EK-SMS</h1>
        <p className="mt-4 text-lg text-gray-600">EL-KENDEH Smart School Management System</p>
        <div className="mt-8 flex gap-4 justify-center">
          <Link
            href="/login"
            className="rounded-md bg-blue-600 px-6 py-3 text-white hover:bg-blue-700"
          >
            Login
          </Link>
          <Link
            href="/about"
            className="rounded-md border border-gray-300 px-6 py-3 text-gray-700 hover:bg-gray-100"
          >
            Learn More
          </Link>
        </div>
      </div>
    </div>
  );
}
