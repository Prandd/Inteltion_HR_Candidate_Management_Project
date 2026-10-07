import {
    useEffect,
    useState
} from "react";

import {
    useNavigate
} from "react-router-dom";

import api from "../api/axios";

import PipelineStatCard from "../components/PipelineStatCard";
import PipelineColumn from "../components/PipelineColumn";
import PipelineCandidateCard from "../components/PipelineCandidateCard";
import { formatStatusLabel } from "../utils/status";

import type {
    CandidateSummary
} from "../types/candidate";


function Dashboard(){

    const navigate = useNavigate();

    const [candidates,setCandidates] = useState<CandidateSummary[]>([]);
    const [loading,setLoading] = useState(true);

    const [search,setSearch] = useState("");
    const [debouncedSearch,setDebouncedSearch] = useState("");

    const [experience,setExperience] = useState<number | "">("");
    const [position,setPosition] = useState("All");
    const [owner,setOwner] = useState("all");

    const [sortBy,setSortBy] = useState("latest");

    const [view,setView] = useState<"board"|"table">("board");
    const [tablePage,setTablePage] = useState(1);
    const [selectedCandidateIds,setSelectedCandidateIds] = useState<Set<string>>(new Set());


    const columns = [
        {
            name:"New",
            color:"blue" as const
        },
        {
            name:"CV passed",
            color:"cyan" as const
        },
        {
            name:"Assessment",
            color:"orange" as const
        },
        {
            name:"Interview",
            color:"purple" as const
        },
        {
            name:"Hired",
            color:"green" as const
        },
        {
            name:"Rejected",
            color:"red" as const
        }
    ];



    useEffect(()=>{

        const timer = setTimeout(()=>{

            setDebouncedSearch(search);

        },500);


        return ()=>clearTimeout(timer);

    },[search]);



    useEffect(()=>{
        let cancelled = false;

        async function loadCandidates(){
            try{
                const response = await api.get("/candidates");
                if(!cancelled){
                    setCandidates(
                        Array.isArray(response.data.data)
                            ? response.data.data
                            : []
                    );
                }
            }
            catch(error){
                console.error("Failed to fetch candidates", error);
            }
            finally{
                if(!cancelled){
                    setLoading(false);
                }
            }
        }

        void loadCandidates();
        return ()=>{
            cancelled = true;
        };
    },[]);



    const filteredCandidates = candidates.filter(candidate=>{

        const keyword = debouncedSearch
            .toLowerCase()
            .trim();


        const skillMatch =
            candidate.top_skills?.some(skill=>
                skill.toLowerCase().includes(keyword)
            );


        const matchSearch =

            keyword === ""

            ||

            candidate.full_name
            ?.toLowerCase()
            .includes(keyword)

            ||

            candidate.email
            ?.toLowerCase()
            .includes(keyword)

            ||

            skillMatch;



        const years =
            candidate.experience_total ?? 0;



        const matchExperience =

            experience === ""

            ||

            years >= experience;



        const matchPosition =

            position === "All"

            ||

            candidate.applied_position === position;



        return (

            matchSearch

            &&

            matchExperience

            &&

            matchPosition

            &&

            (owner === "all" || (owner === "unassigned"
                ? !candidate.owner_account_id
                : candidate.owner_account_id === owner))

        );


    });



    const sortedCandidates = [...filteredCandidates].sort((a,b)=>{


        if(sortBy==="latest"){

            return (

                new Date(b.created_at ?? 0).getTime()

                -

                new Date(a.created_at ?? 0).getTime()

            );

        }



        if(sortBy==="oldest"){

            return (

                new Date(a.created_at ?? 0).getTime()

                -

                new Date(b.created_at ?? 0).getTime()

            );

        }



        if(sortBy==="name_asc"){

            return (

                a.full_name || ""

            ).localeCompare(

                b.full_name || ""

            );

        }



        if(sortBy==="name_desc"){

            return (

                b.full_name || ""

            ).localeCompare(

                a.full_name || ""

            );

        }



        return 0;


    });

    const tablePageSize = 10;
    const tablePageCount = Math.max(1, Math.ceil(sortedCandidates.length / tablePageSize));
    const currentTablePage = Math.min(tablePage, tablePageCount);
    const pageCandidates = sortedCandidates.slice(
        (currentTablePage - 1) * tablePageSize,
        currentTablePage * tablePageSize
    );

    function toggleCandidateSelection(candidateId:string){
        setSelectedCandidateIds(current=>{
            const next = new Set(current);
            if(next.has(candidateId)) next.delete(candidateId);
            else next.add(candidateId);
            return next;
        });
    }

    function togglePageSelection(){
        setSelectedCandidateIds(current=>{
            const next = new Set(current);
            const allSelected = pageCandidates.length > 0
                && pageCandidates.every(candidate=>next.has(candidate.candidate_id));
            pageCandidates.forEach(candidate=>{
                if(allSelected) next.delete(candidate.candidate_id);
                else next.add(candidate.candidate_id);
            });
            return next;
        });
    }

    function statusBadgeClass(status:string){
        if(status === "Hired") return "bg-emerald-50 text-emerald-700";
        if(status === "Interview") return "bg-violet-50 text-violet-700";
        if(status === "CV rejected" || status === "Rejected") return "bg-rose-50 text-rose-700";
        if(status === "Assessment") return "bg-amber-50 text-amber-700";
        if(status === "CV passed") return "bg-cyan-50 text-cyan-700";
        return "bg-blue-50 text-blue-700";
    }

    function formatSubmittedDate(value?:string){
        if(!value) return "-";
        const date = new Date(value);
        if(Number.isNaN(date.getTime())) return "-";
        return new Intl.DateTimeFormat("en",{
            month:"short",
            day:"numeric",
            year:"numeric"
        }).format(date);
    }

    const hasCandidates =
    sortedCandidates.length > 0;



    function getCandidates(status:string){

        return sortedCandidates.filter(candidate=>

            (

                candidate.status || "New"

            )

            ===

            status

        );

    }



    const positions = [

        "All",

        ...

        Array.from(

            new Set(

                candidates

                .map(candidate=>

                    candidate.applied_position

                )

                .filter(Boolean)

            )

        )

    ];



    const owners = Array.from(new Map(
        candidates.filter(candidate => candidate.owner_account_id).map(candidate => [
            candidate.owner_account_id!,
            candidate.owner_name || candidate.owner_account_id!,
        ])
    ).entries()).sort((a, b) => a[1].localeCompare(b[1]));

    if(loading){

        return (

            <div className="p-10 text-gray-500">

                Loading dashboard...

            </div>

        );

    }

        return (

        <div className="
            min-h-screen
            bg-[#f7f9ff]
            p-6
        ">

            <div className="
                flex
                justify-between
                items-center
                mb-6
            ">

                <div>

                    <h1 className="
                        text-2xl
                        font-bold
                        text-gray-900
                    ">
                        Dashboard
                    </h1>

                    <p className="
                        text-sm
                        text-gray-500
                    ">
                        Manage your recruitment pipeline
                    </p>

                </div>


                <button
                    onClick={()=>navigate("/upload")}
                    className="
                        bg-blue-600
                        hover:bg-blue-700
                        text-white
                        px-4
                        md:px-5
                        py-2.5
                        text-sm
                        rounded-xl
                        font-medium
                    "
                >
                    + Upload CV
                </button>

            </div>





            {/* STAT CARDS */}

            <div className="
                grid
                grid-cols-2
                md:grid-cols-3
                xl:grid-cols-6
                gap-4
                mb-6
            ">

                <PipelineStatCard
                    title="All Candidates"
                    value={filteredCandidates.length}
                    color="blue"
                    icon="👥"
                />

                <PipelineStatCard
                    title="New"
                    value={getCandidates("New").length}
                    color="blue"
                    icon="＋"
                />

                <PipelineStatCard
                    title="Assessment"
                    value={getCandidates("Assessment").length}
                    color="orange"
                    icon="📝"
                />

                <PipelineStatCard
                    title="Interview"
                    value={getCandidates("Interview").length}
                    color="purple"
                    icon="💬"
                />

                <PipelineStatCard
                    title="Hired"
                    value={getCandidates("Hired").length}
                    color="green"
                    icon="✓"
                />

                <PipelineStatCard
                    title="Reject"
                    value={getCandidates("Rejected").length}
                    color="red"
                    icon="×"
                />

            </div>






            {/* FILTER AREA */}

            <div className="
                bg-white
                rounded-2xl
                p-5
                mb-6
                shadow-sm
            ">


                <input
                    value={search}
                    onChange={e=>
                        setSearch(
                            e.target.value
                        )
                    }
                    placeholder="Search candidate name, email, skill..."
                    className="
                        w-full
                        h-10
                        bg-white
                        border
                        border-gray-200
                        rounded-lg
                        px-4
                        text-sm
                        text-gray-700
                        placeholder:text-gray-400
                        outline-none
                        focus:ring-2
                        focus:ring-blue-100
                        mb-4
                    "
                />




                <div className="
                    flex
                    flex-wrap
                    items-center
                    gap-3
                ">



                    {/* EXPERIENCE */}

                    <input
                        type="number"
                        min="0"
                        step="0.5"
                        value={experience}
                        onChange={e=>
                            setExperience(
                                e.target.value === ""
                                ?
                                ""
                                :
                                Number(e.target.value)
                            )
                        }
                        placeholder="Min Experience (years)"
                        className="
                            h-10
                            w-full
                            md:w-64
                            bg-white
                            border
                            border-gray-200
                            rounded-lg
                            px-4
                            text-sm
                            text-gray-700
                            placeholder:text-gray-400
                            outline-none
                            focus:ring-2
                            focus:ring-blue-100
                        "
                    />





                    {/* OWNER */}

                    <select
                        aria-label="Filter by owner"
                        value={owner}
                        onChange={event => {
                            setOwner(event.target.value);
                            setTablePage(1);
                            setSelectedCandidateIds(new Set());
                        }}
                        className="h-10 w-full md:w-56 bg-white border border-gray-200 rounded-lg px-4 text-sm text-gray-700 outline-none focus:ring-2 focus:ring-blue-100"
                    >
                        <option value="all">Owner: All</option>
                        {owners.map(([accountId, name]) => (
                            <option key={accountId} value={accountId}>Owner: {name}</option>
                        ))}
                        {candidates.some(candidate => !candidate.owner_account_id) && (
                            <option value="unassigned">Owner: Unassigned</option>
                        )}
                    </select>

                    {/* POSITION */}

                    <select
                        value={position}
                        onChange={e=>
                            setPosition(
                                e.target.value
                            )
                        }
                        className="
                            h-10
                            w-full
                            md:w-64
                            bg-white
                            border
                            border-gray-200
                            rounded-lg
                            px-4
                            text-sm
                            text-gray-700
                            outline-none
                            appearance-none
                            focus:ring-2
                            focus:ring-blue-100
                        "
                    >

                        {
                            positions.map(pos=>(

                                <option
                                    key={pos}
                                    value={pos}
                                >

                                    {
                                        pos === "All"
                                        ?
                                        "Position: All"
                                        :
                                        `Position: ${pos}`
                                    }

                                </option>

                            ))
                        }

                    </select>





                    {/* SORT */}

                    <select
                        value={sortBy}
                        onChange={e=>
                            setSortBy(
                                e.target.value
                            )
                        }
                        className="
                            h-10
                            w-full
                            md:w-56
                            bg-white
                            border
                            border-gray-200
                            rounded-lg
                            px-4
                            text-sm
                            text-gray-700
                            outline-none
                            appearance-none
                            focus:ring-2
                            focus:ring-blue-100
                        "
                    >

                        <option value="latest">
                            Sort: Latest Import
                        </option>

                        <option value="oldest">
                            Sort: Oldest Import
                        </option>

                        <option value="name_asc">
                            Sort: Name A-Z
                        </option>

                        <option value="name_desc">
                            Sort: Name Z-A
                        </option>

                    </select>





                    {/* VIEW */}

                    <div className="
                        flex
                        gap-2
                        w-full
                        md:w-auto
                        md:ml-auto
                    ">

                        <button
                            onClick={()=>
                                setView("board")
                            }
                            aria-pressed={view === "board"}
                            className={`
                                h-10 px-5 rounded-lg text-sm font-medium transition-colors
                                ${view === "board"
                                    ? "bg-blue-600 text-white hover:bg-blue-700"
                                    : "border border-gray-200 bg-white text-gray-700 hover:bg-gray-50"}
                            `}
                        >
                            Board
                        </button>


                        <button
                            onClick={()=>
                                setView("table")
                            }
                            aria-pressed={view === "table"}
                            className={`
                                h-10 px-5 rounded-lg text-sm font-medium transition-colors
                                ${view === "table"
                                    ? "bg-blue-600 text-white hover:bg-blue-700"
                                    : "border border-gray-200 bg-white text-gray-700 hover:bg-gray-50"}
                            `}
                        >
                            Table
                        </button>

                    </div>


                </div>


            </div>

            {/* BOARD VIEW */}

{
    view === "board" &&

    (
        hasCandidates

        ?

        <div className="
            grid
            grid-cols-1
            md:grid-cols-2
            xl:grid-cols-6
            gap-5
        ">

            {
                columns.map(({name,color})=>(

                    <PipelineColumn
                        key={name}
                        name={
                            name === "CV rejected"
                            ?
                            "Failed / Rejected"
                            :
                            name
                        }
                        count={
                            getCandidates(name).length
                        }
                        color={color}
                    >

                        <div
                            className="
                            space-y-3
                            min-w-0
                            w-full
                            "
                        >

                            {
                                getCandidates(name).map(candidate=>(

                                    <PipelineCandidateCard
                                        key={
                                            candidate.candidate_id
                                        }
                                        candidate={candidate}
                                    />

                                ))
                            }

                        </div>


                    </PipelineColumn>

                ))
            }

        </div>


        :


        <div

            className="
            bg-white
            rounded-2xl
            p-10
            text-center
            text-gray-400
            "

        >

            No candidates found

        </div>
    )
}




            {/* TABLE VIEW */}

            {
                view === "table" &&

                <div className="
                    bg-white
                    rounded-2xl
                    shadow-sm
                    overflow-hidden
                ">

                    <div className="overflow-x-auto">

                    <table className="w-full min-w-[980px] text-sm">
                        <thead className="border-b border-gray-200 bg-gray-50/80">
                            <tr className="text-[11px] font-semibold uppercase tracking-wide text-gray-500">
                                <th className="w-12 px-4 py-3 text-left">
                                    <input
                                        type="checkbox"
                                        aria-label="Select candidates on this page"
                                        checked={pageCandidates.length > 0 && pageCandidates.every(candidate=>selectedCandidateIds.has(candidate.candidate_id))}
                                        onChange={togglePageSelection}
                                        className="h-4 w-4 rounded border-gray-300 accent-blue-600"
                                    />
                                </th>
                                <th className="px-3 py-3 text-left">Candidate</th>
                                <th className="px-3 py-3 text-left">Position</th>
                                <th className="px-3 py-3 text-left">Experience</th>
                                <th className="px-3 py-3 text-left">SQL test</th>
                                <th className="px-3 py-3 text-left">Stage &amp; status</th>
                                <th className="px-3 py-3 text-left">Submitted</th>
                                <th className="px-4 py-3 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {pageCandidates.length === 0 ? (
                                <tr>
                                    <td colSpan={8} className="px-6 py-14 text-center text-sm text-gray-400">
                                        No candidates found
                                    </td>
                                </tr>
                            ) : pageCandidates.map(candidate=>{
                                const initials = (candidate.full_name || "?")
                                    .split(/\s+/)
                                    .filter(Boolean)
                                    .slice(0,2)
                                    .map(part=>part[0])
                                    .join("")
                                    .toUpperCase();
                                const status = candidate.status || "New";

                                return (
                                    <tr
                                        key={candidate.candidate_id}
                                        className="group transition-colors hover:bg-blue-50/30"
                                    >
                                        <td className="px-4 py-3.5">
                                            <input
                                                type="checkbox"
                                                aria-label={`Select ${candidate.full_name || "candidate"}`}
                                                checked={selectedCandidateIds.has(candidate.candidate_id)}
                                                onChange={()=>toggleCandidateSelection(candidate.candidate_id)}
                                                className="h-4 w-4 rounded border-gray-300 accent-blue-600"
                                            />
                                        </td>
                                        <td className="px-3 py-3.5">
                                            <div className="flex min-w-0 items-center gap-3">
                                                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-blue-50 text-xs font-semibold text-blue-700">
                                                    {initials || "?"}
                                                </div>
                                                <div className="min-w-0">
                                                    <p className="truncate font-semibold text-gray-800">
                                                        {candidate.full_name || "Unknown Candidate"}
                                                    </p>
                                                    <p className="mt-0.5 truncate text-xs text-gray-400">
                                                        {candidate.email || "No email provided"}
                                                    </p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-3 py-3.5">
                                            <span className="inline-flex max-w-40 truncate rounded-md bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">
                                                {candidate.applied_position || "Unassigned"}
                                            </span>
                                        </td>
                                        <td className="whitespace-nowrap px-3 py-3.5 text-sm text-gray-600">
                                            {candidate.experience_total ?? 0} yrs
                                        </td>
                                        <td className="px-3 py-3.5">
                                            {candidate.sql_test_score != null ? (
                                                <span className={`inline-flex rounded-md px-2 py-1 text-xs font-medium ${candidate.sql_test_score >= 80 ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>
                                                    {candidate.sql_test_score}%
                                                </span>
                                            ) : (
                                                <span className="text-xs text-gray-400">-</span>
                                            )}
                                        </td>
                                        <td className="px-3 py-3.5">
                                            <span className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-medium ${statusBadgeClass(status)}`}>
                                                <span className="h-1.5 w-1.5 rounded-full bg-current" />
                                                {formatStatusLabel(status)}
                                            </span>
                                        </td>
                                        <td className="whitespace-nowrap px-3 py-3.5 text-xs text-gray-500">
                                            {formatSubmittedDate(candidate.created_at)}
                                        </td>
                                        <td className="px-4 py-3.5 text-right">
                                            <button
                                                type="button"
                                                onClick={()=>navigate(`/candidate/${candidate.candidate_id}`)}
                                                className="inline-flex items-center gap-2 rounded-md px-2.5 py-1.5 text-xs font-semibold text-blue-700 transition-colors hover:bg-blue-50"
                                            >
                                                View profile
                                                <span aria-hidden="true">→</span>
                                            </button>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>

                    <div className="flex flex-col gap-3 border-t border-gray-100 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
                        <p className="text-xs text-gray-500">
                            Showing {sortedCandidates.length === 0 ? 0 : (currentTablePage - 1) * tablePageSize + 1} to {Math.min(currentTablePage * tablePageSize, sortedCandidates.length)} of {sortedCandidates.length} candidates
                            {selectedCandidateIds.size > 0 && ` · ${selectedCandidateIds.size} selected`}
                        </p>
                        <div className="flex items-center gap-1.5 self-end sm:self-auto">
                            <button
                                type="button"
                                disabled={currentTablePage === 1}
                                onClick={()=>setTablePage(page=>Math.max(1, page - 1))}
                                className="rounded-md border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
                            >
                                Previous
                            </button>
                            {Array.from({length:tablePageCount},(_,index)=>index + 1).map(page=>(
                                <button
                                    key={page}
                                    type="button"
                                    aria-current={currentTablePage === page ? "page" : undefined}
                                    onClick={()=>setTablePage(page)}
                                    className={`h-8 min-w-8 rounded-md px-2 text-xs font-medium ${currentTablePage === page ? "bg-blue-600 text-white" : "text-gray-600 hover:bg-gray-100"}`}
                                >
                                    {page}
                                </button>
                            ))}
                            <button
                                type="button"
                                disabled={currentTablePage === tablePageCount}
                                onClick={()=>setTablePage(page=>Math.min(tablePageCount, page + 1))}
                                className="rounded-md border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
                            >
                                Next
                            </button>
                        </div>
                    </div>

                     </div>
                </div>

            }



        </div>

    );

}


export default Dashboard;
