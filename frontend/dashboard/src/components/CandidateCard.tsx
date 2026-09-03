import { useNavigate } from "react-router-dom";

import type { CandidateSummary } from "../types/candidate";


interface Props {

    candidate: CandidateSummary;

}



function CandidateCard(
    {
        candidate
    }: Props
) {


    const navigate = useNavigate();



    return (


        <div

            className="
            bg-white
            border
            rounded-xl
            p-5
            min-h-[230px]
            flex
            flex-col
            hover:shadow-md
            transition
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


                    <h2

                        className="
                        text-lg
                        font-bold
                        "

                    >

                        {
                            candidate.full_name ||
                            "Unknown Candidate"
                        }

                    </h2>



                    <p

                        className="
                        text-gray-500
                        "

                    >

                        {
                            candidate.applied_position ||
                            "-"
                        }

                    </p>


                </div>





                <span

                    className="
                    bg-blue-100
                    text-blue-700
                    px-3
                    py-1
                    rounded-full
                    text-xs
                    "

                >

                    {
                        candidate.status
                    }

                </span>



            </div>







            <hr
                className="
                my-4
                "
            />








            {/* Information */}


            <div

                className="
                space-y-2
                text-sm
                flex-1
                "

            >



                <p>

                    <b>
                        Location:
                    </b>

                    {" "}

                    {
                        candidate.location ||
                        "-"
                    }

                </p>





                <p>

                    <b>
                        Experience:
                    </b>

                    {" "}

                    {
                        candidate.experience_total || 0
                    }

                    {" years"}

                </p>





                <p>

                    <b>
                        Skills:
                    </b>

                    {" "}

                    {
                        candidate.top_skills?.length
                        ?
                        candidate.top_skills.join(", ")
                        :
                        "-"
                    }

                </p>





                <p>

                    <b>
                        Confidence:
                    </b>

                    {" "}

                    {
                        candidate.extraction_confidence
                        ?
                        Math.round(
                            candidate.extraction_confidence * 100
                        )
                        :
                        0
                    }

                    %

                </p>



            </div>








            {/* Button */}


            <div

                className="
                flex
                justify-end
                mt-5
                "

            >



                <button

                    onClick={
                        ()=>navigate(
                            `/candidate/${candidate.candidate_id}`
                        )
                    }

                    className="
                    text-blue-600
                    font-medium
                    hover:underline
                    "

                >

                    View Profile

                </button>


            </div>





        </div>


    );

}



export default CandidateCard;