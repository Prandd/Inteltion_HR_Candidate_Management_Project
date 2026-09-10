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





    const [
        candidates,
        setCandidates
    ] = useState<CandidateSummary[]>([]);



    const [
        loading,
        setLoading
    ] = useState(true);



    const [
        search,
        setSearch
    ] = useState("");



    const [
        status,
        setStatus
    ] = useState("All");



    const [
        experience,
        setExperience
    ] = useState("All");



    const [
        position,
        setPosition
    ] = useState("All");



    const [
        view,
        setView
    ] = useState<"board"|"table">("board");






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








    async function fetchCandidates(){


        try{


            const response =
                await api.get(
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

            console.error(error);

        }


        finally{

            setLoading(false);

        }


    }









    function getCandidates(status:string){


        return candidates.filter(

            candidate=>

            (

                candidate.status || "New"

            )

            ===

            status

        );


    }









    const filteredCandidates =

        candidates.filter(candidate=>{


            const keyword =
                search.toLowerCase();



            const matchSearch =


                keyword === ""

                ||

                candidate.full_name
                ?.toLowerCase()
                .includes(keyword)

                ||

                candidate.email
                ?.toLowerCase()
                .includes(keyword);



            const matchStatus =


                status==="All"

                ||

                candidate.status===status;



            const years =
                candidate.experience_total ?? 0;



            const matchExperience =


                experience==="All"

                ||

                (
                    experience==="0-2"
                    &&
                    years<=2
                )

                ||

                (
                    experience==="3-5"
                    &&
                    years>=3
                    &&
                    years<=5
                )

                ||

                (
                    experience==="5+"
                    &&
                    years>5
                );



            const matchPosition =


                position==="All"

                ||

                candidate.applied_position===position;



            return (

                matchSearch

                &&

                matchStatus

                &&

                matchExperience

                &&

                matchPosition

            );


        });








    const positions = [

        "All",

        ...

        Array.from(

            new Set(

                candidates.map(

                    c=>c.applied_position

                )

            )

        )

    ];









    if(loading){

        return (

            <div className="p-10">

                Loading dashboard...

            </div>

        );

    }









    return (


        <div

            className="
            min-h-screen
            bg-[#f5f7ff]
            p-6
            "

        >






            <div

                className="
                flex
                justify-between
                mb-6
                "

            >



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
                    text-white
                    px-5
                    py-2
                    rounded-xl
                    "

                >

                    + Upload CV

                </button>



            </div>









            <div

                className="
                grid
                grid-cols-6
                gap-4
                mb-6
                "

            >


                <PipelineStatCard
                    title="All Candidates"
                    value={candidates.length}
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









            <div

                className="
                bg-white
                border
                rounded-2xl
                p-5
                mb-6
                "

            >


                <input

                    value={search}

                    onChange={
                        e=>setSearch(e.target.value)
                    }

                    placeholder="
                    Search candidate name, email, skill...
                    "

                    className="
                    w-full
                    border
                    rounded-xl
                    px-4
                    py-3
                    mb-4
                    "

                />



                <div className="
                flex
                gap-3
                ">


                    <select

                        value={status}

                        onChange={
                            e=>setStatus(e.target.value)
                        }

                        className="
                        border
                        rounded-lg
                        px-3
                        py-2
                        "

                    >

                        <option>All</option>
                        <option>New</option>
                        <option>Assessment</option>
                        <option>Interview</option>
                        <option>Hired</option>
                        <option>Rejected</option>

                    </select>





                    <select

                        value={experience}

                        onChange={
                            e=>setExperience(e.target.value)
                        }

                        className="
                        border
                        rounded-lg
                        px-3
                        py-2
                        "

                    >

                        <option>All</option>
                        <option>0-2</option>
                        <option>3-5</option>
                        <option>5+</option>


                    </select>






                    <select

                        value={position}

                        onChange={
                            e=>setPosition(e.target.value)
                        }

                        className="
                        border
                        rounded-lg
                        px-3
                        py-2
                        "

                    >

                        {
                            positions.map(pos=>(

                                <option key={pos}>
                                    {pos==="All"
                                    ?
                                    "All Positions"
                                    :
                                    pos}
                                </option>

                            ))
                        }

                    </select>





                    <div className="ml-auto flex gap-2">


                        <button

                            onClick={()=>setView("board")}

                            className="
                            bg-blue-600
                            text-white
                            px-4
                            py-2
                            rounded-lg
                            "

                        >

                            Board

                        </button>



                        <button

                            onClick={()=>setView("table")}

                            className="
                            border
                            px-4
                            py-2
                            rounded-lg
                            "

                        >

                            Table

                        </button>


                    </div>



                </div>



            </div>









            {
            view==="board"

            &&


            <div

                className="
                grid
                grid-cols-5
                gap-5
                "

            >


                {

                    columns.map(({name,color})=>(


                        <PipelineColumn

                            key={name}

                            name={
                                name==="Rejected"
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

                                filteredCandidates

                                .filter(
                                    c=>
                                    (
                                        c.status || "New"
                                    )===name
                                )

                                .map(candidate=>(


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




        </div>


    );


}



export default Dashboard;