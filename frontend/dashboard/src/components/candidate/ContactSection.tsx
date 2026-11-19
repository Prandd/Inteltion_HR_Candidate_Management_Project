import { useRef, useState } from "react";
import { isAxiosError } from "axios";
import api from "../../api/axios";
import type { CandidateDetailType, ContactEntry } from "../../types/candidate";

// Same limits the API enforces (backend/app/schemas.py).
const MAX_LABEL = 50;
const MAX_VALUE = 500;

interface Row extends ContactEntry {
    key: number;
}

const INPUT_CLASS = "w-full rounded-lg border border-gray-200 p-2.5 text-sm text-gray-800 outline-none focus:ring-2 focus:ring-blue-200";

function ContactSection({ candidate, onSaved }: {
    candidate: CandidateDetailType;
    onSaved: (candidate: CandidateDetailType) => void;
}) {
    const [editing, setEditing] = useState(false);
    const [email, setEmail] = useState("");
    const [phone, setPhone] = useState("");
    const [rows, setRows] = useState<Row[]>([]);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");
    const [saved, setSaved] = useState(false);
    const nextKey = useRef(0);

    const contacts = candidate.contacts ?? [];

    function newRow(entry?: ContactEntry): Row {
        nextKey.current += 1;
        return { key: nextKey.current, label: entry?.label ?? "", value: entry?.value ?? "" };
    }

    function startEditing() {
        setEmail(candidate.email || "");
        setPhone(candidate.phone || "");
        setRows(contacts.map(newRow));
        setError("");
        setSaved(false);
        setEditing(true);
    }

    function updateRow(key: number, patch: Partial<ContactEntry>) {
        setRows(current => current.map(row => row.key === key ? { ...row, ...patch } : row));
    }

    async function save(event: React.FormEvent) {
        event.preventDefault();
        if (saving) return;

        // A row left completely blank is just dropped; a half-filled one is a mistake.
        const cleaned: ContactEntry[] = [];
        for (const row of rows) {
            const label = row.label.trim();
            const value = row.value.trim();
            if (!label && !value) continue;
            if (!label || !value) {
                setError("Each contact needs both a name (e.g. LINE) and the contact itself. Fill in both, or remove the row.");
                return;
            }
            cleaned.push({ label, value });
        }

        if (email.trim() === (candidate.email || "").trim()
            && phone.trim() === (candidate.phone || "").trim()
            && JSON.stringify(cleaned) === JSON.stringify(contacts)) {
            setEditing(false);
            setSaved(false);
            setError("");
            return;
        }
        setSaving(true);
        setError("");
        try {
            const response = await api.put(`/candidates/${candidate.candidate_id}`, {
                email: email.trim(),
                phone: phone.trim(),
                contacts: cleaned,
            });
            onSaved(response.data.data);
            setEditing(false);
            setSaved(true);
        } catch (err) {
            setError(saveErrorMessage(err));
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
                        className={`mt-1 ${INPUT_CLASS}`} />
                </label>
                <label className="block text-xs text-gray-500">Phone number
                    <input type="tel" value={phone} onChange={event => setPhone(event.target.value)} placeholder="e.g. +66 80 123 4567"
                        className={`mt-1 ${INPUT_CLASS}`} />
                </label>

                <div>
                    <p className="text-xs text-gray-500">Other contacts</p>
                    {rows.length === 0 && <p className="mt-2 text-sm text-gray-400">No other contacts yet.</p>}
                    <ul className="mt-2 space-y-3">
                        {rows.map((row, index) => <li key={row.key} className="flex items-start gap-2">
                            <div className="grid min-w-0 flex-1 gap-2 sm:grid-cols-[2fr_3fr]">
                                <input type="text" value={row.label} maxLength={MAX_LABEL}
                                    onChange={event => updateRow(row.key, { label: event.target.value })}
                                    placeholder="Name, e.g. LINE" aria-label={`Contact ${index + 1} name`}
                                    className={INPUT_CLASS} />
                                <input type="text" value={row.value} maxLength={MAX_VALUE}
                                    onChange={event => updateRow(row.key, { value: event.target.value })}
                                    placeholder="Contact, e.g. candidate.line" aria-label={`Contact ${index + 1} value`}
                                    className={INPUT_CLASS} />
                            </div>
                            <button type="button" onClick={() => setRows(current => current.filter(item => item.key !== row.key))}
                                aria-label={`Remove contact ${index + 1}`}
                                className="mt-1 shrink-0 rounded-lg px-2.5 py-1.5 text-sm text-gray-400 hover:bg-red-50 hover:text-red-600">✕</button>
                        </li>)}
                    </ul>
                    <button type="button" onClick={() => setRows(current => [...current, newRow()])}
                        className="mt-3 rounded-lg px-3 py-1.5 text-sm font-medium text-blue-600 hover:bg-blue-50">+ Add contact</button>
                </div>

                <div className="flex flex-wrap items-center gap-3 border-t border-gray-100 pt-4">
                    <button type="submit" className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">{saving ? "Saving..." : "Save changes"}</button>
                    <button type="button" onClick={() => { setEditing(false); setError(""); }} className="rounded-lg px-3 py-2 text-sm text-gray-500 hover:bg-gray-50">Cancel</button>
                </div>
            </fieldset>
        </form> : <div className="space-y-5">
            <ContactItem icon="✉" label="Email" value={candidate.email} href={candidate.email ? `mailto:${candidate.email}` : undefined} />
            <ContactItem icon="☎" label="Phone" value={candidate.phone} href={candidate.phone ? `tel:${candidate.phone}` : undefined} />
            {contacts.length === 0
                ? <ContactItem icon="＋" label="Other contacts" />
                : contacts.map((contact, index) => {
                    const link = linkFor(contact.value);
                    return <ContactItem key={`${index}-${contact.label}`} icon="＋" label={contact.label}
                        value={contact.value} href={link?.href} external={link?.external} />;
                })}
        </div>}
    </section>;
}

// Only http(s) URLs and email addresses become links; anything else (a LINE ID,
// a phone number, free text) is shown as plain text. Never javascript: and co.
function linkFor(value: string): { href: string; external: boolean } | undefined {
    const text = value.trim();
    if (/^https?:\/\/\S+$/i.test(text)) return { href: text, external: true };
    if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(text)) return { href: `mailto:${text}`, external: false };
    return undefined;
}

