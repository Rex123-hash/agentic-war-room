import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getTeam } from '../../api/services'
import { maskEmail } from '../../utils/formatting'
import PageHeader from '../layout/PageHeader'

export default function Team() {
  const { data: raw = [], isLoading } = useQuery({ queryKey: ['team'], queryFn: getTeam, refetchInterval: 8000 })
  const [search, setSearch] = useState('')
  const [avail, setAvail] = useState('All')

  const members = useMemo(() => raw.map(m => ({
    ...m,
    email: maskEmail(m.email),
    availability: m.available === true || m.available === 1 || m.available === 'Available' ? 'Available' : 'Unavailable',
  })), [raw])

  const filtered = useMemo(() => members.filter(m => {
    const haystack = `${m.name} ${m.role} ${m.email} ${m.skills}`.toLowerCase()
    return (
      (!search || haystack.includes(search.toLowerCase())) &&
      (avail === 'All' || m.availability === avail)
    )
  }), [members, search, avail])

  return (
    <div className="page-fade">
      <PageHeader title="Team Status" subtitle="Overview of team members, roles, skills, and current availability." icon="team" />

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 12, marginBottom: 16 }}>
        <input className="st-input" placeholder="Search by name, role, email, or skills" value={search} onChange={e => setSearch(e.target.value)} />
        <select className="st-select" value={avail} onChange={e => setAvail(e.target.value)}>
          {['All', 'Available', 'Unavailable'].map(a => <option key={a}>{a}</option>)}
        </select>
      </div>

      <div style={{ background: 'rgba(0,0,0,0.40)', border: '1px solid rgba(255,255,255,0.10)', borderRadius: 12, backdropFilter: 'blur(10px)', overflow: 'hidden' }}>
        <div style={{ padding: '12px 16px', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
          <span style={{ fontSize: 13, color: '#A1A1AA' }}>{filtered.length} member{filtered.length !== 1 ? 's' : ''}</span>
        </div>

        {isLoading ? (
          <div style={{ padding: 32, textAlign: 'center', color: '#71717A', fontSize: 14 }}>Loading team…</div>
        ) : filtered.length === 0 ? (
          <div style={{ padding: 32, textAlign: 'center', color: '#71717A', fontSize: 14 }}>No team members found.</div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="stratify-table">
              <thead>
                <tr>
                  {['ID', 'Name', 'Role', 'Email', 'Skills', 'Status'].map(h => <th key={h}>{h}</th>)}
                </tr>
              </thead>
              <tbody>
                {filtered.map(m => (
                  <tr key={m.id}>
                    <td style={{ color: '#71717A' }}>{m.id}</td>
                    <td style={{ fontWeight: 500 }}>{m.name}</td>
                    <td style={{ color: '#A1A1AA' }}>{m.role || '—'}</td>
                    <td style={{ color: '#A1A1AA', fontFamily: 'monospace', fontSize: 13 }}>{m.email || '—'}</td>
                    <td style={{ color: '#A1A1AA', fontSize: 13 }}>{m.skills || '—'}</td>
                    <td>
                      <span style={{
                        fontSize: 12, fontWeight: 600, padding: '3px 8px', borderRadius: 999,
                        background: m.availability === 'Available' ? 'rgba(71,212,107,0.12)' : 'rgba(255,106,99,0.12)',
                        color: m.availability === 'Available' ? '#47D46B' : '#FF6A63',
                        border: `1px solid ${m.availability === 'Available' ? 'rgba(71,212,107,0.25)' : 'rgba(255,106,99,0.25)'}`,
                      }}>
                        {m.availability}
                      </span>
                    </td>
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
