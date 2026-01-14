/**
 * Terms & Conditions Page
 *
 * Legal terms and conditions for using EK-SMS.
 */

import Link from "next/link";

export default function TermsPage() {
    return (
        <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-4xl mx-auto">
                <div className="text-center mb-12">
                    <h1 className="text-4xl font-bold text-gray-900">Terms & Conditions</h1>
                    <p className="mt-4 text-gray-600">
                        Last updated: January 2026
                    </p>
                </div>

                <div className="bg-white rounded-lg shadow-md p-8 prose prose-gray max-w-none">
                    <h2>1. Acceptance of Terms</h2>
                    <p>
                        By accessing and using the EK-SMS (EL-KENDEH Smart School Management System) platform,
                        you accept and agree to be bound by the terms and provision of this agreement.
                    </p>

                    <h2>2. Description of Service</h2>
                    <p>
                        EK-SMS provides a comprehensive school management platform that includes student
                        enrollment, fee management, academic tracking, and communication tools for educational
                        institutions in West Africa.
                    </p>

                    <h2>3. User Accounts</h2>
                    <p>
                        To access certain features of the platform, you must register for an account.
                        You are responsible for maintaining the confidentiality of your account credentials
                        and for all activities that occur under your account.
                    </p>

                    <h2>4. Data Privacy</h2>
                    <p>
                        We are committed to protecting the privacy of students, parents, and school staff.
                        All personal data is handled in accordance with applicable data protection laws.
                        We do not sell or share personal information with third parties except as required
                        to provide our services.
                    </p>

                    <h2>5. Acceptable Use</h2>
                    <p>
                        You agree to use the platform only for lawful purposes and in accordance with these
                        terms. You may not use the service to:
                    </p>
                    <ul>
                        <li>Violate any applicable laws or regulations</li>
                        <li>Infringe on the rights of others</li>
                        <li>Transmit harmful or malicious content</li>
                        <li>Attempt to gain unauthorized access to the system</li>
                    </ul>

                    <h2>6. Fees and Payment</h2>
                    <p>
                        Certain features of EK-SMS may require payment. All fees are clearly communicated
                        before any charges are applied. Payment terms and refund policies will be provided
                        at the time of purchase.
                    </p>

                    <h2>7. Intellectual Property</h2>
                    <p>
                        The EK-SMS platform, including its design, features, and content, is protected by
                        intellectual property laws. You may not copy, modify, or distribute any part of
                        the platform without our express written permission.
                    </p>

                    <h2>8. Limitation of Liability</h2>
                    <p>
                        EK-SMS is provided &quot;as is&quot; without warranties of any kind. We are not liable for
                        any indirect, incidental, or consequential damages arising from your use of the
                        platform.
                    </p>

                    <h2>9. Termination</h2>
                    <p>
                        We reserve the right to suspend or terminate your access to the platform at any
                        time for violations of these terms or for any other reason at our discretion.
                    </p>

                    <h2>10. Changes to Terms</h2>
                    <p>
                        We may update these terms from time to time. Continued use of the platform after
                        changes constitutes acceptance of the new terms.
                    </p>

                    <h2>11. Contact Information</h2>
                    <p>
                        If you have any questions about these Terms & Conditions, please contact us at
                        support@ek-sms.com.
                    </p>
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
