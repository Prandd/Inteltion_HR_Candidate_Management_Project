import {
    useState
} from "react";


import type {
    CandidateDetailType
} from "../../types/candidate";



interface Props {

    candidate: CandidateDetailType;

}



function ExperienceSection({

    candidate

}:Props){


    const experiences =
        candidate.experience ?? [];



    const [
        openIndex,
        setOpenIndex
    ] = useState<number>(0);




    return (

        <section

            className="
            space-y-4
            "

        >



            {/* HEADER */}

            <div

                className="
                flex
                justify-between
                items-center
                "

            >

                <div>


                    <h2

                        className="
                        text-sm
                        font-bold
                        text-gray-900
                        uppercase
                        "

                    >

                        EXPERIENCE

                    </h2>


                    <p

                        className="
                        text-xs
                        text-gray-400
                        mt-1
                        "

                    >

                        Click roles to expand or collapse details

                    </p>


                </div>



                <span

                    className="
                    text-xs
                    px-3
                    py-1
                    rounded-full
                    bg-gray-100
                    text-gray-600
                    font-medium
                    "

                >

                    {experiences.length} Positions

                </span>


            </div>







            {/* EXPERIENCE LIST */}


            <div

                className="
                space-y-3
                "

            >


                {
                    experiences.map(

                        (exp,index)=>(


                            <div

                                key={index}

                                className="
                                border
                                border-gray-200
                                rounded-xl
                                overflow-hidden
                                bg-white
                                "

                            >



                                {/* HEADER */}

                                <button

                                    onClick={()=>


                                        setOpenIndex(

                                            openIndex === index

                                            ?

                                            -1

                                            :

                                            index

                                        )

                                    }


                                    className="
                                    w-full
                                    flex
                                    justify-between
                                    items-center
                                    p-4
                                    text-left
                                    "

                                >


                                    <div>


                                        <div

                                            className="
                                            flex
                                            items-center
                                            gap-2
                                            "

                                        >

                                            <h3

                                                className="
                                                text-sm
                                                font-semibold
                                                text-gray-900
                                                "

                                            >

                                                {
                                                    exp.position
                                                    ||
                                                    "-"
                                                }

                                            </h3>


                                            {
                                                index===0 &&

                                                <span

                                                    className="
                                                    text-[10px]
                                                    px-2
                                                    py-1
                                                    rounded-full
                                                    bg-green-50
                                                    text-green-600
                                                    font-medium
                                                    "

                                                >

                                                    Current Role

                                                </span>

                                            }


                                        </div>




                                        <p

                                            className="
                                            text-sm
                                            text-gray-600
                                            mt-1
                                            "

                                        >

                                            {
                                                exp.company
                                                ||
                                                "-"
                                            }

                                        </p>


                                    </div>






                                    <div

                                        className="
                                        flex
                                        items-center
                                        gap-3
                                        "

                                    >


                                        <span

                                            className="
                                            text-xs
                                            text-gray-500
                                            border
                                            rounded-lg
                                            px-2
                                            py-1
                                            "

                                        >

                                            {
                                                exp.start_date
                                                ||
                                                "-"
                                            }

                                            {" - "}

                                            {
                                                exp.end_date
                                                ||
                                                "Present"
                                            }

                                        </span>



                                        <span

                                            className="
                                            text-gray-400
                                            text-sm
                                            "

                                        >

                                            {
                                                openIndex===index

                                                ?

                                                "⌃"

                                                :

                                                "⌄"
                                            }

                                        </span>


                                    </div>



                                </button>







                                {/* DETAIL */}


                                {
                                    openIndex===index &&


                                    <div

                                        className="
                                        px-4
                                        pb-4
                                        border-t
                                        border-gray-100
                                        "

                                    >


                                        {
                                            exp.description &&

                                            <p

                                                className="
                                                text-sm
                                                text-gray-600
                                                leading-6
                                                mt-4
                                                "

                                            >

                                                {
                                                    exp.description
                                                }


                                            </p>

                                        }



                                        {
                                            exp.skills &&

                                            <div

                                                className="
                                                flex
                                                flex-wrap
                                                gap-2
                                                mt-4
                                                "

                                            >

                                                {
                                                    exp.skills.map(

                                                        skill=>(

                                                            <span

                                                                key={skill}

                                                                className="
                                                                text-xs
                                                                px-2
                                                                py-1
                                                                rounded-md
                                                                bg-blue-50
                                                                text-blue-600
                                                                "

                                                            >

                                                                {skill}

                                                            </span>

                                                        )

                                                    )
                                                }


                                            </div>

                                        }



                                    </div>


                                }


                            </div>


                        )

                    )
                }



            </div>



        </section>

    );

}



export default ExperienceSection;