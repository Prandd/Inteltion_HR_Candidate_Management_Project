import {
    BrowserRouter,
    Routes,
    Route,
    Navigate
} from "react-router-dom";

import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import CandidateDetail from "./pages/CandidateDetail";
import UploadCandidate from "./pages/UploadCandidate";
import Positions from "./pages/Positions";
import PositionRequirements from "./pages/PositionRequirements";
import Login from "./pages/Login";
import PositionDetail from "./pages/PositionDetail";

function ProtectedRoute({
    children
}: {
    children: React.ReactNode;
}) {
    const accessToken = sessionStorage.getItem(
        "inteltion_access_token"
    );

    if (!accessToken) {
        return (
            <Navigate
                to="/login"
                replace
            />
        );
    }

    return children;
}

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route
                    path="/login"
                    element={
                        <Login />
                    }
                />

                <Route
                    element={
                        <ProtectedRoute>
                            <Layout />
                        </ProtectedRoute>
                    }
                >
                    <Route
                        path="/"
                        element={
                            <Dashboard />
                        }
                    />

                    <Route
                        path="/candidate/:id"
                        element={
                            <CandidateDetail />
                        }
                    />

                    <Route
                        path="/upload"
                        element={
                            <UploadCandidate />
                        }
                    />

                    <Route
                        path="/positions"
                        element={
                            <Positions />
                        }
                    />

                    <Route
                        path="/positions/:id"
                        element={
                            <PositionDetail />
                        }
                    />

                    <Route
                        path="/positions/new"
                        element={
                            <PositionRequirements />
                        }
                    />
                </Route>

                <Route
                    path="*"
                    element={
                        <Navigate
                            to="/"
                            replace
                        />
                    }
                />
            </Routes>
        </BrowserRouter>
    );
}

export default App;