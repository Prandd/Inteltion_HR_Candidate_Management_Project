import {
    BrowserRouter,
    Routes,
    Route
} from "react-router-dom";


import Layout from "./components/Layout";


import Dashboard from "./pages/Dashboard";
import CandidateDetail from "./pages/CandidateDetail";
import UploadCandidate from "./pages/UploadCandidate";
import CandidatePipeline from "./pages/CandidatePipeline";
import Positions from "./pages/Positions";
import PositionRequirements from "./pages/PositionRequirements";



function App(){


    return (

        <BrowserRouter>


            <Routes>


                <Route element={<Layout/>}>


                    <Route
                        path="/"
                        element={<Dashboard/>}
                    />


                    <Route
                        path="/candidate/:id"
                        element={<CandidateDetail/>}
                    />


                    <Route
                        path="/upload"
                        element={<UploadCandidate/>}
                    />


                    <Route
                        path="/pipeline"
                        element={<CandidatePipeline/>}
                    />


                    <Route
                        path="/positions"
                        element={<Positions/>}
                    />


                    <Route
                        path="/positions/new"
                        element={<PositionRequirements/>}
                    />


                </Route>


            </Routes>


        </BrowserRouter>

    );

}


export default App;