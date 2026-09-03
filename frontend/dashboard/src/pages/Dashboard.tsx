import {
    useEffect,
    useState
} from "react";


import api from "../api/axios";


import CandidateCard from "../components/CandidateCard";
import StatCard from "../components/StatCard";
import RequisitionCard from "../components/RequisitionCard";


import type {
    CandidateSummary
} from "../types/candidate";





function Dashboard(){



    const [
        candidates,
        setCandidates
    ] = useState<CandidateSummary[]>([]);



    const [
        loading,
        setLoading
    ] = useState(true);



    const [
        error,
        setError
    ] = useState("");







    useEffect(()=>{


        fetchCandidates();


    }, []);








    async function fetchCandidates(){


        try{


            setLoading(true);

            setError("");



            const response =
                await api.get(
                    "/candidates"
                );



            console.log(
                "Candidates:",
                response.data.data
            );



            setCandidates(
                response.data.data || []
            );



        }
        catch(err){


            console.error(
                err
            );


            setError(
                "Cannot load candidates"
            );


        }
        finally{


            setLoading(false);


        }


    }








    if(loading){


        return (

            <div className="p-10">

                Loading candidates...

            </div>

        );

    }






    if(error){


        return (

            <div
                className="
                p-10
                text-red-600
                "
            >

                {error}

            </div>

        );

    }









    return (

        <div
            className="
            p-8
            pt-10
            "
        >


            {/* Dashboard Header */}

            <div
                className="
                mb-10
                "
            >


                <h1
                    className="
                    text-3xl
                    font-bold
                    "
                >

                    Dashboard

                </h1>



                <p
                    className="
                    text-gray-500
                    "
                >

                    Manage your recruitment pipeline

                </p>


            </div>









            {/* Statistics */}


            <div
                className="
                grid
                grid-cols-1
                md:grid-cols-3
                gap-8
                mb-10
                "
            >


                <StatCard

                    title="Active Candidates"

                    value={
                        candidates.length
                    }

                />



                <StatCard

                    title="Avg. Time To Hire"

                    value="24 Days"

                />



                <StatCard

                    title="Open Positions"

                    value="8"

                />


            </div>









            {/* Main Content */}


            <div
                className="
                grid
                grid-cols-1
                lg:grid-cols-4
                gap-8
                items-start
                "
            >







                {/* Talent Roster */}


                <section

                    className="
                    lg:col-span-3
                    bg-white
                    rounded-xl
                    p-8
                    "

                >



                    <h2

                        className="
                        text-2xl
                        font-bold
                        mb-8
                        "

                    >

                        Talent Roster

                    </h2>







                    <div

                        className="
                        grid
                        grid-cols-1
                        md:grid-cols-2
                        gap-6
                        "

                    >



                        {
                            candidates.map(

                                candidate => (


                                    <CandidateCard


                                        key={
                                            candidate.candidate_id
                                        }


                                        candidate={
                                            candidate
                                        }


                                    />


                                )

                            )
                        }



                    </div>




                </section>












                {/* Active Requisitions */}



                <section

                    className="
                    "

                >


                    <h2

                        className="
                        text-2xl
                        font-bold
                        mb-8
                        "

                    >

                        Active Requisitions

                    </h2>





                    <div

                        className="
                        space-y-6
                        "

                    >




                        <RequisitionCard


                            title="AI Engineer"


                            location="Remote / HQ"


                            candidates={12}


                        />





                        <RequisitionCard


                            title="Data Engineer"


                            location="Bangkok"


                            candidates={8}


                        />




                    </div>




                </section>







            </div>





        </div>

    );

}



export default Dashboard;