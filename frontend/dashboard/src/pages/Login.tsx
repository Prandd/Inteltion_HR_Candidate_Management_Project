import {
    useState
} from "react";


import {
    useNavigate,
    Navigate
} from "react-router-dom";





function Login(){


    const navigate = useNavigate();





    const isAuthenticated =

        localStorage.getItem(
            "inteltion_auth"
        );



    if(isAuthenticated){


        return (

            <Navigate

                to="/"

                replace

            />

        );


    }









    const [

        email,

        setEmail

    ] = useState("");





    const [

        password,

        setPassword

    ] = useState("");






    const [

        error,

        setError

    ] = useState("");









    function handleLogin(

        e:React.FormEvent

    ){


        e.preventDefault();





        if(!email.trim() || !password.trim()){


            setError(
                "Please enter email and password"
            );


            return;


        }






        // MVP authentication
        // Replace with backend auth later


        localStorage.setItem(

            "inteltion_auth",

            "true"

        );





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




                {/* LOGO */}


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
                        rounded-xl
                        bg-blue-600
                        text-white
                        flex
                        items-center
                        justify-center
                        text-xl
                        font-bold
                        "

                    >

                        I


                    </div>




                    <h1

                        className="
                        text-2xl
                        font-bold
                        text-blue-600
                        mt-3
                        "

                    >

                        Inteltion


                    </h1>



                    <p

                        className="
                        text-sm
                        text-gray-400
                        "

                    >

                        Talent Acquisition


                    </p>



                </div>








                <form

                    onSubmit={handleLogin}

                    className="
                    space-y-5
                    "

                >




                    {

                    error &&


                    <div

                        className="
                        bg-red-50
                        text-red-600
                        text-sm
                        px-4
                        py-3
                        rounded-xl
                        "

                    >

                        {error}


                    </div>


                    }







                    <div>


                        <label

                            className="
                            text-sm
                            text-gray-600
                            "

                        >

                            Email


                        </label>



                        <input


                            value={email}


                            onChange={e=>{

                                setEmail(
                                    e.target.value
                                );


                                setError("");

                            }}


                            placeholder="admin@inteltion.com"


                            className="
                            mt-2
                            w-full
                            border
                            rounded-xl
                            px-4
                            py-3
                            outline-none
                            focus:ring-2
                            focus:ring-blue-100
                            "

                        />


                    </div>








                    <div>


                        <label

                            className="
                            text-sm
                            text-gray-600
                            "

                        >

                            Password


                        </label>



                        <input


                            type="password"


                            value={password}


                            onChange={e=>{

                                setPassword(
                                    e.target.value
                                );


                                setError("");

                            }}


                            placeholder="••••••••"


                            className="
                            mt-2
                            w-full
                            border
                            rounded-xl
                            px-4
                            py-3
                            outline-none
                            focus:ring-2
                            focus:ring-blue-100
                            "

                        />


                    </div>









                    <button


                        className="
                        w-full
                        bg-blue-600
                        hover:bg-blue-700
                        text-white
                        py-3
                        rounded-xl
                        font-semibold
                        "

                    >

                        Login


                    </button>






                </form>





            </div>



        </div>


    );



}



export default Login;