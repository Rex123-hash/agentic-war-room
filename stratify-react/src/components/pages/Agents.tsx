import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useChatStore } from '../../stores/chatStore'
import { analyze, analyzeDaily, analyzeMCP, getMetrics } from '../../api/services'
import StructuredResult from '../shared/StructuredResult'
import PageHeader from '../layout/PageHeader'

type ModeResult = { summary: string; mode: string; status: string } | null

const QUICK_PROMPTS = [
  ['Critical Bug',        'A critical issue is open, delivery is at risk today, and we need an action plan. Create a Google Calendar emergency huddle for immediate coordination.'],
  ['Production Issue',    'Production is unstable, users are impacted, and immediate coordination is required.'],
  ['Sprint Delay',        'Sprint delivery is at risk because some tasks are blocked and deadlines are close.'],
  ['Team Unavailability', 'A key team member is unavailable and we have active blockers. What do we do?'],
  ['Missed Deadline',     'We missed a deadline on a critical deliverable. What are the next steps?'],
  ['Resource Conflict',   'Two high-priority tasks are competing for the same resource. Help us prioritise.'],
]

export default function Agents() {
  const { history, sessionToken, draftPrompt, addMessage, setDraftPrompt, clearChat } = useChatStore()
  const [loading, setLoading]       = useState(false)
  const [loadingMsg, setLoadingMsg] = useState('')
  const [result, setResult]         = useState<ModeResult>(null)
  const [error, setError]           = useState('')
  const [showAll, setShowAll]       = useState(false)

  useQuery({ queryKey: ['metrics'], queryFn: getMetrics, refetchInterval: 10000 })

  async function runAnalysis() {
    if (!draftPrompt.trim()) { setError('Please enter a project situation first.'); return }
    setError(''); setLoading(true); setLoadingMsg('Coordinating agents...')
    addMessage({ role: 'user', content: draftPrompt })
    try {
      const data = await analyze(draftPrompt, sessionToken)
      addMessage({ role: 'assistant', content: data.summary })
      setResult({ summary: data.summary, mode: 'INTERACTIVE', status: data.status })
    } catch { setError('Cannot connect to backend.') }
    finally { setLoading(false) }
  }

  async function runDaily() {
    setError(''); setLoading(true); setLoadingMsg('Running autonomous daily check...')
    try {
      const data = await analyzeDaily()
      setResult({ summary: data.summary, mode: 'AUTONOMOUS', status: data.status })
    } catch { setError('Daily check failed.') }
    finally { setLoading(false) }
  }

  async function runMCP() {
    const goal = draftPrompt.trim() || 'Check urgent open tasks and team availability. If delivery risk is present, create an emergency huddle.'
    setError(''); setLoading(true); setLoadingMsg('Running MCP operations...')
    try {
      const data = await analyzeMCP(goal, sessionToken)
      addMessage({ role: 'assistant', content: data.summary })
      setResult({ summary: data.summary, mode: 'MCP', status: data.status })
    } catch { setError('MCP check failed.') }
    finally { setLoading(false) }
  }

  function cleanPreview(content: string): string {
    return content
      .replace(/EXECUTIVE SUMMARY[\s=]*/gi, '')
      .replace(/={3,}/g, '')
      .replace(/\n{3,}/g, '\n\n')
      .trim()
      .slice(0, 220)
  }

  const visiblePrompts = showAll ? QUICK_PROMPTS : QUICK_PROMPTS.slice(0, 3)
  const lastFour = history.slice(-4)

  return (
    <div className="page-fade">
      <PageHeader
        title="Agents"
        subtitle="Describe a real project situation — the system analyses it using your live data and suggests next actions."
        icon="agent"
      />

      {/* ── Quick prompts ──────────────────────────── */}
      <div style={{ marginBottom: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
          <span style={{ fontSize: 14, fontWeight: 600, color: '#A1A1AA' }}>Quick prompts</span>
          <button
            onClick={() => setShowAll(p => !p)}
            style={{ background: 'none', border: 'none', color: '#6366F1', fontSize: 14, cursor: 'pointer', fontWeight: 600, padding: 0 }}
          >
            {showAll ? 'Show less' : 'Show all'}
          </button>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
          {visiblePrompts.map(([label, prompt]) => (
            <button
              key={label}
              className="st-btn"
              onClick={() => setDraftPrompt(prompt)}
              style={{ width: '100%', fontSize: 14, fontWeight: 500 }}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Input card ────────────────────────────── */}
      <div className="glass" style={{ borderRadius: 12, padding: 20, marginBottom: 14, boxShadow: '0 18px 40px rgba(0,0,0,0.18)' }}>
        <label style={{ display: 'block', fontSize: 14, color: '#A1A1AA', marginBottom: 8, fontWeight: 500 }}>
          Your Message
        </label>
        <textarea
          className="st-textarea"
          value={draftPrompt}
          onChange={e => setDraftPrompt(e.target.value)}
          rows={4}
          placeholder="e.g. We have 2 blocked tasks, one critical issue, and a team member unavailable. What should we prioritise today?"
          style={{ marginBottom: 8, fontSize: 14 }}
        />
        <div style={{ fontSize: 13, color: '#52525B', marginBottom: 14, lineHeight: 1.5 }}>
          Tip: mention the issue, who is affected, the deadline, and any blocking problem — the agents use your live project data.
        </div>

        {/* Equal 4-column action buttons */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
          <button className="st-btn st-btn-primary" onClick={runAnalysis} disabled={loading} style={{ fontSize: 14 }}>
            {loading && loadingMsg.includes('Coordinating') ? 'Analyzing…' : 'Analyze Situation'}
          </button>
          <button className="st-btn" onClick={runDaily} disabled={loading} style={{ fontSize: 14 }}>
            {loading && loadingMsg.includes('daily') ? 'Running…' : 'Daily Auto Check'}
          </button>
          <button className="st-btn" onClick={runMCP} disabled={loading} style={{ fontSize: 14 }}>
            {loading && loadingMsg.includes('MCP') ? 'Running…' : 'MCP Ops Check'}
          </button>
          <button className="st-btn" onClick={() => { clearChat(); setResult(null); setError('') }} style={{ fontSize: 14 }}>
            Clear
          </button>
        </div>
      </div>

      {/* ── Status bar ────────────────────────────── */}
      {error && (
        <div style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.20)', borderRadius: 8, padding: '11px 16px', fontSize: 14, color: '#FCA5A5', marginBottom: 12 }}>
          {error}
        </div>
      )}
      {loading && (
        <div style={{ background: 'rgba(11,55,25,0.9)', border: '1px solid #1D4F2B', borderRadius: 8, padding: '11px 16px', fontSize: 14, color: '#E8FFF0', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 10 }}>
          <span className="st-spinner" />
          {loadingMsg}
        </div>
      )}

      {/* ── Result + Conversation ─────────────────── */}
      {(result || lastFour.length > 0) && (
        <div style={{ display: 'grid', gridTemplateColumns: lastFour.length > 0 ? '1fr 2.4fr' : '1fr', gap: 20, alignItems: 'start', marginBottom: 20 }}>

          {lastFour.length > 0 && (
            <div className="glass" style={{ borderRadius: 12, padding: 20 }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#FAFAFA', marginBottom: 12 }}>Conversation</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {lastFour.map((msg, i) => (
                  <div key={i} className="conv-item">
                    <div className="conv-icon">{msg.role === 'user' ? '💬' : '✓'}</div>
                    <div style={{ fontSize: 14, lineHeight: 1.55 }}>
                      {cleanPreview(msg.content)}{msg.content.length > 220 ? '…' : ''}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {result && (
            <div>
              <StructuredResult summary={result.summary} modeLabel={result.mode} />
              {result.status === 'fallback' && (
                <div style={{ background: 'rgba(234,179,8,0.05)', border: '1px solid rgba(234,179,8,0.20)', borderRadius: 8, padding: '11px 16px', fontSize: 14, color: '#FDE68A', marginTop: 10 }}>
                  Live model execution is unavailable — local fallback response returned.
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ── Safety section ────────────────────────── */}
      {result && (
        <div style={{
          borderTop: '1px solid rgba(255,255,255,0.08)',
          paddingTop: 20,
          marginTop: 4,
        }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: '#A1A1AA', marginBottom: 16 }}>
            Safety & Context
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>

            <div className="glass" style={{ borderRadius: 10, padding: 16 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: '#6366F1', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 8 }}>AI Sources</div>
              <div style={{ fontSize: 14, color: '#A1A1AA', lineHeight: 1.6 }}>
                Powered by <strong style={{ color: '#FAFAFA' }}>Vertex AI</strong> · Gemini 2.5 Flash via Google ADK.
                Responses are AI-generated and grounded in your live project data.
              </div>
            </div>

            <div className="glass" style={{ borderRadius: 10, padding: 16 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: '#47D46B', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 8 }}>Data Used</div>
              <div style={{ fontSize: 14, color: '#A1A1AA', lineHeight: 1.6 }}>
                Live tasks, team availability, and action logs from <strong style={{ color: '#FAFAFA' }}>Firestore</strong>.
                No external data sources were accessed.
              </div>
            </div>

            <div className="glass" style={{ borderRadius: 10, padding: 16 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: '#FF6A63', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 8 }}>Disclaimer</div>
              <div style={{ fontSize: 14, color: '#A1A1AA', lineHeight: 1.6 }}>
                This output is advisory only. Always verify recommendations with your team before taking action on critical decisions.
              </div>
            </div>

          </div>
        </div>
      )}
    </div>
  )
}
