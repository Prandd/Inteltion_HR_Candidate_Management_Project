interface Props {

    title:string;

    value:number;

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

    icon?:string;

}



function PipelineStatCard({

    title,

    value,

    color="blue",

    icon="○"

}:Props){



    const theme = {


        blue:{
            box:"bg-blue-50",
            text:"text-blue-600"
        },


        orange:{
            box:"bg-orange-50",
            text:"text-orange-600"
        },


        purple:{
            box:"bg-purple-50",
            text:"text-purple-600"
        },


        green:{
            box:"bg-green-50",
            text:"text-green-600"
        },


        red:{
            box:"bg-red-50",
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
            p-5
            flex
            items-center
            gap-4
            hover:shadow-md
            transition
            "

        >



            {/* ICON */}

            <div

                className={`
                w-12
                h-12
                rounded-xl
                flex
                items-center
                justify-center
                text-lg
                font-semibold
                ${style.box}
                ${style.text}
                `}

            >

                {icon}


            </div>





            {/* CONTENT */}

            <div>


                <p

                    className="
                    text-xs
                    text-gray-500
                    font-medium
                    "

                >

                    {title}

                </p>



                <div

                    className="
                    flex
                    items-baseline
                    gap-2
                    mt-1
                    "

                >


                    <h2

                        className="
                        text-3xl
                        font-bold
                        text-gray-900
                        "

                    >

                        {value}

                    </h2>


                    <span

                        className="
                        text-xs
                        text-gray-400
                        "

                    >

                        candidates

                    </span>


                </div>


            </div>



        </div>


    );

}


export default PipelineStatCard;