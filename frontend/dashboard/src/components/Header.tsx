import {
    useState,
    useEffect,
    useRef
} from "react";


function Header(){


    const [
        search,
        setSearch
    ] = useState("");



    const [
        openProfile,
        setOpenProfile
    ] = useState(false);



    const profileRef = useRef<HTMLDivElement>(null);






    useEffect(()=>{


        function handleClickOutside(
            event:MouseEvent
        ){


            if(

                profileRef.current &&

                !profileRef.current.contains(
                    event.target as Node
                )

            ){

                setOpenProfile(false);

            }


        }




        document.addEventListener(

            "mousedown",

            handleClickOutside

        );




        return ()=>{


            document.removeEventListener(

                "mousedown",

                handleClickOutside

            );


        };


    },[]);







    function logout(){


        localStorage.removeItem(
            "inteltion_auth"
        );


        window.location.href="/login";


    }







    return (


        <header


            className="

            h-14

            bg-white

            border-b

            border-gray-200

            flex

            items-center

            justify-end

            px-6

            shrink-0

            "

        >





            <div


                className="

                flex

                items-center

                gap-4

                "

            >




                {/* SEARCH */}


                <div

                    className="
                    relative
                    "

                >


                    <input


                        value={search}


                        onChange={e=>

                            setSearch(
                                e.target.value
                            )

                        }


                        placeholder="Search..."


                        className="

                        w-[280px]

                        h-9

                        bg-white

                        border

                        border-gray-200

                        rounded-lg

                        pl-9

                        pr-4

                        text-sm

                        text-gray-700

                        outline-none

                        focus:ring-2

                        focus:ring-blue-100

                        "

                    />





                    <span

                        className="

                        absolute

                        left-3

                        top-2

                        text-gray-400

                        "

                    >

                        🔍


                    </span>


                </div>








                {/* NOTIFICATION */}


                <button


                    className="

                    relative

                    w-9

                    h-9

                    flex

                    items-center

                    justify-center

                    rounded-lg

                    hover:bg-gray-50

                    "

                >

                    🔔



                    <span


                        className="

                        absolute

                        -top-1

                        -right-1

                        bg-blue-600

                        text-white

                        text-[10px]

                        w-4

                        h-4

                        rounded-full

                        flex

                        items-center

                        justify-center

                        "

                    >

                        3


                    </span>


                </button>









                {/* PROFILE */}



                <div


                    ref={profileRef}


                    className="

                    relative

                    "

                >



                    <button


                        onClick={()=>setOpenProfile(!openProfile)}


                        className="

                        flex

                        items-center

                        gap-3

                        "

                    >




                        <div


                            className="

                            w-9

                            h-9

                            rounded-full

                            bg-blue-600

                            text-white

                            flex

                            items-center

                            justify-center

                            font-semibold

                            text-sm

                            "

                        >

                            HR


                        </div>






                        <div>


                            <div

                                className="

                                flex

                                items-center

                                gap-1

                                "

                            >


                                <p

                                    className="

                                    text-sm

                                    font-semibold

                                    text-gray-900

                                    "

                                >

                                    HR Admin


                                </p>



                                <span

                                    className="
                                    text-gray-400
                                    text-xs
                                    "

                                >

                                    ▾


                                </span>


                            </div>




                            <p

                                className="
                                text-xs
                                text-gray-400
                                "

                            >

                                Recruiter


                            </p>


                        </div>



                    </button>









                    {
                    openProfile &&


                    <div


                        className="

                        absolute

                        right-0

                        top-12

                        w-44

                        bg-white

                        border

                        border-gray-200

                        rounded-xl

                        shadow-lg

                        p-2

                        z-50

                        "

                    >



                        <button


                            className="

                            w-full

                            text-left

                            px-3

                            py-2

                            rounded-lg

                            text-sm

                            hover:bg-gray-50

                            "

                        >

                            Profile


                        </button>






                        <button


                            onClick={logout}


                            className="

                            w-full

                            text-left

                            px-3

                            py-2

                            rounded-lg

                            text-sm

                            text-red-600

                            hover:bg-red-50

                            "

                        >

                            Logout


                        </button>



                    </div>


                    }


                </div>





            </div>


        </header>


    );


}



export default Header;