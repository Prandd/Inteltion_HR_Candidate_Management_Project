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
    "cyan"
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
            header:"bg-blue-50",
            text:"text-blue-600"
        },

        cyan:{
            dot:"bg-cyan-500",
            header:"bg-cyan-50",
            text:"text-cyan-600"
        },

        orange:{
            dot:"bg-orange-500",
            header:"bg-orange-50",
            text:"text-orange-600"
        },

        purple:{
            dot:"bg-purple-500",
            header:"bg-purple-50",
            text:"text-purple-600"
        },

        green:{
            dot:"bg-green-500",
            header:"bg-green-50",
            text:"text-green-600"
        },

        red:{
            dot:"bg-red-500",
            header:"bg-red-50",
            text:"text-red-600"
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
            min-h-[620px]
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
                    px-3
                    py-1
                    rounded-full
                    text-xs
                    font-semibold
                    ${style.header}
                    ${style.text}
                    `}

                >

                    {count}

                </span>


            </div>




            {/* CONTENT */}

            <div

                className="
                flex-1
                overflow-y-auto
                space-y-3
                pr-1
                scrollbar-hide
                "

            >

                {
                    count === 0

                    ?

                    <div

                        className="
                        h-full
                        flex
                        flex-col
                        items-center
                        justify-center
                        gap-2
                        text-gray-400
                        "

                    >

                        <span

                            className="
                            text-2xl
                            "

                        >

                            📂

                        </span>


                        <p

                            className="
                            text-sm
                            "

                        >

                            No candidates

                        </p>


                    </div>


                    :

                    children

                }


            </div>


        </div>

    );

}


export default PipelineColumn;