import axios from "axios";

// VITE_API_BASE_URL (set per-Vercel-project, not per-branch) lets multiple
// deployments share this same code and point at different backends without
// touching vercel.json - falls back to the "/api" proxy rewrite for anyone
// who hasn't set it.
const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || "/api",
});

api.interceptors.request.use((config) => {
    const token = sessionStorage.getItem("inteltion_access_token");

    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
});

api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            sessionStorage.removeItem("inteltion_access_token");
            sessionStorage.removeItem("inteltion_account");

            if (window.location.pathname !== "/login") {
                window.location.href = "/login";
            }
        }

        return Promise.reject(error);
    }
);

export default api;
