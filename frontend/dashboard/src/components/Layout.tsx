import {
    Outlet
} from "react-router-dom";


import Sidebar from "./Sidebar";

import Header from "./Header";





function Layout(){


    return (


        <div

            className="
            h-screen
            overflow-hidden
            bg-[#f7f9ff]
            "

        >





            {/* FIXED SIDEBAR */}

            <Sidebar />









            {/* MAIN AREA */}


            <div

                className="
                ml-[240px]
                h-screen
                flex
                flex-col
                "

            >





                {/* FIXED HEADER AREA */}

                <div

                    className="
                    h-14
                    shrink-0
                    "

                >

                    <Header />

                </div>









                {/* PAGE CONTENT SCROLL ONLY */}


                <main

                    className="
                    flex-1
                    overflow-y-auto
                    "

                >

                    <Outlet />


                </main>






            </div>





        </div>


    );


}



export default Layout;