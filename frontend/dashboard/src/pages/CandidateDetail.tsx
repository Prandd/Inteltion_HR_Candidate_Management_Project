import {
    useEffect,
    useState
} from "react";


import type {
    ReactNode
} from "react";


import {
    useParams
} from "react-router-dom";


import api from "../api/axios";


import StatusDropdown from "../components/StatusDropdown";


import type {
    CandidateDetailType
} from "../types/candidate";







function CandidateDetail(){


    const {id}=useParams();



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


            const response =

                await api.get(
                    `/candidates/${id}`
                );



            setCandidate(
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






    useEffect(()=>{

        fetchCandidate();

    },[id]);








    if(loading)

        return (

            <div className="p-10">

                Loading candidate...

            </div>

        );






    if(!candidate)

        return (

            <div className="p-10">

                Candidate not found

            </div>

        );







    const confidence = Math.round(

        (candidate.extraction_confidence ?? 0)
        *
        100

    );








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
                max-w-6xl
                mx-auto
                space-y-5
                "

            >








                {/* PROFILE HEADER */}



                <div

                    className="
                    bg-white
                    border
                    rounded-2xl
                    p-6
                    flex
                    justify-between
                    "

                >




                    <div

                        className="
                        flex
                        gap-5
                        items-center
                        "

                    >



                        <div

                            className="
                            w-20
                            h-20
                            rounded-2xl
                            bg-blue-600
                            text-white
                            flex
                            items-center
                            justify-center
                            text-3xl
                            font-bold
                            "

                        >

                            {
                                candidate.full_name
                                ?.charAt(0)
                            }

                        </div>







                        <div>


                            <h1

                                className="
                                text-2xl
                                font-bold
                                "

                            >

                                {
                                    candidate.full_name
                                }

                            </h1>




                            <p className="
                            text-gray-500
                            mt-1
                            ">

                                {
                                    candidate.applied_position || "-"
                                }

                            </p>




                            <p className="
                            text-sm
                            text-gray-400
                            mt-2
                            ">

                                📍 {candidate.location || "-"}

                            </p>



                        </div>



                    </div>








                    <div

                        className="
                        flex
                        items-end
                        gap-6
                        "

                    >



                        <div>


                            <p className="
                            text-xs
                            text-gray-400
                            mb-2
                            ">

                                Status

                            </p>



                            <StatusDropdown


                                candidateId={
                                    candidate.candidate_id
                                }


                                currentStatus={
                                    candidate.status || "New"
                                }


                                onUpdate={
                                    fetchCandidate
                                }


                            />

                        </div>









                        <div

                            className="
                            w-32
                            "

                        >

                            <div className="
                            flex
                            justify-between
                            text-xs
                            mb-2
                            ">

                                <span className="text-gray-400">

                                    AI Match

                                </span>


                                <b className="text-blue-600">

                                    {confidence}%

                                </b>


                            </div>





                            <div className="
                            h-2
                            bg-gray-100
                            rounded-full
                            overflow-hidden
                            ">


                                <div

                                    className="
                                    h-full
                                    bg-blue-600
                                    rounded-full
                                    "

                                    style={{

                                        width:`${confidence}%`

                                    }}

                                />


                            </div>


                        </div>




                    </div>





                </div>









                {/* GRID */}



                <div

                    className="
                    grid
                    grid-cols-3
                    gap-5
                    "

                >






                    <div

                        className="
                        col-span-2
                        space-y-5
                        "

                    >





                        <InfoCard title="AI Summary">


                            <div

                                className="
                                bg-blue-50
                                rounded-xl
                                p-5
                                text-gray-700
                                text-sm
                                "

                            >

                                {
                                    candidate.summary ||
                                    "No summary available"
                                }


                            </div>


                        </InfoCard>








                        <InfoCard title="Experience">


                        {

                        candidate.experience?.length

                        ?

                        candidate.experience.map((exp,index)=>(


                            <div

                                key={index}

                                className="
                                border-l-2
                                border-blue-500
                                pl-5
                                mb-5
                                "

                            >

                                <h3 className="font-semibold">

                                    {exp.position}

                                </h3>


                                <p className="text-sm">

                                    {exp.company}

                                </p>



                                <p className="
                                text-xs
                                text-gray-400
                                mt-1
                                ">

                                    {exp.start_date}
                                    {" - "}
                                    {exp.end_date}

                                </p>


                            </div>


                        ))

                        :

                        <p className="text-gray-400">

                            No experience

                        </p>

                        }


                        </InfoCard>








                    </div>








                    <div

                        className="
                        space-y-5
                        "

                    >




                        <InfoCard title="Contact">


                            <InfoItem

                                label="Email"

                                value={
                                    candidate.email || "-"
                                }

                            />


                            <InfoItem

                                label="Phone"

                                value={
                                    candidate.phone || "-"
                                }

                            />


                        </InfoCard>








                        <InfoCard title="Skills">


                            <div className="
                            flex
                            flex-wrap
                            gap-2
                            ">


                            {

                            candidate.skills?.map(skill=>(


                                <span

                                    key={skill.skill}

                                    className="
                                    bg-blue-50
                                    text-blue-700
                                    px-3
                                    py-1
                                    rounded-full
                                    text-xs
                                    "

                                >

                                    {skill.skill}


                                </span>


                            ))

                            }


                            </div>


                        </InfoCard>






                        <InfoCard title="Resume">


                            {

                            candidate.resume_url

                            ?

                            <a

                                href={candidate.resume_url}

                                target="_blank"

                                className="
                                block
                                text-center
                                bg-blue-600
                                text-white
                                py-3
                                rounded-xl
                                text-sm
                                font-medium
                                "

                            >

                                Download Resume


                            </a>


                            :

                            <p className="text-gray-400">

                                No resume available

                            </p>

                            }


                        </InfoCard>



                    </div>



                </div>






            </div>



        </div>

    );


}









function InfoCard({

    title,

    children

}:{

    title:string;

    children:ReactNode;

}){


    return (

        <section

            className="
            bg-white
            border
            rounded-2xl
            p-5
            "

        >


            <h2 className="
            font-bold
            text-base
            mb-4
            ">

                {title}

            </h2>


            {children}


        </section>

    );


}







function InfoItem({

    label,

    value

}:{

    label:string;

    value:string;

}){


    return (

        <div className="mb-4">


            <p className="
            text-xs
            text-gray-400
            ">

                {label}

            </p>


            <p className="
            text-sm
            font-medium
            mt-1
            ">

                {value}

            </p>


        </div>

    );


}





export default CandidateDetail;