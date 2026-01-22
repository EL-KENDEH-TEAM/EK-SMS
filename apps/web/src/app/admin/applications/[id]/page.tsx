'use client';

// Task 6: Application Detail Status Board Completed
// Task 7: Multi-Event Timeline Completed
// Task 8: Application Detail 5 Info Sections Completed
// Task 9: Internal Notes System Completed
// Task 10: High-Fidelity Action Toolbar Completed

import React, { useEffect, useState, useMemo } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
    getApplicationDetail,
    startReview,
    approveApplication,
    rejectApplication,
    requestMoreInfo,
    addInternalNote
} from '@/lib/api/admin-applications';
import type { ApplicationDetail, ApplicationStatus } from '@/app/admin/types/admin';

/**
 * Reusable Information Section Component (Wireframe Style)
 */
const InfoSection = ({ title, children }: { title: string; children: React.ReactNode }) => (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden mb-8">
        <div className="px-8 py-5 border-b border-slate-100">
            <h3 className="text-lg font-bold text-slate-800">{title}</h3>
        </div>
        <div className="p-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-x-12 gap-y-10">
                {children}
            </div>
        </div>
    </div>
);

/**
 * Reusable Information Field Component (Wireframe Style)
 */
const InfoField = ({ label, value, type = 'text', className = '' }: { label: string; value: string | number | React.ReactNode; type?: 'text' | 'email' | 'link'; className?: string }) => (
    <div className={`space-y-2 ${className}`}>
        <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest">{label}</label>
        <div className="text-sm font-bold text-slate-700">
            {type === 'email' ? (
                <a href={`mailto:${value}`} className="text-blue-600 hover:underline select-all">{value}</a>
            ) : type === 'link' ? (
                <a href={value as string} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                    {String(value).replace(/^https?:\/\//, '')}
                </a>
            ) : (
                <span className="break-words whitespace-pre-wrap">{value}</span>
            )}
        </div>
    </div>
);

/**
 * Enum Formatter Utilities
 */
const formatSchoolType = (type: string) => {
    const types: Record<string, string> = {
        public: 'Public',
        private: 'Private',
        mission: 'Mission',
        vocational: 'Vocational',
        university: 'University'
    };
    return types[type] || type.charAt(0).toUpperCase() + type.slice(1);
};

const formatPopulation = (pop: string) => {
    const pops: Record<string, string> = {
        under_100: 'Less than 100 students',
        '100_to_300': '100 - 300 students',
        '300_to_500': '300 - 500 students',
        over_500: 'More than 500 students'
    };
    return pops[pop] || pop;
};

/**
 * Application Detail View - Final Wireframe Alignment
 */
export function ApplicationDetailPage() {
    const { id } = useParams() as { id: string };
    const router = useRouter();

    const [app, setApp] = useState<ApplicationDetail | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isActionLoading, setIsActionLoading] = useState(false);

    // Internal Notes State
    const [noteContent, setNoteContent] = useState('');
    const [isNoteSaving, setIsNoteSaving] = useState(false);

    // Modal States
    const [showRejectionModal, setShowRejectionModal] = useState(false);
    const [showInfoModal, setShowInfoModal] = useState(false);
    const [showApproveModal, setShowApproveModal] = useState(false);
    const [rejectionReason, setRejectionReason] = useState('');
    const [infoMessage, setInfoMessage] = useState('');

    useEffect(() => {
        async function fetchDetail() {
            try {
                const response = await getApplicationDetail(id);
                if (response.data) {
                    setApp(response.data);
                    if (response.data.status === 'pending_review') {
                        await startReview(id);
                        const updated = await getApplicationDetail(id);
                        if (updated.data) setApp(updated.data);
                    }
                }
            } catch (error) {
                console.error('Fetch failed:', error);
            } finally {
                setIsLoading(false);
            }
        }
        fetchDetail();
    }, [id]);

    const handleSaveNote = async () => {
        if (!noteContent.trim() || isNoteSaving) return;
        setIsNoteSaving(true);
        try {
            await addInternalNote(id, noteContent);
            setNoteContent('');
            const response = await getApplicationDetail(id);
            if (response.data) setApp(response.data);
        } catch (error) {
            console.error('Note failed:', error);
        } finally {
            setIsNoteSaving(false);
        }
    };

    const handleAction = async (action: () => Promise<unknown>, successMsg: string) => {
        setIsActionLoading(true);
        try {
            await action();
            // In a real app we'd use a toast here
            if (successMsg.includes('Rejected') || successMsg.includes('Approved')) {
                router.push('/admin/applications');
            } else {
                const response = await getApplicationDetail(id);
                if (response.data) setApp(response.data);
            }
            setShowRejectionModal(false);
            setShowInfoModal(false);
            setShowApproveModal(false);
        } catch (error) {
            console.error('Action failed:', error);
        } finally {
            setIsActionLoading(false);
        }
    };

    const sortedNotes = useMemo(() => {
        if (!app?.internal_notes) return [];
        return [...app.internal_notes].sort((a, b) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
    }, [app?.internal_notes]);

    if (isLoading) return <div className="p-12 text-center text-slate-400 font-bold uppercase tracking-widest animate-pulse min-h-screen bg-slate-50">Loading Audit Record...</div>;
    if (!app) return <div className="p-12 text-center bg-slate-50 min-h-screen pt-40"><h2 className="text-3xl font-bold text-slate-800 mb-8">Application Not Found</h2><Link href="/admin/applications" className="text-blue-600 font-bold border-b border-blue-600 pb-1">Back to Applications</Link></div>;

    const statusBadgeStyles: Record<ApplicationStatus, string> = {
        awaiting_applicant_verification: 'bg-slate-100 text-slate-600 border-slate-200',
        awaiting_principal_confirmation: 'bg-slate-100 text-slate-600 border-slate-200',
        pending_review: 'bg-yellow-100 text-yellow-800 border-yellow-200',
        under_review: 'bg-blue-100 text-blue-700 border-blue-200',
        more_info_requested: 'bg-orange-100 text-orange-700 border-orange-200',
        approved: 'bg-green-100 text-green-700 border-green-200',
        rejected: 'bg-red-100 text-red-700 border-red-200',
        expired: 'bg-slate-100 text-slate-700 border-slate-200',
    };

    return (
        <div className="bg-slate-50 min-h-screen text-slate-900 p-10 font-sans pb-32">

            {/* Page Header */}
            <div className="max-w-5xl mx-auto mb-10">
                <div className="flex justify-between items-start mb-6">
                    <div>
                        <h1 className="text-4xl font-bold text-[#1e293b] mb-2">{app.school_name}</h1>
                        <p className="text-sm font-medium text-slate-400">Application ID: <span className="uppercase">{app.id}</span></p>
                    </div>
                </div>
                <Link href="/admin/applications" className="inline-flex items-center px-4 py-2 bg-white border border-slate-200 rounded-lg text-xs font-bold text-slate-700 hover:bg-slate-50 transition-all shadow-sm">
                    <span className="mr-2">←</span> Back to Applications
                </Link>
            </div>

            <div className="max-w-5xl mx-auto">

                {/* Application Status Block */}
                <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden mb-12">
                    <div className="px-8 py-6 border-b border-slate-100 flex justify-between items-center">
                        <h3 className="text-xl font-bold text-slate-800">Application Status</h3>
                        <span className={`px-4 py-1.5 rounded-full text-[11px] font-bold uppercase tracking-tight border ${statusBadgeStyles[app.status]}`}>
                            {app.status.replace('_', ' ')}
                        </span>
                    </div>
                    <div className="p-10">
                        <div className="flex gap-4 mb-8">
                            {app.applicant_verified_at && (
                                <span className="bg-[#ecfdf5] text-[#059669] text-[11px] font-bold px-4 py-2.5 rounded-xl flex items-center gap-2 border border-[#d1fae5]">
                                    ✓ Applicant Verified
                                </span>
                            )}
                            {app.principal_confirmed_at && (
                                <span className="bg-[#ecfdf5] text-[#059669] text-[11px] font-bold px-4 py-2.5 rounded-xl flex items-center gap-2 border border-[#d1fae5]">
                                    ✓ Principal Confirmed
                                </span>
                            )}
                        </div>

                        {app.applicant_verified_at && app.principal_confirmed_at && app.status === 'under_review' && (
                            <div className="bg-[#eff6ff] border-l-[6px] border-[#3b82f6] p-6 mb-10 rounded-r-xl shadow-sm">
                                <p className="text-[12px] font-bold text-[#1d4ed8] flex items-center gap-2">
                                    Ready for Review: <span className="font-medium text-[#3b82f6]">This application has completed all verification steps and is ready for your review.</span>
                                </p>
                            </div>
                        )}

                        {app.status === 'rejected' && app.decision_reason && (
                            <div className="bg-red-50 border-l-[6px] border-red-500 p-6 mb-10 rounded-r-xl shadow-sm">
                                <p className="text-[12px] font-bold text-red-700 mb-1 uppercase tracking-tight">Rejection Reason</p>
                                <p className="text-sm text-red-600 font-medium">{app.decision_reason}</p>
                            </div>
                        )}

                        {app.reviewed_at && (
                            <div className="bg-slate-50 border border-slate-200 p-5 rounded-xl mb-10 flex justify-between items-center">
                                <div className="space-y-1">
                                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Reviewed By</p>
                                    <p className="text-sm font-bold text-slate-700">{app.reviewed_by || 'Administrator'}</p>
                                </div>
                                <div className="text-right space-y-1">
                                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Decision Date</p>
                                    <p className="text-sm font-bold text-slate-700">{new Date(app.reviewed_at).toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' })}</p>
                                </div>
                            </div>
                        )}

                        {/* Visual Timeline */}
                        <div className="space-y-0 relative ml-3">
                            {(app.timeline ?? []).slice(0, 3).map((event, i) => (
                                <div key={event.id} className="group flex gap-8 items-start relative pb-10 last:pb-0">
                                    {i < Math.min((app.timeline ?? []).length, 3) - 1 && (
                                        <div className="absolute left-[11px] top-6 w-[2px] h-full bg-slate-100"></div>
                                    )}
                                    <div className="relative z-10 w-6 h-6 rounded-full bg-white flex items-center justify-center border-2 border-blue-500 shadow-sm">
                                        <div className="w-2.5 h-2.5 rounded-full bg-blue-500"></div>
                                    </div>
                                    <div className="-mt-1">
                                        <p className="text-[13px] font-bold text-slate-800">{event.label}</p>
                                        <p className="text-[11px] text-slate-400 font-bold mt-1 uppercase tracking-tight">
                                            {new Date(event.timestamp).toLocaleString([], { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' }).replace(',', ' at')}
                                        </p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Info Sections */}
                <InfoSection title="School Information">
                    <InfoField label="School Name" value={app.school_name} />
                    <InfoField label="Year Established" value={app.year_established} />
                    <InfoField label="School Type" value={formatSchoolType(app.school_type)} />
                    <InfoField label="Student Population" value={formatPopulation(app.student_population)} />
                </InfoSection>

                <InfoSection title="Location">
                    <InfoField label="Country" value={app.country_code === 'LR' ? 'Liberia' : app.country_code === 'SL' ? 'Sierra Leone' : app.country_code} />
                    <InfoField label="City" value={app.city} />
                    <div className="hidden md:block"></div>
                    <InfoField label="Address" value={app.address} className="md:col-span-3" />
                </InfoSection>

                <InfoSection title="Contact Information">
                    <InfoField label="School Phone" value={app.school_phone || 'N/A'} />
                    <InfoField label="School Email" value={app.school_email} type="email" />
                    <InfoField label="Principal Name" value={app.principal_name} />
                    <InfoField label="Principal Email" value={app.principal_email} type="email" />
                    <InfoField label="Principal Phone" value={app.principal_phone} />
                </InfoSection>

                <InfoSection title="Applicant & Admin Designation">
                    {app.applicant_is_principal && (
                        <div className="md:col-span-3 bg-[#eff6ff] border-l-4 border-[#3b82f6] p-4 mb-6 rounded-r-xl">
                            <p className="text-[11px] font-bold text-[#1d4ed8]">
                                The applicant is also the Principal of the school.
                            </p>
                        </div>
                    )}
                    <InfoField label="Applicant" value={`${app.applicant_name} (${app.applicant_role || 'Principal'})`} />
                    <InfoField label="Designated School Admin" value={`${app.principal_name} (Principal)`} />
                </InfoSection>

                <InfoSection title="Additional Details">
                    <InfoField label="WHY EK-SMS?" value={app.mission_statement || 'N/A'} className="md:col-span-3" />
                    <InfoField label="ONLINE PRESENCE" value={
                        <div className="space-y-1">
                            {app.website && <div className="text-slate-600 font-medium whitespace-nowrap overflow-hidden text-ellipsis">Website: <a href={app.website} target="_blank" className="text-blue-600 hover:underline">{app.website}</a></div>}
                            {(app.online_presence ?? []).map((social, i) => (
                                <div key={i} className="text-slate-600 font-medium whitespace-nowrap overflow-hidden text-ellipsis">{social.type}: <a href={social.url} target="_blank" className="text-blue-600 hover:underline">{social.url}</a></div>
                            ))}
                        </div>
                    } className="md:col-span-3" />
                    <InfoField label="ADDITIONAL COMMENTS" value={(app.reasons ?? []).join(' | ') || 'None stated'} className="md:col-span-3" />
                </InfoSection>

                {/* Internal Notes Section (Wireframe Aligned) */}
                <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden mb-12">
                    <div className="px-8 py-5 border-b border-slate-100 flex justify-between items-center">
                        <h3 className="text-lg font-bold text-slate-800">Internal Notes</h3>
                        <span className="text-[10px] font-medium text-slate-400 uppercase tracking-widest">Only visible to platform administrators</span>
                    </div>
                    <div className="p-8">
                        <div className="space-y-6 mb-10">
                            {sortedNotes.length === 0 ? (
                                <p className="text-center py-8 text-slate-400 font-medium italic text-sm">Zero administrator notes filed.</p>
                            ) : (
                                sortedNotes.map((note, idx) => (
                                    <div key={`${note.created_at}-${idx}`} className="bg-slate-50 border-l-4 border-blue-500 p-6 rounded-r-xl flex justify-between items-start">
                                        <div className="space-y-2 flex-1">
                                            <p className="text-xs font-bold text-slate-800">{note.created_by || 'Admin User'}</p>
                                            <p className="text-sm text-slate-600 font-medium leading-relaxed">{note.note}</p>
                                        </div>
                                        <div className="text-[10px] font-bold text-slate-400 uppercase ml-4 whitespace-nowrap">
                                            {new Date(note.created_at).toLocaleString([], { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' }).replace(',', ' at')}
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>

                        <div className="space-y-3">
                            <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest">Add Internal Note</label>
                            <textarea
                                value={noteContent}
                                onChange={(e) => setNoteContent(e.target.value)}
                                placeholder="Add a note that only admins can see..."
                                className="w-full bg-white border border-slate-200 rounded-xl p-5 text-sm font-medium text-slate-700 focus:ring-2 focus:ring-blue-500/20 outline-none min-h-[120px] transition-all placeholder:text-slate-400"
                            />
                            <div className="flex justify-between items-center">
                                <span className={`text-[10px] font-bold uppercase tracking-widest ${noteContent.length > 2000 ? 'text-red-400' : 'text-slate-400'}`}>
                                    {noteContent.length} / 2000 characters
                                </span>
                                <button
                                    onClick={handleSaveNote}
                                    disabled={!noteContent.trim() || noteContent.length > 2000 || isNoteSaving}
                                    className="px-8 py-2.5 bg-white border border-slate-200 rounded-xl text-xs font-bold text-slate-700 hover:bg-slate-50 transition-all disabled:opacity-50 shadow-sm"
                                >
                                    {isNoteSaving ? 'Saving...' : 'Save Note'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Final Action Bar (High-Fidelity) */}
                <div className="fixed bottom-0 left-0 right-0 lg:left-64 bg-white/90 backdrop-blur-md border-t border-slate-200 p-6 flex justify-end gap-4 z-50 px-12">
                    {app.status === 'approved' || app.status === 'rejected' ? (
                        <p className="text-xs font-bold text-slate-400 italic py-2">Decision finalized: No further modifications permitted</p>
                    ) : (
                        <>
                            <button
                                onClick={() => setShowInfoModal(true)}
                                className="flex items-center gap-2 bg-[#f59e0b] hover:bg-[#d97706] text-white px-6 py-2.5 rounded-xl font-bold text-xs transition-all shadow-md active:scale-95"
                            >
                                📝 Request More Info
                            </button>
                            <button
                                onClick={() => setShowRejectionModal(true)}
                                className="flex items-center gap-2 bg-[#ef4444] hover:bg-[#dc2626] text-white px-6 py-2.5 rounded-xl font-bold text-xs transition-all shadow-md active:scale-95"
                            >
                                ✕ Reject Application
                            </button>
                            <button
                                onClick={() => setShowApproveModal(true)}
                                className="flex items-center gap-2 bg-[#10b981] hover:bg-[#059669] text-white px-8 py-2.5 rounded-xl font-bold text-xs transition-all shadow-lg active:scale-95"
                            >
                                ✓ Approve Application
                            </button>
                        </>
                    )}
                </div>
            </div>

            {/* Modal Components for Tasks 11, 12, 13 (Briefly implemented for visual pass) */}
            {showInfoModal && (
                <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-[100] flex items-center justify-center p-6" onClick={() => setShowInfoModal(false)}>
                    <div className="bg-white w-full max-w-[500px] rounded-3xl p-10 shadow-2xl" onClick={e => e.stopPropagation()}>
                        <h3 className="text-2xl font-bold text-slate-800 mb-6">Request More Information</h3>
                        <textarea
                            value={infoMessage}
                            onChange={(e) => setInfoMessage(e.target.value)}
                            placeholder="Detail what is missing..."
                            className="w-full border border-slate-200 rounded-2xl p-5 text-sm mb-2 min-h-[150px] outline-none focus:ring-2 focus:ring-blue-500/20"
                        />
                        <div className="flex justify-between items-center mb-6 px-1">
                            <span className={`text-[10px] font-bold uppercase tracking-widest ${infoMessage.length < 10 || infoMessage.length > 1000 ? 'text-red-400' : 'text-slate-400'}`}>
                                {infoMessage.length} / 1000 characters
                            </span>
                            {infoMessage.length > 0 && infoMessage.length < 10 && (
                                <span className="text-[10px] font-bold text-red-500 uppercase tracking-widest">Min. 10 characters required</span>
                            )}
                        </div>
                        <div className="flex gap-4">
                            <button onClick={() => setShowInfoModal(false)} className="flex-1 px-6 py-3 rounded-xl font-bold text-slate-400 hover:bg-slate-50 transition-all">Cancel</button>
                            <button
                                disabled={infoMessage.length < 10 || infoMessage.length > 1000 || isActionLoading}
                                onClick={() => handleAction(() => requestMoreInfo(id, infoMessage), 'Sent')}
                                className="flex-1 bg-[#f59e0b] hover:bg-[#d97706] disabled:opacity-50 text-white px-6 py-3 rounded-xl font-bold shadow-lg shadow-amber-500/20 transition-all"
                            >
                                {isActionLoading ? 'Sending...' : 'Send Request'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {showRejectionModal && (
                <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-[100] flex items-center justify-center p-6" onClick={() => setShowRejectionModal(false)}>
                    <div className="bg-white w-full max-w-[500px] rounded-3xl p-10 shadow-2xl" onClick={e => e.stopPropagation()}>
                        <h3 className="text-2xl font-bold text-slate-800 mb-2">Reject Application</h3>
                        <p className="text-sm text-slate-500 mb-6 font-medium">Please provide a clear reason for rejecting this application. This will be visible to the applicant.</p>
                        <textarea
                            value={rejectionReason}
                            onChange={(e) => setRejectionReason(e.target.value)}
                            placeholder="Reason for rejection..."
                            className="w-full border border-slate-200 rounded-2xl p-5 text-sm mb-2 min-h-[120px] outline-none focus:ring-2 focus:ring-red-500/20"
                        />
                        <div className="flex justify-between items-center mb-6 px-1">
                            <span className={`text-[10px] font-bold uppercase tracking-widest ${rejectionReason.length < 20 || rejectionReason.length > 1000 ? 'text-red-400' : 'text-slate-400'}`}>
                                {rejectionReason.length} / 1000 characters
                            </span>
                            {rejectionReason.length > 0 && rejectionReason.length < 20 && (
                                <span className="text-[10px] font-bold text-red-500 uppercase tracking-widest">Min. 20 characters required</span>
                            )}
                        </div>
                        <div className="flex gap-4">
                            <button onClick={() => setShowRejectionModal(false)} className="flex-1 px-6 py-3 rounded-xl font-bold text-slate-400 hover:bg-slate-50 transition-all">Cancel</button>
                            <button
                                disabled={rejectionReason.length < 20 || rejectionReason.length > 1000 || isActionLoading}
                                onClick={() => handleAction(() => rejectApplication(id, rejectionReason), 'Rejected')}
                                className="flex-1 bg-[#ef4444] hover:bg-[#dc2626] disabled:opacity-50 text-white px-6 py-3 rounded-xl font-bold shadow-lg shadow-red-500/20 transition-all"
                            >
                                {isActionLoading ? 'Rejecting...' : 'Confirm Rejection'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {showApproveModal && (
                <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-[100] flex items-center justify-center p-6" onClick={() => setShowApproveModal(false)}>
                    <div className="bg-white w-full max-w-[450px] rounded-3xl p-10 shadow-2xl text-center" onClick={e => e.stopPropagation()}>
                        <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-6 text-2xl">✓</div>
                        <h3 className="text-2xl font-bold text-slate-800 mb-2">Approve Application</h3>
                        <p className="text-sm text-slate-500 mb-6 font-medium">Are you sure you want to approve **{app.school_name}**?</p>

                        <div className="bg-red-50 border border-red-100 rounded-xl p-4 mb-8 text-left">
                            <p className="text-[10px] font-bold text-red-700 uppercase tracking-widest mb-1">⚠️ Critical Operation</p>
                            <p className="text-[11px] text-red-600 font-medium leading-relaxed">
                                This action triggers an atomic transaction that provisions the school tenant and admin account. **It cannot be undone through the UI.**
                            </p>
                        </div>

                        <div className="flex gap-4">
                            <button onClick={() => setShowApproveModal(false)} className="flex-1 px-6 py-3 rounded-xl font-bold text-slate-400 hover:bg-slate-50 transition-all">Cancel</button>
                            <button
                                disabled={isActionLoading}
                                onClick={() => handleAction(() => approveApplication(id), 'Approved')}
                                className="flex-1 bg-[#10b981] hover:bg-[#059669] disabled:opacity-50 text-white px-6 py-3 rounded-xl font-bold shadow-lg shadow-emerald-500/20 transition-all"
                            >
                                {isActionLoading ? 'Approving...' : 'Yes, Approve'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* ... Other modals would follow a similar high-fidelity light theme ... */}

        </div>
    );
}

export default ApplicationDetailPage;
