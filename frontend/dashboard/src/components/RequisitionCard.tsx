interface Props {

    title:string;
    location:string;
    candidates:number;

}


function RequisitionCard({
    title,
    location,
    candidates

}:Props){


    return (

        <div
            className="
            bg-white
            border
            border-gray-200
            rounded-xl
            p-5
            mb-5
            "
        >


            <h3
                className="
                text-xl
                font-semibold
                text-blue-700
                "
            >
                {title}
            </h3>



            <p
                className="
                text-gray-500
                mt-1
                "
            >
                📍 {location}
            </p>



            <hr
                className="
                my-4
                "
            />



            <div
                className="
                flex
                justify-between
                items-center
                "
            >

                <span>

                    {candidates} Candidates

                </span>



                <button
                    className="
                    border
                    border-blue-600
                    text-blue-600
                    px-4
                    py-1
                    rounded-lg
                    "
                >
                    View
                </button>


            </div>


        </div>

    );


}


export default RequisitionCard;