import {
    useState
} from "react";


import {
    useNavigate
} from "react-router-dom";




function Login(){



    const navigate = useNavigate();



    const [
        email,
        setEmail
    ] = useState("");



    const [
        password,
        setPassword
    ] = useState("");





    function login(){


        // temporary frontend login

        if(!email || !password){

            alert(
                "Please enter email and password"
            );

            return;

        }



        navigate("/");

    }







    return (


        <div


            className="

            min-h-screen

            bg-[#f7f9ff]

            flex

            items-center

            justify-center

            "

        >




            <div


                className="

                bg-white

                w-[420px]

                rounded-2xl

                border

                p-8

                shadow-sm

                "


            >






                {/* Logo */}



                <div

                    className="

                    text-center

                    mb-8

                    "

                >



                    <div


                        className="

                        mx-auto

                        w-12

                        h-12

                        bg-blue-600

                        rounded-xl

                        flex

                        items-center

                        justify-center

                        text-white

                        font-bold

                        text-xl

                        "

                    >

                        ▦


                    </div>





                    <h1


                        className="

                        text-2xl

                        font-bold

                        text-blue-600

                        mt-4

                        "

                    >

                        Inteltion


                    </h1>





                    <p

                        className="

                        text-gray-500

                        text-sm

                        "

                    >

                        Talent Acquisition


                    </p>



                </div>









                {/* Form */}



                <div className="space-y-4">



                    <div>


                        <label

                            className="

                            text-sm

                            font-medium

                            "

                        >

                            Email


                        </label>



                        <input


                            value={email}


                            onChange={

                                e=>

                                setEmail(

                                    e.target.value

                                )

                            }



                            placeholder="Enter email"


                            className="

                            mt-2

                            w-full

                            border

                            rounded-xl

                            px-4

                            py-3

                            outline-none

                            focus:ring-2

                            focus:ring-blue-200

                            "

                        />


                    </div>









                    <div>


                        <label

                            className="

                            text-sm

                            font-medium

                            "

                        >

                            Password


                        </label>



                        <input


                            type="password"


                            value={password}


                            onChange={

                                e=>

                                setPassword(

                                    e.target.value

                                )

                            }



                            placeholder="Enter password"


                            className="

                            mt-2

                            w-full

                            border

                            rounded-xl

                            px-4

                            py-3

                            outline-none

                            focus:ring-2

                            focus:ring-blue-200

                            "

                        />


                    </div>





                </div>









                <button


                    onClick={login}


                    className="

                    mt-8

                    w-full

                    bg-blue-600

                    text-white

                    py-3

                    rounded-xl

                    font-semibold

                    hover:bg-blue-700

                    "

                >

                    Login


                </button>







            </div>



        </div>


    );


}



export default Login;