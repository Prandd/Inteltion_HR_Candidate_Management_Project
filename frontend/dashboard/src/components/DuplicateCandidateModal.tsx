import { useEffect, useRef } from "react";

export interface DuplicateCandidate {
    candidate_id: string;
    full_name?: string;
    email?: string;
    phone?: string;
    applied_position?: string;
    status?: string;
    created_at?: string;
    updated_at?: string;
    rejected_at?: string | null;
    rejected_from_status?: string | null;
    rejection_reason?: string;
    latest_comment?: string;
    latest_comment_by?: string;
}

export interface PendingUploadReview {
    pending_upload_id: string;
    filename: string;
    extracted_preview: Record<string, unknown>;
    duplicate_candidates: DuplicateCandidate[];
    uploaded_by: string;
    created_at: string;
}

interface Props {
    review: PendingUploadReview;
    loading?: boolean;
    action?: "update" | "create-new" | null;
    error?: string;
    onClose: () => void;
    onUpdateRecord: () => void;
    onCreateNewCycle: () => void;
}

function DuplicateCandidateModal({ review, loading = false, action, error,
    onClose, onUpdateRecord, onCreateNewCycle }: Props) {
    const dialogRef = useRef<HTMLDialogElement>(null);
    // The backend updates the newest matching record. Keep that target visible.
    const candidate = [...review.duplicate_candidates].sort((a, b) =>
        (b.updated_at || "").localeCompare(a.updated_at || "") ||
        b.candidate_id.localeCompare(a.candidate_id))[0];

    useEffect(() => {
        const dialog = dialogRef.current;
        const previousFocus = document.activeElement;
        const previousOverflow = document.body.style.overflow;
        dialog?.showModal();
        document.body.style.overflow = "hidden";
        return () => {
            dialog?.close();
            document.body.style.overflow = previousOverflow;
            if (previousFocus instanceof HTMLElement) previousFocus.focus();
        };
    }, []);

    function previewValue(key: string) {
        const value = review.extracted_preview[key];
        return typeof value === "string" || typeof value === "number"
            ? String(value) || "Not provided" : "Not provided";
    }

    return (
        <dialog ref={dialogRef} aria-labelledby="duplicate-review-title"
            aria-describedby="duplicate-review-description" aria-busy={loading}
            onCancel={event => { event.preventDefault(); if (!loading) onClose(); }}
            className="fixed inset-0 m-auto max-h-[92dvh] w-[calc(100%_-_2rem)] max-w-2xl overflow-hidden rounded-2xl border border-slate-200 bg-white p-0 text-slate-900 shadow-xl backdrop:bg-slate-950/40">
            <div className="flex max-h-[92dvh] flex-col">
                <header className="flex shrink-0 items-start justify-between gap-4 border-b border-slate-100 px-6 py-4">
                    <div>
                        <p className="mb-2 text-xs font-medium text-amber-700">Duplicate review</p>
                        <h2 id="duplicate-review-title" className="text-xl font-semibold tracking-tight">This candidate may already exist</h2>
                        <p id="duplicate-review-description" className="mt-2 text-sm leading-6 text-slate-500">
                            Review the match, then choose how to save this CV.
                        </p>
                    </div>
                    <button type="button" onClick={onClose} disabled={loading} aria-label="Close duplicate review"
                        className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-xl text-slate-400 transition hover:bg-slate-100 hover:text-slate-700 focus-visible:outline-2 focus-visible:outline-blue-600 disabled:opacity-40">×</button>
                </header>

                <div className="min-h-0 space-y-4 overflow-y-auto px-6 py-4">
                    <div>
                        <h3 className="text-xs font-medium text-slate-500">Uploaded CV</h3>
                        <p className="mt-1 break-all text-sm text-slate-700">{review.filename}</p>
                        <dl className="mt-3 grid gap-3 rounded-xl bg-slate-50 p-4 sm:grid-cols-3">
                            <InfoRow label="Name" value={previewValue("full_name")} />
                            <InfoRow label="Email" value={previewValue("email")} />
                            <InfoRow label="Phone" value={previewValue("phone")} />
                        </dl>
                    </div>

                    <section>
                        <div className="mb-2 flex items-center justify-between gap-2">
                            <h3 className="text-xs font-medium text-slate-500">Existing candidate</h3>
                            {review.duplicate_candidates.length > 1 && <span className="text-xs text-slate-400">
                                {review.duplicate_candidates.length} matches · most recently updated shown
                            </span>}
                        </div>
                        {candidate ? <div className="rounded-xl border border-slate-200 p-4">
                            <div className="flex flex-wrap items-center justify-between gap-2">
                                <p className="text-sm font-semibold">{candidate.full_name || "Unnamed candidate"}</p>
                                <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-600">{candidate.status || "Unknown status"}</span>
                            </div>
                            <p className="mt-1 break-words text-xs text-slate-500">{[candidate.email, candidate.phone].filter(Boolean).join(" · ") || "No contact details"}</p>
                            <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500">
                                <span>{candidate.applied_position || "No position assigned"}{candidate.created_at && ` · Imported ${formatDate(candidate.created_at)}`}</span>
                                <a href={`/candidate/${candidate.candidate_id}`} target="_blank" rel="noopener noreferrer"
                                    className="font-medium text-blue-600 hover:text-blue-800 focus-visible:outline-2 focus-visible:outline-blue-600">View profile ↗</a>
                            </div>
                            {(candidate.rejected_at || candidate.rejection_reason || candidate.latest_comment) && <details className="mt-3 border-t border-slate-100 pt-3 text-xs text-slate-500">
                                <summary className="cursor-pointer font-medium hover:text-slate-800">Previous feedback</summary>
                                <div className="mt-3 space-y-2 leading-5">
                                    {candidate.rejected_at && <p>Rejected {formatDate(candidate.rejected_at)}{candidate.rejected_from_status && ` from ${candidate.rejected_from_status}`}</p>}
                                    {candidate.rejection_reason && <p className="break-words">Reason: {candidate.rejection_reason}</p>}
                                    {candidate.latest_comment && <p className="break-words">{candidate.latest_comment_by || "Latest comment"}: {candidate.latest_comment}</p>}
                                </div>
                            </details>}
                        </div> : <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-500">The matching record is unavailable. You can create a new candidate.</p>}
                    </section>

                    <div className="grid gap-3 sm:grid-cols-2">
                        <ActionCard title="Create new candidate"
                            description="Save this CV as a separate application. The existing record stays unchanged."
                            buttonText={action === "create-new" ? "Creating..." : "Create new"}
                            onClick={onCreateNewCycle} disabled={loading} />
                        <ActionCard title="Replace existing CV"
                            description="Replace CV details and restart the application at New. Keep the owner, HR notes and history."
                            buttonText={action === "update" ? "Replacing..." : "Replace & restart"}
                            onClick={onUpdateRecord} disabled={loading || !candidate} />
                    </div>
                    {error && <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm leading-5 text-red-700">{error}</p>}
                </div>

                <footer className="flex shrink-0 items-center justify-between gap-3 border-t border-slate-100 px-6 py-4">
                    <p aria-live="polite" className="text-xs text-slate-400">{loading ? "Saving your choice..." : "Choose an action to finish this upload."}</p>
                    <button type="button" onClick={onClose} disabled={loading}
                        className="shrink-0 rounded-lg px-3 py-2 text-sm text-slate-500 transition hover:bg-slate-50 hover:text-slate-800 focus-visible:outline-2 focus-visible:outline-blue-600 disabled:opacity-40">Review later</button>
                </footer>
            </div>
        </dialog>
    );
}

function InfoRow({ label, value }: { label: string; value: string }) {
    return <div className="min-w-0"><dt className="text-xs text-slate-400">{label}</dt>
        <dd className="mt-1 break-words text-sm font-medium text-slate-700">{value}</dd></div>;
}

function ActionCard({ title, description, buttonText, onClick, disabled }: {
    title: string; description: string; buttonText: string; onClick: () => void; disabled: boolean;
}) {
    return <div className="flex flex-col rounded-xl border border-slate-200 p-4">
        <h3 className="text-sm font-semibold">{title}</h3>
        <p className="mb-3 mt-2 flex-1 text-xs leading-5 text-slate-500">{description}</p>
        <button type="button" onClick={onClick} disabled={disabled}
            className="min-h-10 rounded-lg border border-blue-200 bg-blue-50 px-3 py-2 text-sm font-medium text-blue-700 transition hover:border-blue-300 hover:bg-blue-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:cursor-not-allowed disabled:opacity-40">{buttonText}</button>
    </div>;
}

function formatDate(value: string) {
    const date = new Date(/(?:Z|[+-]\d{2}:\d{2})$/i.test(value) ? value : `${value}Z`);
    if (Number.isNaN(date.getTime())) return "Unknown date";
    return new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", year: "numeric" }).format(date);
}

export default DuplicateCandidateModal;
