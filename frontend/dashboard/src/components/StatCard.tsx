interface Props {

    title:string;

    value:number;

}





function StatCard({

    title,

    value

}:Props){



    return (


        <div


            className="

            bg-white

            border

            border-gray-200

            rounded-xl

            p-4

            hover:shadow-sm

            transition

            "


        >





            {/* TITLE */}



            <p


                className="

                text-xs

                font-medium

                text-gray-500

                "

            >

                {title}


            </p>









            {/* VALUE */}



            <h2


                className="

                text-3xl

                font-bold

                text-gray-900

                mt-3

                "

            >

                {value}


            </h2>









            {/* FOOTER */}



            <div


                className="

                flex

                items-center

                gap-2

                mt-3

                "

            >


                <div


                    className="

                    w-2

                    h-2

                    rounded-full

                    bg-blue-600

                    "

                />



                <p


                    className="

                    text-xs

                    text-gray-400

                    "

                >

                    Candidates


                </p>


            </div>






        </div>


    );


}



export default StatCard;