import {
    useState
} from "react";





function Header(){


    const [
        search,
        setSearch
    ] = useState("");





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


                        onChange={

                            e=>

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

                        text-sm

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









                {/* USER */}



                <div


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



                            <span className="text-gray-400 text-xs">

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




                </div>







            </div>






        </header>


    );


}



export default Header;