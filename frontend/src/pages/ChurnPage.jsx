import React, { useEffect, useState } from "react";
import { churn } from "../services/api";

const riskColors = { LOW: "#34d399", MEDIUM: "#f59e0b", HIGH: "#f97316", CRITICAL: "#ef4444" };

export default function ChurnPage() {
  const [atRisk, setAtRisk] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    churn.atRisk()
      .then((res) => setAtRisk(res.data.at_risk_customers))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={styles.msg}>Loading churn data...</div>;

  return (
    <div>
      <h2 style={styles.heading}>Churn Risk — At-Risk Customers ({atRisk.length})</h2>
      <div style={styles.tableWrap}>
        <table style={styles.table}>
          <thead>
            <tr>{["Customer", "Email", "Region", "Churn Probability", "Risk Level", "Key Factors"].map((h) => (
              <th key={h} style={styles.th}>{h}</th>
            ))}</tr>
          </thead>
          <tbody>
            {atRisk.map((c) => (
              <tr key={c.customer_id} style={styles.tr}>
                <td style={styles.td}>{c.first_name} {c.last_name}</td>
                <td style={styles.td}>{c.email}</td>
                <td style={styles.td}>{c.region}</td>
                <td style={styles.td}>
                  <div style={styles.probBar}>
                    <div style={{ ...styles.probFill, width: `${c.churn_probability * 100}%`, background: riskColors[c.risk_level] }} />
                    <span style={styles.probText}>{(c.churn_probability * 100).toFixed(1)}%</span>
                  </div>
                </td>
                <td style={styles.td}>
                  <span style={{ ...styles.badge, background: riskColors[c.risk_level] }}>{c.risk_level}</span>
                </td>
                <td style={styles.td}>
                  <span style={styles.features}>
                    {Array.isArray(c.top_features)
                      ? c.top_features.join(", ")
                      : (typeof c.top_features === "string" ? JSON.parse(c.top_features).join(", ") : "—")}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {atRisk.length === 0 && <div style={styles.msg}>No at-risk customers found.</div>}
      </div>
    </div>
  );
}

const styles = {
  heading: { margin: "0 0 20px", fontSize: 22, color: "#1a1a2e" },
  tableWrap: { background: "#fff", borderRadius: 10, boxShadow: "0 1px 4px rgba(0,0,0,0.08)", overflow: "auto" },
  table: { width: "100%", borderCollapse: "collapse" },
  th: { padding: "12px 16px", textAlign: "left", fontSize: 11, fontWeight: 600, color: "#666", borderBottom: "1px solid #f0f0f0", background: "#fafafa" },
  tr: { borderBottom: "1px solid #f5f5f5" },
  td: { padding: "11px 16px", fontSize: 13, color: "#333" },
  badge: { padding: "2px 8px", borderRadius: 12, color: "#fff", fontSize: 11, fontWeight: 600 },
  probBar: { position: "relative", background: "#f0f0f0", borderRadius: 4, height: 18, width: 120, overflow: "hidden" },
  probFill: { position: "absolute", top: 0, left: 0, height: "100%", borderRadius: 4, opacity: 0.8 },
  probText: { position: "absolute", top: 0, left: 0, right: 0, textAlign: "center", fontSize: 11, fontWeight: 600, lineHeight: "18px", color: "#333" },
  features: { fontSize: 11, color: "#666" },
  msg: { padding: 20, color: "#888", textAlign: "center" },
};
