import {
    BrowserRouter,
    Routes,
    Route
} from "react-router-dom";


import Layout from "./components/Layout";


import Dashboard from "./pages/Dashboard";

import CandidateDetail from "./pages/CandidateDetail";

import UploadCandidate from "./pages/UploadCandidate";

import Positions from "./pages/Positions";

import PositionRequirements from "./pages/PositionRequirements";

import Login from "./pages/Login";







function App(){


    return (


        <BrowserRouter>


            <Routes>





                {/* LOGIN */}



                <Route


                    path="/login"


                    element={

                        <Login/>

                    }


                />









                {/* APPLICATION */}



                <Route


                    element={

                        <Layout/>

                    }


                >





                    {/* Dashboard

                        Dashboard = Candidate Pipeline Board

                    */}



                    <Route


                        path="/"


                        element={

                            <Dashboard/>

                        }


                    />









                    {/* Candidate Detail */}



                    <Route


                        path="/candidate/:id"


                        element={

                            <CandidateDetail/>

                        }


                    />









                    {/* Upload CV */}



                    <Route


                        path="/upload"


                        element={

                            <UploadCandidate/>

                        }


                    />









                    {/* Positions */}



                    <Route


                        path="/positions"


                        element={

                            <Positions/>

                        }


                    />









                    {/* Create Position */}



                    <Route


                        path="/positions/new"


                        element={

                            <PositionRequirements/>

                        }


                    />





                </Route>





            </Routes>



        </BrowserRouter>


    );


}





export default App;