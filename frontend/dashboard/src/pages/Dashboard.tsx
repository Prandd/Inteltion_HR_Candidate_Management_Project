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

    const [sortBy,setSortBy] = useState("latest");

    const [view,setView] = useState<"board"|"table">("board");


    const columns = [
        {
            name:"New",
            color:"blue" as const
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

        fetchCandidates();

    },[]);



    useEffect(()=>{

        const timer = setTimeout(()=>{

            setDebouncedSearch(search);

        },500);


        return ()=>clearTimeout(timer);

    },[search]);



    async function fetchCandidates(){

        try{

            const response = await api.get(
                "/candidates"
            );


            setCandidates(

                Array.isArray(response.data.data)

                ?

                response.data.data

                :

                []

            );


        }
        catch(error){

            console.error(
                "Failed to fetch candidates",
                error
            );

        }
        finally{

            setLoading(false);

        }

    }



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
                        px-5
                        py-2.5
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
                grid-cols-6
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
                    title="Failed"
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
                            w-64
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
                            w-64
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
                            w-56
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
                        ml-auto
                        flex
                        gap-2
                    ">

                        <button
                            onClick={()=>
                                setView("board")
                            }
                            className="
                                h-10
                                px-5
                                bg-blue-600
                                hover:bg-blue-700
                                text-white
                                rounded-lg
                                text-sm
                                font-medium
                            "
                        >
                            Board
                        </button>


                        <button
                            onClick={()=>
                                setView("table")
                            }
                            className="
                                h-10
                                px-5
                                bg-white
                                border
                                border-gray-200
                                rounded-lg
                                text-sm
                                font-medium
                            "
                        >
                            Table
                        </button>

                    </div>


                </div>


            </div>

                {/* BOARD VIEW */}

            {
                view === "board" &&

                <div className="
                    grid
                    grid-cols-5
                    gap-5
                ">

                    {
                        columns.map(({name,color})=>(

                            <PipelineColumn
                                key={name}
                                name={
                                    name === "Rejected"
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

                            </PipelineColumn>

                        ))
                    }

                </div>
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

                    <table className="
                        w-full
                        text-sm
                    ">

                        <thead className="
                            bg-gray-50
                        ">

                            <tr>

                                <th className="
                                    text-left
                                    px-5
                                    py-3
                                    text-gray-500
                                ">
                                    Candidate
                                </th>


                                <th className="
                                    text-left
                                    px-5
                                    py-3
                                    text-gray-500
                                ">
                                    Position
                                </th>


                                <th className="
                                    text-left
                                    px-5
                                    py-3
                                    text-gray-500
                                ">
                                    Experience
                                </th>


                                <th className="
                                    text-left
                                    px-5
                                    py-3
                                    text-gray-500
                                ">
                                    Status
                                </th>

                            </tr>

                        </thead>




                        <tbody>

                            {
                                sortedCandidates.map(candidate=>(

                                    <tr
                                        key={
                                            candidate.candidate_id
                                        }
                                        className="
                                            border-t
                                            hover:bg-gray-50
                                            cursor-pointer
                                        "
                                        onClick={()=>navigate(
                                            `/candidate/${candidate.candidate_id}`
                                        )}
                                    >

                                        <td className="
                                            px-5
                                            py-4
                                        ">

                                            <p className="
                                                font-medium
                                                text-gray-900
                                            ">
                                                {
                                                    candidate.full_name
                                                }
                                            </p>

                                            <p className="
                                                text-xs
                                                text-gray-400
                                            ">
                                                {
                                                    candidate.email
                                                }
                                            </p>

                                        </td>



                                        <td className="
                                            px-5
                                            py-4
                                        ">
                                            {
                                                candidate.applied_position
                                                ||
                                                "-"
                                            }
                                        </td>



                                        <td className="
                                            px-5
                                            py-4
                                        ">
                                            {
                                                candidate.experience_total
                                                ||
                                                0
                                            }
                                            {" "}years
                                        </td>



                                        <td className="
                                            px-5
                                            py-4
                                        ">
                                            {
                                                candidate.status
                                                ||
                                                "New"
                                            }
                                        </td>


                                    </tr>

                                ))
                            }

                        </tbody>


                    </table>


                </div>

            }



        </div>

    );

}


export default Dashboard;