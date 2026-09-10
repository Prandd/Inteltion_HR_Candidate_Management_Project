import {
    useEffect,
    useState
} from "react";


import {
    useNavigate
} from "react-router-dom";


import api from "../api/axios";





interface Position {


    id:string;

    title:string;

    department?:string;

    location?:string;

    status?:string;

    candidate_count?:number;

    created_at?:string;


}









function Positions(){


    const navigate = useNavigate();



    const [
        positions,
        setPositions
    ] = useState<Position[]>([]);



    const [
        loading,
        setLoading
    ] = useState(true);






    useEffect(()=>{

        fetchPositions();

    },[]);






    async function fetchPositions(){


        try{


            const response =
                await api.get(
                    "/positions"
                );



            setPositions(

                Array.isArray(response.data.data)

                ?

                response.data.data

                :

                []

            );


        }


        catch(error){

            console.error(error);

        }


        finally{

            setLoading(false);

        }


    }








    function statusStyle(status:string){


        if(status==="Closed")

            return "bg-red-50 text-red-600";


        if(status==="Open")

            return "bg-green-50 text-green-600";


        return "bg-blue-50 text-blue-600";


    }







    if(loading){


        return (

            <div className="p-10">

                Loading positions...

            </div>

        );

    }









    return (


        <div


            className="

            min-h-screen

            bg-[#f7f9ff]

            p-6

            "

        >






            {/* HEADER */}



            <div


                className="

                flex

                justify-between

                items-start

                mb-6

                "

            >



                <div>


                    <h1 className="

                    text-3xl

                    font-bold

                    text-gray-900

                    ">

                        Positions

                    </h1>




                    <p className="

                    text-gray-500

                    mt-1

                    ">

                        Manage job openings and requirements

                    </p>


                </div>








                <button


                    onClick={()=>navigate(

                        "/positions/new"

                    )}


                    className="

                    bg-blue-600

                    hover:bg-blue-700

                    text-white

                    px-5

                    py-3

                    rounded-xl

                    text-sm

                    font-semibold

                    "

                >

                    + Create Position


                </button>



            </div>









            {/* STATS */}



            <div


                className="

                grid

                grid-cols-3

                gap-5

                mb-6

                "

            >



                <Stat

                    title="Total Positions"

                    value={positions.length}

                />


                <Stat

                    title="Open"

                    value={

                        positions.filter(

                            p=>p.status==="Open"

                        ).length

                    }

                />


                <Stat

                    title="Candidates"

                    value={

                        positions.reduce(

                            (sum,p)=>

                            sum+(p.candidate_count||0),

                            0

                        )

                    }

                />



            </div>









            {

            positions.length===0


            ?



            <div


                className="

                bg-white

                border

                rounded-2xl

                p-12

                text-center

                "

            >


                <p className="

                text-gray-700

                font-semibold

                ">

                    No positions yet


                </p>


                <p className="

                text-sm

                text-gray-400

                mt-2

                ">

                    Create a position to start matching candidates


                </p>


            </div>





            :





            <div


                className="

                grid

                grid-cols-3

                gap-5

                "

            >



            {

            positions.map(position=>(



                <div


                    key={position.id}


                    onClick={()=>navigate(

                        `/positions/${position.id}`

                    )}


                    className="

                    bg-white

                    border

                    border-gray-200

                    rounded-2xl

                    p-5

                    cursor-pointer

                    hover:shadow-md

                    transition

                    "

                >







                    <div


                        className="

                        flex

                        justify-between

                        "

                    >



                        <div className="flex gap-3">


                            <div


                                className="

                                w-10

                                h-10

                                rounded-xl

                                bg-blue-50

                                flex

                                items-center

                                justify-center

                                "

                            >

                                💼


                            </div>




                            <div>


                                <h2 className="

                                font-bold

                                text-gray-900

                                ">


                                    {position.title}


                                </h2>



                                <p className="

                                text-xs

                                text-gray-400

                                mt-1

                                ">


                                    {position.department || "-"}


                                </p>


                            </div>


                        </div>







                        <span


                            className={`

                            text-xs

                            px-3

                            py-1

                            rounded-full

                            font-medium

                            ${

                            statusStyle(

                                position.status || "Open"

                            )

                            }

                            `}


                        >

                            {

                                position.status || "Open"

                            }


                        </span>



                    </div>









                    <div className="

                    mt-5

                    space-y-3

                    ">



                        <Info

                            label="Location"

                            value={
                                position.location || "-"
                            }

                        />



                        <Info

                            label="Candidates"

                            value={

                                String(

                                position.candidate_count || 0

                                )

                            }

                        />



                    </div>







                    <div


                        className="

                        mt-5

                        pt-4

                        border-t

                        flex

                        justify-between

                        "

                    >


                        <span className="

                        text-xs

                        text-gray-400

                        ">

                            AI Matching Enabled

                        </span>



                        <span className="

                        text-blue-600

                        text-sm

                        font-semibold

                        ">

                            View →

                        </span>


                    </div>




                </div>



            ))

            }


            </div>


            }





        </div>


    );


}








function Stat({

    title,

    value

}:{

    title:string;

    value:number;

}){


    return (

        <div className="

        bg-white

        border

        rounded-2xl

        p-5

        ">


            <p className="

            text-sm

            text-gray-500

            ">

                {title}

            </p>


            <p className="

            text-3xl

            font-bold

            mt-2

            ">

                {value}

            </p>


        </div>

    );


}








function Info({

    label,

    value

}:{

    label:string;

    value:string;

}){


    return (

        <div className="

        flex

        justify-between

        text-sm

        ">


            <span className="text-gray-400">

                {label}

            </span>


            <span className="font-medium">

                {value}

            </span>


        </div>

    );

}




export default Positions;