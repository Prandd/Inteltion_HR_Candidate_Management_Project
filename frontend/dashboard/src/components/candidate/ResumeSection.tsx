import type {
    CandidateDetailType
} from "../../types/candidate";


interface Props {

    candidate:CandidateDetailType;

}



function ResumeSection({

    candidate

}:Props){


    return (

        <section

            className="
            bg-white
            border
            rounded-2xl
            p-5
            "

        >


            <h2

                className="
                text-sm
                font-bold
                uppercase
                mb-4
                "

            >

                Resume

            </h2>




            <div

                className="
                flex
                justify-between
                items-center
                bg-gray-50
                rounded-xl
                p-4
                "

            >


                <div

                    className="
                    flex
                    items-center
                    gap-3
                    "

                >


                    <div

                        className="
                        w-10
                        h-10
                        rounded-xl
                        bg-red-50
                        text-red-600
                        flex
                        items-center
                        justify-center
                        "

                    >

                        PDF

                    </div>




                    <div>


                        <p

                            className="
                            text-sm
                            font-medium
                            "

                        >

                            {
                                candidate.resume_filename
                                ||
                                "No resume uploaded"
                            }

                        </p>


                        <p

                            className="
                            text-xs
                            text-gray-400
                            mt-1
                            "

                        >

                            Uploaded resume

                        </p>


                    </div>



                </div>





                <div

                    className="
                    flex
                    gap-2
                    "

                >


                    <button

                        className="
                        px-3
                        py-2
                        text-xs
                        rounded-lg
                        bg-blue-50
                        text-blue-600
                        "

                    >

                        View

                    </button>



                    <button

                        className="
                        px-3
                        py-2
                        text-xs
                        rounded-lg
                        bg-gray-100
                        text-gray-600
                        "

                    >

                        Download

                    </button>


                </div>



            </div>



        </section>

    );

}


export default ResumeSection;