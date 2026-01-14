/**
 * About Page
 *
 * Information about EK-SMS platform.
 */

import Link from "next/link";

export default function AboutPage() {
    return (
        <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-3xl mx-auto">
                <div className="text-center mb-12">
                    <h1 className="text-4xl font-bold text-gray-900">About EK-SMS</h1>
                    <p className="mt-4 text-xl text-gray-600">
                        EL-KENDEH Smart School Management System
                    </p>
                </div>

                <div className="bg-white rounded-lg shadow-md p-8 space-y-6">
                    <section>
                        <h2 className="text-2xl font-semibold text-gray-900 mb-4">Our Mission</h2>
                        <p className="text-gray-600">
                            EK-SMS is a comprehensive school management platform designed specifically for
                            schools in West Africa. Our mission is to bring transparency, efficiency, and
                            modern technology to educational institutions across the region.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold text-gray-900 mb-4">Key Features</h2>
                        <ul className="list-disc list-inside text-gray-600 space-y-2">
                            <li>Student enrollment and records management</li>
                            <li>Fee collection and financial transparency</li>
                            <li>Academic performance tracking</li>
                            <li>Parent and guardian communication</li>
                            <li>Staff management and payroll</li>
                            <li>Reporting and analytics</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold text-gray-900 mb-4">Get Started</h2>
                        <p className="text-gray-600 mb-4">
                            Ready to transform your school&apos;s management? Register your school today
                            and join the growing community of modern educational institutions.
                        </p>
                        <Link
                            href="/register"
                            className="inline-block rounded-md bg-blue-600 px-6 py-3 text-white hover:bg-blue-700"
                        >
                            Register Your School
                        </Link>
                    </section>
                </div>

                <div className="mt-8 text-center">
                    <Link href="/" className="text-blue-600 hover:text-blue-800">
                        ← Back to Home
                    </Link>
                </div>
            </div>
        </div>
    );
}
