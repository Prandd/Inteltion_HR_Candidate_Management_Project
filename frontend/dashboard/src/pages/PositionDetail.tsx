import {
    useEffect,
    useState
} from "react";


import {
    useNavigate,
    useParams
} from "react-router-dom";


import api from "../api/axios";





interface Position {


    id:string;

    title:string;

    department:string;

    description:string;

    location:string;

    skills:string[];

    status:string;

    candidate_count:number;


}








function PositionDetail(){



    const navigate = useNavigate();


    const {

        id

    } = useParams();





    const [

        position,

        setPosition

    ] = useState<Position | null>(null);





    const [

        loading,

        setLoading

    ] = useState(true);







    useEffect(()=>{


        if(id)

            fetchPosition();


    },[id]);









    async function fetchPosition(){


        try{


            const response = await api.get(

                `/positions/${id}`

            );



            setPosition(

                response.data.data

            );


        }


        catch(error){


            console.error(error);


        }


        finally{


            setLoading(false);


        }


    }









    if(loading){


        return (

            <div className="p-10">

                Loading position...

            </div>

        );


    }









    if(!position){


        return (

            <div className="p-10">

                Position not found

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





            <button


                onClick={()=>navigate("/positions")}


                className="
                text-sm
                text-gray-500
                mb-5
                "

            >

                ← Back to Positions


            </button>









            <div


                className="
                bg-white
                border
                rounded-2xl
                p-6
                max-w-4xl
                "

            >





                <div

                    className="
                    flex
                    justify-between
                    "

                >



                    <div>


                        <h1

                            className="
                            text-3xl
                            font-bold
                            "

                        >

                            {position.title}


                        </h1>



                        <p

                            className="
                            text-gray-500
                            mt-2
                            "

                        >

                            {position.department}


                        </p>


                    </div>







                    <span

                        className="
                        bg-green-50
                        text-green-600
                        px-4
                        py-2
                        rounded-full
                        h-fit
                        "

                    >

                        {position.status}


                    </span>



                </div>









                <div

                    className="
                    mt-8
                    space-y-4
                    "

                >



                    <Info

                        label="Location"

                        value={position.location}

                    />



                    <Info

                        label="Candidates"

                        value={

                            String(

                                position.candidate_count

                            )

                        }

                    />



                </div>









                <div className="mt-8">


                    <h2

                        className="
                        font-bold
                        text-lg
                        "

                    >

                        Job Description


                    </h2>



                    <p

                        className="
                        text-gray-600
                        mt-2
                        "

                    >

                        {

                        position.description ||

                        "-"

                        }


                    </p>


                </div>









                <div className="mt-8">


                    <h2

                        className="
                        font-bold
                        text-lg
                        "

                    >

                        Required Skills


                    </h2>





                    <div

                        className="
                        flex
                        flex-wrap
                        gap-2
                        mt-3
                        "

                    >



                    {

                    position.skills.map(skill=>(


                        <span

                            key={skill}

                            className="
                            bg-blue-50
                            text-blue-600
                            px-3
                            py-1
                            rounded-full
                            text-sm
                            "

                        >

                            {skill}


                        </span>


                    ))

                    }



                    </div>


                </div>







            </div>





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

        <div

            className="
            flex
            justify-between
            "

        >

            <span className="text-gray-400">

                {label}

            </span>


            <span className="font-medium">

                {value}

            </span>


        </div>

    );


}







export default PositionDetail;