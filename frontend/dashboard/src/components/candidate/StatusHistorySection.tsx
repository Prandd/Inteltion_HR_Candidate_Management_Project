import type {
    CandidateDetailType
} from "../../types/candidate";



interface Props {

    candidate: CandidateDetailType;

}





function StatusHistorySection({

    candidate

}:Props){



    const history =
        candidate.status_history ?? [];




    return (

        <section

            className="
            bg-white
            border
            rounded-2xl
            p-5
            "

        >



            <div

                className="
                flex
                justify-between
                items-center
                mb-6
                "

            >

                <div>


                    <h2

                        className="
                        text-sm
                        font-bold
                        text-gray-900
                        uppercase
                        "

                    >

                        Status History & Audit Trail

                    </h2>



                    <p

                        className="
                        text-xs
                        text-gray-400
                        mt-1
                        "

                    >

                        Track candidate status changes and activities

                    </p>


                </div>





                <span

                    className="
                    text-xs
                    bg-gray-100
                    text-gray-600
                    px-3
                    py-1
                    rounded-full
                    "

                >

                    {history.length} events

                </span>



            </div>









            {

                history.length > 0

                ?

                <div

                    className="
                    space-y-6
                    "

                >


                    {

                    history.map(

                        (item,index)=>(


                            <div

                                key={index}

                                className="
                                relative
                                pl-8
                                "

                            >



                                {/* Timeline line */}


                                {

                                index !== history.length-1 &&


                                <div

                                className={`
                                absolute
                                left-0
                                top-2
                                w-4
                                h-4
                                rounded-full
                                border-4

                                ${
                                item.status === "CV rejected"

                                ?

                                "bg-red-600 border-red-100"

                                :

                                "bg-blue-600 border-blue-100"

                                }

                                `}

                                />

                                }






                                {/* Timeline dot */}


                                <div

                                className={`
                                absolute
                                left-0
                                top-2
                                w-4
                                h-4
                                rounded-full
                                border-4

                                ${
                                item.status === "CV rejected"

                                ?

                                "bg-red-600 border-red-100"

                                :

                                "bg-blue-600 border-blue-100"

                                }

                                `}

/>







                                <div>


                                    {/* STATUS + TIME */}


                                    <div

                                        className="
                                        flex
                                        justify-between
                                        gap-3
                                        "

                                    >



                                        <h3

                                            className="
                                            text-sm
                                            font-semibold
                                            text-gray-900
                                            "

                                        >

                                            {item.status}

                                        </h3>





                                        <p

                                            className="
                                            text-xs
                                            text-gray-400
                                            whitespace-nowrap
                                            "

                                        >

                                            {

                                            item.changed_at

                                            ?

                                            new Date(
                                                item.changed_at
                                            )
                                            .toLocaleString(
                                                "en-GB",
                                                {
                                                    dateStyle:"medium",
                                                    timeStyle:"short"
                                                }
                                            )

                                            :

                                            "-"

                                            }


                                        </p>



                                    </div>









                                    {/* DETAILS */}


                                    <div

                                        className="
                                        mt-3
                                        text-sm
                                        text-gray-600
                                        space-y-2
                                        "

                                    >





                                        {
                                            item.previous_status &&


                                            <p>


                                                <span

                                                    className="
                                                    text-gray-400
                                                    "

                                                >

                                                    Previous status:

                                                </span>


                                                {" "}


                                                <span

                                                    className="
                                                    font-medium
                                                    text-gray-700
                                                    "

                                                >

                                                    {
                                                        item.previous_status
                                                    }

                                                </span>



                                            </p>

                                        }







                                        <p>


                                            <span

                                                className="
                                                text-gray-400
                                                "

                                            >

                                                Action:

                                            </span>


                                            {" "}


                                           {
                                            item.status === "CV rejected"

                                            ?

                                            `Rejected after ${item.previous_status || "-"}`

                                            :

                                            item.action || "-"
                                        }


                                        </p>







                                        <p>


                                            <span

                                                className="
                                                text-gray-400
                                                "

                                            >

                                                Changed by:

                                            </span>


                                            {" "}


                                            {
                                                item.changed_by
                                                ||
                                                "System"
                                            }


                                        </p>






                                        {


                                            <div

                                                className="
                                                mt-3
                                                bg-red-50
                                                border
                                                border-red-100
                                                rounded-lg
                                                px-3
                                                py-2
                                                text-xs
                                                text-red-600
                                                "

                                            >

                                                Rejected after:

                                                {" "}

                                                <b>
                                                    {item.previous_status}
                                                </b>


                                            </div>


                                        }



                                    </div>




                                </div>




                            </div>


                        )

                    )

                    }



                </div>


                :


                <p

                    className="
                    text-sm
                    text-gray-400
                    "

                >

                    No status history available

                </p>


            }



        </section>

    );

}



export default StatusHistorySection;