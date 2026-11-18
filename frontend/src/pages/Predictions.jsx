import React, { useState } from "react";
import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS, CategoryScale, LinearScale,
  BarElement, Title, Tooltip, Legend,
} from "chart.js";
import { predictions } from "../services/api";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const riskColors = {
  LOW: "#34d399", MEDIUM: "#f59e0b", HIGH: "#f97316", CRITICAL: "#ef4444",
};

function ResultCard({ result, type }) {
  if (!result) return null;
  const isError = result.error;

  if (isError) {
    return (
      <div style={{ ...styles.resultCard, borderLeft: "4px solid #ef4444" }}>
        <div style={{ color: "#ef4444" }}>{result.error}</div>
      </div>
    );
  }

  const borderColor = result.risk_level
    ? riskColors[result.risk_level]
    : "#7c83fd";

  const forecastChart = result.forecast && result.forecast.length > 0
    ? {
        labels: result.forecast.map((_, i) => `Day ${i + 1}`),
        datasets: [{
          label: "Forecast Revenue ($)",
          data: result.forecast,
          backgroundColor: "#7c83fd",
          borderRadius: 4,
        }],
      }
    : null;

  return (
    <div style={{ ...styles.resultCard, borderLeft: `4px solid ${borderColor}` }}>
      {result.prediction && (
        <div style={styles.resultPrediction}>{result.prediction}</div>
      )}
      {result.probability !== undefined && (
        <div style={styles.resultRow}>
          <span>Probability: <b>{(result.probability * 100).toFixed(1)}%</b></span>
          <span style={{ ...styles.riskBadge, background: riskColors[result.risk_level] }}>
            {result.risk_level}
          </span>
        </div>
      )}
      {result.top_features?.length > 0 && (
        <div style={styles.features}>
          Key factors: {result.top_features.join(", ")}
        </div>
      )}
      {forecastChart && (
        <div style={{ marginTop: 16 }}>
          <div style={styles.features}>
            {result.horizon_days}-day forecast
            {result.method && (
              <span style={styles.methodBadge}>{result.method}</span>
            )}
          </div>
          <Bar
            data={forecastChart}
            options={{
              responsive: true,
              plugins: { legend: { display: false } },
              scales: { y: { beginAtZero: false } },
            }}
            height={120}
          />
          <div style={styles.forecastValues}>
            {result.forecast.map((v, i) => (
              <span key={i} style={styles.forecastVal}>
                D{i + 1}: ${v.toLocaleString()}
              </span>
            ))}
          </div>
        </div>
      )}
      <div style={styles.version}>Model: {result.model_version}</div>
    </div>
  );
}

