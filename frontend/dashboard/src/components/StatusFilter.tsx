import { useEffect, useRef } from "react";
import { CANDIDATE_STATUSES } from "../../../../shared-contracts/status";

function StatusFilter({ selected, onChange }: { selected: string[]; onChange: (statuses: string[]) => void }) {
    const ref = useRef<HTMLDetailsElement>(null);
    const label = selected.length === 0 ? "Status: All"
        : `Status: ${selected.join(", ")}`;

    useEffect(() => {
        function closeOutside(event: PointerEvent) {
            if (ref.current && !ref.current.contains(event.target as Node)) ref.current.open = false;
        }
        function closeOnEscape(event: KeyboardEvent) {
            if (event.key === "Escape" && ref.current?.open) {
                ref.current.open = false;
                ref.current.querySelector("summary")?.focus();
            }
        }
        document.addEventListener("pointerdown", closeOutside);
        document.addEventListener("keydown", closeOnEscape);
        return () => {
            document.removeEventListener("pointerdown", closeOutside);
            document.removeEventListener("keydown", closeOnEscape);
        };
    }, []);

    return <details ref={ref} className="relative w-full md:w-56">
        <summary aria-label="Filter by status" title={label}
            className="flex h-10 cursor-pointer list-none items-center justify-between gap-2 rounded-lg border border-gray-200 bg-white px-4 text-sm text-gray-700 outline-none focus-visible:ring-2 focus-visible:ring-blue-200 [&::-webkit-details-marker]:hidden">
            <span className="truncate">{label}</span>
            <span aria-hidden="true" className="shrink-0 text-xs text-gray-400">▾</span>
        </summary>
        <div className="absolute left-0 top-full z-30 mt-2 w-full min-w-56 rounded-xl border border-gray-200 bg-white p-2 shadow-lg">
            <div className="mb-1 flex items-center justify-between gap-2 px-2 py-1.5">
                <span className="text-xs font-medium text-gray-500">Select statuses</span>
                {selected.length > 0 && <button type="button" onClick={() => onChange([])}
                    className="text-xs font-medium text-blue-600 hover:text-blue-800">Clear</button>}
            </div>
            <div role="group" aria-label="Candidate statuses" className="max-h-72 overflow-y-auto">
                <label className="flex cursor-pointer items-center gap-3 rounded-lg px-2 py-2 text-sm text-gray-700 hover:bg-gray-50">
                    <input type="checkbox" checked={selected.length === 0} onChange={() => onChange([])} className="h-4 w-4 accent-blue-600" />
                    All statuses
                </label>
                <div className="my-1 border-t border-gray-100" />
                {CANDIDATE_STATUSES.filter(status => status !== "Review" && status !== "Needs information" && status !== "Archived").map(status => <label key={status}
                    className="flex cursor-pointer items-center gap-3 rounded-lg px-2 py-2 text-sm text-gray-700 hover:bg-blue-50">
                    <input type="checkbox" checked={selected.includes(status)}
                        onChange={() => onChange(selected.includes(status) ? selected.filter(value => value !== status) : [...selected, status])}
                        className="h-4 w-4 accent-blue-600" />
                    {status}
                </label>)}
            </div>
            <p aria-live="polite" className="px-2 pb-1 pt-2 text-xs text-gray-400">
                {selected.length === 0 ? "Showing all statuses" : `${selected.length} status${selected.length === 1 ? "" : "es"} selected`}
            </p>
        </div>
    </details>;
}

export default StatusFilter;
