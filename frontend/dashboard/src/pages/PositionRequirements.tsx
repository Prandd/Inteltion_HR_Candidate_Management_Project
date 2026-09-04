import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";

interface ToolRequirement {
    name: string;
    weight: number;
    experience: number;
    recency: number;
}

interface SkillDomain {
    id: number;
    name: string;
    tools: ToolRequirement[];
}

const createTool = (): ToolRequirement => ({
    name: "",
    weight: 3,
    experience: 1,
    recency: 1
});

function PositionRequirements() {
    const navigate = useNavigate();
    const [title, setTitle] = useState("");
    const [department, setDepartment] = useState("Data Science & AI");
    const [description, setDescription] = useState("");
    const [domains, setDomains] = useState<SkillDomain[]>([
        { id: 1, name: "Programming", tools: [{ name: "Python", weight: 5, experience: 3, recency: 1 }] },
        { id: 2, name: "Machine Learning", tools: [{ name: "TensorFlow", weight: 4, experience: 2, recency: 2 }] },
        { id: 3, name: "Data Visualization", tools: [{ name: "Tableau", weight: 3, experience: 1, recency: 1 }] }
    ]);

    function updateDomain(domainId: number, name: string) {
        setDomains(current => current.map(domain => (
            domain.id === domainId ? { ...domain, name } : domain
        )));
    }

    function updateTool(domainId: number, toolIndex: number, changes: Partial<ToolRequirement>) {
        setDomains(current => current.map(domain => {
            if (domain.id !== domainId) {
                return domain;
            }
            return {
                ...domain,
                tools: domain.tools.map((tool, index) => (
                    index === toolIndex ? { ...tool, ...changes } : tool
                ))
            };
        }));
    }

    function addDomain() {
        setDomains(current => [...current, {
            id: Date.now(),
            name: "New Skill Domain",
            tools: [createTool()]
        }]);
    }

    function addTool(domainId: number) {
        setDomains(current => current.map(domain => (
            domain.id === domainId
                ? { ...domain, tools: [...domain.tools, createTool()] }
                : domain
        )));
    }

    function removeDomain(domainId: number) {
        setDomains(current => current.filter(domain => domain.id !== domainId));
    }

    function publishPosition(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        if (!title.trim()) {
            return;
        }
        navigate("/positions");
    }

    return (
        <form onSubmit={publishPosition} className="min-h-screen bg-slate-50 px-5 py-7 sm:px-8 lg:px-10">
            <div className="mx-auto max-w-6xl">
                <div className="mb-7">
                    <p className="mb-2 text-sm font-semibold uppercase tracking-[0.18em] text-blue-600">Position setup</p>
                    <h1 className="text-3xl font-bold tracking-tight text-slate-900">Position Requirements</h1>
                </div>

                <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
                    <div className="mb-5 flex items-center gap-2 border-b border-slate-200 pb-4">
                        <span className="text-blue-700" aria-hidden="true">▣</span>
                        <h2 className="text-lg font-semibold text-slate-800">Position Overview</h2>
                    </div>
                    <div className="grid gap-5 md:grid-cols-2">
                        <label className="text-sm font-medium text-slate-700">
                            Job Title
                            <input
                                value={title}
                                onChange={event => setTitle(event.target.value)}
                                placeholder="e.g. Senior AI Engineer"
                                className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2.5 font-normal outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
                                required
                            />
                        </label>
                        <label className="text-sm font-medium text-slate-700">
                            Department
                            <select value={department} onChange={event => setDepartment(event.target.value)} className="mt-2 w-full rounded-md border border-slate-300 bg-white px-3 py-2.5 font-normal outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100">
                                <option>Data Science &amp; AI</option>
                                <option>Engineering</option>
                                <option>Product &amp; Design</option>
                                <option>Research</option>
                            </select>
                        </label>
                        <label className="text-sm font-medium text-slate-700 md:col-span-2">
                            Job Specifications / Description
                            <textarea
                                value={description}
                                onChange={event => setDescription(event.target.value)}
                                placeholder="Describe the role and primary responsibilities..."
                                rows={4}
                                className="mt-2 w-full resize-y rounded-md border border-slate-300 px-3 py-2.5 font-normal outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
                            />
                        </label>
                    </div>
                </section>

                <section className="mt-5 rounded-xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
                    <div className="mb-4 flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 pb-4">
                        <div className="flex items-center gap-2">
                            <span className="text-blue-700" aria-hidden="true">◉</span>
                            <h2 className="text-lg font-semibold text-slate-800">Skills &amp; Tools Matrix</h2>
                        </div>
                        <button type="button" onClick={addDomain} className="text-sm font-semibold text-blue-700 hover:text-blue-900">+ Add Skill Domain</button>
                    </div>

                    <div className="mb-5 rounded-md border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-slate-600">
                        <p className="font-semibold text-slate-700">ⓘ &nbsp;Skill Graph Integration Active</p>
                        <p>Weightings and recency requirements will be automatically calibrated against the Inteltion global talent graph to optimize candidate matching.</p>
                    </div>

                    <div className="space-y-4">
                        {domains.map(domain => (
                            <div key={domain.id} className="rounded-lg border border-slate-200 p-3 sm:p-4">
                                <div className="mb-3 flex items-center gap-2">
                                    <input value={domain.name} onChange={event => updateDomain(domain.id, event.target.value)} className="min-w-0 flex-1 border border-slate-300 px-2 py-1.5 text-lg font-semibold text-slate-700 outline-none focus:border-blue-600" aria-label="Skill domain name" />
                                    <button type="button" onClick={() => removeDomain(domain.id)} aria-label={`Delete ${domain.name}`} className="px-1 text-slate-400 hover:text-red-600">▥</button>
                                </div>
                                <div className="hidden grid-cols-[minmax(130px,1fr)_170px_170px_170px_20px] gap-2 bg-slate-50 px-2 py-2 text-xs font-medium text-slate-500 sm:grid">
                                    <span>Tool / Language</span><span>Weight (1-5)</span><span>Min. Exp (Yrs)</span><span>Recency (Yrs)</span><span />
                                </div>
                                {domain.tools.map((tool, index) => (
                                    <div key={`${domain.id}-${index}`} className="grid gap-3 border-b border-slate-200 py-3 last:border-b-0 sm:grid-cols-[minmax(130px,1fr)_170px_170px_170px_20px] sm:items-center sm:gap-2">
                                        <label className="text-xs text-slate-500 sm:text-sm"><span className="sm:hidden">Tool / Language</span><input value={tool.name} onChange={event => updateTool(domain.id, index, { name: event.target.value })} placeholder="e.g. Python" className="mt-1 w-full rounded border border-slate-300 px-2 py-1.5 text-sm text-slate-700 outline-none focus:border-blue-600" /></label>
                                        <Stepper label="Weight (1-5)" value={tool.weight} onChange={value => updateTool(domain.id, index, { weight: value })} min={1} max={5} />
                                        <Stepper label="Min. Exp (Yrs)" value={tool.experience} onChange={value => updateTool(domain.id, index, { experience: value })} min={0} max={20} />
                                        <Stepper label="Recency (Yrs)" value={tool.recency} onChange={value => updateTool(domain.id, index, { recency: value })} min={0} max={20} />
                                        <button type="button" onClick={() => setDomains(current => current.map(item => item.id === domain.id ? { ...item, tools: item.tools.filter((_, toolIndex) => toolIndex !== index) } : item))} aria-label="Delete tool" className="hidden text-slate-400 hover:text-red-600 sm:block">×</button>
                                    </div>
                                ))}
                                <button type="button" onClick={() => addTool(domain.id)} className="mt-2 text-xs font-semibold text-blue-700 hover:text-blue-900">+ Add Tool</button>
                            </div>
                        ))}
                    </div>
                </section>

                <div className="flex justify-end gap-3 py-6">
                    <button type="button" onClick={() => navigate("/positions")} className="rounded-md border border-slate-300 bg-white px-5 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50">Cancel</button>
                    <button type="submit" className="rounded-md bg-blue-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-800">Publish Position</button>
                </div>
            </div>
        </form>
    );
}

interface StepperProps {
    label: string;
    value: number;
    min: number;
    max: number;
    onChange: (value: number) => void;
}

function Stepper({ label, value, min, max, onChange }: StepperProps) {
    return (
        <label className="text-xs text-slate-500">
            <span>{label}</span>
            <span className="mt-1 flex w-fit items-center rounded border border-slate-300">
                <button type="button" onClick={() => onChange(Math.max(min, value - 1))} className="px-2 py-1 text-slate-500 hover:bg-slate-100" aria-label={`Decrease ${label}`}>-</button>
                <output className="min-w-8 border-x border-slate-300 px-2 py-1 text-center text-sm text-slate-700">{value}</output>
                <button type="button" onClick={() => onChange(Math.min(max, value + 1))} className="px-2 py-1 text-slate-500 hover:bg-slate-100" aria-label={`Increase ${label}`}>+</button>
            </span>
        </label>
    );
}

export default PositionRequirements;
