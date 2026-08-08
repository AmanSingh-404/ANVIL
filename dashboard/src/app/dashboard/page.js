'use client';

import { useState, useRef, useEffect } from 'react';

export default function DashboardPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

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
  );
}

const styles = {
  page: {
    display: 'flex', flexDirection: 'column', height: '100vh',
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
};