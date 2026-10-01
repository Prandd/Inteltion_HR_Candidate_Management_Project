import { useState } from "react";
import { useNavigate, Navigate } from "react-router-dom";
import api from "../api/axios";

function Login() {
    const navigate = useNavigate();

    const isAuthenticated = sessionStorage.getItem(
        "inteltion_access_token"
    );

    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    if (isAuthenticated) {
        return (
            <Navigate
                to="/"
                replace
            />
        );
    }

    async function handleLogin(
        e: React.FormEvent
    ) {
        e.preventDefault();

        if (!username.trim() || !password.trim()) {
            setError("Please enter username and password");
            return;
        }

        try {
            setError("");
            setIsLoading(true);

            const response = await api.post(
                "/auth/login",
                {
                    username: username.trim(),
                    password
                }
            );

            const {
                access_token,
                account
            } = response.data.data;

            sessionStorage.setItem(
                "inteltion_access_token",
                access_token
            );

            sessionStorage.setItem(
                "inteltion_account",
                JSON.stringify(account)
            );

            navigate("/", {
                replace: true
            });
        } catch {
            setError("Invalid username or password");
        } finally {
            setIsLoading(false);
        }
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
                    className="space-y-5"
                >
                    {error && (
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
                    )}

                    <div>
                        <label
                            className="
                            text-sm
                            text-gray-600
                            "
                        >
                            Username
                        </label>

                        <input
                            value={username}
                            onChange={(e) => {
                                setUsername(e.target.value);
                                setError("");
                            }}
                            placeholder="admin"
                            autoComplete="username"
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
                            onChange={(e) => {
                                setPassword(e.target.value);
                                setError("");
                            }}
                            placeholder="••••••••"
                            autoComplete="current-password"
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
                        type="submit"
                        disabled={isLoading}
                        className="
                        w-full
                        bg-blue-600
                        hover:bg-blue-700
                        disabled:opacity-50
                        disabled:cursor-not-allowed
                        text-white
                        py-3
                        rounded-xl
                        font-semibold
                        "
                    >
                        {isLoading ? "Logging in..." : "Login"}
                    </button>
                </form>
            </div>
        </div>
    );
}

export default Login;