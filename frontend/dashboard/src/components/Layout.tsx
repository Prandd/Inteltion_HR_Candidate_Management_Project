import { Outlet } from "react-router-dom";

import Sidebar from "./Sidebar";
import Header from "./Header";


function Layout(){

    return (

        <div className="flex">


            <Sidebar />


            <div
                className="
                flex-1
                bg-gray-50
                min-h-screen
                "
            >


                <Header />


                <main>

                    <Outlet />

                </main>


            </div>


        </div>

    );

}


export default Layout;