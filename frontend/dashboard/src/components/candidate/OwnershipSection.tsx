import { useEffect, useState } from "react";
import { isAxiosError } from "axios";
import api from "../../api/axios";
import type { CandidateDetailType } from "../../types/candidate";

interface OwnerOption {
    account_id: string;
    full_name: string;
    username: string;
}

function OwnershipSection({ candidate, onUpdate }: {
    candidate: CandidateDetailType;
    onUpdate: () => Promise<void>;
}) {
    const [accounts, setAccounts] = useState<OwnerOption[]>([]);
    const [selected, setSelected] = useState("");
    const [reason, setReason] = useState("");
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");
    let accountId = "";
    try {
        accountId = JSON.parse(sessionStorage.getItem("inteltion_account") || "null")?.account_id || "";
    } catch { /* A missing session never grants transfer access. */ }
    const canTransfer = !!accountId && accountId === candidate.owner_account_id;

    useEffect(() => {
        let cancelled = false;
        setSelected("");
        setReason("");
        setError("");
        setAccounts([]);
        if (!canTransfer) return;
        setLoading(true);
        api.get(`/candidates/${candidate.candidate_id}/ownership-options`)
            .then(response => { if (!cancelled) setAccounts(response.data.data); })
            .catch(() => { if (!cancelled) setError("Unable to load users. Please refresh and try again."); })
            .finally(() => { if (!cancelled) setLoading(false); });
        return () => { cancelled = true; };
    }, [candidate.candidate_id, candidate.owner_account_id, canTransfer]);

    async function transfer(event: React.FormEvent) {
        event.preventDefault();
        if (!selected || saving) return;
        setSaving(true);
        setError("");
        try {
            const response = await api.post(`/candidates/${candidate.candidate_id}/transfer-ownership`, {
                new_owner_account_id: selected,
                reason: reason.trim(),
            });
            // Refresh the parent so both permissions and the audit trail use the new owner.
            if (response.data.data) await onUpdate();
        } catch (err) {
            setError(isAxiosError(err) && typeof err.response?.data?.error === "string"
                ? err.response.data.error : "Unable to transfer ownership. Please try again.");
        } finally {
            setSaving(false);
        }
    }

    return (
        <section className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
            <h2 className="text-sm font-bold text-gray-900 uppercase">Candidate Owner</h2>
            <p className="mt-2 text-sm text-gray-700">{candidate.owner_name || "Unassigned"}</p>
            {canTransfer ? (
                <form onSubmit={transfer} className="mt-4 space-y-3">
                    <label className="block text-xs text-gray-600">
                        Transfer ownership to
                        <select value={selected} onChange={e => setSelected(e.target.value)}
                            disabled={loading || saving} required className="mt-1 w-full rounded-lg border border-gray-200 p-2 text-sm">
                            <option value="">{loading ? "Loading users..." : "Select a user"}</option>
                            {accounts.map(account => <option key={account.account_id} value={account.account_id}>
                                {account.full_name || account.username} ({account.username})
                            </option>)}
                        </select>
                    </label>
                    {!loading && !error && accounts.length === 0 && (
                        <p className="text-xs text-gray-500">No other active users are available.</p>
                    )}
                    <label className="block text-xs text-gray-600">
                        Reason (optional)
                        <textarea value={reason} onChange={e => setReason(e.target.value)} disabled={saving}
                            rows={2} className="mt-1 w-full rounded-lg border border-gray-200 p-2 text-sm" />
                    </label>
                    <p className="text-xs text-gray-500">The new owner will manage future ownership transfers.</p>
                    <button type="submit" disabled={!selected || loading || saving}
                        className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white disabled:opacity-50">
                        {saving ? "Transferring..." : "Transfer ownership"}
                    </button>
                </form>
            ) : <p className="mt-3 text-xs text-gray-500">Only the current owner can transfer ownership.</p>}
            {error && <p role="alert" className="mt-3 text-sm text-red-600">{error}</p>}
        </section>
    );
}

export default OwnershipSection;
