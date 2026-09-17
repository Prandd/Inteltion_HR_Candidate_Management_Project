import type {
    CandidateDetailType
} from "../../types/candidate";


interface Props {

    candidate: CandidateDetailType;

}



function CandidateSummary({

    candidate

}: Props){


    return (

        <section

            className="
            bg-white
            border
            border-gray-200
            rounded-2xl
            p-6
            shadow-sm
            "

        >


            {/* Header */}

            <div

                className="
                flex
                items-center
                gap-3
                mb-5
                "

            >

                <div

                    className="
                    w-9
                    h-9
                    rounded-xl
                    bg-blue-100
                    flex
                    items-center
                    justify-center
                    "

                >

                    <span

                        className="
                        text-lg
                        "

                    >

                        ✨

                    </span>


                </div>



                <h2

                    className="
                    text-base
                    font-semibold
                    text-gray-900
                    "

                >

                    AI Summary

                </h2>


            </div>




            {/* Summary Content */}

            <div

                className="
                bg-blue-50
                border
                border-blue-100
                rounded-xl
                p-5
                "

            >

                <p

                    className="
                    text-sm
                    leading-6
                    text-gray-700
                    "

                >

                    {
                        candidate.summary?.trim()
                        ||
                        "No summary available"
                    }


                </p>


            </div>


        </section>

    );


}


export default CandidateSummary;