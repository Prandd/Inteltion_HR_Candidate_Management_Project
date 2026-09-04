import {
    useNavigate,
    useLocation
} from "react-router-dom";


function Sidebar() {


    const navigate = useNavigate();

    const location = useLocation();



    const menuClass = (path:string) => {


        return `

        w-full
        text-left
        px-4
        py-3
        rounded-xl
        font-medium

        ${
            location.pathname === path

            ?

            `
            bg-blue-50
            text-blue-700
            `

            :

            `
            hover:bg-gray-100
            text-gray-700
            `

        }

        `;

    };





    return (

        <aside

            className="
            relative
            w-72
            min-h-screen
            bg-white
            border-r
            px-6
            py-8
            "

        >



            {/* Logo */}

            <div className="mb-10">


                <h1

                    className="
                    text-3xl
                    font-bold
                    text-blue-700
                    "

                >

                    Inteltion

                </h1>


                <p className="text-gray-500">

                    Talent Acquisition

                </p>


            </div>





            {/* Add Candidate */}

            <button


                onClick={() => navigate("/upload")}


                className="
                w-full
                bg-blue-600
                text-white
                py-3
                rounded-xl
                mb-8
                hover:bg-blue-700
                "

            >

                + Add Candidate


            </button>






            {/* Menu */}

            <nav className="space-y-2">



                <button


                    onClick={() => navigate("/")}


                    className={menuClass("/")}

                >

                    Dashboard


                </button>





                <button


                    onClick={() => navigate("/positions")}


                    className={menuClass("/positions")}


                >

                    Positions


                </button>






                <button


                    onClick={() => navigate("/pipeline")}


                    className={menuClass("/pipeline")}


                >

                    Candidate Flow


                </button>



            </nav>







            {/* Bottom */}

            <div

                className="
                absolute
                bottom-8
                left-6
                "

            >

                <p

                    className="
                    text-gray-400
                    text-sm
                    "

                >

                    Settings


                </p>


            </div>





        </aside>

    );


}


export default Sidebar;