import { useState } from "react";
import { isAxiosError } from "axios";
import api from "../../api/axios";
import type { CandidateDetailType, Education } from "../../types/candidate";

interface Props {
    candidate: CandidateDetailType;
    onSaved: (candidate: CandidateDetailType) => void;
}

const emptyEducation = (): Education => ({ institution: "", degree: "", field: "", year: "" });
const fields = [
    { key: "institution", label: "Institution", placeholder: "University or school" },
    { key: "degree", label: "Degree", placeholder: "e.g. Bachelor of Science" },
    { key: "field", label: "Field of study", placeholder: "e.g. Computer Science" },
    { key: "year", label: "Year or period", placeholder: "e.g. 2024 or 2020–2024" },
] as const;

function EducationSection({ candidate, onSaved }: Props) {
    const [editing, setEditing] = useState(false);
    const [draft, setDraft] = useState<Education[]>([]);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");
    const [saved, setSaved] = useState(false);

    function startEditing() {
        setDraft(candidate.education?.length ? candidate.education.map(item => ({ ...item })) : [emptyEducation()]);
        setError("");
        setSaved(false);
        setEditing(true);
    }

    async function save(event: React.FormEvent) {
        event.preventDefault();
        if (saving) return;
        const education = draft.map(item => ({
            institution: (item.institution || "").trim(), degree: (item.degree || "").trim(),
            field: (item.field || "").trim(), year: (item.year || "").trim(),
        }));
        if (education.some(item => !Object.values(item).some(Boolean))) {
            setError("Fill in at least one field for each entry, or remove empty entries.");
            return;
        }
        const original = (candidate.education || []).map(item => ({
            institution: (item.institution || "").trim(), degree: (item.degree || "").trim(),
            field: (item.field || "").trim(), year: (item.year || "").trim(),
        }));
        if (JSON.stringify(education) === JSON.stringify(original)) {
            setEditing(false);
            setSaved(false);
            setError("");
            return;
        }
        setSaving(true);
        setError("");
        try {
            const response = await api.put(`/candidates/${candidate.candidate_id}`, { education });
            onSaved(response.data.data);
            setEditing(false);
            setSaved(true);
        } catch (err) {
            setError(isAxiosError(err) && typeof err.response?.data?.error === "string"
                ? err.response.data.error : "Unable to save education. Please try again.");
        } finally { setSaving(false); }
    }

    return <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="mb-5 flex items-center justify-between gap-3">
            <h2 className="text-base font-semibold text-gray-900">Education</h2>
            {!editing && <button type="button" onClick={startEditing} className="rounded-lg px-3 py-1.5 text-sm font-medium text-blue-600 hover:bg-blue-50">Edit education</button>}
        </div>
        {error && <p role="alert" className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}
        {saved && !editing && <p role="status" className="mb-4 text-sm text-green-700">Education updated.</p>}
        {editing ? <form onSubmit={save}>
            <fieldset disabled={saving} className="space-y-4 disabled:opacity-60">
                {draft.map((item, index) => <div key={index} className="rounded-xl border border-gray-200 p-4">
                    <div className="mb-3 flex items-center justify-between gap-3">
                        <h3 className="text-sm font-medium text-gray-700">Education {index + 1}</h3>
                        <button type="button" onClick={() => setDraft(previous => previous.filter((_, i) => i !== index))}
                            aria-label={`Remove education ${index + 1}`} className="text-xs text-red-600 hover:text-red-800">Remove</button>
                    </div>
                    <div className="grid gap-3 sm:grid-cols-2">
                        {fields.map(({ key, label, placeholder }) => <label key={key} className="block text-xs text-gray-500">
                            {label}
                            <input value={item[key] || ""} placeholder={placeholder}
                                onChange={event => setDraft(previous => previous.map((entry, i) => i === index ? { ...entry, [key]: event.target.value } : entry))}
                                className="mt-1 w-full rounded-lg border border-gray-200 bg-white p-2.5 text-sm text-gray-800 outline-none focus:ring-2 focus:ring-blue-200" />
                        </label>)}
                    </div>
                </div>)}
                {draft.length === 0 && <p className="text-sm text-gray-400">No education entries. Save to remove the existing education.</p>}
                <button type="button" onClick={() => setDraft(previous => [...previous, emptyEducation()])}
                    className="rounded-lg border border-blue-200 px-3 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50">+ Add education</button>
                <div className="flex items-center gap-3 border-t border-gray-100 pt-4">
                    <button type="submit" className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">{saving ? "Saving..." : "Save changes"}</button>
                    <button type="button" onClick={() => { setEditing(false); setError(""); }} className="rounded-lg px-3 py-2 text-sm text-gray-500 hover:bg-gray-50">Cancel</button>
                </div>
            </fieldset>
        </form> : candidate.education?.length ? <div className="space-y-6">
            {candidate.education.map((item, index) => <div key={index} className="relative pl-8">
                {index !== candidate.education!.length - 1 && <div className="absolute left-[7px] top-4 bottom-[-24px] w-[2px] bg-blue-100" />}
                <div className="absolute left-0 top-2 h-4 w-4 rounded-full border-4 border-blue-100 bg-blue-600" />
                <h3 className="break-words text-sm font-semibold text-gray-900">{item.degree || "Degree not provided"}</h3>
                <p className="mt-1 break-words text-sm text-gray-600">{item.institution || "Institution not provided"}</p>
                {item.field && <p className="mt-1 break-words text-sm text-gray-500">{item.field}</p>}
                {item.year && <span className="mt-3 inline-flex rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-600">{item.year}</span>}
            </div>)}
        </div> : <p className="text-sm text-gray-400">No education available. Use Edit education to add an entry.</p>}
    </section>;
}

export default EducationSection;
