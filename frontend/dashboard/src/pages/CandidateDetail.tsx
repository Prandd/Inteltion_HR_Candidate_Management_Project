import {
    useEffect,
    useState
} from "react";


import {
    useParams,
    useNavigate
} from "react-router-dom";


import api from "../api/axios";

import StatusDropdown from "../components/StatusDropdown";


import type {
    CandidateDetailType
} from "../types/candidate";





function CandidateDetail(){


    const { id } = useParams();


    const navigate = useNavigate();



    const [
        candidate,
        setCandidate
    ] = useState<CandidateDetailType | null>(null);



    const [
        loading,
        setLoading
    ] = useState(true);



    const [
        error,
        setError
    ] = useState("");







    useEffect(()=>{


        if(id){

            fetchCandidate();

        }


    },[id]);







    async function fetchCandidate(){


        try{


            setLoading(true);

            setError("");



            const response =
                await api.get(
                    `/candidates/${id}`
                );



            setCandidate(
                response.data.data
            );


        }
        catch(err){


            console.error(err);


            setError(
                "Cannot load candidate"
            );


        }
        finally{


            setLoading(false);


        }


    }








    if(loading){


        return (

            <div className="p-10">

                Loading candidate...

            </div>

        );

    }








    if(error || !candidate){


        return (

            <div className="p-10">


                <p className="text-red-600">

                    {
                        error ||
                        "Candidate not found"
                    }

                </p>


                <button

                    onClick={
                        ()=>navigate(-1)
                    }

                    className="
                    mt-5
                    text-blue-600
                    "

                >

                    ← Back

                </button>


            </div>

        );

    }









    return (

        <div
            className="
            px-8
            pb-8
            "
        >




            <button

                onClick={
                    ()=>navigate(-1)
                }

                className="
                text-blue-600
                mb-6
                "

            >

                ← Back

            </button>








            <div

                className="
                bg-white
                rounded-xl
                p-8
                shadow-sm
                "

            >







                {/* Header */}


                <div

                    className="
                    flex
                    justify-between
                    items-start
                    "

                >



                    <div>


                        <h1

                            className="
                            text-3xl
                            font-bold
                            "

                        >

                            {
                                candidate.full_name ||
                                "Unknown Candidate"
                            }

                        </h1>



                        <p>

                            {
                                candidate.applied_position ||
                                "-"
                            }

                        </p>



                        <p>

                            📍

                            {" "}

                            {
                                candidate.location ||
                                "-"
                            }

                        </p>


                    </div>







                    <StatusDropdown


                        candidateId={
                            candidate.candidate_id
                        }


                        currentStatus={
                            candidate.status
                        }


                        onUpdate={
                            fetchCandidate
                        }


                    />


                </div>








                <hr className="my-6"/>








                {/* Contact */}


                <h2 className="text-xl font-bold">

                    Contact

                </h2>



                <p>

                    Email:

                    {" "}

                    {
                        candidate.email ||
                        "-"
                    }

                </p>



                <p>

                    Phone:

                    {" "}

                    {
                        candidate.phone ||
                        "-"
                    }

                </p>









                <hr className="my-6"/>








                {/* Resume */}


                <h2 className="text-xl font-bold mb-3">

                    Resume

                </h2>




                {
                    candidate.resume_url &&

                    <a

                        href={
                            `http://localhost:8000${candidate.resume_url}`
                        }

                        target="_blank"

                        className="
                        inline-block
                        bg-blue-600
                        text-white
                        px-5
                        py-2
                        rounded-lg
                        "

                    >

                        View Resume

                    </a>

                }









                <hr className="my-6"/>








                {/* Summary */}


                <h2 className="text-xl font-bold">

                    Summary

                </h2>



                <p

                    className="
                    mt-3
                    text-gray-600
                    "

                >

                    {
                        candidate.summary ||
                        "No summary available"
                    }


                </p>









                <hr className="my-6"/>








                {/* Skills */}


                <h2 className="text-xl font-bold mb-3">

                    Skills

                </h2>



                <div

                    className="
                    flex
                    gap-2
                    flex-wrap
                    "

                >


                    {
                        candidate.skills?.length

                        ?

                        candidate.skills.map(

                            skill=>(

                                <span

                                    key={
                                        skill.skill
                                    }

                                    className="
                                    bg-gray-100
                                    px-3
                                    py-1
                                    rounded
                                    "

                                >

                                    {skill.skill}

                                </span>

                            )

                        )

                        :

                        <span>

                            No skills

                        </span>

                    }


                </div>









                <hr className="my-6"/>








                {/* Experience */}


                <h2 className="text-xl font-bold mb-4">

                    Experience

                </h2>




                <div className="space-y-4">


                    {
                        candidate.experience?.length

                        ?

                        candidate.experience.map(

                            (exp,index)=>(

                                <div

                                    key={index}

                                    className="
                                    border
                                    rounded-lg
                                    p-4
                                    "

                                >


                                    <h3 className="font-bold">

                                        {
                                            exp.position
                                        }

                                    </h3>


                                    <p>

                                        {
                                            exp.company
                                        }

                                    </p>



                                    <p className="text-gray-500 text-sm">

                                        {
                                            exp.start_date
                                        }

                                        {" - "}

                                        {
                                            exp.end_date
                                        }

                                    </p>



                                    <p className="mt-2">

                                        {
                                            exp.description
                                        }

                                    </p>


                                </div>


                            )

                        )

                        :

                        <p>

                            No experience

                        </p>

                    }


                </div>









                <hr className="my-6"/>








                {/* Education */}


                <h2 className="text-xl font-bold mb-3">

                    Education

                </h2>





                {
                    candidate.education?.length

                    ?

                    candidate.education.map(

                        (edu,index)=>(


                            <div

                                key={index}

                                className="mb-3"

                            >


                                <b>

                                    {
                                        edu.institution
                                    }

                                </b>



                                <p>

                                    {
                                        edu.degree
                                    }

                                    {" "}

                                    {
                                        edu.field
                                    }

                                </p>



                                <p>

                                    {
                                        edu.year
                                    }

                                </p>


                            </div>


                        )

                    )

                    :

                    <p>

                        No education

                    </p>

                }





            </div>


        </div>

    );

}



export default CandidateDetail;