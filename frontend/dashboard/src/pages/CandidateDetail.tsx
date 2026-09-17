import {
    useEffect,
    useState
} from "react";


import {
    useParams,
    useNavigate
} from "react-router-dom";


import api from "../api/axios";


import type {
    CandidateDetailType
} from "../types/candidate";



import CandidateHeader from "../components/candidate/CandidateHeader";

import CandidateSummary from "../components/candidate/CandidateSummary";

import ExperienceSection from "../components/candidate/ExperienceSection";

import EducationSection from "../components/candidate/EducationSection";

import SkillsSection from "../components/candidate/SkillsSection";

import ContactSection from "../components/candidate/ContactSection";

import ResumeSection from "../components/candidate/ResumeSection";

import StatusHistorySection from "../components/candidate/StatusHistorySection";

import CommentSection from "../components/candidate/CommentSection";

import SectionCard from "../components/candidate/SectionCard";

import {
    useLocation,
} from "react-router-dom";



function CandidateDetail(){


    const {
        id
    } = useParams();



    const navigate = useNavigate();


    const location = useLocation();


    const fromDuplicateUpload =
    location.state?.fromDuplicateUpload;

    const [
        candidate,
        setCandidate
    ] = useState<CandidateDetailType|null>(null);



    const [
        loading,
        setLoading
    ] = useState(true);







    async function fetchCandidate(){


        if(!id)
            return;



        try{


            const res =
                await api.get(
                    `/candidates/${id}`
                );


            setCandidate(
                res.data.data
            );


        }
        catch(err){

            console.error(err);

        }
        finally{

            setLoading(false);

        }


    }







    async function deleteCandidate(){


        if(
            !window.confirm(
                "Are you sure you want to delete this candidate?"
            )
        )
            return;




        try{


            await api.delete(
                `/candidates/${id}`
            );


            navigate("/");


        }
        catch(err){

            console.error(err);

        }


    }







    useEffect(()=>{

        fetchCandidate();

    },[id]);







    if(loading){

        return (

            <div className="p-10">

                Loading candidate...

            </div>

        );

    }





    if(!candidate){

        return (

            <div className="p-10">

                Candidate not found

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


            <div

                className="
                max-w-7xl
                mx-auto
                space-y-6
                "

            >




                {/* HEADER */}


                <CandidateHeader

                    candidate={candidate}

                    onDelete={deleteCandidate}

                    onUpdate={fetchCandidate}

                />


            {
                    fromDuplicateUpload &&

                    <div
                        className="
                        bg-orange-50
                        border
                        border-orange-200
                        rounded-xl
                        p-4
                        flex
                        justify-between
                        items-center
                        "
                    >

                        <div>

                            <p className="
                            text-sm
                            font-semibold
                            text-orange-700
                            ">
                                Duplicate candidate detected
                            </p>


                            <p className="
                            text-xs
                            text-orange-600
                            mt-1
                            ">
                                You can return to upload and replace this candidate.
                            </p>

                        </div>


                        <button

                            onClick={()=>{

                                

                                console.log(
                                    "SEND STATE",
                                    {
                                        forceUpload:true,
                                        duplicateCandidateId:candidate.candidate_id
                                    }
                                );


                                navigate(
                                    "/upload",
                                    {
                                        state:{
                                            forceUpload:true,
                                            duplicateCandidateId:candidate.candidate_id
                                        }
                                    }
                                );

                            }}

                            className="
                            px-4
                            py-2
                            rounded-xl
                            bg-orange-500
                            text-white
                            "

                        >

                            Upload Anyway

                        </button>


                    </div>
                }






                <div

                    className="
                    grid
                    grid-cols-12
                    gap-6
                    "

                >





                    {/* LEFT CONTENT */}


                    <div

                        className="
                        col-span-8
                        space-y-6
                        "

                    >





                        <CandidateSummary

                            candidate={candidate}

                        />







                        <SectionCard

                            title="Experience"

                        >

                            {

                                candidate.experience?.length

                                ?

                                <ExperienceSection

                                    candidate={candidate}

                                />

                                :

                                <p className="text-gray-400">

                                    No experience available

                                </p>

                            }


                        </SectionCard>









                        <SectionCard

                            title="Education"

                        >


                            {

                                candidate.education?.length

                                ?

                                <EducationSection

                                    candidate={candidate}

                                />

                                :

                                <p className="text-gray-400">

                                    No education available

                                </p>


                            }


                        </SectionCard>









                        <CommentSection

                            candidate={candidate}

                            onUpdate={fetchCandidate}

                        />





                    </div>









                    {/* RIGHT SIDEBAR */}



                    <div

                        className="
                        col-span-4
                        space-y-6
                        "

                    >





                        <ContactSection

                            candidate={candidate}

                        />







                        <ResumeSection

                            candidate={candidate}

                        />









                        <SectionCard

                            title="Skills"

                        >


                            {

                                candidate.skills?.length

                                ?

                                <SkillsSection

                                    candidate={candidate}

                                />

                                :

                                <p className="text-gray-400">

                                    No skills available

                                </p>


                            }


                        </SectionCard>








                        <StatusHistorySection

                            candidate={candidate}

                        />






                    </div>



                </div>





            </div>


        </div>


    );

}



export default CandidateDetail;