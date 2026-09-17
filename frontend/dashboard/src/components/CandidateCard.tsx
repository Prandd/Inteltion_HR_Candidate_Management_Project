import {
    useNavigate
} from "react-router-dom";


import type {
    CandidateSummary
} from "../types/candidate";



interface Props {

    candidate: CandidateSummary;

}





function CandidateCard({

    candidate

}: Props){



    const navigate = useNavigate();



    const skills =
        candidate.top_skills ?? [];




    const confidence = Math.round(

        (candidate.extraction_confidence ?? 0)

        * 100

    );







    function getStatusStyle(status:string){


        switch(status){


            case "Interview":

                return "bg-yellow-50 text-yellow-600";


            case "Hired":

                return "bg-green-50 text-green-600";


            case "CV rejected":
            case "Rejected":

                return "bg-red-50 text-red-600";


            case "Assessment":

                return "bg-purple-50 text-purple-600";


            default:

                return "bg-blue-50 text-blue-600";


        }


    }







    return (


        <div


            onClick={()=>navigate(

                `/candidate/${candidate.candidate_id}`

            )}


            className="

            bg-white

            border

            border-gray-200

            rounded-xl

            p-4

            cursor-pointer

            hover:shadow-md

            transition

            "

        >







            {/* HEADER */}



            <div

                className="

                flex

                justify-between

                items-start

                gap-3

                "

            >



                <div

                    className="min-w-0"

                >



                    <h2

                        className="

                        text-sm

                        font-bold

                        text-gray-900

                        truncate

                        "

                    >

                        {

                            candidate.full_name ||

                            "Unknown Candidate"

                        }


                    </h2>




                    <p

                        className="

                        text-xs

                        text-gray-500

                        mt-1

                        "

                    >

                        {

                            candidate.applied_position ||

                            "-"

                        }


                    </p>



                </div>







                <div className="flex flex-col items-start gap-1">


                    <span

                        className={`

                        text-[11px]

                        font-medium

                        px-3

                        py-1

                        rounded-full

                        whitespace-nowrap

                        ${
                            getStatusStyle(
                                candidate.status || "New"
                            )
                        }

                        `}

                    >

                        {
                            candidate.status || "New"
                        }


                    </span>



                        {
                            candidate.status === "CV rejected"
                            &&
                            candidate.rejected_after
                            &&
                            <p
                                className="
                                text-xs
                                text-red-500
                                font-medium
                                mt-1
                                "
                            >
                                Rejected after {candidate.rejected_after}
                            </p>
                        }


                </div>



            </div>









            {/* INFO */}



            <div

                className="

                mt-4

                space-y-2

                text-xs

                "

            >




                <p>


                    <span

                        className="text-gray-500"

                    >

                        Location:

                    </span>


                    {" "}


                    {

                        candidate.location || "-"

                    }


                </p>






                <p>


                    <span

                        className="text-gray-500"

                    >

                        Experience:

                    </span>


                    {" "}


                    <b>

                        {

                            candidate.experience_total ?? 0

                        }

                        {" "}yrs

                    </b>


                </p>




            </div>









            {/* SKILLS */}



            {

            skills.length > 0 &&


            <div

                className="

                flex

                flex-wrap

                gap-2

                mt-4

                "

            >


                {

                skills

                .slice(0,3)

                .map(skill=>(


                    <span


                        key={skill}


                        className="

                        bg-gray-100

                        text-gray-600

                        text-[11px]

                        px-2

                        py-1

                        rounded

                        "

                    >

                        {skill}


                    </span>


                ))


                }


            </div>


            }









            {/* AI CONFIDENCE */}



            <div

                className="mt-4"

            >



                <div

                    className="

                    flex

                    justify-between

                    text-[11px]

                    mb-2

                    "

                >


                    <span

                        className="text-gray-500"

                    >

                        AI Confidence

                    </span>



                    <span

                        className="font-medium"

                    >

                        {confidence}%

                    </span>


                </div>







                <div

                    className="

                    h-1.5

                    bg-gray-100

                    rounded-full

                    overflow-hidden

                    "

                >



                    <div


                        className="

                        h-full

                        bg-blue-600

                        rounded-full

                        "

                        style={{

                            width:`${confidence}%`

                        }}


                    />



                </div>



            </div>









            {/* FOOTER */}



            <div

                className="

                mt-4

                flex

                justify-between

                items-center

                "

            >



                <span

                    className="

                    text-[11px]

                    text-gray-400

                    truncate

                    max-w-[160px]

                    "

                >

                    {

                        candidate.email || "-"

                    }


                </span>






                <span


                    className="

                    text-xs

                    text-blue-600

                    font-medium

                    "

                >

                    View →

                </span>



            </div>






        </div>


    );

}





export default CandidateCard;