function saveErrorMessage(err: unknown): string {
    const fallback = "Unable to save contact details. Please try again.";
    if (!isAxiosError(err)) return fallback;
    const body = err.response?.data;
    // The API answers a rejected body with error "Validation error" plus a detail
    // list; the first entry says what is wrong ("Value error, Each contact needs ...").
    const detail = body?.detail?.[0]?.msg;
    if (typeof detail === "string" && detail) return detail.replace(/^Value error, /, "");
    return typeof body?.error === "string" ? body.error : fallback;
}

function ContactItem({ icon, label, value, href, external }: { icon: string; label: string; value?: string; href?: string; external?: boolean }) {
    return <div className="flex items-start gap-3">
        <div aria-hidden="true" className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-sm text-blue-600">{icon}</div>
        <div className="min-w-0">
            <p className="break-words text-xs text-gray-400">{label}</p>
            {href ? <a href={href} {...(external ? { target: "_blank", rel: "noopener noreferrer" } : {})} className="mt-1 block break-all text-sm font-medium text-gray-800 hover:text-blue-600">{value}</a>
                : value ? <p className="mt-1 whitespace-pre-wrap break-words text-sm font-medium text-gray-800">{value}</p>
                : <p className="mt-1 text-sm text-gray-400">Not provided</p>}
        </div>
    </div>;
}

export default ContactSection;
