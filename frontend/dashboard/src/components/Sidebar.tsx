import {
    useNavigate,
    useLocation
} from "react-router-dom";





function Sidebar(){


    const navigate = useNavigate();

    const location = useLocation();









    function menuClass(path:string){


        const active =

            location.pathname === path;





        return `

        flex

        items-center

        gap-3

        w-full

        px-4

        py-3

        rounded-xl

        text-sm

        font-medium

        transition-all


        ${
            active

            ?

            `

            bg-blue-50

            text-blue-600

            `

            :

            `

            text-gray-600

            hover:bg-gray-50

            hover:text-blue-600

            `

        }

        `;


    }











    return (



        <aside


            className="

            fixed

            left-0

            top-0

            w-[240px]

            h-screen

            bg-white

            border-r

            border-gray-200

            flex

            flex-col

            px-5

            py-6

            z-50

            "

        >







            {/* LOGO */}



            <div

                className="

                mb-8

                "

            >



                <div

                    className="

                    flex

                    items-center

                    gap-3

                    "

                >





                    <div


                        className="

                        w-10

                        h-10

                        rounded-xl

                        bg-blue-600

                        text-white

                        flex

                        items-center

                        justify-center

                        font-bold

                        text-lg

                        "

                    >

                        I


                    </div>







                    <div>


                        <h1


                            className="

                            text-xl

                            font-bold

                            text-blue-600

                            "

                        >

                            Inteltion


                        </h1>





                        <p


                            className="

                            text-xs

                            text-gray-400

                            "

                        >

                            Talent Acquisition


                        </p>



                    </div>




                </div>


            </div>









            {/* ADD CANDIDATE */}



            <button



                onClick={

                    ()=>navigate("/upload")

                }



                className="

                w-full

                bg-blue-600

                hover:bg-blue-700

                text-white

                py-3

                rounded-xl

                text-sm

                font-semibold

                mb-8

                transition

                "

            >


                + Add Candidate


            </button>









            {/* MENU */}



            <nav

                className="

                space-y-2

                "

            >






                <button


                    onClick={

                        ()=>navigate("/")

                    }


                    className={

                        menuClass("/")

                    }


                >


                    <span className="text-base">

                        ▦

                    </span>


                    Dashboard


                </button>









                <button


                    onClick={

                        ()=>navigate("/positions")

                    }


                    className={

                        menuClass("/positions")

                    }


                >


                    <span className="text-base">

                        ▣

                    </span>


                    Positions


                </button>








            </nav>









            {/* BOTTOM */}



            <div


                className="

                mt-auto

                space-y-2

                "

            >





                <button


                    className="

                    w-full

                    flex

                    items-center

                    gap-3

                    px-4

                    py-3

                    rounded-xl

                    text-sm

                    text-gray-600

                    hover:bg-gray-50

                    transition

                    "

                >


                    <span>
                        ⚙
                    </span>


                    Settings


                </button>








                <button


                    className="

                    w-full

                    flex

                    items-center

                    gap-3

                    px-4

                    py-3

                    rounded-xl

                    text-sm

                    text-gray-600

                    hover:bg-gray-50

                    transition

                    "

                >


                    <span>
                        ?
                    </span>


                    Support


                </button>





            </div>





        </aside>


    );


}





export default Sidebar;