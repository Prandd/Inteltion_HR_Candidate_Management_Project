import { useEffect, useState } from "react";
import api from "../../api/axios";
import type { CandidateDetailType } from "../../types/candidate";

interface StatusEvent {
    history_id: string;
    from_status: string | null;
    to_status: string;
    changed_by: string;
    changed_by_name?: string;
    changed_at: string;
    reason: string;
}
interface OwnershipEvent {
    ownership_history_id: string;
    from_owner_account_id: string | null;
    to_owner_account_id: string;
    from_owner_name?: string;
    to_owner_name?: string;
    changed_by: string;
    changed_by_name?: string;
    changed_at: string;
    reason: string;
}
interface AuditEvent {
    id: string;
    title: string;
    detail: string;
    actor: string;
    date: string;
    reason: string;
    ownership: boolean;
}

// SQLite can return UTC timestamps without an offset; interpret them as UTC.
function eventDate(value: string) {
    return new Date(/(?:Z|[+-]\d{2}:\d{2})$/i.test(value) ? value : `${value}Z`);
}

function eventStyle(item: AuditEvent) {
    if (item.ownership || item.title === "Interview") return { dot: "bg-purple-500 border-purple-100", text: "text-purple-600" };
    if (item.title === "Assessment") return { dot: "bg-orange-500 border-orange-100", text: "text-orange-600" };
    if (item.title === "Hired") return { dot: "bg-green-500 border-green-100", text: "text-green-600" };
    if (item.title === "Rejected") return { dot: "bg-red-600 border-red-100", text: "text-red-600" };
    if (item.title === "CV passed") return { dot: "bg-cyan-500 border-cyan-100", text: "text-cyan-600" };
    return { dot: "bg-blue-600 border-blue-100", text: "text-blue-600" };
}

function StatusHistorySection({ candidate }: { candidate: CandidateDetailType }) {
    const [history, setHistory] = useState<AuditEvent[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        let cancelled = false;
        async function fetchHistory() {
            setLoading(true);
            setError("");
            try {
                const [statuses, owners] = await Promise.all([
                    api.get(`/candidates/${candidate.candidate_id}/status-history`),
                    api.get(`/candidates/${candidate.candidate_id}/ownership-history`),
                ]);
                const statusEvents: AuditEvent[] = (statuses.data.data as StatusEvent[]).map(item => ({
                    id: `status-${item.history_id}`,
                    title: item.to_status,
                    detail: item.from_status ? `${item.from_status} → ${item.to_status}` : `Status set to ${item.to_status}`,
                    actor: item.changed_by_name || item.changed_by,
                    date: item.changed_at,
                    reason: item.reason,
                    ownership: false,
                }));
                const ownerEvents: AuditEvent[] = (owners.data.data as OwnershipEvent[]).map(item => ({
                    id: `owner-${item.ownership_history_id}`,
                    title: item.from_owner_account_id ? "Owner changed" : "CV imported · Owner assigned",
                    detail: item.from_owner_account_id
                        ? `${item.from_owner_name || item.from_owner_account_id} → ${item.to_owner_name || item.to_owner_account_id}`
                        : `Imported by ${item.to_owner_name || item.to_owner_account_id}`,
                    actor: item.changed_by_name || item.changed_by,
                    date: item.changed_at,
                    reason: item.reason === "created by upload" ? "" : item.reason,
                    ownership: true,
                }));
                const events = [...statusEvents, ...ownerEvents].sort((a, b) =>
                    eventDate(b.date).getTime() - eventDate(a.date).getTime() || a.id.localeCompare(b.id));
                if (!cancelled) setHistory(events);
            } catch {
                if (!cancelled) {
                    setHistory([]);
                    setError("Unable to load audit history. Please refresh and try again.");
                }
            } finally {
                if (!cancelled) setLoading(false);
            }
        }
        fetchHistory();
        return () => { cancelled = true; };
    }, [candidate.candidate_id, candidate.status, candidate.owner_account_id]);

    return (
        <section className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
            <div className="flex justify-between items-center gap-3 mb-6">
                <div>
                    <h2 className="text-sm font-bold text-gray-900 uppercase">Status History & Audit Trail</h2>
                    <p className="text-xs text-gray-400 mt-1">CV import, ownership and status changes</p>
                </div>
                <span className="shrink-0 text-xs bg-gray-100 text-gray-600 px-3 py-1 rounded-full">{history.length} events</span>
            </div>
            {loading ? <p className="text-sm text-gray-400">Loading audit history...</p>
                : error ? <p role="alert" className="text-sm text-red-500">{error}</p>
                : history.length === 0 ? <p className="text-sm text-gray-400">No audit history available.</p>
                : <div className="space-y-6">
                    {history.map((item, index) => (
                        <div key={item.id} className="relative pl-8">
                            {index !== history.length - 1 && <div className="absolute left-[7px] top-6 bottom-[-24px] w-px bg-gray-200" />}
                            <div className={`absolute left-0 top-1 w-4 h-4 rounded-full border-4 ${eventStyle(item).dot}`} />
                            <div className="flex flex-wrap justify-between gap-2">
                                <h3 className={`text-sm font-semibold ${eventStyle(item).text}`}>{item.title}</h3>
                                <span className="text-xs text-gray-400">{Number.isNaN(eventDate(item.date).getTime()) ? item.date : eventDate(item.date).toLocaleString()}</span>
                            </div>
                            <p className="mt-1 text-xs text-gray-500 break-words">{item.detail}</p>
                            {item.reason && <p className="mt-2 text-sm text-gray-600 break-words">{item.reason}</p>}
                            {item.actor && <p className="mt-2 text-xs text-gray-400">Changed by: {item.actor}</p>}
                        </div>
                    ))}
                </div>}
        </section>
    );
}

export default StatusHistorySection;
