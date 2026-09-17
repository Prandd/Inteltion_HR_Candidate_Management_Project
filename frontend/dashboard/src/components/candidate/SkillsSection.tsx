import type {
    CandidateDetailType
} from "../../types/candidate";


interface Props {

    candidate: CandidateDetailType;

}



function SkillsSection({

    candidate

}: Props){


    return (

        <div

            className="
            space-y-5
            "

        >


            {
                candidate.skills?.map(

                    (group,index)=>(


                        <div

                            key={index}

                            className="
                            space-y-3
                            "

                        >



                            {/* Skill Category */}

                            <h3

                                className="
                                text-sm
                                font-semibold
                                text-gray-800
                                "

                            >

                                {
                                    group.skill
                                }


                            </h3>




                            {/* Skill Tags */}

                            <div

                                className="
                                flex
                                flex-wrap
                                gap-2
                                "

                            >

                                {
                                    group.tools?.map(

                                        tool=>(

                                            <span

                                                key={tool}

                                                className="
                                                px-3
                                                py-1.5
                                                rounded-full
                                                bg-blue-50
                                                text-blue-600
                                                text-xs
                                                font-medium
                                                border
                                                border-blue-100
                                                "

                                            >

                                                {tool}

                                            </span>

                                        )

                                    )
                                }


                            </div>


                        </div>


                    )

                )
            }


        </div>

    );


}


export default SkillsSection;