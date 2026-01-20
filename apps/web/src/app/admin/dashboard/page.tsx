'use client';

/**
 * Admin Dashboard Overview
 * 
 * Displays key metrics and navigation hub.
 */

export function AdminDashboardPage() {
    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold text-[#1a365d] mb-6">Admin Dashboard</h1>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {/* Stats cards will go here */}
                <div className="bg-white p-6 rounded-lg shadow-sm border-l-4 border-blue-500">
                    <p className="text-sm text-gray-500 uppercase font-semibold">Pending Review</p>
                    <h2 className="text-3xl font-bold mt-2">--</h2>
                </div>
            </div>
        </div>
    );
}

export default AdminDashboardPage;
