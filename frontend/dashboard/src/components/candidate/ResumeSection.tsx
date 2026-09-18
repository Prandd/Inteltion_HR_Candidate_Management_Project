import type {
    CandidateDetailType
} from "../../types/candidate";


interface Props {

    candidate: CandidateDetailType;

}



function ResumeSection({

    candidate

}: Props){


    const resumeUrl =
        candidate.resume_url;



    function openResume(){


        console.log(
            "OPEN RESUME:",
            resumeUrl
        );


        if(!resumeUrl){

            console.error(
                "Resume URL is empty"
            );

            return;

        }


        window.open(
            resumeUrl,
            "_blank",
            "noopener,noreferrer"
        );

    }




    function downloadResume(){


        console.log(
            "DOWNLOAD RESUME:",
            resumeUrl
        );


        if(!resumeUrl){

            console.error(
                "Resume URL is empty"
            );

            return;

        }


        const a =
            document.createElement("a");


        a.href = resumeUrl;


        a.download =
            candidate.resume_filename
            ||
            "resume.pdf";


        document.body.appendChild(a);


        a.click();


        document.body.removeChild(a);


    }




    return (

        <section

            className="
            bg-white
            border
            rounded-2xl
            p-5
            "

        >


            <h2

                className="
                text-sm
                font-bold
                mb-4
                "

            >

                Resume

            </h2>



            <p

                className="
                text-sm
                text-gray-600
                truncate
                "

            >

                {
                    candidate.resume_filename
                    ||
                    "No resume"
                }

            </p>



            <div

                className="
                flex
                gap-3
                mt-4
                "

            >


                <button

                    onClick={openResume}

                    className="
                    px-4
                    py-2
                    rounded-lg
                    bg-blue-50
                    text-blue-600
                    text-sm
                    font-medium
                    "

                >

                    View

                </button>



                <button

                    onClick={downloadResume}

                    className="
                    px-4
                    py-2
                    rounded-lg
                    bg-gray-100
                    text-gray-700
                    text-sm
                    font-medium
                    "

                >

                    Download

                </button>


            </div>


        </section>

    );

}


export default ResumeSection;