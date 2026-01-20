'use client';

/**
 * Admin Applications List
 * 
 * Filterable table of all school registration applications.
 */

export function AdminApplicationsPage() {
    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold text-[#1a365d] mb-6">Applications</h1>
            <div className="bg-white rounded-lg shadow-sm overflow-hidden border border-gray-200">
                <div className="p-4 border-b border-gray-200 bg-gray-50">
                    <p className="text-gray-600">Loading applications...</p>
                </div>
            </div>
        </div>
    );
}

export default AdminApplicationsPage;
