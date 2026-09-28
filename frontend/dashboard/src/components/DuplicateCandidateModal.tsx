import {
    useNavigate
} from "react-router-dom";

import { formatStatusLabel } from "../utils/status";


interface DuplicateCandidate {

    candidate_id:string;

    full_name?:string;

    email?:string;

    phone?:string;

    applied_position?:string;

    status?:string;

}



interface Props {

    candidate:DuplicateCandidate;

    onClose:()=>void;

    onConfirmUpload:()=>void;

}




function DuplicateCandidateModal({

    candidate,

    onClose,

    onConfirmUpload

}:Props){


    const navigate = useNavigate();



    function viewCandidate(){

        navigate(
            `/candidate/${candidate.candidate_id}`,
            {
                state:{
                    fromDuplicateUpload:true,
                    duplicateCandidateId:candidate.candidate_id
                }
            }
        );


        onClose();

    }



    return (

        <div

            className="
            fixed
            inset-0
            bg-black/40
            flex
            items-center
            justify-center
            z-50
            "

        >


            <div

                className="
                bg-white
                rounded-2xl
                w-full
                max-w-md
                p-6
                shadow-xl
                "

            >



                {/* HEADER */}

                <div

                    className="
                    flex
                    items-start
                    gap-3
                    mb-5
                    "

                >

                    <div

                        className="
                        w-11
                        h-11
                        rounded-xl
                        bg-yellow-50
                        text-yellow-600
                        flex
                        items-center
                        justify-center
                        text-xl
                        "

                    >

                        ⚠️

                    </div>



                    <div>


                        <h2

                            className="
                            text-lg
                            font-semibold
                            text-gray-900
                            "

                        >

                            Duplicate Candidate Found

                        </h2>



                        <p

                            className="
                            text-sm
                            text-gray-500
                            mt-1
                            "

                        >

                            This candidate already exists in the system.

                        </p>


                    </div>


                </div>





                {/* INFORMATION */}

                <div

                    className="
                    bg-gray-50
                    border
                    border-gray-200
                    rounded-xl
                    p-4
                    space-y-4
                    "

                >


                    <InfoRow

                        label="Name"

                        value={
                            candidate.full_name || "-"
                        }

                    />



                    <InfoRow

                        label="Email"

                        value={
                            candidate.email || "-"
                        }

                    />



                    <InfoRow

                        label="Phone"

                        value={
                            candidate.phone || "-"
                        }

                    />



                    <InfoRow

                        label="Position"

                        value={
                            candidate.applied_position || "-"
                        }

                    />



                    <InfoRow

                        label="Current Status"

                        value={
                            formatStatusLabel(candidate.status || "-")
                        }

                    />


                </div>





                {/* ACTION */}

                <div

                    className="
                    flex
                    justify-end
                    gap-3
                    mt-6
                    "

                >


                    <button

                        onClick={onClose}

                        className="
                        px-4
                        py-2
                        rounded-xl
                        text-sm
                        bg-gray-100
                        text-gray-600
                        hover:bg-gray-200
                        "

                    >

                        Cancel

                    </button>



                    <button

                        onClick={viewCandidate}

                        className="
                        px-4
                        py-2
                        rounded-xl
                        text-sm
                        bg-blue-600
                        text-white
                        hover:bg-blue-700
                        "

                    >

                        View Candidate

                    </button>



                    <button

                        onClick={onConfirmUpload}

                        className="
                        px-4
                        py-2
                        rounded-xl
                        text-sm
                        bg-orange-500
                        text-white
                        hover:bg-orange-600
                        "

                    >

                        Upload Anyway

                    </button>


                </div>



            </div>


        </div>

    );

}





function InfoRow({

    label,

    value

}:{

    label:string;

    value:string;

}){


    return (

        <div>


            <p

                className="
                text-xs
                text-gray-400
                "

            >

                {label}

            </p>



            <p

                className="
                text-sm
                font-medium
                text-gray-800
                mt-1
                "

            >

                {value}

            </p>


        </div>

    );

}



export default DuplicateCandidateModal;