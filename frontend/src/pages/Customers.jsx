import React, { useEffect, useState } from "react";
import { customers as customersApi } from "../services/api";

export default function Customers() {
  const [list, setList] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    customersApi.list(200)
      .then((res) => setList(res.data.customers))
      .catch(() => setError("Failed to load customers"))
      .finally(() => setLoading(false));
  }, []);

  const filtered = list.filter((c) =>
    `${c.first_name} ${c.last_name} ${c.email} ${c.region}`.toLowerCase().includes(search.toLowerCase())
  );

  const riskColor = { "High Value": "#34d399", "Loyal": "#7c83fd", "At Risk": "#f59e0b", "New Customer": "#60a5fa", "Low Engagement": "#9ca3af" };

  if (loading) return <div style={styles.msg}>Loading customers...</div>;
  if (error) return <div style={{ ...styles.msg, color: "#ef4444" }}>{error}</div>;

  return (
    <div>
      <div style={styles.header}>
        <h2 style={styles.heading}>Customers ({list.length})</h2>
        <input
          style={styles.search}
          placeholder="Search by name, email, region..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>
      <div style={styles.tableWrap}>
        <table style={styles.table}>
          <thead>
            <tr>
              {["Name", "Email", "Region", "Segment", "LTV", "Orders", "Last Purchase"].map((h) => (
                <th key={h} style={styles.th}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((c) => (
              <tr key={c.id} style={styles.tr}>
                <td style={styles.td}>{c.first_name} {c.last_name}</td>
                <td style={styles.td}>{c.email}</td>
                <td style={styles.td}>{c.region}</td>
                <td style={styles.td}>
                  <span style={{ ...styles.badge, background: riskColor[c.segment] || "#e5e7eb", color: "#fff" }}>
                    {c.segment || "—"}
                  </span>
                </td>
                <td style={styles.td}>${Number(c.lifetime_value).toLocaleString()}</td>
                <td style={styles.td}>{c.total_orders}</td>
                <td style={styles.td}>{c.last_purchase_date || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && <div style={styles.msg}>No customers found.</div>}
      </div>
    </div>
  );
}

const styles = {
  header: { display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 },
  heading: { margin: 0, fontSize: 22, color: "#1a1a2e" },
  search: { padding: "8px 14px", border: "1px solid #ddd", borderRadius: 6, fontSize: 14, width: 280 },
  tableWrap: { background: "#fff", borderRadius: 10, boxShadow: "0 1px 4px rgba(0,0,0,0.08)", overflow: "auto" },
  table: { width: "100%", borderCollapse: "collapse" },
  th: { padding: "12px 16px", textAlign: "left", fontSize: 12, fontWeight: 600, color: "#666", borderBottom: "1px solid #f0f0f0", background: "#fafafa" },
  tr: { borderBottom: "1px solid #f5f5f5" },
  td: { padding: "11px 16px", fontSize: 13, color: "#333" },
  badge: { padding: "2px 8px", borderRadius: 12, fontSize: 11, fontWeight: 600 },
  msg: { padding: 20, color: "#888", textAlign: "center" },
};
