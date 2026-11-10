import { useState } from "react";
import { isAxiosError } from "axios";
import api from "../../api/axios";
import type { CandidateDetailType } from "../../types/candidate";

function ContactSection({ candidate, onSaved }: {
    candidate: CandidateDetailType;
    onSaved: (candidate: CandidateDetailType) => void;
}) {
    const [editing, setEditing] = useState(false);
    const [email, setEmail] = useState("");
    const [phone, setPhone] = useState("");
    const [other, setOther] = useState("");
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");
    const [saved, setSaved] = useState(false);

    function startEditing() {
        setEmail(candidate.email || "");
        setPhone(candidate.phone || "");
        setOther(candidate.contact_other || "");
        setError("");
        setSaved(false);
        setEditing(true);
    }

    async function save(event: React.FormEvent) {
        event.preventDefault();
        if (saving) return;
        if (email.trim() === (candidate.email || "").trim()
            && phone.trim() === (candidate.phone || "").trim()
            && other.trim() === (candidate.contact_other || "").trim()) {
            setEditing(false);
            setSaved(false);
            setError("");
            return;
        }
        setSaving(true);
        setError("");
        try {
            const response = await api.put(`/candidates/${candidate.candidate_id}`, { email: email.trim(), phone: phone.trim(), contact_other: other.trim() });
            onSaved(response.data.data);
            setEditing(false);
            setSaved(true);
        } catch (err) {
            setError(isAxiosError(err) && typeof err.response?.data?.error === "string"
                ? err.response.data.error : "Unable to save contact details. Please try again.");
        } finally { setSaving(false); }
    }

    return <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="mb-5 flex items-center justify-between gap-3">
            <h2 className="text-base font-semibold text-gray-900">Contact</h2>
            {!editing && <button type="button" onClick={startEditing} className="rounded-lg px-3 py-1.5 text-sm font-medium text-blue-600 hover:bg-blue-50">Edit contact</button>}
        </div>
        {error && <p role="alert" className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}
        {saved && !editing && <p role="status" className="mb-4 text-sm text-green-700">Contact details updated.</p>}
        {editing ? <form onSubmit={save}>
            <fieldset disabled={saving} className="space-y-4 disabled:opacity-60">
                <label className="block text-xs text-gray-500">Email
                    <input type="email" value={email} onChange={event => setEmail(event.target.value)} placeholder="name@example.com"
                        className="mt-1 w-full rounded-lg border border-gray-200 p-2.5 text-sm text-gray-800 outline-none focus:ring-2 focus:ring-blue-200" />
                </label>
                <label className="block text-xs text-gray-500">Phone number
                    <input type="tel" value={phone} onChange={event => setPhone(event.target.value)} placeholder="e.g. +66 80 123 4567"
                        className="mt-1 w-full rounded-lg border border-gray-200 p-2.5 text-sm text-gray-800 outline-none focus:ring-2 focus:ring-blue-200" />
                </label>
                <label className="block text-xs text-gray-500">Other contact
                    <textarea value={other} onChange={event => setOther(event.target.value)} rows={3}
                        placeholder="LINE ID, LinkedIn, another phone number, or other contact details"
                        className="mt-1 w-full rounded-lg border border-gray-200 p-2.5 text-sm text-gray-800 outline-none focus:ring-2 focus:ring-blue-200" />
                </label>
                <div className="flex flex-wrap items-center gap-3 border-t border-gray-100 pt-4">
                    <button type="submit" className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">{saving ? "Saving..." : "Save changes"}</button>
                    <button type="button" onClick={() => { setEditing(false); setError(""); }} className="rounded-lg px-3 py-2 text-sm text-gray-500 hover:bg-gray-50">Cancel</button>
                </div>
            </fieldset>
        </form> : <div className="space-y-5">
            <ContactItem icon="✉" label="Email" value={candidate.email} href={candidate.email ? `mailto:${candidate.email}` : undefined} />
            <ContactItem icon="☎" label="Phone" value={candidate.phone} href={candidate.phone ? `tel:${candidate.phone}` : undefined} />
            <ContactItem icon="＋" label="Other" value={candidate.contact_other} />
        </div>}
    </section>;
}

function ContactItem({ icon, label, value, href }: { icon: string; label: string; value?: string; href?: string }) {
    return <div className="flex items-start gap-3">
        <div aria-hidden="true" className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-sm text-blue-600">{icon}</div>
        <div className="min-w-0">
            <p className="text-xs text-gray-400">{label}</p>
            {href ? <a href={href} className="mt-1 block break-all text-sm font-medium text-gray-800 hover:text-blue-600">{value}</a>
                : value ? <p className="mt-1 whitespace-pre-wrap break-words text-sm font-medium text-gray-800">{value}</p>
                : <p className="mt-1 text-sm text-gray-400">Not provided</p>}
        </div>
    </div>;
}

export default ContactSection;
