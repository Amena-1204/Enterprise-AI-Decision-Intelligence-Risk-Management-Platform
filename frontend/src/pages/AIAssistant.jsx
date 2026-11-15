import React, { useState, useRef, useEffect } from "react";
import { ai } from "../services/api";

const REPORT_TYPES = ["performance", "churn", "fraud", "sales"];

export default function AIAssistant() {
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hello! I'm your Enterprise AI assistant. Ask me about customers, churn risk, fraud, sales trends, or request a business report." }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [reportType, setReportType] = useState("performance");
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const query = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: query }]);
    setLoading(true);
    try {
      const res = await ai.ask(query);
      setMessages((prev) => [...prev, {
        role: "assistant",
        content: res.data.answer,
        meta: {
          agent: res.data.agent,
          tokens: res.data.tokens_used,
          latency: res.data.latency_ms,
          local: res.data.llm_configured === false,
        },
      }]);
    } catch (err) {
      setMessages((prev) => [...prev, { role: "assistant", content: "Sorry, I encountered an error. Please try again.", error: true }]);
    } finally {
      setLoading(false);
    }
  };

  const generateReport = async () => {
    setLoading(true);
    setMessages((prev) => [...prev, { role: "user", content: `Generate a ${reportType} report` }]);
    try {
      const res = await ai.report(reportType);
      setMessages((prev) => [...prev, {
        role: "assistant",
        content: res.data.answer,
        meta: {
          agent: res.data.agent,
          tokens: res.data.tokens_used,
          latency: res.data.latency_ms,
          local: res.data.llm_configured === false,
        },
      }]);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: "Failed to generate report.", error: true }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <h2 style={styles.heading}>AI Assistant</h2>
      <div style={styles.reportBar}>
        <select style={styles.select} value={reportType} onChange={(e) => setReportType(e.target.value)}>
          {REPORT_TYPES.map((t) => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)} Report</option>)}
        </select>
        <button style={styles.reportBtn} onClick={generateReport} disabled={loading}>Generate Report</button>
      </div>
      <div style={styles.chatBox}>
        {messages.map((msg, i) => (
          <div key={i} style={{ ...styles.message, ...(msg.role === "user" ? styles.userMsg : styles.assistantMsg) }}>
            <div style={styles.msgContent}>{msg.content}</div>
            {msg.meta && (
              <div style={styles.msgMeta}>
                Agent: {msg.meta.agent} ·{" "}
                {msg.meta.local ? (
                  <span style={styles.localBadge} title="OPENAI_API_KEY is not set, so answers are built from platform data instead of a language model">
                    local mode
                  </span>
                ) : (
                  `${msg.meta.tokens} tokens`
                )}{" "}
                · {msg.meta.latency}ms
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div style={{ ...styles.message, ...styles.assistantMsg }}>
            <div style={styles.typing}>Thinking...</div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <form onSubmit={sendMessage} style={styles.inputRow}>
        <input
          style={styles.input}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about churn risk, fraud patterns, sales trends..."
          disabled={loading}
        />
        <button style={styles.sendBtn} type="submit" disabled={loading || !input.trim()}>Send</button>
      </form>
    </div>
  );
}

const styles = {
  container: { display: "flex", flexDirection: "column", height: "calc(100vh - 120px)" },
  heading: { margin: "0 0 12px", fontSize: 22, color: "#1a1a2e" },
  reportBar: { display: "flex", gap: 8, marginBottom: 12 },
  select: { padding: "8px 12px", border: "1px solid #ddd", borderRadius: 6, fontSize: 14 },
  reportBtn: { padding: "8px 16px", background: "#7c83fd", color: "#fff", border: "none", borderRadius: 6, cursor: "pointer", fontSize: 14 },
  chatBox: { flex: 1, background: "#fff", borderRadius: 10, padding: 16, overflowY: "auto", boxShadow: "0 1px 4px rgba(0,0,0,0.08)", display: "flex", flexDirection: "column", gap: 12 },
  message: { maxWidth: "80%", padding: "10px 14px", borderRadius: 10, lineHeight: 1.6 },
  userMsg: { alignSelf: "flex-end", background: "#7c83fd", color: "#fff" },
  assistantMsg: { alignSelf: "flex-start", background: "#f3f4f6", color: "#1a1a2e" },
  msgContent: { fontSize: 14, whiteSpace: "pre-wrap" },
  msgMeta: { fontSize: 10, color: "#aaa", marginTop: 4 },
  localBadge: {
    background: "#fef3c7", color: "#92400e", padding: "1px 6px",
    borderRadius: 4, fontSize: 10, fontWeight: 600,
  },
  typing: { fontSize: 14, color: "#888", fontStyle: "italic" },
  inputRow: { display: "flex", gap: 8, marginTop: 12 },
  input: { flex: 1, padding: "10px 14px", border: "1px solid #ddd", borderRadius: 8, fontSize: 14 },
  sendBtn: { padding: "10px 20px", background: "#7c83fd", color: "#fff", border: "none", borderRadius: 8, cursor: "pointer", fontSize: 14, fontWeight: 600 },
};
