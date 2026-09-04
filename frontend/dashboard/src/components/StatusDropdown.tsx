import { useState } from "react";
import api from "../api/axios";


interface Props {

    candidateId: string;

    currentStatus: string;

    onUpdate?: () => void;

}



function StatusDropdown({

    candidateId,

    currentStatus,

    onUpdate

}: Props){



    const [status,setStatus] =
        useState(currentStatus);



    const [loading,setLoading] =
        useState(false);





    const statuses = [

        "New",

        "Review",

        "Assessment",

        "Interview",

        "CV passed",

        "Hired",

        "Rejected",

        "Needs information"

    ];






    async function updateStatus(
        value:string
    ){


        try{


            setLoading(true);



            setStatus(value);



            await api.put(

                `/candidates/${candidateId}`,

                {

                    status:value

                }

            );



            console.log(
                "Status updated:",
                value
            );



            if(onUpdate){

                onUpdate();

            }



        }
        catch(error){


            console.error(
                error
            );


            alert(
                "Update status failed"
            );

            setStatus(
                currentStatus
            );


        }
        finally{


            setLoading(false);


        }


    }





    return (


        <div>


            <label
                className="
                block
                font-bold
                mb-2
                "
            >

                Status

            </label>




            <select


                value={status}


                disabled={loading}


                onChange={
                    e =>
                    updateStatus(
                        e.target.value
                    )
                }


                className="

                border

                rounded-lg

                px-3

                py-2

                "

            >



                {
                    statuses.map(
                        s => (

                            <option

                                key={s}

                                value={s}

                            >

                                {s}

                            </option>

                        )

                    )
                }



            </select>



        </div>


    );


}



export default StatusDropdown;