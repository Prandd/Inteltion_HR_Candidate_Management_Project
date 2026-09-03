import { useState } from "react";
import { useNavigate } from "react-router-dom";

type PositionStatus = "Open" | "Closed" | "Drafts";

interface Position {
    id: number;
    title: string;
    department: string;
    location: string;
    candidates: number;
    status: PositionStatus;
}

const initialPositions: Position[] = [
    {
        id: 1,
        title: "AI Engineer",
        department: "Data Science & Analytics",
        location: "San Francisco, CA",
        candidates: 12,
        status: "Open"
    },
    {
        id: 2,
        title: "Data Engineer",
        department: "Cloud Infrastructure",
        location: "Remote",
        candidates: 8,
        status: "Open"
    },
    {
        id: 3,
        title: "Sr. Cloud Architect",
        department: "Cloud Infrastructure",
        location: "New York, NY",
        candidates: 24,
        status: "Open"
    },
    {
        id: 4,
        title: "ML Intern",
        department: "Research",
        location: "Remote",
        candidates: 45,
        status: "Closed"
    }
];

const filters: Array<"All" | PositionStatus> = ["All", "Open", "Closed", "Drafts"];

function Positions() {
    const navigate = useNavigate();
    const positions = initialPositions;
    const [activeFilter, setActiveFilter] = useState<(typeof filters)[number]>("All");

    const visiblePositions = positions.filter(
        position => activeFilter === "All" || position.status === activeFilter
    );

    return (
        <div className="min-h-screen bg-slate-50 px-6 py-8 sm:px-9 lg:px-10">
            <div className="mx-auto max-w-6xl">
                <div className="mb-8 flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
                    <div>
                        <p className="mb-2 text-sm font-semibold uppercase tracking-[0.18em] text-blue-600">
                            Recruitment workspace
                        </p>
                        <h1 className="text-3xl font-bold tracking-tight text-slate-900">
                            Positions List
                        </h1>
                        <p className="mt-2 text-slate-500">
                            Manage current job openings and candidate pipelines.
                        </p>
                    </div>
                    <button
                        type="button"
                        onClick={() => navigate("/positions/new")}
                        className="rounded-lg bg-blue-700 px-5 py-3 font-semibold text-white shadow-sm transition hover:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                    >
                        <span aria-hidden="true" className="mr-2">+</span>
                        Create New Position
                    </button>
                </div>

                <div className="mb-7 flex flex-wrap items-center justify-between gap-4">
                    <div className="inline-flex rounded-lg border border-slate-200 bg-white p-1 shadow-sm" role="tablist" aria-label="Position filters">
                        {filters.map(filter => (
                            <button
                                key={filter}
                                type="button"
                                role="tab"
                                aria-selected={activeFilter === filter}
                                onClick={() => setActiveFilter(filter)}
                                className={`rounded-md px-4 py-2 text-sm font-medium transition ${
                                    activeFilter === filter
                                        ? "bg-blue-50 text-blue-700"
                                        : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"
                                }`}
                            >
                                {filter}
                            </button>
                        ))}
                    </div>
                    <p className="text-sm text-slate-500">
                        {visiblePositions.length} {visiblePositions.length === 1 ? "position" : "positions"}
                    </p>
                </div>

                {visiblePositions.length > 0 ? (
                    <div className="grid gap-5 md:grid-cols-2">
                        {visiblePositions.map(position => (
                            <article
                                key={position.id}
                                className={`rounded-xl border bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md ${
                                    position.status === "Closed" ? "border-slate-200 opacity-70" : "border-slate-200"
                                }`}
                            >
                                <div className="flex items-start justify-between gap-4">
                                    <span className={`rounded-full px-3 py-1 text-xs font-semibold ${
                                        position.status === "Open"
                                            ? "bg-sky-100 text-sky-700"
                                            : position.status === "Closed"
                                                ? "bg-slate-200 text-slate-500"
                                                : "bg-amber-100 text-amber-700"
                                    }`}>
                                        {position.status === "Closed" ? "⊘" : "⊙"} {position.status}
                                    </span>
                                    <button type="button" aria-label={`More options for ${position.title}`} className="text-xl leading-none text-slate-400 hover:text-slate-700">
                                        ⋮
                                    </button>
                                </div>
                                <h2 className="mt-5 text-xl font-semibold text-slate-800">{position.title}</h2>
                                <p className="mt-1 text-sm text-slate-500">
                                    {position.department} <span aria-hidden="true">•</span> {position.location}
                                </p>
                                <div className="my-5 border-t border-slate-200" />
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <span className="grid h-9 w-9 place-items-center rounded-full bg-blue-50 text-lg text-blue-700" aria-hidden="true">♟</span>
                                        <div>
                                            <p className="font-semibold text-slate-800">{position.candidates}</p>
                                            <p className="text-xs text-slate-500">Candidates</p>
                                        </div>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => navigate("/pipeline")}
                                        aria-label={`View candidates for ${position.title}`}
                                        className="grid h-9 w-9 place-items-center rounded-md border border-blue-200 text-lg text-blue-700 transition hover:bg-blue-50"
                                    >
                                        →
                                    </button>
                                </div>
                            </article>
                        ))}
                    </div>
                ) : (
                    <div className="rounded-xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center">
                        <h2 className="text-lg font-semibold text-slate-800">No positions found</h2>
                        <p className="mt-2 text-slate-500">Try another filter or create a new position.</p>
                    </div>
                )}
            </div>

        </div>
    );
}

export default Positions;
