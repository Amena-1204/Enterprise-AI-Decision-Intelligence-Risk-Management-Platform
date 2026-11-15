import React, { createContext, useContext, useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate, NavLink } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Customers from "./pages/Customers";
import Predictions from "./pages/Predictions";
import FraudPage from "./pages/FraudPage";
import ChurnPage from "./pages/ChurnPage";
import AIAssistant from "./pages/AIAssistant";
import Login from "./pages/Login";

export const AuthContext = createContext(null);

export function useAuth() {
  return useContext(AuthContext);
}

function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("token"));
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem("user")); } catch { return null; }
  });

  const login = (token, user) => {
    localStorage.setItem("token", token);
    localStorage.setItem("user", JSON.stringify(user));
    setToken(token);
    setUser(user);
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ token, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

function PrivateRoute({ children }) {
  const { token } = useAuth();
  return token ? children : <Navigate to="/login" replace />;
}

function Nav() {
  const { user, logout } = useAuth();
  const links = [
    { to: "/", label: "Dashboard" },
    { to: "/customers", label: "Customers" },
    { to: "/predictions", label: "Predictions" },
    { to: "/fraud", label: "Fraud" },
    { to: "/churn", label: "Churn" },
    { to: "/ai", label: "AI Assistant" },
  ];

  return (
    <nav style={styles.nav}>
      <span style={styles.brand}>Enterprise AI</span>
      <div style={styles.navLinks}>
        {links.map(({ to, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            style={({ isActive }) => ({ ...styles.navLink, ...(isActive ? styles.navLinkActive : {}) })}
          >
            {label}
          </NavLink>
        ))}
      </div>
      <div style={styles.navUser}>
        <span style={styles.userLabel}>{user?.username} ({user?.role})</span>
        <button onClick={logout} style={styles.logoutBtn}>Logout</button>
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/*"
            element={
              <PrivateRoute>
                <div style={styles.layout}>
                  <Nav />
                  <main style={styles.main}>
                    <Routes>
                      <Route path="/" element={<Dashboard />} />
                      <Route path="/customers" element={<Customers />} />
                      <Route path="/predictions" element={<Predictions />} />
                      <Route path="/fraud" element={<FraudPage />} />
                      <Route path="/churn" element={<ChurnPage />} />
                      <Route path="/ai" element={<AIAssistant />} />
                    </Routes>
                  </main>
                </div>
              </PrivateRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

const styles = {
  layout: { display: "flex", flexDirection: "column", minHeight: "100vh", background: "#f0f2f5" },
  nav: {
    display: "flex", alignItems: "center", background: "#1a1a2e", color: "#fff",
    padding: "0 24px", height: 56, gap: 24, position: "sticky", top: 0, zIndex: 100,
  },
  brand: { fontWeight: 700, fontSize: 18, color: "#7c83fd", whiteSpace: "nowrap" },
  navLinks: { display: "flex", gap: 4, flex: 1 },
  navLink: {
    color: "#aaa", textDecoration: "none", padding: "6px 12px",
    borderRadius: 6, fontSize: 14, transition: "all 0.2s",
  },
  navLinkActive: { color: "#fff", background: "#7c83fd22" },
  navUser: { display: "flex", alignItems: "center", gap: 12 },
  userLabel: { fontSize: 13, color: "#aaa" },
  logoutBtn: {
    background: "transparent", border: "1px solid #555", color: "#ccc",
    padding: "4px 12px", borderRadius: 6, cursor: "pointer", fontSize: 13,
  },
  main: { flex: 1, padding: 24, maxWidth: 1400, margin: "0 auto", width: "100%" },
};
