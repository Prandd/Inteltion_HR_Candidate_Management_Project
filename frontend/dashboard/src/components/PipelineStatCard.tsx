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


        blue:
        "bg-blue-50 text-blue-600",


        orange:
        "bg-orange-50 text-orange-600",


        purple:
        "bg-purple-50 text-purple-600",


        green:
        "bg-green-50 text-green-600",


        red:
        "bg-red-50 text-red-600"


    };






    return (



        <div


            className="

            bg-white

            border

            border-gray-200

            rounded-xl

            px-4

            py-3

            h-[92px]

            flex

            items-center

            gap-4

            hover:shadow-sm

            transition

            "

        >





            {/* ICON */}


            <div


                className={`

                w-10

                h-10

                rounded-xl

                flex

                items-center

                justify-center

                text-base

                font-semibold

                ${theme[color]}

                `}


            >

                {icon}


            </div>









            {/* TEXT */}



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

                    items-end

                    gap-2

                    mt-1

                    "

                >


                    <h2


                        className="

                        text-2xl

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

                        mb-1

                        "

                    >

                        Candidates


                    </span>


                </div>



            </div>






        </div>



    );


}





export default PipelineStatCard;