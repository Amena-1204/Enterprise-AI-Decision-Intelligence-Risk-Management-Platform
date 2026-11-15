import React, { useEffect, useState } from "react";
import { fraud } from "../services/api";

const riskColors = { LOW: "#34d399", MEDIUM: "#f59e0b", HIGH: "#f97316", CRITICAL: "#ef4444" };

export default function FraudPage() {
  const [cases, setCases] = useState([]);
  const [regional, setRegional] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([fraud.overview(), fraud.regional()])
      .then(([c, r]) => { setCases(c.data.fraud_cases); setRegional(r.data.regional_fraud); })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={styles.msg}>Loading fraud data...</div>;

  return (
    <div>
      <h2 style={styles.heading}>Fraud Detection</h2>
      <div style={styles.grid}>
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>Fraud Cases ({cases.length})</h3>
          <table style={styles.table}>
            <thead>
              <tr>{["Txn ID", "Customer", "Amount", "Country", "Probability", "Risk"].map((h) => (
                <th key={h} style={styles.th}>{h}</th>
              ))}</tr>
            </thead>
            <tbody>
              {cases.map((c) => (
                <tr key={c.transaction_id} style={styles.tr}>
                  <td style={styles.td}>#{c.transaction_id}</td>
                  <td style={styles.td}>#{c.customer_id}</td>
                  <td style={styles.td}>${Number(c.amount).toLocaleString()}</td>
                  <td style={styles.td}>{c.country}</td>
                  <td style={styles.td}>{(c.fraud_probability * 100).toFixed(1)}%</td>
                  <td style={styles.td}>
                    <span style={{ ...styles.badge, background: riskColors[c.risk_level] }}>{c.risk_level}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>Regional Breakdown</h3>
          {regional.map((r) => (
            <div key={r.country} style={styles.regionRow}>
              <span style={styles.regionName}>{r.country}</span>
              <span style={styles.regionCount}>{r.fraud_count} cases</span>
              <span style={styles.regionProb}>{(r.avg_probability * 100).toFixed(1)}% avg</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

const styles = {
  heading: { margin: "0 0 20px", fontSize: 22, color: "#1a1a2e" },
  grid: { display: "grid", gridTemplateColumns: "2fr 1fr", gap: 16 },
  card: { background: "#fff", borderRadius: 10, padding: 20, boxShadow: "0 1px 4px rgba(0,0,0,0.08)" },
  cardTitle: { margin: "0 0 16px", fontSize: 15, color: "#333" },
  table: { width: "100%", borderCollapse: "collapse" },
  th: { padding: "10px 12px", textAlign: "left", fontSize: 11, fontWeight: 600, color: "#666", borderBottom: "1px solid #f0f0f0" },
  tr: { borderBottom: "1px solid #f5f5f5" },
  td: { padding: "10px 12px", fontSize: 13, color: "#333" },
  badge: { padding: "2px 8px", borderRadius: 12, color: "#fff", fontSize: 11, fontWeight: 600 },
  regionRow: { display: "flex", alignItems: "center", padding: "10px 0", borderBottom: "1px solid #f5f5f5", gap: 8 },
  regionName: { flex: 1, fontSize: 14, fontWeight: 600 },
  regionCount: { fontSize: 13, color: "#ef4444" },
  regionProb: { fontSize: 12, color: "#888", minWidth: 70, textAlign: "right" },
  msg: { padding: 20, color: "#888" },
};
