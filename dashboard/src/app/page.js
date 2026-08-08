'use client';

import { useEffect } from 'react';
import Link from 'next/link';
import AnvilLogo from './components/AnvilLogo';

const SPECS = [
  <>5 <b>pipeline stages</b></>,
  <>0 <b>network access</b> by default</>,
  <>2 <b>independent review layers</b></>,
  <>200 <b>lesson memory cap</b></>,
  <>3 <b>approvals</b> to auto-trust</>,
  <>50% <b>failure threshold</b> triggers re-forge</>,
  <>SQLite + <b>Chroma</b> vector store</>,
  <>Groq <b>Llama 3.3 70B</b> inference</>,
];

export default function LandingPage() {
  useEffect(() => {
    const nav = document.getElementById('nav');
    const onScroll = () => nav?.classList.toggle('scrolled', window.scrollY > 20);
    window.addEventListener('scroll', onScroll);

    const revealEls = document.querySelectorAll('.reveal');
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('in-view');
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 }
    );
    revealEls.forEach((el) => io.observe(el));

    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!prefersReduced) {
      document.querySelector('.pulse-dot')?.classList.add('run');
    }

    return () => {
      window.removeEventListener('scroll', onScroll);
      io.disconnect();
    };
  }, []);

  return (
    <>
      <nav id="nav">
        <div className="logo">
          <AnvilLogo />
          ANVIL
        </div>
        <div className="nav-links">
          <a href="#stack">Stack</a>
          <a href="#pipeline">Pipeline</a>
          <a href="#demo">Demo</a>
        </div>
        <Link href="/dashboard" className="nav-cta">Start building</Link>
      </nav>

      <section className="hero">
        <div className="eyebrow"><span className="eyebrow-dot"></span>self-extending agent</div>
        <h1>An agent that<br /><span className="brand">forges</span> its <span className="tight">own tools.</span></h1>
        <div className="hero-sub reveal">
          <p>ANVIL writes new capabilities at runtime, tests them in a sandbox, gets them reviewed for safety, and keeps what works — growing more capable the longer it runs.</p>
          <div className="hero-ctas">
            <Link href="/dashboard" className="btn-primary">See it run</Link>
            <a className="btn-secondary" href="#stack">Explore the stack</a>
          </div>
        </div>
      </section>

      <div className="ticker-wrap">
        <div className="ticker">
          {[...SPECS, ...SPECS].map((item, i) => (
            <span className="ticker-item" key={i}>{item}</span>
          ))}
        </div>
      </div>

      <section className="stack reveal" id="stack">
        <div className="stack-head">
          <div className="stack-label">the stack</div>
          <h2>Build your perfect loop. Generate adds capability, Validate adds trust, Govern adds control.</h2>
        </div>
        <div className="stack-grid">
          <div className="stack-card">
            <div className="stack-tag">Capability</div>
            <h3>Generate</h3>
            <p>A dedicated codegen agent writes new tools and their own test cases at runtime — no developer redeploy required.</p>
            <ul className="stack-specs">
              <li><span>Codegen model</span><span>Groq / Llama 3.3</span></li>
              <li><span>Test cases per tool</span><span>2–3 auto-written</span></li>
              <li><span>Retry on failure</span><span>up to 2 attempts</span></li>
            </ul>
          </div>
          <div className="stack-card">
            <div className="stack-tag">Trust</div>
            <h3>Validate</h3>
            <p>Every tool runs isolated first, then faces an independent adversarial review before it&apos;s ever trusted.</p>
            <ul className="stack-specs">
              <li><span>Network access</span><span>disabled</span></li>
              <li><span>Filesystem scope</span><span>scratch/ only</span></li>
              <li><span>Review agent</span><span>separate context</span></li>
            </ul>
          </div>
          <div className="stack-card">
            <div className="stack-tag">Control</div>
            <h3>Govern</h3>
            <p>Side-effecting tools pause for human approval until they&apos;ve earned automatic trust — every decision logged.</p>
            <ul className="stack-specs">
              <li><span>Approval to auto-trust</span><span>3 uses</span></li>
              <li><span>Failure re-forge threshold</span><span>50% rate</span></li>
              <li><span>Audit log</span><span>every decision</span></li>
            </ul>
          </div>
        </div>
      </section>

      <section className="schematic-section reveal" id="pipeline">
        <div className="schematic-frame">
          <svg className="pipeline" viewBox="0 0 1000 240" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" className="arrowhead" /></marker>
              <marker id="arrow-brand" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" className="arrowhead-brand" /></marker>
            </defs>
            <path className="flow-path" markerEnd="url(#arrow)" d="M140,90 L220,90" />
            <path className="flow-path" markerEnd="url(#arrow)" d="M340,90 L420,90" style={{ animationDelay: '0.25s' }} />
            <path className="flow-path" markerEnd="url(#arrow)" d="M540,90 L620,90" style={{ animationDelay: '0.5s' }} />
            <path className="flow-path" markerEnd="url(#arrow)" d="M740,90 L820,90" style={{ animationDelay: '0.75s' }} />
            <path className="loop-path" markerEnd="url(#arrow-brand)" d="M860,130 C860,200 140,200 140,130" />
            <circle className="pulse-dot" r="4" style={{ offsetPath: "path('M140,90 L220,90 L340,90 L420,90 L540,90 L620,90 L740,90 L820,90 L860,90 L860,130 C860,200 140,200 140,130 Z')" }} />
            <g><rect className="node-box" x="20" y="55" width="120" height="70" rx="8" /><text className="node-label" x="80" y="88" textAnchor="middle">PLANNER</text><text className="node-sub" x="80" y="104" textAnchor="middle">decides what&apos;s needed</text></g>
            <g><rect className="node-box" x="220" y="55" width="120" height="70" rx="8" /><text className="node-label" x="280" y="88" textAnchor="middle">FORGE</text><text className="node-sub" x="280" y="104" textAnchor="middle">writes tool + tests</text></g>
            <g><rect className="node-box" x="420" y="55" width="120" height="70" rx="8" /><text className="node-label" x="480" y="88" textAnchor="middle">SANDBOX</text><text className="node-sub" x="480" y="104" textAnchor="middle">runs it isolated</text></g>
            <g><rect className="node-box" x="620" y="55" width="120" height="70" rx="8" /><text className="node-label" x="680" y="88" textAnchor="middle">CRITIC</text><text className="node-sub" x="680" y="104" textAnchor="middle">checks for unsafe code</text></g>
            <g><rect className="node-box" x="820" y="55" width="120" height="70" rx="8" /><text className="node-label" x="880" y="88" textAnchor="middle">REGISTRY</text><text className="node-sub" x="880" y="104" textAnchor="middle">keeps it if it earns a place</text></g>
            <text x="500" y="225" textAnchor="middle" className="node-sub" fill="var(--brand)" fontSize="10">registered tools loop back into future planning</text>
          </svg>
        </div>
      </section>

      <div className="stages-intro reveal">
        <div className="stack-label"> how it forges</div>
        <div className="squeeze">
          <span className="s1">Plan</span><span className="s2">Forge</span><span className="s3">Sandbox</span><span className="s4">Critic</span><span className="s5">Keep</span>
        </div>
      </div>
      <section className="stages reveal">
        <div className="stage-row">
          <div className="stage"><span className="stage-num">01</span><h3>Detect the gap</h3><p>The planner recognizes when no existing tool fits the task at hand.</p></div>
          <div className="stage"><span className="stage-num">02</span><h3>Write &amp; test</h3><p>A dedicated codegen agent writes the tool and its own test cases.</p></div>
          <div className="stage"><span className="stage-num">03</span><h3>Run isolated</h3><p>No network, no filesystem access outside scratch, hard timeouts.</p></div>
          <div className="stage"><span className="stage-num">04</span><h3>Independent critic</h3><p>A separate agent checks for unsafe patterns tests wouldn&apos;t catch.</p></div>
          <div className="stage"><span className="stage-num">05</span><h3>Register &amp; reuse</h3><p>Approved tools persist — instantly available next time, no re-forging.</p></div>
        </div>
      </section>

      <section className="demo reveal" id="demo">
        <div className="demo-head">
          <div className="stack-label"> see it forge</div>
          <h2 style={{ fontSize: 'clamp(1.8rem, 3.4vw, 2.6rem)', fontWeight: 700, letterSpacing: '-0.02em' }}>A capability gap, closed live.</h2>
        </div>
        <div className="terminal">
          <div className="terminal-bar"><span className="terminal-dot"></span><span className="terminal-dot"></span><span className="terminal-dot"></span><span className="terminal-title">anvil — core.agent</span></div>
          <div className="terminal-body">
            <div><span className="t-prompt">You:</span> <span className="t-ink">reverse the string hello world</span></div>
            <div className="t-muted">[Iteration 1] Planner decided: no_tool_fits</div>
            <div className="t-muted">→ No existing tool fits. Attempting to forge a new tool...</div>
            <div className="t-brand">=== TOOL FORGED, TESTED, AND CRITIC-APPROVED ===</div>
            <div className="t-muted">Class: StringReversalTool</div>
            <div className="t-ok">Critic verdict: approve — no unsafe patterns detected</div>
            <div className="t-muted">&nbsp;</div>
            <div><span className="t-prompt">ANVIL:</span> <span className="t-ink">dlrow olleh</span></div>
          </div>
        </div>
      </section>

      <section className="closing reveal">
        <h2>Put self-extension to work.</h2>
        <p>Clone the repo, run it locally, and watch it write its first tool in under a minute.</p>
        <Link href="/dashboard" className="btn-primary">Get started ↗</Link>
      </section>

      <footer>
        <span className="mono" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <AnvilLogo size="footer" />
          ANVIL — built by Aman Singh
        </span>
        <span className="mono"><a href="https://github.com/AmanSingh-404/ANVIL" target="_blank" rel="noopener noreferrer">github.com/AmanSingh-404/ANVIL ↗</a></span>
      </footer>
    </>
  );
}