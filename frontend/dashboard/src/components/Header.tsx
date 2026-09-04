import { useLocation } from "react-router-dom";


function Header(){

    const location = useLocation();

    const pageTitle = location.pathname === "/positions/new"
        ? "Position Requirements"
        : location.pathname === "/positions"
            ? "Positions List"
            : "Dashboard";

    const pageDescription = location.pathname === "/positions/new"
        ? ""
        : location.pathname === "/positions"
            ? "Manage current job openings and candidate pipelines."
            : "Manage your recruitment pipeline";

    return (

        <header
            className="
            h-20
            bg-white
            border-b
            flex
            items-center
            justify-between
            px-8
            "
        >

            <div>

                <h1
                    className="
                    text-2xl
                    font-bold
                    "
                >
                    {pageTitle}
                </h1>


                {pageDescription && (
                    <p className="text-gray-500">
                        {pageDescription}
                    </p>
                )}

            </div>



            <div
                className="
                flex
                items-center
                gap-4
                "
            >

                <button
                    className="
                    border
                    rounded-lg
                    px-4
                    py-2
                    "
                >
                    🔔
                </button>



                <div
                    className="
                    w-10
                    h-10
                    rounded-full
                    bg-blue-600
                    "
                >

                </div>


            </div>


        </header>

    );

}


export default Header;