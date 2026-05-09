import { parseSummary } from '../../utils/formatting'

interface Props { summary: string; modeLabel: string }

const modeClass: Record<string, string> = {
  INTERACTIVE: 'mode-interactive',
  AUTONOMOUS: 'mode-auto',
  MCP: 'mode-mcp',
}

const statusColor: Record<string, string> = {
  RED: '#FF6A63', YELLOW: '#FFC72C', GREEN: '#47D46B',
}
const statusBg: Record<string, string> = {
  RED: 'rgba(255,106,99,0.10)', YELLOW: 'rgba(255,199,44,0.10)', GREEN: 'rgba(71,212,107,0.10)',
}
const statusBorder: Record<string, string> = {
  RED: 'rgba(255,106,99,0.28)', YELLOW: 'rgba(255,199,44,0.28)', GREEN: 'rgba(71,212,107,0.28)',
}

const cols = [
  { key: 'red_flags' as const,       title: 'Red Flags',      color: '#FF6A63' },
  { key: 'actions' as const,         title: 'Actions Taken',  color: '#47D46B' },
  { key: 'recommendations' as const, title: 'Recommendations',color: '#5A93FF' },
]

export default function StructuredResult({ summary, modeLabel }: Props) {
  const parsed = parseSummary(summary)
  const status = parsed.status.toUpperCase().trim()
  const sc  = statusColor[status]  ?? '#A1A1AA'
  const sb  = statusBg[status]     ?? 'rgba(161,161,170,0.08)'
  const sbd = statusBorder[status] ?? 'rgba(161,161,170,0.20)'

  const hasData = cols.some(c => parsed[c.key].length > 0)

  return (
    <div style={{
      marginTop: 20,
      borderRadius: 16,
      overflow: 'hidden',
      border: '1px solid rgba(255,255,255,0.10)',
      boxShadow: '0 24px 56px rgba(0,0,0,0.28)',
    }}>

      {/* ── Header ─────────────────────────────────── */}
      <div style={{
        background: 'rgba(255,255,255,0.03)',
        borderBottom: '1px solid rgba(255,255,255,0.08)',
        padding: '14px 22px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span className={`mode-pill ${modeClass[modeLabel] ?? 'mode-interactive'}`} style={{ margin: 0, fontSize: 10, letterSpacing: '0.08em' }}>
            {modeLabel} MODE
          </span>
          <span style={{ color: '#52525B', fontSize: 13, fontWeight: 400 }}>Executive Summary</span>
        </div>

        {status && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: 7,
            background: sb, border: `1px solid ${sbd}`,
            borderRadius: 8, padding: '5px 14px',
          }}>
            <div style={{ width: 7, height: 7, borderRadius: '50%', background: sc, boxShadow: `0 0 8px ${sc}` }} />
            <span style={{ fontWeight: 700, fontSize: 13, color: sc, letterSpacing: '0.04em' }}>{status}</span>
          </div>
        )}
      </div>

      {/* ── Body ───────────────────────────────────── */}
      <div style={{ background: 'rgba(0,0,0,0.25)', padding: '28px 24px' }}>
        {hasData ? (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 28 }}>
            {cols.map(({ key, title, color }) => {
              const items = parsed[key]
              return (
                <div key={key}>

                  {/* Column header */}
                  <div style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    marginBottom: 16, paddingBottom: 12,
                    borderBottom: '1px solid rgba(255,255,255,0.08)',
                  }}>
                    <span style={{
                      fontSize: 13, fontWeight: 800,
                      letterSpacing: '0.08em', textTransform: 'uppercase',
                      color,
                    }}>
                      {title}
                    </span>
                    {items.length > 0 && (
                      <span style={{
                        fontSize: 12, fontWeight: 700,
                        background: 'rgba(255,255,255,0.06)',
                        border: '1px solid rgba(255,255,255,0.10)',
                        color: '#A1A1AA',
                        borderRadius: 999, padding: '2px 9px',
                      }}>
                        {items.length}
                      </span>
                    )}
                  </div>

                  {/* Cards */}
                  {items.length > 0 ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                      {items.map((item, i) => (
                        <div key={i} style={{
                          background: 'rgba(255,255,255,0.04)',
                          border: '1px solid rgba(255,255,255,0.09)',
                          borderRadius: 10,
                          padding: '13px 15px',
                          fontSize: 14,
                          color: '#D4D4D8',
                          lineHeight: 1.65,
                        }}>
                          {item}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{ color: '#52525B', fontSize: 13, fontStyle: 'italic', paddingTop: 4 }}>
                      None reported.
                    </div>
                  )}

                </div>
              )
            })}
          </div>
        ) : (
          <pre style={{ whiteSpace: 'pre-wrap', fontSize: 13, color: '#A1A1AA', lineHeight: 1.75, margin: 0 }}>
            {summary}
          </pre>
        )}
      </div>
    </div>
  )
}
