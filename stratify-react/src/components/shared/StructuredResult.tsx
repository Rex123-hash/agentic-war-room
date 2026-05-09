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

export default function StructuredResult({ summary, modeLabel }: Props) {
  const parsed = parseSummary(summary)
  const color = statusColor[parsed.status.toUpperCase().trim()] ?? '#A1A1AA'

  return (
    <div
      style={{
        background: 'rgba(0,0,0,0.40)', border: '1px solid rgba(255,255,255,0.10)',
        borderRadius: 12, padding: 24, backdropFilter: 'blur(10px)', marginTop: 16,
      }}
    >
      <span className={`mode-pill ${modeClass[modeLabel] ?? 'mode-interactive'}`}>
        {modeLabel} MODE
      </span>

      {parsed.status && (
        <div style={{ fontSize: 14, marginBottom: 12 }}>
          Status: <strong style={{ color }}>{parsed.status}</strong>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 1fr 1fr', gap: 24 }}>
        {[
          { title: 'Red Flags', items: parsed.red_flags, color: '#FF6A63' },
          { title: 'Actions Taken', items: parsed.actions, color: '#47D46B' },
          { title: 'Recommendations', items: parsed.recommendations, color: '#5A93FF' },
        ].map(({ title, items, color: c }) => (
          <div key={title}>
            <div style={{ fontWeight: 700, marginBottom: 8, fontSize: 14, color: c }}>{title}</div>
            {items.length > 0 ? (
              <div className="flex flex-col gap-1.5">
                {items.map((item, i) => (
                  <div key={i} className="signal-item" style={{ fontSize: 13 }}>{item}</div>
                ))}
              </div>
            ) : (
              <div style={{ color: '#71717A', fontSize: 13 }}>None reported.</div>
            )}
          </div>
        ))}
      </div>

      {(parsed.red_flags.length === 0 && parsed.actions.length === 0 && parsed.recommendations.length === 0) && (
        <pre style={{ whiteSpace: 'pre-wrap', fontSize: 13, color: '#A1A1AA', lineHeight: 1.7 }}>{summary}</pre>
      )}
    </div>
  )
}
