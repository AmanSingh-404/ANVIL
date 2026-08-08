'use client';

import { useState, useRef, useEffect, useCallback } from 'react';

export default function DashboardPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);
  const [tools, setTools] = useState([]);

  const fetchTools = useCallback(async () => {
    try {
      const res = await fetch('http://localhost:5000/api/tools');
      const data = await res.json();
      setTools(data.tools || []);
    } catch (err) {
      console.error('Failed to fetch tools:', err);
    }
  }, []);

  useEffect(() => {
    fetchTools();
  }, [fetchTools]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function sendMessage() {
    const text = input.trim();
    if (!text || loading) return;

    setMessages((prev) => [...prev, { role: 'user', content: text }]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch('http://localhost:5000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      });
      const data = await res.json();

      if (data.error) {
        setMessages((prev) => [...prev, { role: 'error', content: data.error }]);
      } else {
        setMessages((prev) => [...prev, { role: 'agent', content: data.response }]);
        fetchTools(); // a new tool may have just been forged — refresh the registry panel
      }
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'error', content: `Could not reach ANVIL backend: ${err.message}` }]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <div style={styles.layout}>
      <div style={styles.page}>
        <header style={styles.header}>
          <h1 style={styles.h1}>ANVIL Dashboard</h1>
          <span style={styles.statusDot}></span>
        </header>

        <div style={styles.chatWindow}>
          {messages.length === 0 && (
            <div style={styles.empty}>Ask ANVIL something — if it doesn&apos;t have a tool for it, watch it forge one.</div>
          )}
          {messages.map((m, i) => (
            <div key={i} style={m.role === 'user' ? styles.userMsg : m.role === 'error' ? styles.errorMsg : styles.agentMsg}>
              <span style={styles.msgRole}>{m.role === 'user' ? 'You' : m.role === 'error' ? 'Error' : 'ANVIL'}</span>
              <div>{m.content}</div>
            </div>
          ))}
          {loading && <div style={styles.agentMsg}><span style={styles.msgRole}>ANVIL</span><div style={styles.thinking}>thinking...</div></div>}
          <div ref={bottomRef} />
        </div>

        <div style={styles.inputRow}>
          <textarea
            style={styles.textarea}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a request for ANVIL..."
            rows={1}
          />
          <button style={styles.sendBtn} onClick={sendMessage} disabled={loading}>Send</button>
        </div>
      </div>

      <aside style={styles.registryPanel}>
        <div style={styles.registryHeader}>
          <span style={styles.registryTitle}>Tool Registry</span>
          <span style={styles.registryCount}>{tools.length}</span>
        </div>
        <div style={styles.registryList}>
          {tools.length === 0 && <div style={styles.registryEmpty}>No tools forged yet.</div>}
          {tools.map((t) => (
            <div key={t.name} style={styles.toolCard}>
              <div style={styles.toolName}>{t.name} <span style={styles.toolVersion}>v{t.version}</span></div>
              <div style={styles.toolMeta}>
                <span style={t.risk_tier === 'read_only' ? styles.badgeSafe : styles.badgeRisk}>{t.risk_tier}</span>
                {t.auto_approved && <span style={styles.badgeAuto}>auto-approved</span>}
              </div>
              <div style={styles.toolStats}>
                <span style={styles.statOk}>{t.success_count} ok</span>
                <span style={styles.statFail}>{t.failure_count} fail</span>
              </div>
            </div>
          ))}
        </div>
      </aside>
    </div>
  );
}

