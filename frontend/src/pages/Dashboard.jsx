import React, { useEffect, useState } from "react";
import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS, CategoryScale, LinearScale,
  BarElement, Title, Tooltip, Legend,
} from "chart.js";
import { dashboard } from "../services/api";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

function KPICard({ label, value, sub, color = "#7c83fd" }) {
  return (
    <div style={{ ...styles.card, borderTop: `4px solid ${color}` }}>
      <div style={styles.kpiValue}>{value}</div>
      <div style={styles.kpiLabel}>{label}</div>
      {sub && <div style={styles.kpiSub}>{sub}</div>}
    </div>
  );
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    dashboard.summary()
      .then((res) => setData(res.data))
      .catch(() => setError("Failed to load dashboard data"));
  }, []);

  if (error) return <div style={styles.error}>{error}</div>;
  if (!data) return <div style={styles.loading}>Loading dashboard...</div>;

  const regionChart = {
    labels: data.regional_performance.map((r) => r.region),
    datasets: [{
      label: "Revenue ($)",
      data: data.regional_performance.map((r) => r.revenue),
      backgroundColor: "#7c83fd",
      borderRadius: 4,
    }],
  };

  const productChart = {
    labels: data.top_products.map((p) => p.name.split(" ").slice(0, 2).join(" ")),
    datasets: [{
      label: "Revenue ($)",
      data: data.top_products.map((p) => p.revenue),
      backgroundColor: "#34d399",
      borderRadius: 4,
    }],
  };

  const chartOptions = {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: { y: { beginAtZero: true } },
  };

  return (
    <div>
      <h2 style={styles.heading}>Dashboard</h2>
      <div style={styles.kpiGrid}>
        <KPICard label="Total Customers" value={data.total_customers.toLocaleString()} color="#7c83fd" />
        <KPICard label="Total Revenue" value={`$${(data.total_revenue / 1000).toFixed(1)}K`} color="#34d399" />
        <KPICard label="Churn Rate" value={`${(data.churn_rate * 100).toFixed(1)}%`} color="#f59e0b" />
        <KPICard label="Fraud Cases" value={data.fraud_count} color="#ef4444" />
        <KPICard label="High Risk Customers" value={data.high_risk_customers} color="#f97316" />
        <KPICard
          label="Sales Growth"
          value={`${data.sales_growth_pct > 0 ? "+" : ""}${data.sales_growth_pct}%`}
          color={data.sales_growth_pct >= 0 ? "#34d399" : "#ef4444"}
          sub="vs prior 30 days"
        />
      </div>
      <div style={styles.chartsRow}>
        <div style={styles.chartCard}>
          <h3 style={styles.chartTitle}>Revenue by Region</h3>
          <Bar data={regionChart} options={chartOptions} />
        </div>
        <div style={styles.chartCard}>
          <h3 style={styles.chartTitle}>Top Products</h3>
          <Bar data={productChart} options={chartOptions} />
        </div>
      </div>
    </div>
  );
}

const styles = {
  heading: { margin: "0 0 20px", fontSize: 22, color: "#1a1a2e" },
  kpiGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: 16, marginBottom: 24 },
  card: { background: "#fff", borderRadius: 10, padding: "20px 16px", boxShadow: "0 1px 4px rgba(0,0,0,0.08)" },
  kpiValue: { fontSize: 28, fontWeight: 700, color: "#1a1a2e" },
  kpiLabel: { fontSize: 13, color: "#666", marginTop: 4 },
  kpiSub: { fontSize: 11, color: "#aaa", marginTop: 2 },
  chartsRow: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 },
  chartCard: { background: "#fff", borderRadius: 10, padding: 20, boxShadow: "0 1px 4px rgba(0,0,0,0.08)" },
  chartTitle: { margin: "0 0 16px", fontSize: 15, color: "#333" },
  error: { color: "#ef4444", padding: 20 },
  loading: { color: "#888", padding: 20 },
};
