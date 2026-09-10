import React from "react";


interface Props {

    name: string;

    count: number;

    children?: React.ReactNode;

}




function PipelineCard({

    name,

    count,

    children

}: Props){



    return (


        <div


            className="

            bg-white

            border

            border-gray-200

            rounded-2xl

            p-4

            min-h-[650px]

            w-full

            "

        >





            {/* HEADER */}


            <div


                className="

                flex

                items-center

                justify-between

                mb-4

                "


            >




                <h2


                    className="

                    text-[16px]

                    font-bold

                    text-gray-900

                    "

                >


                    {name}


                </h2>







                <span


                    className="


                    min-w-[30px]

                    h-[24px]

                    flex

                    items-center

                    justify-center


                    bg-gray-100

                    text-gray-500

                    text-xs

                    font-semibold


                    rounded-full


                    "


                >


                    {count}


                </span>



            </div>









            {/* CANDIDATE LIST */}



            <div


                className="

                flex

                flex-col

                gap-3

                "

            >


                {children}



            </div>





        </div>


    );

}



export default PipelineCard;