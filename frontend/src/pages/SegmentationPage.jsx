import React, { useEffect, useState } from "react";
import { segments } from "../services/api";

const SEGMENT_COLORS = {
  "High Value":     "#7c83fd",
  "Loyal":          "#34d399",
  "At Risk":        "#f97316",
  "New Customer":   "#60a5fa",
  "Low Engagement": "#9ca3af",
};

export default function SegmentationPage() {
  const [summary, setSummary] = useState([]);
  const [loading, setLoading] = useState(true);
  const [predResult, setPredResult] = useState(null);
  const [predLoading, setPredLoading] = useState(false);
  const [form, setForm] = useState({
    lifetime_value: "", total_orders: "", account_age_days: "",
    days_since_last_purchase: "", support_tickets: "", avg_order_value: "",
  });

  useEffect(() => {
    segments.summary()
      .then((res) => setSummary(res.data.segment_summary || []))
      .catch(() => setSummary([]))
      .finally(() => setLoading(false));
  }, []);

  const predict = async (e) => {
    e.preventDefault();
    setPredLoading(true);
    setPredResult(null);
    try {
      const res = await segments.predict(form);
      setPredResult(res.data);
    } catch (err) {
      setPredResult({ error: err.response?.data?.error || "Prediction failed" });
    } finally {
      setPredLoading(false);
    }
  };

  const Field = ({ label, field }) => (
    <label style={styles.field}>
      <span style={styles.fieldLabel}>{label}</span>
      <input
        style={styles.input}
        type="number"
        value={form[field]}
        onChange={(e) => setForm({ ...form, [field]: e.target.value })}
      />
    </label>
  );

  return (
    <div>
      <h2 style={styles.heading}>Customer Segmentation</h2>
      <div style={styles.grid}>
        {/* Segment Summary */}
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>Segment Distribution</h3>
          {loading ? (
            <div style={styles.msg}>Loading...</div>
          ) : summary.length === 0 ? (
            <div style={styles.msg}>No segment data. Run train_segmentation.py first.</div>
          ) : (
            summary.map((s) => (
              <div key={s.segment_label} style={styles.segRow}>
                <span
                  style={{
                    ...styles.segDot,
                    background: SEGMENT_COLORS[s.segment_label] || "#888",
                  }}
                />
                <div style={styles.segInfo}>
                  <span style={styles.segLabel}>{s.segment_label}</span>
                  <span style={styles.segDesc}>{s.description}</span>
                </div>
                <span style={styles.segCount}>{s.customer_count} customers</span>
              </div>
            ))
          )}
        </div>

        {/* Predict Segment */}
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>Predict Customer Segment</h3>
          <form onSubmit={predict} style={styles.form}>
            <Field label="Lifetime Value ($)"          field="lifetime_value" />
            <Field label="Total Orders"                field="total_orders" />
            <Field label="Account Age (days)"          field="account_age_days" />
            <Field label="Days Since Last Purchase"    field="days_since_last_purchase" />
            <Field label="Support Tickets"             field="support_tickets" />
            <Field label="Avg Order Value ($)"         field="avg_order_value" />
            <button style={styles.btn} type="submit" disabled={predLoading}>
              {predLoading ? "Predicting..." : "Predict Segment"}
            </button>
          </form>

          {predResult && (
            <div style={{
              ...styles.resultCard,
              borderLeft: `4px solid ${SEGMENT_COLORS[predResult.segment_label] || "#888"}`,
            }}>
              {predResult.error ? (
                <div style={{ color: "#ef4444" }}>{predResult.error}</div>
              ) : (
                <>
                  <div style={styles.resultLabel}>{predResult.segment_label}</div>
                  <div style={styles.resultDesc}>{predResult.description}</div>
                  <div style={styles.resultMeta}>
                    Cluster ID: {predResult.cluster_id} · Model: {predResult.model_version}
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const styles = {
  heading:     { margin: "0 0 20px", fontSize: 22, color: "#1a1a2e" },
  grid:        { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 },
  card:        { background: "#fff", borderRadius: 10, padding: 20, boxShadow: "0 1px 4px rgba(0,0,0,0.08)" },
  cardTitle:   { margin: "0 0 16px", fontSize: 15, color: "#333", fontWeight: 600 },
  msg:         { color: "#888", fontSize: 13 },
  segRow:      { display: "flex", alignItems: "flex-start", gap: 10, padding: "10px 0", borderBottom: "1px solid #f5f5f5" },
  segDot:      { width: 12, height: 12, borderRadius: "50%", marginTop: 4, flexShrink: 0 },
  segInfo:     { flex: 1, display: "flex", flexDirection: "column", gap: 2 },
  segLabel:    { fontSize: 14, fontWeight: 600, color: "#1a1a2e" },
  segDesc:     { fontSize: 11, color: "#888" },
  segCount:    { fontSize: 13, color: "#555", whiteSpace: "nowrap" },
  form:        { display: "flex", flexDirection: "column", gap: 10 },
  field:       { display: "flex", flexDirection: "column", gap: 3 },
  fieldLabel:  { fontSize: 12, color: "#666", fontWeight: 600 },
  input:       { padding: "7px 10px", border: "1px solid #ddd", borderRadius: 6, fontSize: 13 },
  btn:         { padding: "9px", background: "#7c83fd", color: "#fff", border: "none", borderRadius: 6, fontSize: 14, fontWeight: 600, cursor: "pointer", marginTop: 4 },
  resultCard:  { marginTop: 16, padding: 14, background: "#f9fafb", borderRadius: 8 },
  resultLabel: { fontSize: 18, fontWeight: 700, color: "#1a1a2e", marginBottom: 4 },
  resultDesc:  { fontSize: 13, color: "#555", marginBottom: 6 },
  resultMeta:  { fontSize: 11, color: "#aaa" },
};
