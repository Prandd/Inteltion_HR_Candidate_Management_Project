interface Props {
    title: string;
    value: string | number;
}


function StatCard({title,value}:Props){

    return (

        <div
            className="
            bg-white
            rounded-2xl
            p-6
            border
            shadow-sm
            "
        >

            <p
                className="
                text-gray-500
                text-sm
                "
            >
                {title}
            </p>


            <h2
                className="
                text-5xl
                font-bold
                mt-3
                "
            >
                {value}
            </h2>


        </div>

    );

}


export default StatCard;