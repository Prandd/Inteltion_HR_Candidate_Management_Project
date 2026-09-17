import type {
    CandidateDetailType
} from "../../types/candidate";


interface Props {

    candidate: CandidateDetailType;

}



function EducationSection({

    candidate

}: Props){


    return (

        <div

            className="
            space-y-6
            "

        >

            {
                candidate.education?.map(

                    (edu,index)=>(

                        <div

                            key={index}

                            className="
                            relative
                            pl-8
                            "

                        >


                            {/* Timeline line */}

                            {
                                index !== candidate.education!.length - 1 &&

                                <div

                                    className="
                                    absolute
                                    left-[7px]
                                    top-4
                                    bottom-[-24px]
                                    w-[2px]
                                    bg-blue-100
                                    "

                                />

                            }




                            {/* Timeline dot */}

                            <div

                                className="
                                absolute
                                left-0
                                top-2
                                w-4
                                h-4
                                rounded-full
                                bg-blue-600
                                border-4
                                border-blue-100
                                "

                            />





                            {/* Education Content */}

                            <div>


                                <h3

                                    className="
                                    text-sm
                                    font-semibold
                                    text-gray-900
                                    "

                                >

                                    {
                                        edu.degree
                                        ||
                                        "-"
                                    }


                                </h3>




                                <p

                                    className="
                                    text-sm
                                    text-gray-600
                                    mt-1
                                    "

                                >

                                    {
                                        edu.institution
                                        ||
                                        "-"
                                    }

                                </p>




                                <p

                                    className="
                                    text-sm
                                    text-gray-500
                                    mt-1
                                    "

                                >

                                    {
                                        edu.field
                                        ||
                                        "-"
                                    }

                                </p>




                                {

                                    edu.year &&

                                    <span

                                        className="
                                        inline-flex
                                        mt-3
                                        px-3
                                        py-1
                                        rounded-full
                                        bg-blue-50
                                        text-blue-600
                                        text-xs
                                        font-medium
                                        "

                                    >

                                        {edu.year}

                                    </span>

                                }



                            </div>


                        </div>


                    )

                )
            }


        </div>

    );

}


export default EducationSection;