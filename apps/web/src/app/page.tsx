/**
 * Home Page
 *
 * Landing page / entry point.
 */

import Link from "next/link";

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-[#f5f5f5]">
      <div className="text-center max-w-2xl px-4">
        <h1 className="text-4xl sm:text-5xl font-bold text-[#1a365d]">EK-SMS</h1>
        <p className="mt-4 text-lg text-[#4b5563]">EL-KENDEH Smart School Management System</p>
        <p className="mt-2 text-[#6b7280]">Transparent, tamper-proof grade management for schools across West Africa</p>
        <div className="mt-8 flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/register"
            className="rounded-lg bg-[#1a365d] px-8 py-3 text-white font-medium hover:bg-[#1e4976] transition-colors"
          >
            Register Your School
          </Link>
          <Link
            href="/login"
            className="rounded-lg border-2 border-[#1a365d] px-8 py-3 text-[#1a365d] font-medium hover:bg-[#1a365d] hover:text-white transition-colors"
          >
            Login
          </Link>
          <Link
            href="/about"
            className="rounded-lg border border-[#d1d5db] px-8 py-3 text-[#4b5563] font-medium hover:bg-[#e5e7eb] transition-colors"
          >
            Learn More
          </Link>
        </div>
      </div>
    </div>
  );
}
