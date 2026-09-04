import { useState } from "react";
import { useNavigate } from "react-router-dom";

import api from "../api/axios";


function UploadCandidate(){


    const navigate = useNavigate();


    const [file,setFile] =
        useState<File | null>(null);


    const [loading,setLoading] =
        useState(false);




    async function upload(){


        if(!file){

            alert("Please select resume");

            return;

        }



        const formData =
            new FormData();



        formData.append(
            "file",
            file
        );





        try{


            setLoading(true);



            const response =
                await api.post(

                    "/candidates/upload",

                    formData,

                    {
                        headers:{
                            "Content-Type":
                            "multipart/form-data"
                        }
                    }

                );



            console.log(
                "Upload response:",
                response.data
            );





            alert(
                "Upload success"
            );



            // กลับ Dashboard
            // Dashboard จะ fetch candidate ใหม่

            navigate("/", {
                replace:true
            });



        }
        catch(error){


            console.error(
                "Upload error:",
                error
            );



            alert(
                "Upload failed"
            );


        }
        finally{


            setLoading(false);


        }


    }






    return (

        <div
            className="
            bg-gray-50
            min-h-screen
            p-8
            "
        >


            <div
                className="
                bg-white
                rounded-xl
                p-8
                max-w-xl
                "
            >


                <h1
                    className="
                    text-3xl
                    font-bold
                    mb-6
                    "
                >

                    Upload Candidate Resume

                </h1>





                <input

                    type="file"

                    accept=".pdf,.docx"

                    onChange={
                        (e)=>

                        setFile(
                            e.target.files?.[0] ?? null
                        )
                    }


                    className="
                    border
                    p-3
                    rounded
                    w-full
                    "

                />





                {
                    file && (

                    <p
                        className="
                        mt-3
                        text-gray-600
                        "
                    >

                        Selected:
                        {" "}
                        {file.name}

                    </p>

                    )
                }





                <button

                    onClick={upload}

                    disabled={loading}


                    className="
                    mt-6
                    bg-blue-600
                    text-white
                    px-6
                    py-3
                    rounded-lg
                    disabled:bg-gray-400
                    "

                >

                    {
                        loading
                        ?
                        "Uploading..."
                        :
                        "Upload CV"
                    }


                </button>



            </div>


        </div>

    );


}


export default UploadCandidate;