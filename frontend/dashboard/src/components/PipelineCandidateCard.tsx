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



    const statusStyle:Record<string,{
        badge:string;
        dot:string;
    }> = {

        New:{
            badge:"bg-blue-50 text-blue-600",
            dot:"bg-blue-500"
        },

        "CV passed":{
            badge:"bg-cyan-50 text-cyan-600",
            dot:"bg-cyan-500"
        },

        Assessment:{
            badge:"bg-orange-50 text-orange-600",
            dot:"bg-orange-500"
        },

        Interview:{
            badge:"bg-purple-50 text-purple-600",
            dot:"bg-purple-500"
        },

        Hired:{
            badge:"bg-green-50 text-green-600",
            dot:"bg-green-500"
        },

        "CV rejected":{
            badge:"bg-red-50 text-red-600",
            dot:"bg-red-500"
        }

    };



    const current =
        statusStyle[status]
        ||
        {
            badge:"bg-gray-100 text-gray-600",
            dot:"bg-gray-400"
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
            rounded-2xl
            p-4
            cursor-pointer
            hover:shadow-md
            transition
            min-h-[260px]
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

                <div className="
                    flex
                    gap-3
                    min-w-0
                ">


                    <div

                        className="
                        w-10
                        h-10
                        rounded-xl
                        bg-blue-600
                        text-white
                        flex
                        items-center
                        justify-center
                        font-semibold
                        "

                    >

                        {
                            candidate.full_name
                            ?.charAt(0)
                            ||
                            "?"
                        }


                    </div>



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
                                candidate.full_name
                                ||
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
                                candidate.applied_position
                                ||
                                "-"
                            }

                        </p>


                    </div>


                </div>



                <span

                    className={`
                    flex
                    items-center
                    gap-1.5
                    text-[11px]
                    px-2.5
                    py-1
                    rounded-full
                    font-medium
                    ${current.badge}
                    `}

                >

                    <span

                        className={`
                        w-1.5
                        h-1.5
                        rounded-full
                        ${current.dot}
                        `}

                    />

                    {status}

                </span>


            </div>




            {/* INFO */}

            <div

                className="
                mt-5
                space-y-3
                text-xs
                "

            >


                <div className="
                    flex
                    items-center
                    gap-2
                ">

                    <span>
                        📍
                    </span>

                    <span className="text-gray-600 truncate">

                        {
                            candidate.location
                            ||
                            "Location not provided"
                        }

                    </span>

                </div>



                <div className="
                    flex
                    items-center
                    gap-2
                ">

                    <span>
                        💼
                    </span>

                    <span className="text-gray-600">

                        {
                            candidate.experience_total
                            ??
                            0
                        }
                        {" "}years experience

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
                    mt-5
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





            {/* FOOTER */}

            <div

                className="
                mt-6
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
                    text-xs
                    text-gray-400
                    "

                >

                    View profile

                </span>


                <span

                    className="
                    text-blue-600
                    "

                >

                    →

                </span>


            </div>



        </div>

    );

}


export default PipelineCandidateCard;