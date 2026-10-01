import { useEffect, useState } from "react";
import api from "../../api/axios";
import type { CandidateDetailType } from "../../types/candidate";

interface Props {
    candidate: CandidateDetailType;
}

interface StatusHistoryItem {
    history_id: string;
    candidate_id: string;
    from_status: string | null;
    to_status: string;
    changed_by: string;
    changed_at: string;
    reason: string;
}

function StatusHistorySection({ candidate }: Props) {
    const [history, setHistory] = useState<StatusHistoryItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        async function fetchStatusHistory() {
            if (!candidate.candidate_id) {
                setHistory([]);
                setLoading(false);
                return;
            }

            try {
                setLoading(true);
                setError("");

                const response = await api.get(
                    `/candidates/${candidate.candidate_id}/status-history`
                );

                setHistory(
                    Array.isArray(response.data.data)
                        ? response.data.data
                        : []
                );
            } catch (err) {
                console.error("Failed to load status history:", err);
                setHistory([]);
                setError("Unable to load status history.");
            } finally {
                setLoading(false);
            }
        }

        fetchStatusHistory();
    }, [candidate.candidate_id, candidate.status]);

    function formatDate(value: string) {
        const date = new Date(value);

        if (Number.isNaN(date.getTime())) {
            return value;
        }

        return date.toLocaleString();
    }

    function statusStyle(status: string) {
        switch (status) {
            case "Assessment":
                return {
                    dot: "bg-orange-500 border-orange-100",
                    text: "text-orange-600",
                };

            case "Interview":
                return {
                    dot: "bg-purple-500 border-purple-100",
                    text: "text-purple-600",
                };

            case "Hired":
                return {
                    dot: "bg-green-500 border-green-100",
                    text: "text-green-600",
                };

            case "Rejected":
                return {
                    dot: "bg-red-600 border-red-100",
                    text: "text-red-600",
                };

            case "CV passed":
                return {
                    dot: "bg-cyan-500 border-cyan-100",
                    text: "text-cyan-600",
                };

            default:
                return {
                    dot: "bg-blue-600 border-blue-100",
                    text: "text-blue-600",
                };
        }
    }

    return (
        <section className="bg-white border rounded-2xl p-5">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h2 className="text-sm font-bold text-gray-900 uppercase">
                        Status History & Audit Trail
                    </h2>

                    <p className="text-xs text-gray-400 mt-1">
                        Track candidate status changes and activities
                    </p>
                </div>

                <span className="text-xs bg-gray-100 text-gray-600 px-3 py-1 rounded-full">
                    {history.length} events
                </span>
            </div>

            {loading ? (
                <p className="text-sm text-gray-400">
                    Loading status history...
                </p>
            ) : error ? (
                <p className="text-sm text-red-500">
                    {error}
                </p>
            ) : history.length === 0 ? (
                <p className="text-sm text-gray-400">
                    No status history available.
                </p>
            ) : (
                <div className="space-y-6">
                    {history.map((item, index) => {
                        const style = statusStyle(item.to_status);

                        return (
                            <div
                                key={item.history_id}
                                className="relative pl-8"
                            >
                                {index !== history.length - 1 && (
                                    <div className="absolute left-[7px] top-6 bottom-[-24px] w-px bg-gray-200" />
                                )}

                                <div
                                    className={`
                                        absolute
                                        left-0
                                        top-1
                                        w-4
                                        h-4
                                        rounded-full
                                        border-4
                                        ${style.dot}
                                    `}
                                />

                                <div>


                                    {/* STATUS + TIME */}


                                    <div

                                        className="
                                        flex
                                        justify-between
                                        gap-3
                                        "

                                    >



                                        <div className="flex min-w-0 flex-1 flex-col">
                                            <h3 className={`text-sm font-semibold ${style.text}`}>
                                                {item.to_status}
                                            </h3>
                                            <p className="mt-1 text-xs text-gray-500">
                                                {item.from_status
                                                    ? `${item.from_status} → ${item.to_status}`
                                                    : `Status set to ${item.to_status}`}
                                            </p>
                                        </div>
                                        <span className="whitespace-nowrap text-xs text-gray-400">
                                            {formatDate(item.changed_at)}
                                        </span>
                                    </div>

                                    {item.reason && (
                                        <p className="mt-2 text-sm text-gray-600">
                                            {item.reason}
                                        </p>
                                    )}

                                    {item.changed_by && (
                                        <p className="mt-2 text-xs text-gray-400">
                                            Changed by: {item.changed_by}
                                        </p>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </section>
    );
}

export default StatusHistorySection;