export default function Predictions() {
  const [tab, setTab] = useState("churn");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const [churnForm, setChurnForm] = useState({
    customer_id: "", days_since_last_purchase: "", total_orders: "",
    lifetime_value: "", support_tickets: "",
  });
  const [fraudForm, setFraudForm] = useState({
    transaction_id: "", amount: "", hour_of_day: "",
    is_foreign_country: "0", is_unusual_device: "0", customer_avg_amount: "",
  });
  const [salesForm, setSalesForm] = useState({
    rolling_mean_7: "", month: "", horizon: "7",
  });

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    try {
      let res;
      if (tab === "churn")       res = await predictions.predictChurn(churnForm);
      else if (tab === "fraud")  res = await predictions.predictFraud(fraudForm);
      else                       res = await predictions.predictSales(salesForm);
      setResult(res.data);
    } catch (err) {
      setResult({ error: err.response?.data?.error || "Prediction failed" });
    } finally {
      setLoading(false);
    }
  };

  const Field = ({ label, value, onChange, type = "number" }) => (
    <label style={styles.field}>
      <span style={styles.fieldLabel}>{label}</span>
      <input
        style={styles.input}
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  );

  return (
    <div>
      <h2 style={styles.heading}>Predictions</h2>
      <div style={styles.tabs}>
        {["churn", "fraud", "sales"].map((t) => (
          <button
            key={t}
            onClick={() => { setTab(t); setResult(null); }}
            style={{ ...styles.tab, ...(tab === t ? styles.tabActive : {}) }}
          >
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      <div style={styles.formCard}>
        <form onSubmit={submit} style={styles.form}>
          {tab === "churn" && (
            <>
              <Field label="Customer ID" value={churnForm.customer_id}
                onChange={(v) => setChurnForm({ ...churnForm, customer_id: v })} />
              <Field label="Days Since Last Purchase" value={churnForm.days_since_last_purchase}
                onChange={(v) => setChurnForm({ ...churnForm, days_since_last_purchase: v })} />
              <Field label="Total Orders" value={churnForm.total_orders}
                onChange={(v) => setChurnForm({ ...churnForm, total_orders: v })} />
              <Field label="Lifetime Value ($)" value={churnForm.lifetime_value}
                onChange={(v) => setChurnForm({ ...churnForm, lifetime_value: v })} />
              <Field label="Support Tickets" value={churnForm.support_tickets}
                onChange={(v) => setChurnForm({ ...churnForm, support_tickets: v })} />
            </>
          )}
          {tab === "fraud" && (
            <>
              <Field label="Transaction ID" value={fraudForm.transaction_id}
                onChange={(v) => setFraudForm({ ...fraudForm, transaction_id: v })} />
              <Field label="Amount ($)" value={fraudForm.amount}
                onChange={(v) => setFraudForm({ ...fraudForm, amount: v })} />
              <Field label="Hour of Day (0–23)" value={fraudForm.hour_of_day}
                onChange={(v) => setFraudForm({ ...fraudForm, hour_of_day: v })} />
              <Field label="Customer Avg Amount ($)" value={fraudForm.customer_avg_amount}
                onChange={(v) => setFraudForm({ ...fraudForm, customer_avg_amount: v })} />
              <label style={styles.field}>
                <span style={styles.fieldLabel}>Foreign Country</span>
                <select style={styles.input} value={fraudForm.is_foreign_country}
                  onChange={(e) => setFraudForm({ ...fraudForm, is_foreign_country: e.target.value })}>
                  <option value="0">No</option>
                  <option value="1">Yes</option>
                </select>
              </label>
              <label style={styles.field}>
                <span style={styles.fieldLabel}>Unusual Device</span>
                <select style={styles.input} value={fraudForm.is_unusual_device}
                  onChange={(e) => setFraudForm({ ...fraudForm, is_unusual_device: e.target.value })}>
                  <option value="0">No</option>
                  <option value="1">Yes</option>
                </select>
              </label>
            </>
          )}
          {tab === "sales" && (
            <>
              <Field label="Rolling Mean 7-day Revenue ($)" value={salesForm.rolling_mean_7}
                onChange={(v) => setSalesForm({ ...salesForm, rolling_mean_7: v })} />
              <Field label="Month (1–12)" value={salesForm.month}
                onChange={(v) => setSalesForm({ ...salesForm, month: v })} />
              <Field label="Forecast Horizon (days, 1–90)" value={salesForm.horizon}
                onChange={(v) => setSalesForm({ ...salesForm, horizon: v })} />
            </>
          )}
          <button style={styles.btn} type="submit" disabled={loading}>
            {loading ? "Running..." : "Run Prediction"}
          </button>
        </form>

        <ResultCard result={result} type={tab} />
      </div>
    </div>
  );
}

const styles = {
  heading:           { margin: "0 0 16px", fontSize: 22, color: "#1a1a2e" },
  tabs:              { display: "flex", gap: 8, marginBottom: 16 },
  tab:               { padding: "8px 20px", border: "1px solid #ddd", borderRadius: 6, background: "#fff", cursor: "pointer", fontSize: 14 },
  tabActive:         { background: "#7c83fd", color: "#fff", border: "1px solid #7c83fd" },
  formCard:          { background: "#fff", borderRadius: 10, padding: 24, boxShadow: "0 1px 4px rgba(0,0,0,0.08)", maxWidth: 600 },
  form:              { display: "flex", flexDirection: "column", gap: 12 },
  field:             { display: "flex", flexDirection: "column", gap: 4 },
  fieldLabel:        { fontSize: 12, color: "#666", fontWeight: 600 },
  input:             { padding: "8px 12px", border: "1px solid #ddd", borderRadius: 6, fontSize: 14 },
  btn:               { padding: 10, background: "#7c83fd", color: "#fff", border: "none", borderRadius: 6, fontSize: 14, fontWeight: 600, cursor: "pointer", marginTop: 4 },
  resultCard:        { marginTop: 20, padding: 16, background: "#f9fafb", borderRadius: 8 },
  resultPrediction:  { fontSize: 20, fontWeight: 700, color: "#1a1a2e", marginBottom: 8 },
  resultRow:         { display: "flex", alignItems: "center", gap: 12, marginBottom: 8 },
  riskBadge:         { padding: "2px 10px", borderRadius: 12, color: "#fff", fontSize: 12, fontWeight: 700 },
  features:          { fontSize: 13, color: "#555", marginBottom: 4 },
  methodBadge:       { marginLeft: 8, background: "#e0e7ff", color: "#3730a3", padding: "1px 8px", borderRadius: 4, fontSize: 11, fontWeight: 600 },
  forecastValues:    { display: "flex", flexWrap: "wrap", gap: 6, marginTop: 8 },
  forecastVal:       { background: "#e0e7ff", color: "#3730a3", padding: "2px 8px", borderRadius: 4, fontSize: 11 },
  version:           { fontSize: 11, color: "#aaa", marginTop: 8 },
};
