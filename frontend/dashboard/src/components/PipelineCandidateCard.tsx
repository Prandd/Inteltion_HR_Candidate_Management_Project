import {
    useNavigate
} from "react-router-dom";


import type {
    CandidateSummary
} from "../types/candidate";





interface Props {

    candidate: CandidateSummary;

}








function PipelineCandidateCard({

    candidate

}:Props){


    const navigate = useNavigate();





    const status =
        candidate.status || "New";





    const skills =
        candidate.top_skills ?? [];





    const confidence =

        Math.round(

            (candidate.extraction_confidence ?? 0)

            *

            100

        );







    const statusStyle:Record<string,string> = {


        New:
        "bg-blue-50 text-blue-600",


        Assessment:
        "bg-orange-50 text-orange-600",


        Interview:
        "bg-purple-50 text-purple-600",


        Hired:
        "bg-green-50 text-green-600",


        Rejected:
        "bg-red-50 text-red-600",


    };









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

                gap-2

                "

            >



                <div className="min-w-0">


                    <h3


                        className="

                        text-sm

                        font-semibold

                        text-gray-900

                        truncate

                        "

                    >

                        {
                            candidate.full_name ||
                            "Unknown Candidate"
                        }


                    </h3>





                    <p


                        className="

                        text-xs

                        text-gray-500

                        mt-1

                        truncate

                        "

                    >

                        {
                            candidate.applied_position ||
                            "-"
                        }


                    </p>



                </div>







                <span


                    className={`

                    text-[11px]

                    px-2

                    py-1

                    rounded-full

                    font-medium

                    ${

                    statusStyle[status]

                    ||

                    "bg-gray-100 text-gray-600"

                    }

                    `}


                >

                    {status}


                </span>



            </div>









            {/* DETAIL */}



            <div


                className="

                mt-4

                space-y-2

                text-xs

                "

            >



                <div

                    className="

                    flex

                    justify-between

                    "

                >

                    <span className="text-gray-400">

                        Experience

                    </span>


                    <span className="font-medium text-gray-700">

                        {
                            candidate.experience_total ?? 0
                        } yrs

                    </span>


                </div>






                <div

                    className="

                    flex

                    justify-between

                    "

                >

                    <span className="text-gray-400">

                        Location

                    </span>


                    <span className="text-gray-700 truncate max-w-[120px]">

                        {
                            candidate.location || "-"
                        }

                    </span>


                </div>



            </div>









            {/* SKILLS */}



            {

            skills.length > 0 &&


            <div


                className="

                flex

                flex-wrap

                gap-1.5

                mt-4

                "

            >


                {

                skills.slice(0,3).map(skill=>(


                    <span


                        key={skill}


                        className="

                        bg-gray-100

                        text-gray-600

                        text-[11px]

                        px-2

                        py-1

                        rounded-full

                        "

                    >

                        {skill}


                    </span>


                ))

                }


            </div>


            }









            {/* AI MATCH */}



            <div className="mt-4">


                <div


                    className="

                    flex

                    justify-between

                    text-[11px]

                    mb-1

                    "

                >


                    <span className="text-gray-400">

                        AI Match

                    </span>



                    <span className="text-blue-600 font-medium">

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

                        bg-blue-500

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

                pt-3

                border-t

                border-gray-100

                flex

                justify-between

                items-center

                "

            >



                <span


                    className="

                    text-[11px]

                    text-gray-400

                    "

                >

                    View Profile

                </span>





                <span


                    className="

                    text-blue-600

                    text-sm

                    "

                >

                    →

                </span>



            </div>







        </div>


    );


}





export default PipelineCandidateCard;