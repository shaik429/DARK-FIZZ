import { createContext, useContext, useState } from "react";
import { authApi } from "../api";

const AuthContext = createContext(null);

function storedUser() {
  try {
    return JSON.parse(localStorage.getItem("user"));
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(storedUser);

  async function login(email, password) {
    const data = await authApi.login({ email: email.trim(), password });
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("user", JSON.stringify(data.user));
    setUser(data.user);
    return data.user;
  }

  function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setUser(null);
  }

  const isManager = user?.role === "manager";
  return <AuthContext.Provider value={{ user, login, logout, isManager }}>{children}</AuthContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => useContext(AuthContext);
