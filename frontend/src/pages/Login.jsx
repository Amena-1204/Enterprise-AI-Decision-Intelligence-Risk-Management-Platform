import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../App";
import { auth } from "../services/api";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await auth.login(form.email, form.password);
      login(res.data.token, res.data.user);
      navigate("/");
    } catch (err) {
      setError(err.response?.data?.error || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.title}>Enterprise AI Platform</h1>
        <p style={styles.subtitle}>Sign in to your account</p>
        {error && <div style={styles.error}>{error}</div>}
        <form onSubmit={handleSubmit} style={styles.form}>
          <input
            style={styles.input}
            type="email"
            placeholder="Email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            required
          />
          <input
            style={styles.input}
            type="password"
            placeholder="Password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            required
          />
          <button style={styles.btn} type="submit" disabled={loading}>
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>
      </div>
    </div>
  );
}

const styles = {
  container: {
    minHeight: "100vh", display: "flex", alignItems: "center",
    justifyContent: "center", background: "#1a1a2e",
  },
  card: {
    background: "#fff", borderRadius: 12, padding: 40,
    width: 360, boxShadow: "0 8px 32px rgba(0,0,0,0.3)",
  },
  title: { margin: "0 0 4px", fontSize: 22, color: "#1a1a2e" },
  subtitle: { margin: "0 0 24px", color: "#888", fontSize: 14 },
  error: {
    background: "#fee2e2", color: "#dc2626", padding: "10px 14px",
    borderRadius: 6, marginBottom: 16, fontSize: 14,
  },
  form: { display: "flex", flexDirection: "column", gap: 12 },
  input: {
    padding: "10px 14px", border: "1px solid #ddd", borderRadius: 6,
    fontSize: 14, outline: "none",
  },
  btn: {
    padding: "11px", background: "#7c83fd", color: "#fff", border: "none",
    borderRadius: 6, fontSize: 15, fontWeight: 600, cursor: "pointer",
  },
};
