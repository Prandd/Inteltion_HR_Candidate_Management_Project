import StatusDropdown from "../StatusDropdown";


import type {
    CandidateDetailType
} from "../../types/candidate";



interface Props {

    candidate: CandidateDetailType;

    onDelete:()=>void;

    onUpdate:()=>void;

}




function CandidateHeader({

    candidate,

    onDelete,

    onUpdate

}:Props){


    return (

        <section

            className="
            bg-white
            border
            border-gray-200
            rounded-2xl
            p-6
            shadow-sm
            flex
            justify-between
            gap-6
            "

        >



            {/* LEFT */}

            <div

                className="
                flex
                items-center
                gap-5
                "

            >



                {/* Avatar */}

                <div

                    className="
                    w-16
                    h-16
                    rounded-full
                    bg-blue-600
                    text-white
                    flex
                    items-center
                    justify-center
                    text-xl
                    font-semibold
                    "

                >

                    {
                        candidate.full_name
                        ?.charAt(0)
                        .toUpperCase()
                        ||
                        "?"
                    }


                </div>






                {/* INFO */}

                <div>


                    <h1

                        className="
                        text-xl
                        font-semibold
                        text-gray-900
                        "

                    >

                        {
                            candidate.full_name
                            ||
                            "Unknown Candidate"
                        }


                    </h1>




                    <p

                        className="
                        text-sm
                        text-gray-600
                        mt-1
                        "

                    >

                        {
                            candidate.applied_position
                            ||
                            "-"
                        }

                    </p>





                    <div

                        className="
                        flex
                        items-center
                        gap-4
                        mt-3
                        "

                    >



                        <div

                            className="
                            flex
                            items-center
                            gap-1.5
                            "

                        >

                            <span className="text-sm">
                                📍
                            </span>


                            <span

                                className="
                                text-xs
                                text-gray-500
                                "

                            >

                                {
                                    candidate.location
                                    ||
                                    "Location not provided"
                                }


                            </span>


                        </div>





                        {
                            candidate.created_at &&


                            <div

                                className="
                                flex
                                items-center
                                gap-1.5
                                "

                            >

                                <span className="text-sm">
                                    🕒
                                </span>


                                <span

                                    className="
                                    text-xs
                                    text-gray-500
                                    "

                                >

                                    Applied

                                    {" "}

                                    {
                                        new Date(
                                            candidate.created_at
                                        )
                                        .toLocaleDateString(
                                            "en-GB"
                                        )
                                    }


                                </span>


                            </div>

                        }


                    </div>



                </div>


            </div>







            {/* RIGHT */}

            <div

                className="
                flex
                items-center
                gap-4
                "

            >





                {/* STATUS */}

                <div

                    className="
                    flex
                    flex-col
                    gap-2
                    "

                >


                    <span

                        className="
                        text-xs
                        text-gray-400
                        "

                    >

                        Current Status

                    </span>



                    <StatusDropdown

                        candidateId={
                            candidate.candidate_id
                        }

                        currentStatus={
                            candidate.status
                            ||
                            "New"
                        }

                        onUpdate={
                            onUpdate
                        }

                    />


                </div>








                {/* DELETE */}

                <button

                    onClick={onDelete}

                    className="
                    px-4
                    py-2
                    rounded-xl
                    bg-red-50
                    text-red-600
                    border
                    border-red-200
                    text-sm
                    font-medium
                    hover:bg-red-100
                    transition
                    "

                >

                    Delete

                </button>



            </div>






        </section>

    );

}


export default CandidateHeader;