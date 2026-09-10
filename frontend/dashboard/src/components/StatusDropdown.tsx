import {
    useState
} from "react";


import api from "../api/axios";




interface Props {

    candidateId:string;

    currentStatus:string;

    onUpdate?:()=>void;

}







function StatusDropdown({

    candidateId,

    currentStatus,

    onUpdate

}:Props){



    const [

        status,

        setStatus

    ] = useState(currentStatus);





    const [

        loading,

        setLoading

    ] = useState(false);





    const [

        open,

        setOpen

    ] = useState(false);









    const statuses = [

        "New",

        "Assessment",

        "Interview",

        "Hired",

        "Rejected",

        "Needs information"

    ];









    function statusStyle(value:string){


        switch(value){


            case "Assessment":

                return {

                    badge:
                    "bg-orange-50 text-orange-600",

                    dot:
                    "bg-orange-500"

                };



            case "Interview":

                return {

                    badge:
                    "bg-purple-50 text-purple-600",

                    dot:
                    "bg-purple-500"

                };



            case "Hired":

                return {

                    badge:
                    "bg-green-50 text-green-600",

                    dot:
                    "bg-green-500"

                };



            case "Rejected":

                return {

                    badge:
                    "bg-red-50 text-red-600",

                    dot:
                    "bg-red-500"

                };



            case "Needs information":

                return {

                    badge:
                    "bg-gray-100 text-gray-600",

                    dot:
                    "bg-gray-400"

                };



            default:

                return {

                    badge:
                    "bg-blue-50 text-blue-600",

                    dot:
                    "bg-blue-500"

                };


        }


    }







    async function updateStatus(

        value:string

    ){


        try{


            setLoading(true);


            setStatus(value);


            setOpen(false);





            await api.put(

                `/candidates/${candidateId}`,

                {

                    status:value

                }

            );






            if(onUpdate){

                onUpdate();

            }



        }


        catch(error){


            console.error(error);


            setStatus(currentStatus);


        }


        finally{


            setLoading(false);


        }


    }









    const current = statusStyle(status);








    return (



        <div

            className="

            relative

            "

        >








            {/* STATUS BUTTON */}



            <button


                disabled={loading}


                onClick={

                    ()=>setOpen(!open)

                }


                className={`

                flex

                items-center

                gap-2

                px-4

                py-2

                rounded-xl

                text-sm

                font-semibold

                transition

                hover:shadow-sm

                ${

                    current.badge

                }

                `}


            >



                <span


                    className={`

                    w-2

                    h-2

                    rounded-full

                    ${

                        current.dot

                    }

                    `}


                />




                {

                loading

                ?

                "Updating..."

                :

                status

                }




                <span

                    className="

                    text-xs

                    opacity-60

                    "

                >

                    ▾

                </span>




            </button>









            {/* MENU */}



            {

            open &&


            <div


                className="

                absolute

                right-0

                mt-2

                w-52

                bg-white

                border

                border-gray-200

                rounded-xl

                shadow-lg

                p-2

                z-50

                "

            >





                {

                statuses.map(item=>{


                    const style = statusStyle(item);



                    return (



                    <button


                        key={item}


                        onClick={

                            ()=>updateStatus(item)

                        }



                        className={`

                        w-full

                        flex

                        items-center

                        gap-3

                        px-3

                        py-2.5

                        rounded-lg

                        text-sm

                        transition

                        hover:bg-gray-50


                        ${

                        item===status

                        ?

                        "bg-gray-50 font-semibold"

                        :

                        "text-gray-700"

                        }


                        `}


                    >



                        <span


                            className={`

                            w-2

                            h-2

                            rounded-full

                            ${

                                style.dot

                            }

                            `}


                        />





                        {item}





                    </button>


                    );


                })

                }



            </div>


            }



        </div>


    );


}





export default StatusDropdown;