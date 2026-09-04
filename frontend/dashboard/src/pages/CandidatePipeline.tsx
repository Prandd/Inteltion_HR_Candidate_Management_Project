import { useEffect, useState } from "react";

import { useNavigate } from "react-router-dom";


import api from "../api/axios";

import PipelineCard from "../components/PipelineCard";


import type { CandidateSummary } from "../types/candidate";



function CandidatePipeline(){


    const navigate = useNavigate();



    const [candidates,setCandidates] =
        useState<CandidateSummary[]>([]);



    const [loading,setLoading] =
        useState(true);





    useEffect(()=>{


        fetchCandidates();


    },[]);





    async function fetchCandidates(){


        try{


            const response =
                await api.get("/candidates");



            console.log(
                "Pipeline candidates:",
                response.data.data
            );



            setCandidates(
                response.data.data
            );


        }
        catch(error){


            console.error(
                "Cannot load candidates",
                error
            );


        }
        finally{


            setLoading(false);


        }


    }





    function filterStatus(status:string){


        return candidates.filter(

            candidate =>
            candidate.status === status

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

        <div className="p-8">



            <div
                className="
                flex
                justify-between
                mb-8
                "
            >


                <div>


                    <h1
                        className="
                        text-3xl
                        font-bold
                        "
                    >

                        Candidate Pipeline

                    </h1>



                    <p className="text-gray-500">

                        Manage candidate progress

                    </p>


                </div>





                <button

                    onClick={()=>navigate("/upload")}

                    className="
                    bg-blue-600
                    text-white
                    px-6
                    py-3
                    rounded-lg
                    "

                >

                    Upload CV

                </button>


            </div>








            <div
                className="
                grid
                grid-cols-4
                gap-6
                "
            >





                <PipelineCard

                    name="New"

                    count={
                        filterStatus("New").length
                    }

                >


                {
                    filterStatus("New")
                    .map(candidate=>(

                        <CandidateItem

                            key={
                                candidate.candidate_id
                            }

                            candidate={
                                candidate
                            }

                        />

                    ))
                }


                </PipelineCard>









                <PipelineCard

                    name="Assessment"

                    count={
                        filterStatus("Assessment").length
                    }

                >


                {
                    filterStatus("Assessment")
                    .map(candidate=>(

                        <CandidateItem

                            key={
                                candidate.candidate_id
                            }

                            candidate={
                                candidate
                            }

                        />

                    ))
                }


                </PipelineCard>









                <PipelineCard

                    name="Interview"

                    count={
                        filterStatus("Interview").length
                    }

                >


                {
                    filterStatus("Interview")
                    .map(candidate=>(

                        <CandidateItem

                            key={
                                candidate.candidate_id
                            }

                            candidate={
                                candidate
                            }

                        />

                    ))
                }


                </PipelineCard>









                <PipelineCard

                    name="Hired"

                    count={
                        filterStatus("Hired").length
                    }

                >


                {
                    filterStatus("Hired")
                    .map(candidate=>(

                        <CandidateItem

                            key={
                                candidate.candidate_id
                            }

                            candidate={
                                candidate
                            }

                        />

                    ))
                }


                </PipelineCard>






            </div>


        </div>

    );

}






function CandidateItem(
    {
        candidate
    }:{
        candidate:CandidateSummary
    }
){


    const navigate = useNavigate();



    return (

        <div

            className="
            bg-white
            border
            rounded-lg
            p-4
            mb-4
            "

        >


            <h3
                className="
                font-bold
                "
            >

                {candidate.full_name}

            </h3>



            <p
                className="
                text-gray-500
                text-sm
                "
            >

                {candidate.applied_position}

            </p>



            <button

                onClick={()=>navigate(
                    `/candidate/${candidate.candidate_id}`
                )}

                className="
                text-blue-600
                text-sm
                mt-3
                "

            >

                View Profile

            </button>



        </div>

    );

}





export default CandidatePipeline;