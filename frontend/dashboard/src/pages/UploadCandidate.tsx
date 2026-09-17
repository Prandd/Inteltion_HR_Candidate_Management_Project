import {
    useEffect,
    useState
} from "react";

import {
    useNavigate
} from "react-router-dom";

import api from "../api/axios";

import DuplicateCandidateModal
from "../components/DuplicateCandidateModal";

import {
    useLocation
} from "react-router-dom";

interface UploadItem{

    file:File;

    progress:number;

    status:
    |
    "ready"
    |
    "uploading"
    |
    "success"
    |
    "error";

}


function UploadCandidate(){

    const navigate = useNavigate();

    const [
        files,
        setFiles
    ] = useState<UploadItem[]>([]);


    const [
        uploading,
        setUploading
    ] = useState(false);


    const [
        stage,
        setStage
    ] = useState("");


    const [
        duplicateCandidate,
        setDuplicateCandidate
    ] = useState<any>(null);

    const [
        duplicateFileIndex,
        setDuplicateFileIndex
    ] = useState<number|null>(null);

    const [
        duplicateCandidateId,
        setDuplicateCandidateId
    ] = useState<string|null>(null);

    const location = useLocation();

    console.log(
        "LOCATION STATE",
        location.state
    );

    const forceUpload =
        location.state?.forceUpload ?? false;


    const [
        forceCandidateId,
        setForceCandidateId
    ] = useState<string|null>(null);


     useEffect(()=>{

        if(
                location.state?.forceUpload
        ){



            setForceCandidateId(
                location.state.duplicateCandidateId
            );


            setStage(
                "Ready to replace duplicate candidate"
            );

        }

    },[location.state]);


    function handleFiles(selected:File[]){

        const newFiles = selected.map(file=>({
            file,
            progress:0,
            status:"ready" as const
        }));

        setFiles(prev=>[
            ...prev,
            ...newFiles
        ]);

    }



    function onFileChange(
        e:React.ChangeEvent<HTMLInputElement>
    ){

        const selected =
            Array.from(
                e.target.files || []
            );

        handleFiles(selected);

    }




    async function uploadFiles(){

        if(files.length===0)
            return;


        setUploading(true);

        setStage(
            "Preparing files..."
        );


        let shouldRedirect = true;


        for(
            let i=0;
            i<files.length;
            i++
        ){

            const success =
                await uploadSingle(
                    i,
                    forceUpload
                );


            if(!success){

                shouldRedirect = false;

                break;

            }

        }


        setUploading(false);



        if(shouldRedirect){

            setTimeout(()=>{

                navigate("/");

            },1000);

        }

    }





    async function uploadSingle(
        index:number,
        forceUpload=false,
        candidateId:string|null=null
    ):Promise<boolean>{

        const item = files[index];

        const formData = new FormData();

        formData.append(
            "file",
            item.file
        );

        if(
            forceUpload &&
            forceCandidateId
        ){

            formData.append(
                "candidate_id",
                forceCandidateId
            );

        }


        updateFile(
            index,
            {
                status:"uploading",
                progress:5
            }
        );


        setStage(
            "Uploading resume..."
        );


        try{
            


            const uploadUrl =

                forceUpload && candidateId

                ?

                `/candidates/upload?force=true&candidate_id=${candidateId}`

                :

                "/candidates/upload";


            console.log(
                "FINAL UPLOAD",
                {
                    forceUpload,
                    forceCandidateId,
                    uploadUrl
                }
            );


            const response = await api.post(

                uploadUrl,

                formData,

                {
                    headers:{
                        "Content-Type":
                        "multipart/form-data"
                    },


                    onUploadProgress:(event)=>{


                        const percent = Math.round(

                            (
                                event.loaded * 30
                            )
                            /
                            (
                                event.total || 1
                            )

                        );



                        updateFile(

                            index,

                            {

                                progress:
                                Math.min(
                                    percent,
                                    30
                                )

                            }

                        );


                    }

                }

            );



            if(response.data?.duplicate && !forceUpload){

                setDuplicateCandidate(
                    response.data.candidate
                );


                setDuplicateFileIndex(
                    index
                );


                setDuplicateCandidateId(
                    response.data.candidate.candidate_id
                );


                updateFile(
                    index,
                    {
                        status:"error"
                    }
                );


                return false;

            }



            setStage(
                "Extracting CV information..."
            );


            updateFile(
                index,
                {
                    progress:55
                }
            );


            await new Promise(resolve=>
                setTimeout(resolve,800)
            );



            setStage(
                "AI analyzing candidate profile..."
            );


            updateFile(
                index,
                {
                    progress:75
                }
            );


            await new Promise(resolve=>
                setTimeout(resolve,1200)
            );



            setStage(
                "Saving candidate profile..."
            );


            updateFile(
                index,
                {
                    progress:90
                }
            );


            await new Promise(resolve=>
                setTimeout(resolve,700)
            );



            updateFile(
                index,
                {
                    progress:100,
                    status:"success"
                }
            );


            setStage(
                "Completed successfully"
            );

            return true;


        }
        catch(error){


            console.error(error);


            updateFile(
                index,
                {
                    status:"error"
                }
            );


            setStage(
                "Upload failed"
            );

            return false;

        }

    }

    function updateFile(
    index:number,
    data:Partial<UploadItem>
){

    setFiles(prev=>
        prev.map(
            (item,i)=>
            i===index
            ?
            {
                ...item,
                ...data
            }
            :
            item
        )
    );

}



function removeFile(index:number){

    if(uploading)
        return;


    setFiles(prev=>
        prev.filter(
            (_,i)=>i!==index
        )
    );

}



return (

    <>

    {
        duplicateCandidate &&

        <DuplicateCandidateModal

            candidate={duplicateCandidate}

            onClose={()=>{
                setDuplicateCandidate(null);
                setDuplicateFileIndex(null);
            }}

            onConfirmUpload={async()=>{

                if(
                    duplicateFileIndex !== null
                ){

                    const success =
                        await uploadSingle(
                            duplicateFileIndex,
                            true,
                            duplicateCandidateId
                        );


                    if(success){

                        setDuplicateCandidate(null);

                        setDuplicateFileIndex(null);

                        setForceCandidateId(null);


                        setStage(
                            "Duplicate candidate uploaded successfully"
                        );


                        setTimeout(()=>{

                            navigate("/");

                        },1500);

                    }

                }

            }}

        />
    }



    <div

        className="
        min-h-screen
        bg-[#f7f9ff]
        p-6
        "

    >

        <div

            className="
            max-w-4xl
            mx-auto
            space-y-6
            "

        >


            <div>


                <button

                    onClick={()=>navigate("/")}

                    className="
                    text-sm
                    text-gray-500
                    mb-4
                    "

                >

                    ← Back

                </button>



                <h1

                    className="
                    text-3xl
                    font-bold
                    text-gray-900
                    "

                >

                    Add Candidate

                </h1>



                <p

                    className="
                    text-gray-500
                    mt-1
                    "

                >

                    Upload resumes and automatically extract candidate information

                </p>


            </div>





            <div

                className="
                bg-white
                border
                rounded-2xl
                p-6
                "

            >



                <label

                    className="
                    h-56
                    border-2
                    border-dashed
                    border-blue-300
                    rounded-2xl
                    flex
                    flex-col
                    items-center
                    justify-center
                    cursor-pointer
                    hover:bg-blue-50
                    transition
                    "

                >


                    <div

                        className="
                        w-14
                        h-14
                        rounded-full
                        bg-blue-50
                        text-blue-600
                        flex
                        items-center
                        justify-center
                        text-3xl
                        mb-3
                        "

                    >

                        ↑

                    </div>



                    <p

                        className="
                        font-semibold
                        text-blue-600
                        "

                    >

                        Click to upload CV

                    </p>



                    <p

                        className="
                        text-sm
                        text-gray-400
                        mt-1
                        "

                    >

                        PDF, DOC, DOCX up to 10MB

                    </p>



                    <input

                        hidden

                        multiple

                        type="file"

                        accept=".pdf,.doc,.docx"

                        onChange={onFileChange}

                    />


                </label>





                <div className="mt-6 space-y-3">


                    {
                        files.map((item,index)=>(


                            <div

                                key={index}

                                className="
                                border
                                rounded-xl
                                p-4
                                "

                            >


                                <div

                                    className="
                                    flex
                                    justify-between
                                    "

                                >

                                    <div>


                                        <p className="font-medium">

                                            {item.file.name}

                                        </p>



                                        <p className="text-xs mt-1 text-gray-500">


                                            {
                                                item.status==="ready" &&
                                                "Ready to upload"
                                            }


                                            {
                                                item.status==="uploading" &&
                                                `Processing ${item.progress}%`
                                            }


                                            {
                                                item.status==="success" &&
                                                "✓ Uploaded successfully"
                                            }


                                            {
                                                item.status==="error" &&
                                                "Upload failed"
                                            }


                                        </p>


                                    </div>



                                    <button

                                        onClick={()=>
                                            removeFile(index)
                                        }

                                        className="
                                        text-red-500
                                        "

                                    >

                                        ×

                                    </button>


                                </div>




                                {
                                    item.status==="uploading" &&

                                    <div

                                        className="
                                        mt-3
                                        h-2
                                        bg-gray-100
                                        rounded-full
                                        overflow-hidden
                                        "

                                    >

                                        <div

                                            className="
                                            h-full
                                            bg-blue-600
                                            transition-all
                                            duration-300
                                            "

                                            style={{
                                                width:
                                                `${item.progress}%`
                                            }}

                                        />


                                    </div>

                                }


                            </div>


                        ))
                    }


                </div>





                {
                    uploading &&

                    <p

                        className="
                        text-center
                        text-sm
                        text-gray-500
                        mt-4
                        "

                    >

                        {stage}

                    </p>

                }






                <button

                    disabled={
                        files.length===0 ||
                        uploading
                    }


                    onClick={uploadFiles}


                    className="
                    mt-6
                    w-full
                    bg-blue-600
                    text-white
                    py-3
                    rounded-xl
                    font-semibold
                    disabled:bg-gray-300
                    "

                >


                    {
                        uploading
                        ?
                        "Processing..."
                        :
                        forceUpload

                        ?

                        "Upload Anyway"

                        :

                        `Upload ${files.length} CV`
                    }


                </button>


            </div>


        </div>


    </div>


    </>

);


}


export default UploadCandidate;