import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  timeout: 15000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Every backend error has the shape { error, message }. Show `message` to the user.
api.interceptors.response.use(
  (response) => {
    window.dispatchEvent(new CustomEvent("server-up"));
    return response;
  },
  (error) => {
    const status = error.response?.status;
    const data = error.response?.data || {};

    if (!error.response || status === 503) {
      window.dispatchEvent(new CustomEvent("server-down", { detail: data.message }));
    } else {
      window.dispatchEvent(new CustomEvent("server-up"));
    }

    const message = !error.response
      ? "Cannot reach the server. Check that the backend is running."
      : data.message || "Something went wrong. Please try again.";

    const onLoginPage = window.location.pathname === "/login";
    if (status === 401 && !onLoginPage) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }

    window.dispatchEvent(new CustomEvent("toast", { detail: { type: "error", message } }));
    error.userMessage = message;
    error.code = data.error;
    error.details = data.details;
    return Promise.reject(error);
  }
);

export default api;
