import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getActionLogs } from '../../api/services'
import PageHeader from '../layout/PageHeader'

export default function ActionLog() {
  const { data: actions = [], isLoading } = useQuery({ queryKey: ['action-logs'], queryFn: () => getActionLogs(20), refetchInterval: 8000 })
  const { data: allActions = [] } = useQuery({ queryKey: ['action-logs-50'], queryFn: () => getActionLogs(50), refetchInterval: 15000 })
  const [search, setSearch] = useState('')

  const filtered = useMemo(() => actions.filter(r => {
    if (!search) return true
    const haystack = `${r.tool} ${r.action} ${r.details} ${r.timestamp}`.toLowerCase()
    return haystack.includes(search.toLowerCase())
  }), [actions, search])

  const calendarRows = useMemo(() => allActions.filter(r => r.tool === 'GoogleCalendar').slice(0, 10), [allActions])

  return (
    <div className="page-fade">
      <PageHeader title="Recent Action Log" subtitle="Review logged operations, tool activity, and external actions captured by the system." icon="log" />

      <input className="st-input" placeholder="Search tool, action, details, or timestamp" value={search} onChange={e => setSearch(e.target.value)} style={{ marginBottom: 16 }} />

      <div style={{ background: 'rgba(0,0,0,0.40)', border: '1px solid rgba(255,255,255,0.10)', borderRadius: 12, backdropFilter: 'blur(10px)', overflow: 'hidden', marginBottom: 24 }}>
        <div style={{ padding: '12px 16px', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
          <span style={{ fontSize: 13, color: '#A1A1AA' }}>{filtered.length} record{filtered.length !== 1 ? 's' : ''}</span>
        </div>

        {isLoading ? (
          <div style={{ padding: 32, textAlign: 'center', color: '#71717A', fontSize: 14 }}>Loading logs…</div>
        ) : filtered.length === 0 ? (
          <div style={{ padding: 32, textAlign: 'center', color: '#71717A', fontSize: 14 }}>No actions logged yet.</div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="stratify-table">
              <thead>
                <tr>
                  {['Tool', 'Action', 'Details', 'Timestamp'].map(h => <th key={h}>{h}</th>)}
                </tr>
              </thead>
              <tbody>
                {filtered.map((r, i) => (
                  <tr key={i}>
                    <td>
                      <span style={{ fontSize: 12, fontWeight: 600, padding: '3px 8px', borderRadius: 999, background: 'rgba(99,102,241,0.12)', color: '#A78BFA', border: '1px solid rgba(99,102,241,0.25)' }}>
                        {r.tool}
                      </span>
                    </td>
                    <td style={{ fontWeight: 500 }}>{r.action}</td>
                    <td style={{ color: '#A1A1AA', fontSize: 13, maxWidth: 400 }}>{r.details?.split('| event_link=')[0]}</td>
                    <td style={{ color: '#71717A', fontSize: 12, whiteSpace: 'nowrap' }}>{r.timestamp}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Real External Actions */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 15, fontWeight: 700, color: '#FAFAFA', marginBottom: 12 }}>Real External Actions</div>
        {calendarRows.length > 0 ? calendarRows.map((r, i) => (
          <div key={i} style={{ background: 'rgba(16,185,129,0.05)', border: '1px solid rgba(16,185,129,0.15)', borderRadius: 8, padding: '10px 14px', fontSize: 14, color: '#A7F3D0', marginBottom: 8 }}>
            {r.details?.split('| event_link=')[0]}
          </div>
        )) : (
          <div style={{ background: 'rgba(37,99,235,0.05)', border: '1px solid rgba(37,99,235,0.15)', borderRadius: 8, padding: '10px 14px', fontSize: 14, color: '#93C5FD' }}>
            No real external action links found yet.
          </div>
        )}
      </div>
    </div>
  )
}
