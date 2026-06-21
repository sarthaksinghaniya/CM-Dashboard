import React, { createContext, useContext, useState, useEffect } from "react";
import api from "../services/api";

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUser();
  }, []);

  const fetchUser = async () => {
    const token = localStorage.getItem("auth_token");
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      const res = await api.get("/auth/me");
      setUser(res.data);
      if (res.data.role) {
        localStorage.setItem("role", res.data.role.toLowerCase());
      }
    } catch (error) {
      console.error("Failed to fetch user, logging out...", error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = (data) => {
    localStorage.setItem("auth_token", data.accessToken);
    if (data.user?.role) {
      localStorage.setItem("role", data.user.role.toLowerCase());
    }
    setUser(data.user);
  };

  const logout = async () => {
    try {
      await api.post('/auth/logout');
    } catch (e) {
      console.error("Logout API failed, continuing local clear", e);
    }
    localStorage.removeItem("auth_token");
    localStorage.removeItem("role");
    setUser(null);
  };

  const role = user?.role?.toLowerCase() || localStorage.getItem("role") || null;

  return (
    <AuthContext.Provider value={{ user, role, login, logout, loading }}>
      {!loading && children}
    </AuthContext.Provider>
  );
};
