function Header(){

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
                    Dashboard
                </h1>


                <p className="text-gray-500">
                    Manage your recruitment pipeline
                </p>

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