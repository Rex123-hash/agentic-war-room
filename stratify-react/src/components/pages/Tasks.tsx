import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getTasks } from '../../api/services'
import { downloadCsv } from '../../utils/formatting'
import PageHeader from '../layout/PageHeader'

export default function Tasks() {
  const { data: tasks = [], isLoading } = useQuery({ queryKey: ['tasks'], queryFn: getTasks, refetchInterval: 8000 })
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('All')
  const [priority, setPriority] = useState('All')

  const statuses = useMemo(() => ['All', ...Array.from(new Set(tasks.map(t => t.status).filter(Boolean))).sort()], [tasks])
  const priorities = useMemo(() => ['All', ...Array.from(new Set(tasks.map(t => t.priority).filter(Boolean))).sort()], [tasks])

  const filtered = useMemo(() => tasks.filter(t => {
    const haystack = `${t.title} ${t.assignee} ${t.status} ${t.priority} ${t.deadline}`.toLowerCase()
    return (
      (!search || haystack.includes(search.toLowerCase())) &&
      (status === 'All' || t.status === status) &&
      (priority === 'All' || t.priority === priority)
    )
  }), [tasks, search, status, priority])

  const priorityColor: Record<string, string> = { Critical: '#FF6A63', High: '#F97316', Medium: '#FFC72C', Low: '#47D46B' }
  const statusColor: Record<string, string> = { Open: '#5A93FF', 'In Progress': '#A78BFA', Blocked: '#FF6A63', Closed: '#47D46B' }

  return (
    <div className="page-fade">
      <PageHeader title="Current Tasks" subtitle="Track and review active work across the project using your live task data." icon="tasks" />

      {/* Filters */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', gap: 12, marginBottom: 16 }}>
        <input className="st-input" placeholder="Search by title, assignee, or status" value={search} onChange={e => setSearch(e.target.value)} />
        <select className="st-select" value={status} onChange={e => setStatus(e.target.value)}>
          {statuses.map(s => <option key={s}>{s}</option>)}
        </select>
        <select className="st-select" value={priority} onChange={e => setPriority(e.target.value)}>
          {priorities.map(p => <option key={p}>{p}</option>)}
        </select>
      </div>

      {/* Table container */}
      <div style={{ background: 'rgba(0,0,0,0.40)', border: '1px solid rgba(255,255,255,0.10)', borderRadius: 12, backdropFilter: 'blur(10px)', overflow: 'hidden' }}>
        <div style={{ padding: '12px 16px', borderBottom: '1px solid rgba(255,255,255,0.08)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: 13, color: '#A1A1AA' }}>{filtered.length} task{filtered.length !== 1 ? 's' : ''}</span>
          <button
            className="st-btn st-btn-sm"
            onClick={() => downloadCsv(filtered.map(t => ({ id: t.id, title: t.title, assignee: t.assignee, status: t.status, priority: t.priority, deadline: t.deadline })), 'project_tasks.csv')}
            disabled={filtered.length === 0}
          >
            Export CSV
          </button>
        </div>

        {isLoading ? (
          <div style={{ padding: 32, textAlign: 'center', color: '#71717A', fontSize: 14 }}>Loading tasks…</div>
        ) : filtered.length === 0 ? (
          <div style={{ padding: 32, textAlign: 'center', color: '#71717A', fontSize: 14 }}>No tasks found.</div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="stratify-table">
              <thead>
                <tr>
                  {['ID', 'Title', 'Assignee', 'Status', 'Priority', 'Deadline'].map(h => <th key={h}>{h}</th>)}
                </tr>
              </thead>
              <tbody>
                {filtered.map(t => (
                  <tr key={t.id}>
                    <td style={{ color: '#71717A' }}>{t.id}</td>
                    <td style={{ fontWeight: 500 }}>{t.title}</td>
                    <td style={{ color: '#A1A1AA' }}>{t.assignee || '—'}</td>
                    <td>
                      <span style={{ fontSize: 12, fontWeight: 600, padding: '3px 8px', borderRadius: 999, background: `${statusColor[t.status] ?? '#71717A'}18`, color: statusColor[t.status] ?? '#A1A1AA', border: `1px solid ${statusColor[t.status] ?? '#71717A'}30` }}>
                        {t.status}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontSize: 12, fontWeight: 600, padding: '3px 8px', borderRadius: 999, background: `${priorityColor[t.priority] ?? '#71717A'}18`, color: priorityColor[t.priority] ?? '#A1A1AA', border: `1px solid ${priorityColor[t.priority] ?? '#71717A'}30` }}>
                        {t.priority}
                      </span>
                    </td>
                    <td style={{ color: '#A1A1AA' }}>{t.deadline || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
