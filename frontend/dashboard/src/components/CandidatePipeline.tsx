import {
    useEffect,
    useState
} from "react";


import {
    useNavigate
} from "react-router-dom";


import api from "../api/axios";


import PipelineColumn from "../components/PipelineColumn";

import PipelineCandidateCard from "../components/PipelineCandidateCard";


import type {
    CandidateSummary
} from "../types/candidate";







function CandidatePipeline(){



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
        filter,
        setFilter
    ] = useState("All");








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









    const filteredCandidates =

        candidates.filter(candidate=>{


            const keyword =
                search.toLowerCase();





            const name =
                candidate.full_name
                ?.toLowerCase() || "";



            const position =
                candidate.applied_position
                ?.toLowerCase() || "";





            const matchSearch =

                keyword === ""

                ||

                name.includes(keyword)

                ||

                position.includes(keyword);







            const matchFilter =

                filter === "All"

                ||

                candidate.status === filter;







            return (

                matchSearch

                &&

                matchFilter

            );


        });











    function getCandidates(status:string){


        return filteredCandidates.filter(

            candidate =>

            (
                candidate.status || "New"
            )

            ===

            status

        );


    }











    if(loading){


        return (

            <div className="p-10">

                Loading pipeline...

            </div>

        );

    }











    return (



        <div


            className="

            min-h-screen

            bg-[#f7f9ff]

            p-8

            "

        >







            {/* HEADER */}



            <div


                className="

                flex

                justify-between

                mb-6

                "

            >



                <div>


                    <h1


                        className="

                        text-3xl

                        font-bold

                        text-gray-900

                        "

                    >

                        Candidate Flow


                    </h1>




                    <p

                        className="

                        text-gray-500

                        mt-1

                        "

                    >

                        Manage candidate progress and pipeline status


                    </p>



                </div>







                <button


                    onClick={()=>navigate("/upload")}


                    className="

                    bg-blue-600

                    text-white

                    px-6

                    py-3

                    rounded-xl

                    "

                >

                    Upload CV


                </button>



            </div>













            {/* FILTER BAR */}



            <div


                className="

                bg-white

                border

                rounded-2xl

                p-4

                mb-6

                "

            >




                <input


                    value={search}


                    onChange={

                        e=>

                        setSearch(
                            e.target.value
                        )

                    }


                    placeholder="Search candidate name, email, or skill..."


                    className="

                    w-full

                    border

                    rounded-xl

                    px-4

                    py-3

                    mb-4

                    "

                />








                <div

                    className="

                    flex

                    gap-4

                    "

                >



                    <select


                        value={filter}


                        onChange={

                            e=>

                            setFilter(
                                e.target.value
                            )

                        }


                        className="

                        border

                        rounded-lg

                        px-4

                        py-2

                        "

                    >


                        <option>
                            All
                        </option>


                        <option>
                            New
                        </option>


                        <option>
                            Assessment
                        </option>


                        <option>
                            Interview
                        </option>


                        <option>
                            Hired
                        </option>


                        <option>
                            Rejected
                        </option>


                    </select>



                </div>



            </div>









            {/* BOARD */}




            <div


                className="

                grid

                grid-cols-5

                gap-5

                "

            >






                <PipelineColumn

                    name="New"

                    count={
                        getCandidates("New").length
                    }

                    color="blue"

                >

                    {

                    getCandidates("New")

                    .map(candidate=>(

                        <PipelineCandidateCard

                            key={
                                candidate.candidate_id
                            }

                            candidate={
                                candidate
                            }

                        />

                    ))

                    }



                </PipelineColumn>









                <PipelineColumn

                    name="Assessment"

                    count={
                        getCandidates("Assessment").length
                    }

                    color="orange"

                >

                    {

                    getCandidates("Assessment")

                    .map(candidate=>(

                        <PipelineCandidateCard

                            key={
                                candidate.candidate_id
                            }

                            candidate={
                                candidate
                            }

                        />

                    ))

                    }



                </PipelineColumn>









                <PipelineColumn

                    name="Interview"

                    count={
                        getCandidates("Interview").length
                    }

                    color="purple"

                >

                    {

                    getCandidates("Interview")

                    .map(candidate=>(

                        <PipelineCandidateCard

                            key={
                                candidate.candidate_id
                            }

                            candidate={
                                candidate
                            }

                        />

                    ))

                    }



                </PipelineColumn>









                <PipelineColumn

                    name="Hired"

                    count={
                        getCandidates("Hired").length
                    }

                    color="green"

                >

                    {

                    getCandidates("Hired")

                    .map(candidate=>(

                        <PipelineCandidateCard

                            key={
                                candidate.candidate_id
                            }

                            candidate={
                                candidate
                            }

                        />

                    ))

                    }



                </PipelineColumn>









                <PipelineColumn

                    name="Failed / Rejected"

                    count={
                        getCandidates("Rejected").length
                    }

                    color="red"

                >

                    {

                    getCandidates("Rejected")

                    .map(candidate=>(

                        <PipelineCandidateCard

                            key={
                                candidate.candidate_id
                            }

                            candidate={
                                candidate
                            }

                        />

                    ))

                    }



                </PipelineColumn>







            </div>






        </div>


    );


}



export default CandidatePipeline;