const styles = {
  page: {
    display: 'flex',
    flexDirection: 'column',
    width: '100vw',
    height: '100vh',
    overflow: 'hidden',
    boxSizing: 'border-box',
    fontFamily: 'var(--font-space-grotesk), sans-serif', background: 'var(--bg)',
  },
  header: {
    display: 'flex', alignItems: 'center', gap: '10px',
    padding: '20px 6vw', borderBottom: '1px solid var(--border)',
  },
  h1: { fontSize: '1.3rem', fontWeight: 700 },
  statusDot: { width: '8px', height: '8px', borderRadius: '50%', background: '#4CAF50' },
  chatWindow: {
    flex: 1, overflowY: 'auto', padding: '24px 6vw', display: 'flex', flexDirection: 'column', gap: '16px',
  },
  empty: { color: 'var(--muted)', fontSize: '0.95rem', margin: 'auto' },
  userMsg: {
    alignSelf: 'flex-end', maxWidth: '70%', background: 'var(--brand)', color: '#fff',
    padding: '12px 16px', borderRadius: '10px 10px 2px 10px', fontSize: '0.92rem',
  },
  agentMsg: {
    alignSelf: 'flex-start', maxWidth: '70%', background: 'var(--bg-panel)', border: '1px solid var(--border)',
    padding: '12px 16px', borderRadius: '10px 10px 10px 2px', fontSize: '0.92rem', whiteSpace: 'pre-wrap',
  },
  errorMsg: {
    alignSelf: 'flex-start', maxWidth: '70%', background: '#FDECEC', border: '1px solid #F5B5B5', color: '#9C2B2B',
    padding: '12px 16px', borderRadius: '10px', fontSize: '0.92rem',
  },
  msgRole: {
    display: 'block', fontFamily: 'var(--font-plex-mono), monospace', fontSize: '0.68rem',
    opacity: 0.6, marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.05em',
  },
  thinking: { color: 'var(--muted)', fontStyle: 'italic' },
  inputRow: {
    display: 'flex', gap: '10px', padding: '16px 6vw', borderTop: '1px solid var(--border)', background: 'var(--bg-panel)',
  },
  textarea: {
    flex: 1, padding: '12px 14px', borderRadius: '8px', border: '1px solid var(--border-strong)',
    fontFamily: 'var(--font-space-grotesk), sans-serif', fontSize: '0.92rem', resize: 'none',
  },
  sendBtn: {
    fontFamily: 'var(--font-plex-mono), monospace', fontSize: '0.85rem', fontWeight: 600,
    background: 'var(--brand)', color: '#fff', padding: '0 22px', borderRadius: '8px', border: 'none', cursor: 'pointer',
  },
 layout: {
  display: 'flex',
  flex: 1,
  width: '100%',
  minWidth: 0,
  minHeight: 0,
  overflow: 'hidden',
},
  registryPanel: {
    width: '300px', flexShrink: 0, borderLeft: '1px solid var(--border)',
    background: 'var(--bg-panel)', display: 'flex', flexDirection: 'column',
    fontFamily: 'var(--font-space-grotesk), sans-serif',
  },
  registryHeader: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '20px 20px 14px', borderBottom: '1px solid var(--border)',
  },
  registryTitle: { fontWeight: 700, fontSize: '0.95rem' },
  registryCount: {
    fontFamily: 'var(--font-plex-mono), monospace', fontSize: '0.75rem',
    background: 'var(--brand-tint)', color: 'var(--brand-dark)', padding: '2px 9px', borderRadius: '100px',
  },
  registryList: { flex: 1, overflowY: 'auto', padding: '14px' },
  registryEmpty: { color: 'var(--muted)', fontSize: '0.85rem', padding: '10px 4px' },
  toolCard: {
    border: '1px solid var(--border)', borderRadius: '8px', padding: '12px 14px', marginBottom: '10px',
  },
  toolName: { fontFamily: 'var(--font-plex-mono), monospace', fontSize: '0.82rem', fontWeight: 600 },
  toolVersion: { color: 'var(--muted-2)', fontWeight: 400 },
  toolMeta: { display: 'flex', gap: '6px', marginTop: '8px', flexWrap: 'wrap' },
  badgeSafe: {
    fontSize: '0.68rem', fontFamily: 'var(--font-plex-mono), monospace', background: '#E8F5E9', color: '#2E7D32',
    padding: '2px 8px', borderRadius: '100px',
  },
  badgeRisk: {
    fontSize: '0.68rem', fontFamily: 'var(--font-plex-mono), monospace', background: '#FFF3E0', color: '#B35C00',
    padding: '2px 8px', borderRadius: '100px',
  },
  badgeAuto: {
    fontSize: '0.68rem', fontFamily: 'var(--font-plex-mono), monospace', background: 'var(--brand-tint)', color: 'var(--brand-dark)',
    padding: '2px 8px', borderRadius: '100px',
  },
  toolStats: { display: 'flex', gap: '10px', marginTop: '8px', fontSize: '0.75rem', fontFamily: 'var(--font-plex-mono), monospace' },
  statOk: { color: '#2E7D32' },
  statFail: { color: '#C23101' },
  
};