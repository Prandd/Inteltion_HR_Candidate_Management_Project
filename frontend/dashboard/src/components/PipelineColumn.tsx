import type {
    ReactNode
} from "react";



interface Props {


    name:string;


    count:number;


    color?:
    |
    "blue"
    |
    "orange"
    |
    "purple"
    |
    "green"
    |
    "red";


    children?:ReactNode;


}





function PipelineColumn({

    name,

    count,

    color="blue",

    children

}:Props){





    const theme = {


        blue:{
            dot:"bg-blue-500",
            badge:"bg-blue-50 text-blue-600"
        },


        orange:{
            dot:"bg-orange-500",
            badge:"bg-orange-50 text-orange-600"
        },


        purple:{
            dot:"bg-purple-500",
            badge:"bg-purple-50 text-purple-600"
        },


        green:{
            dot:"bg-green-500",
            badge:"bg-green-50 text-green-600"
        },


        red:{
            dot:"bg-red-500",
            badge:"bg-red-50 text-red-600"
        }


    };





    const style = theme[color];









    return (


        <div


            className="

            bg-white

            border

            border-gray-200

            rounded-2xl

            p-4

            flex

            flex-col

            h-[620px]

            "

        >





            {/* HEADER */}



            <div


                className="

                flex

                justify-between

                items-center

                mb-4

                "

            >



                <div


                    className="

                    flex

                    items-center

                    gap-2

                    "

                >



                    <span


                        className={`

                        w-2.5

                        h-2.5

                        rounded-full

                        ${style.dot}

                        `}


                    />





                    <h2


                        className="

                        text-sm

                        font-semibold

                        text-gray-900

                        "

                    >

                        {name}


                    </h2>



                </div>








                <span


                    className={`

                    text-xs

                    font-medium

                    px-3

                    py-1

                    rounded-full

                    ${style.badge}

                    `}


                >

                    {count}


                </span>



            </div>









            {/* CARD LIST */}



            <div


                className="

                flex-1

                overflow-y-auto

                space-y-3

                pr-1

                "

            >



                {


                    count === 0


                    ?

                    <div


                        className="

                        h-full

                        flex

                        items-center

                        justify-center

                        text-sm

                        text-gray-400

                        "

                    >

                        No candidates


                    </div>



                    :


                    children


                }



            </div>






        </div>


    );


}



export default PipelineColumn;