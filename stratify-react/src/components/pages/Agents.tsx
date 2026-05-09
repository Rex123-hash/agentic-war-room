import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useChatStore } from '../../stores/chatStore'
import { analyze, analyzeDaily, analyzeMCP, getMetrics } from '../../api/services'
import StructuredResult from '../shared/StructuredResult'
import PageHeader from '../layout/PageHeader'

type ModeResult = { summary: string; mode: string; status: string } | null

export default function Agents() {
  const { history, sessionToken, draftPrompt, addMessage, setDraftPrompt, clearChat } = useChatStore()
  const [loading, setLoading] = useState(false)
  const [loadingMsg, setLoadingMsg] = useState('')
  const [result, setResult] = useState<ModeResult>(null)
  const [error, setError] = useState('')
  const { data: metrics } = useQuery({ queryKey: ['metrics'], queryFn: getMetrics, refetchInterval: 10000 })

  const criticalCount = metrics?.critical_open ?? 0
  const openCount = metrics?.open_tasks ?? 0
  const availableCount = metrics?.available_team ?? 0

  async function runAnalysis() {
    if (!draftPrompt.trim()) { setError('Please enter a real project situation first.'); return }
    setError(''); setLoading(true); setLoadingMsg('Coordinating agents...')
    addMessage({ role: 'user', content: draftPrompt })
    try {
      const data = await analyze(draftPrompt, sessionToken)
      addMessage({ role: 'assistant', content: data.summary })
      setResult({ summary: data.summary, mode: 'INTERACTIVE', status: data.status })
    } catch { setError('Cannot connect to backend. Make sure the backend is running.') }
    finally { setLoading(false) }
  }

  async function runDaily() {
    setError(''); setLoading(true); setLoadingMsg('Running autonomous daily check...')
    try {
      const data = await analyzeDaily()
      setResult({ summary: data.summary, mode: 'AUTONOMOUS', status: data.status })
    } catch { setError('Daily check failed. Make sure the backend is running.') }
    finally { setLoading(false) }
  }

  async function runMCP() {
    const goal = draftPrompt.trim() || 'Check urgent open tasks and team availability. If delivery risk is present, create an emergency huddle.'
    setError(''); setLoading(true); setLoadingMsg('Running MCP operations...')
    try {
      const data = await analyzeMCP(goal, sessionToken)
      addMessage({ role: 'assistant', content: data.summary })
      setResult({ summary: data.summary, mode: 'MCP', status: data.status })
    } catch { setError('MCP check failed. Make sure the backend is running.') }
    finally { setLoading(false) }
  }

  const lastSix = history.slice(-6)

  return (
    <div className="page-fade">
      <PageHeader
        title="Agents"
        subtitle="Run interactive project analysis, autonomous checks, and MCP operations from one workspace."
        icon="agent"
      />

      <div style={{ display: 'grid', gridTemplateColumns: '1.6fr 1fr', gap: 24 }}>
        {/* LEFT */}
        <div>
          {/* Workspace card */}
          <div className="glass" style={{ borderRadius: 12, padding: 24, marginBottom: 16, boxShadow: '0 18px 40px rgba(0,0,0,0.18)' }}>
            <div style={{ fontSize: 16, fontWeight: 700, color: '#FAFAFA', marginBottom: 8 }}>Agent Workspace</div>
            <div style={{ fontSize: 15, color: '#A1A1AA', lineHeight: 1.75, marginBottom: 12 }}>
              Describe a real project issue, delivery risk, blocked task, or team problem.
              The system analyzes it using your live project context and suggests next actions.
            </div>
            <div>
              <span className="badge-pill">Real user input</span>
              <span className="badge-pill">Multi-agent orchestration</span>
              <span className="badge-pill">Real calendar action</span>
            </div>
          </div>

          {/* Quick prompts */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, marginBottom: 12 }}>
            {[
              ['Critical Bug', 'A critical issue is open, delivery is at risk today, and we need an action plan. Create a Google Calendar emergency huddle for immediate coordination.'],
              ['Production Issue', 'Production is unstable, users are impacted, and immediate coordination is required.'],
              ['Sprint Delay', 'Sprint delivery is at risk because some tasks are blocked and deadlines are close.'],
            ].map(([label, prompt]) => (
              <button key={label} className="st-btn" onClick={() => setDraftPrompt(prompt)} style={{ width: '100%' }}>
                {label}
              </button>
            ))}
          </div>

          {/* Textarea */}
          <label style={{ display: 'block', fontSize: 14, color: '#A1A1AA', marginBottom: 6, fontWeight: 500 }}>Your Message</label>
          <textarea
            className="st-textarea"
            value={draftPrompt}
            onChange={e => setDraftPrompt(e.target.value)}
            rows={4}
            placeholder="Example: We have 2 blocked tasks, one critical issue, and one unavailable team member. What should we do today?"
            style={{ marginBottom: 12 }}
          />

          {/* Action buttons */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8, marginBottom: 16 }}>
            <button className="st-btn st-btn-primary" onClick={runAnalysis} disabled={loading}>
              {loading && loadingMsg.includes('Coordinating') ? '⏳ Analyzing…' : 'Analyze Situation'}
            </button>
            <button className="st-btn" onClick={runDaily} disabled={loading}>
              {loading && loadingMsg.includes('daily') ? '⏳ Running…' : 'Run Daily Auto Check'}
            </button>
            <button className="st-btn" onClick={runMCP} disabled={loading}>
              {loading && loadingMsg.includes('MCP') ? '⏳ Running…' : 'Run MCP Ops Check'}
            </button>
            <button className="st-btn" onClick={() => { clearChat(); setResult(null); setError('') }}>
              Clear
            </button>
          </div>

          {error && (
            <div style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.20)', borderRadius: 8, padding: '10px 14px', fontSize: 14, color: '#FCA5A5', marginBottom: 12 }}>
              {error}
            </div>
          )}

          {loading && (
            <div style={{ background: 'rgba(11,55,25,0.9)', border: '1px solid #1D4F2B', borderRadius: 8, padding: '10px 14px', fontSize: 14, color: '#E8FFF0', marginBottom: 12 }}>
              ⏳ {loadingMsg}
            </div>
          )}

          {/* Conversation */}
          <div className="glass" style={{ borderRadius: 12, padding: 24 }}>
            <div style={{ fontSize: 15, fontWeight: 700, color: '#FAFAFA', marginBottom: 12 }}>Conversation</div>
            {lastSix.length > 0 ? lastSix.map((msg, i) => (
              <div key={i} className="conv-item">
                <div className="conv-icon">{msg.role === 'user' ? '💬' : '✓'}</div>
                <div style={{ fontSize: 14 }}>{msg.content.slice(0, 300)}{msg.content.length > 300 ? '…' : ''}</div>
              </div>
            )) : (
              <div style={{ color: '#71717A', fontSize: 15, padding: '12px 0' }}>
                No conversation yet. Type your own project situation and click Analyze Situation.
              </div>
            )}
          </div>

          {result && (
            <StructuredResult summary={result.summary} modeLabel={result.mode} />
          )}

          {result?.status === 'fallback' && (
            <div style={{ background: 'rgba(234,179,8,0.05)', border: '1px solid rgba(234,179,8,0.20)', borderRadius: 8, padding: '10px 14px', fontSize: 14, color: '#FDE68A', marginTop: 10 }}>
              Live model execution is unavailable, so a local fallback response was returned.
            </div>
          )}
        </div>

        {/* RIGHT SIDEBAR */}
        <div>
          <div style={{ paddingBottom: 18, borderBottom: '1px solid rgba(255,255,255,0.10)' }}>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.07em', textTransform: 'uppercase', color: '#71717A', marginBottom: 8 }}>Prompt tips</div>
            <div style={{ fontSize: 15, color: '#A1A1AA', lineHeight: 1.75 }}>
              Mention the issue, who is affected, the deadline, and any blocking problem. Be specific — the agents use your live data.
            </div>
          </div>

          <div style={{ padding: '18px 0', borderBottom: '1px solid rgba(255,255,255,0.10)' }}>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.07em', textTransform: 'uppercase', color: '#71717A', marginBottom: 8 }}>Current snapshot</div>
            <div className="sidebar-stat">
              <span style={{ color: '#A1A1AA', fontSize: 13 }}>Critical open</span>
              <span style={{ fontWeight: 700, color: '#FAFAFA', fontSize: 13 }}>{criticalCount}</span>
            </div>
            <div className="sidebar-stat">
              <span style={{ color: '#A1A1AA', fontSize: 13 }}>Open tasks</span>
              <span style={{ fontWeight: 700, color: '#FAFAFA', fontSize: 13 }}>{openCount}</span>
            </div>
            <div className="sidebar-stat" style={{ borderBottom: 'none' }}>
              <span style={{ color: '#A1A1AA', fontSize: 13 }}>Available team</span>
              <span style={{ fontWeight: 700, color: '#FAFAFA', fontSize: 13 }}>{availableCount}</span>
            </div>
          </div>

          <div style={{ paddingTop: 18 }}>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.07em', textTransform: 'uppercase', color: '#71717A', marginBottom: 8 }}>Capabilities</div>
            <div style={{ fontSize: 15, color: '#A1A1AA', lineHeight: 1.75 }}>
              Live task context · Multi-agent orchestration · MCP operations · Action logging · Calendar coordination
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
