'use client';

import { useState, useRef, useEffect, useCallback } from 'react';

export default function DashboardPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);
  const [tools, setTools] = useState([]);
  const [pendingApproval, setPendingApproval] = useState(null);

  const fetchTools = useCallback(async () => {
    try {
      const res = await fetch('http://localhost:5000/api/tools');
      const data = await res.json();
      setTools(data.tools || []);
    } catch (err) {
      console.error('Failed to fetch tools:', err);
    }
  }, []);

  const pollApproval = useCallback(async () => {
    try {
      const res = await fetch('http://localhost:5000/api/approval/pending');
      const data = await res.json();
      setPendingApproval(data.pending || null);
    } catch (err) {
      console.error('Failed to poll approval:', err);
    }
  }, []);

  useEffect(() => {
    fetchTools();
  }, [fetchTools]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (!loading) {
      setPendingApproval(null);
      return;
    }
    const interval = setInterval(pollApproval, 700);
    return () => clearInterval(interval);
  }, [loading, pollApproval]);

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

  async function resolveApproval(approved) {
    try {
      await fetch('http://localhost:5000/api/approval/resolve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approved }),
      });
      setPendingApproval(null);
    } catch (err) {
      console.error('Failed to resolve approval:', err);
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
        {pendingApproval && (
          <div style={styles.approvalCard}>
            <div style={styles.approvalHeader}>⚠ Approval required</div>
            <div style={styles.approvalTool}>{pendingApproval.tool_name}</div>
            <div style={styles.approvalDesc}>{pendingApproval.description}</div>
            <div style={styles.approvalArgs}>{JSON.stringify(pendingApproval.arguments)}</div>
            <div style={styles.approvalBtns}>
              <button style={styles.approveBtn} onClick={() => resolveApproval(true)}>Approve</button>
              <button style={styles.denyBtn} onClick={() => resolveApproval(false)}>Deny</button>
            </div>
          </div>
        )}

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
  // ============================================
  // MAIN APP
  // ============================================

  layout: {
    display: 'flex',
    width: '100%',
    height: '100vh',
    minHeight: 0,
    overflow: 'hidden',
    background: 'var(--bg)',
    boxSizing: 'border-box',
  },

  // ============================================
  // CHAT SIDE
  // ============================================

  page: {
    flex: 1,
    minWidth: 0,
    minHeight: 0,
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    boxSizing: 'border-box',
    fontFamily: 'var(--font-space-grotesk), sans-serif',
    background: 'var(--bg)',
  },

  // ============================================
  // HEADER
  // ============================================

  header: {
    height: '64px',
    minHeight: '64px',
    flexShrink: 0,

    display: 'flex',
    alignItems: 'center',

    padding: '0 28px',

    borderBottom: '1px solid var(--border)',
    background: 'var(--bg)',

    boxSizing: 'border-box',
  },

  h1: {
    margin: 0,
    fontSize: '1.05rem',
    fontWeight: 700,
    letterSpacing: '-0.02em',
  },

  statusDot: {
    width: '7px',
    height: '7px',
    marginLeft: '4px',
    borderRadius: '50%',
    background: '#4CAF50',
    boxShadow: '0 0 0 3px rgba(76, 175, 80, 0.12)',
  },

  // ============================================
  // CHAT WINDOW
  // ============================================

  chatWindow: {
    flex: 1,
    minHeight: 0,

    overflowY: 'auto',
    overflowX: 'hidden',

    display: 'flex',
    flexDirection: 'column',

    gap: '18px',

    padding: '28px 32px',

    boxSizing: 'border-box',

    scrollbarWidth: 'thin',
  },

  empty: {
    color: 'var(--muted)',
    fontSize: '0.9rem',
    lineHeight: 1.6,

    margin: 'auto',

    textAlign: 'center',

    maxWidth: '520px',
  },

  // ============================================
  // USER MESSAGE
  // ============================================

  userMsg: {
    alignSelf: 'flex-end',

    width: 'fit-content',
    maxWidth: '65%',

    background: 'var(--brand)',
    color: '#fff',

    padding: '11px 15px',

    borderRadius: '10px 10px 3px 10px',

    fontSize: '0.88rem',
    lineHeight: 1.5,

    boxSizing: 'border-box',

    boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
  },

  // ============================================
  // ANVIL MESSAGE
  // ============================================

  agentMsg: {
    alignSelf: 'flex-start',

    width: 'fit-content',
    maxWidth: '65%',

    background: 'var(--bg-panel)',

    border: '1px solid var(--border)',

    padding: '11px 15px',

    borderRadius: '10px 10px 10px 3px',

    fontSize: '0.88rem',
    lineHeight: 1.5,

    whiteSpace: 'pre-wrap',

    boxSizing: 'border-box',
  },

  // ============================================
  // ERROR
  // ============================================

  errorMsg: {
    alignSelf: 'flex-start',

    width: 'fit-content',
    maxWidth: '65%',

    background: '#FDECEC',

    border: '1px solid #F5B5B5',

    color: '#9C2B2B',

    padding: '11px 15px',

    borderRadius: '10px',

    fontSize: '0.88rem',
    lineHeight: 1.5,

    boxSizing: 'border-box',
  },

  // ============================================
  // MESSAGE ROLE
  // ============================================

  msgRole: {
    display: 'block',

    marginBottom: '4px',

    fontFamily: 'var(--font-plex-mono), monospace',

    fontSize: '0.62rem',

    fontWeight: 500,

    opacity: 0.55,

    textTransform: 'uppercase',

    letterSpacing: '0.06em',
  },

  thinking: {
    color: 'var(--muted)',
    fontStyle: 'italic',
  },

  // ============================================
  // APPROVAL CARD
  // ============================================

  approvalCard: {
    flexShrink: 0,

    margin: '0 32px 12px',

    padding: '15px 17px',

    borderRadius: '9px',

    background: '#FFF8F0',

    border: '1px solid #F4C089',

    boxSizing: 'border-box',
  },

  approvalHeader: {
    fontFamily: 'var(--font-plex-mono), monospace',

    fontSize: '0.72rem',

    fontWeight: 600,

    color: '#B35C00',

    marginBottom: '7px',
  },

  approvalTool: {
    fontFamily: 'var(--font-plex-mono), monospace',

    fontSize: '0.84rem',

    fontWeight: 600,
  },

  approvalDesc: {
    fontSize: '0.82rem',

    color: 'var(--muted)',

    marginTop: '4px',

    lineHeight: 1.5,
  },

  approvalArgs: {
    fontFamily: 'var(--font-plex-mono), monospace',

    fontSize: '0.7rem',

    color: 'var(--muted)',

    marginTop: '7px',

    overflowX: 'auto',
  },

  approvalBtns: {
    display: 'flex',

    gap: '8px',

    marginTop: '12px',
  },

  approveBtn: {
    fontFamily: 'var(--font-plex-mono), monospace',

    fontSize: '0.75rem',

    fontWeight: 600,

    background: '#2E7D32',

    color: '#fff',

    padding: '7px 16px',

    borderRadius: '6px',

    border: 'none',

    cursor: 'pointer',
  },

  denyBtn: {
    fontFamily: 'var(--font-plex-mono), monospace',

    fontSize: '0.75rem',

    fontWeight: 600,

    background: '#C23101',

    color: '#fff',

    padding: '7px 16px',

    borderRadius: '6px',

    border: 'none',

    cursor: 'pointer',
  },

  // ============================================
  // INPUT AREA
  // ============================================

  inputRow: {
    flexShrink: 0,

    display: 'flex',

    alignItems: 'center',

    gap: '10px',

    padding: '14px 32px',

    borderTop: '1px solid var(--border)',

    background: 'var(--bg-panel)',

    boxSizing: 'border-box',
  },

  textarea: {
    flex: 1,

    minWidth: 0,

    height: '40px',

    padding: '10px 13px',

    borderRadius: '7px',

    border: '1px solid var(--border-strong)',

    outline: 'none',

    background: 'var(--bg)',

    color: 'var(--text)',

    fontFamily: 'var(--font-space-grotesk), sans-serif',

    fontSize: '0.85rem',

    lineHeight: 1.4,

    resize: 'none',

    boxSizing: 'border-box',
  },

  sendBtn: {
    flexShrink: 0,

    height: '40px',

    fontFamily: 'var(--font-plex-mono), monospace',

    fontSize: '0.75rem',

    fontWeight: 600,

    background: 'var(--brand)',

    color: '#fff',

    padding: '0 20px',

    borderRadius: '7px',

    border: 'none',

    cursor: 'pointer',
  },

  // ============================================
  // TOOL REGISTRY
  // ============================================

  registryPanel: {
    width: '310px',
    minWidth: '310px',

    height: '100%',

    flexShrink: 0,

    display: 'flex',

    flexDirection: 'column',

    overflow: 'hidden',

    borderLeft: '1px solid var(--border)',

    background: 'var(--bg-panel)',

    fontFamily: 'var(--font-space-grotesk), sans-serif',

    boxSizing: 'border-box',
  },

  registryHeader: {
    height: '64px',
    minHeight: '64px',

    flexShrink: 0,

    display: 'flex',

    justifyContent: 'space-between',

    alignItems: 'center',

    padding: '0 18px',

    borderBottom: '1px solid var(--border)',

    boxSizing: 'border-box',
  },

  registryTitle: {
    fontWeight: 700,

    fontSize: '0.88rem',

    letterSpacing: '-0.01em',
  },

  registryCount: {
    fontFamily: 'var(--font-plex-mono), monospace',

    fontSize: '0.68rem',

    background: 'var(--brand-tint)',

    color: 'var(--brand-dark)',

    padding: '3px 8px',

    borderRadius: '100px',
  },

  registryList: {
    flex: 1,

    minHeight: 0,

    overflowY: 'auto',

    overflowX: 'hidden',

    padding: '12px',

    boxSizing: 'border-box',

    scrollbarWidth: 'thin',
  },

  registryEmpty: {
    color: 'var(--muted)',

    fontSize: '0.8rem',

    padding: '10px 4px',
  },

  // ============================================
  // TOOL CARD
  // ============================================

  toolCard: {
    border: '1px solid var(--border)',

    borderRadius: '8px',

    padding: '11px 12px',

    marginBottom: '8px',

    background: 'var(--bg)',

    transition: 'border-color 0.15s ease',
  },

  toolName: {
    fontFamily: 'var(--font-plex-mono), monospace',

    fontSize: '0.76rem',

    fontWeight: 600,

    lineHeight: 1.4,

    wordBreak: 'break-word',
  },

  toolVersion: {
    color: 'var(--muted-2)',

    fontWeight: 400,
  },

  toolMeta: {
    display: 'flex',

    alignItems: 'center',

    gap: '5px',

    marginTop: '7px',

    flexWrap: 'wrap',
  },

  badgeSafe: {
    fontSize: '0.62rem',

    fontFamily: 'var(--font-plex-mono), monospace',

    background: '#E8F5E9',

    color: '#2E7D32',

    padding: '2px 7px',

    borderRadius: '100px',
  },

  badgeRisk: {
    fontSize: '0.62rem',

    fontFamily: 'var(--font-plex-mono), monospace',

    background: '#FFF3E0',

    color: '#B35C00',

    padding: '2px 7px',

    borderRadius: '100px',
  },

  badgeAuto: {
    fontSize: '0.62rem',

    fontFamily: 'var(--font-plex-mono), monospace',

    background: 'var(--brand-tint)',

    color: 'var(--brand-dark)',

    padding: '2px 7px',

    borderRadius: '100px',
  },

  toolStats: {
    display: 'flex',

    gap: '9px',

    marginTop: '7px',

    fontSize: '0.67rem',

    fontFamily: 'var(--font-plex-mono), monospace',
  },

  statOk: {
    color: '#2E7D32',
  },

  statFail: {
    color: '#C23101',
  },
};