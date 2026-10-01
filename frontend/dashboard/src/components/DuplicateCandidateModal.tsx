import { useNavigate } from "react-router-dom";

export interface DuplicateCandidate {
    candidate_id: string;
    full_name?: string;
    email?: string;
    phone?: string;
    applied_position?: string;
    status?: string;
    updated_at?: string;
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
    onClose: () => void;
    onSamePerson: () => void;
    onDifferentPerson: () => void;
}

function DuplicateCandidateModal({
    review,
    loading = false,
    onClose,
    onSamePerson,
    onDifferentPerson
}: Props) {
    const navigate = useNavigate();
    const candidate = review.duplicate_candidates[0];

    function viewCandidate() {
        if (!candidate) return;
        navigate(`/candidate/${candidate.candidate_id}`);
    }

    return (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl w-full max-w-lg p-6 shadow-xl">
                <div className="flex items-start gap-3 mb-5">
                    <div className="w-11 h-11 rounded-xl bg-yellow-50 text-yellow-600 flex items-center justify-center text-xl font-bold">
                        !
                    </div>

                    <div>
                        <h2 className="text-lg font-semibold text-gray-900">
                            Possible Duplicate Candidate
                        </h2>
                        <p className="text-sm text-gray-500 mt-1">
                            Review the possible match before deciding whether this CV
                            belongs to the same person.
                        </p>
                        <p className="text-xs text-gray-400 mt-1">
                            File: {review.filename}
                        </p>
                    </div>
                </div>

                {candidate ? (
                    <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 space-y-4">
                        <InfoRow label="Name" value={candidate.full_name || "-"} />
                        <InfoRow label="Email" value={candidate.email || "-"} />
                        <InfoRow label="Phone" value={candidate.phone || "-"} />
                        <InfoRow
                            label="Position"
                            value={candidate.applied_position || "-"}
                        />
                        <InfoRow
                            label="Current Status"
                            value={candidate.status || "-"}
                        />

                        {review.duplicate_candidates.length > 1 && (
                            <p className="text-xs text-amber-700">
                                {review.duplicate_candidates.length} possible matches
                                were found. The backend will select the most recently
                                updated candidate when you choose Same Person.
                            </p>
                        )}
                    </div>
                ) : (
                    <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 text-sm text-gray-500">
                        No candidate preview is available.
                    </div>
                )}

                <div className="mt-6">
                    <p className="text-sm font-medium text-gray-800 mb-3">
                        Is this CV the same person as the candidate above?
                    </p>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <button
                            onClick={onSamePerson}
                            disabled={loading || !candidate}
                            className="px-4 py-3 rounded-xl text-sm bg-blue-600 text-white hover:bg-blue-700 disabled:bg-gray-300"
                        >
                            Same Person — Update
                        </button>

                        <button
                            onClick={onDifferentPerson}
                            disabled={loading}
                            className="px-4 py-3 rounded-xl text-sm bg-orange-500 text-white hover:bg-orange-600 disabled:bg-gray-300"
                        >
                            Different Person — Create New
                        </button>
                    </div>

                    <div className="flex justify-between gap-3 mt-3">
                        <button
                            onClick={onClose}
                            disabled={loading}
                            className="px-4 py-2 rounded-xl text-sm bg-gray-100 text-gray-600 hover:bg-gray-200 disabled:text-gray-300"
                        >
                            Cancel
                        </button>

                        {candidate && (
                            <button
                                onClick={viewCandidate}
                                disabled={loading}
                                className="px-4 py-2 rounded-xl text-sm border border-blue-200 text-blue-600 hover:bg-blue-50 disabled:text-gray-300"
                            >
                                View Candidate
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

function InfoRow({ label, value }: { label: string; value: string }) {
    return (
        <div>
            <p className="text-xs text-gray-400">{label}</p>
            <p className="text-sm font-medium text-gray-800 mt-1">{value}</p>
        </div>
    );
}

export default DuplicateCandidateModal;
