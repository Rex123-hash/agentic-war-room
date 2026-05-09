import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getTasks, getTeam, addTask, updateTask, deleteTask, addTeamMember, updateMemberAvailability, deleteTeamMember } from '../../api/services'
import PageHeader from '../layout/PageHeader'

type AlertState = { type: 'success' | 'error' | 'warn'; msg: string } | null

function Alert({ state, onClose }: { state: AlertState; onClose: () => void }) {
  if (!state) return null
  const colors: Record<string, { bg: string; border: string; text: string }> = {
    success: { bg: 'rgba(16,185,129,0.05)', border: 'rgba(16,185,129,0.20)', text: '#6EE7B7' },
    error: { bg: 'rgba(239,68,68,0.08)', border: 'rgba(239,68,68,0.20)', text: '#FCA5A5' },
    warn: { bg: 'rgba(234,179,8,0.05)', border: 'rgba(234,179,8,0.20)', text: '#FDE68A' },
  }
  const c = colors[state.type]
  return (
    <div style={{ background: c.bg, border: `1px solid ${c.border}`, borderRadius: 8, padding: '10px 14px', fontSize: 14, color: c.text, marginBottom: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      {state.msg}
      <button onClick={onClose} style={{ background: 'none', border: 'none', color: c.text, cursor: 'pointer', fontSize: 16 }}>×</button>
    </div>
  )
}

const STATUSES = ['Open', 'In Progress', 'Blocked', 'Closed']
const PRIORITIES = ['Low', 'Medium', 'High', 'Critical']

export default function ManageData() {
  const qc = useQueryClient()
  const { data: tasks = [] } = useQuery({ queryKey: ['tasks'], queryFn: getTasks })
  const { data: members = [] } = useQuery({ queryKey: ['team'], queryFn: getTeam })

  const [taskAlert, setTaskAlert] = useState<AlertState>(null)
  const [teamAlert, setTeamAlert] = useState<AlertState>(null)

  // Add Task
  const [addT, setAddT] = useState({ title: '', assignee: '', status: 'Open', priority: 'Medium', deadline: '', description: '' })
  // Update Task
  const [updTaskId, setUpdTaskId] = useState<number | null>(tasks[0]?.id ?? null)
  const [updAssignee, setUpdAssignee] = useState('')
  const [updStatus, setUpdStatus] = useState('Open')
  // Delete Task
  const [delTaskId, setDelTaskId] = useState<number | null>(tasks[0]?.id ?? null)
  const [confirmDelTask, setConfirmDelTask] = useState(false)

  // Add Member
  const [addM, setAddM] = useState({ name: '', role: '', email: '', skills: '', available: true })
  // Update Member
  const [updMemberId, setUpdMemberId] = useState<number | null>(members[0]?.id ?? null)
  const [updAvail, setUpdAvail] = useState('Available')
  // Delete Member
  const [delMemberId, setDelMemberId] = useState<number | null>(members[0]?.id ?? null)
  const [confirmDelMember, setConfirmDelMember] = useState(false)

  const refresh = () => { qc.invalidateQueries({ queryKey: ['tasks'] }); qc.invalidateQueries({ queryKey: ['team'] }); qc.invalidateQueries({ queryKey: ['metrics'] }) }

  async function handleAddTask(e: React.FormEvent) {
    e.preventDefault()
    if (!addT.title.trim()) { setTaskAlert({ type: 'warn', msg: 'Task title is required.' }); return }
    try {
      await addTask(addT)
      refresh()
      setAddT({ title: '', assignee: '', status: 'Open', priority: 'Medium', deadline: '', description: '' })
      setTaskAlert({ type: 'success', msg: 'Task added successfully.' })
    } catch { setTaskAlert({ type: 'error', msg: 'Failed to add task.' }) }
  }

  async function handleUpdateTask(e: React.FormEvent) {
    e.preventDefault()
    if (!updTaskId) return
    if (!updAssignee.trim()) { setTaskAlert({ type: 'warn', msg: 'Assignee cannot be empty while updating a task.' }); return }
    try {
      await updateTask(updTaskId, { assignee: updAssignee, status: updStatus })
      refresh(); setTaskAlert({ type: 'success', msg: 'Task updated successfully.' })
    } catch { setTaskAlert({ type: 'error', msg: 'Failed to update task.' }) }
  }

  async function handleDeleteTask(e: React.FormEvent) {
    e.preventDefault()
    if (!delTaskId) return
    if (!confirmDelTask) { setTaskAlert({ type: 'warn', msg: 'Please confirm task deletion.' }); return }
    try {
      await deleteTask(delTaskId)
      refresh(); setConfirmDelTask(false); setTaskAlert({ type: 'success', msg: 'Task deleted successfully.' })
    } catch { setTaskAlert({ type: 'error', msg: 'Failed to delete task.' }) }
  }

  async function handleAddMember(e: React.FormEvent) {
    e.preventDefault()
    if (!addM.name.trim()) { setTeamAlert({ type: 'warn', msg: 'Team member name is required.' }); return }
    try {
      await addTeamMember(addM)
      refresh(); setAddM({ name: '', role: '', email: '', skills: '', available: true })
      setTeamAlert({ type: 'success', msg: 'Team member added successfully.' })
    } catch { setTeamAlert({ type: 'error', msg: 'Failed to add team member.' }) }
  }

  async function handleUpdateMember(e: React.FormEvent) {
    e.preventDefault()
    if (!updMemberId) return
    try {
      await updateMemberAvailability(updMemberId, updAvail === 'Available')
      refresh(); setTeamAlert({ type: 'success', msg: 'Team member availability updated successfully.' })
    } catch { setTeamAlert({ type: 'error', msg: 'Failed to update availability.' }) }
  }

  async function handleDeleteMember(e: React.FormEvent) {
    e.preventDefault()
    if (!delMemberId) return
    if (!confirmDelMember) { setTeamAlert({ type: 'warn', msg: 'Please confirm team member deletion.' }); return }
    try {
      await deleteTeamMember(delMemberId)
      refresh(); setConfirmDelMember(false); setTeamAlert({ type: 'success', msg: 'Team member deleted successfully.' })
    } catch { setTeamAlert({ type: 'error', msg: 'Failed to delete team member.' }) }
  }

  const formCard = (children: React.ReactNode) => (
    <div style={{ background: 'rgba(0,0,0,0.40)', border: '1px solid rgba(255,255,255,0.10)', borderRadius: 12, padding: 20, backdropFilter: 'blur(10px)', marginBottom: 16 }}>
      {children}
    </div>
  )

  const label = (text: string) => <label style={{ display: 'block', fontSize: 13, color: '#A1A1AA', marginBottom: 5, fontWeight: 500 }}>{text}</label>
  const field = (children: React.ReactNode) => <div style={{ marginBottom: 12 }}>{children}</div>

  return (
    <div className="page-fade">
      <PageHeader title="Manage Project Data" subtitle="Add, update, and remove tasks and team information carefully using the live project database." icon="list" />

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        {/* TASKS column */}
        <div>
          <Alert state={taskAlert} onClose={() => setTaskAlert(null)} />

          {formCard(<>
            <div style={{ fontSize: 15, fontWeight: 700, color: '#FAFAFA', marginBottom: 14 }}>Add Task</div>
            <form onSubmit={handleAddTask}>
              {field(<>{label('Task Title')}<input className="st-input" value={addT.title} onChange={e => setAddT(p => ({ ...p, title: e.target.value }))} placeholder="Task title" /></>)}
              {field(<>{label('Assignee')}<input className="st-input" value={addT.assignee} onChange={e => setAddT(p => ({ ...p, assignee: e.target.value }))} placeholder="Assignee name" /></>)}
              {field(<>{label('Status')}<select className="st-select" value={addT.status} onChange={e => setAddT(p => ({ ...p, status: e.target.value }))}>{STATUSES.map(s => <option key={s}>{s}</option>)}</select></>)}
              {field(<>{label('Priority')}<select className="st-select" value={addT.priority} onChange={e => setAddT(p => ({ ...p, priority: e.target.value }))}>{PRIORITIES.map(p => <option key={p}>{p}</option>)}</select></>)}
              {field(<>{label('Deadline')}<input className="st-input" value={addT.deadline} onChange={e => setAddT(p => ({ ...p, deadline: e.target.value }))} placeholder="2026-04-10" /></>)}
              {field(<>{label('Description')}<textarea className="st-textarea" value={addT.description} onChange={e => setAddT(p => ({ ...p, description: e.target.value }))} rows={3} placeholder="Optional" /></>)}
              <button type="submit" className="st-btn st-btn-primary" style={{ width: '100%' }}>Add Task</button>
            </form>
          </>)}

          {formCard(<>
            <div style={{ fontSize: 15, fontWeight: 700, color: '#FAFAFA', marginBottom: 14 }}>Update Task</div>
            {tasks.length === 0 ? <div style={{ color: '#71717A', fontSize: 14 }}>No tasks available.</div> : (
              <form onSubmit={handleUpdateTask}>
                {field(<>{label('Select Task')}<select className="st-select" value={updTaskId ?? ''} onChange={e => { const t = tasks.find(t => t.id === Number(e.target.value)); setUpdTaskId(Number(e.target.value)); setUpdAssignee(t?.assignee ?? ''); setUpdStatus(t?.status ?? 'Open') }}>{tasks.map(t => <option key={t.id} value={t.id}>{t.id} - {t.title} ({t.status})</option>)}</select></>)}
                {field(<>{label('New Assignee')}<input className="st-input" value={updAssignee} onChange={e => setUpdAssignee(e.target.value)} placeholder="Assignee" /></>)}
                {field(<>{label('New Status')}<select className="st-select" value={updStatus} onChange={e => setUpdStatus(e.target.value)}>{STATUSES.map(s => <option key={s}>{s}</option>)}</select></>)}
                <button type="submit" className="st-btn st-btn-primary" style={{ width: '100%' }}>Update Task</button>
              </form>
            )}
          </>)}

          {formCard(<>
            <div style={{ fontSize: 15, fontWeight: 700, color: '#FAFAFA', marginBottom: 14 }}>Delete Task</div>
            {tasks.length === 0 ? <div style={{ color: '#71717A', fontSize: 14 }}>No tasks available.</div> : (
              <form onSubmit={handleDeleteTask}>
                {field(<>{label('Select Task To Delete')}<select className="st-select" value={delTaskId ?? ''} onChange={e => setDelTaskId(Number(e.target.value))}>{tasks.map(t => <option key={t.id} value={t.id}>{t.id} - {t.title}</option>)}</select></>)}
                {field(<>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 14, color: '#A1A1AA' }}>
                    <input type="checkbox" className="st-checkbox" checked={confirmDelTask} onChange={e => setConfirmDelTask(e.target.checked)} />
                    ⚠️ I understand this will be permanently deleted
                  </label>
                </>)}
                <button type="submit" className="st-btn" style={{ width: '100%', color: '#FF6A63', borderColor: 'rgba(255,106,99,0.25)' }}>Delete Task</button>
              </form>
            )}
          </>)}
        </div>

        {/* TEAM column */}
        <div>
          <Alert state={teamAlert} onClose={() => setTeamAlert(null)} />

          {formCard(<>
            <div style={{ fontSize: 15, fontWeight: 700, color: '#FAFAFA', marginBottom: 14 }}>Add Team Member</div>
            <form onSubmit={handleAddMember}>
              {field(<>{label('Name')}<input className="st-input" value={addM.name} onChange={e => setAddM(p => ({ ...p, name: e.target.value }))} placeholder="Full name" /></>)}
              {field(<>{label('Role')}<input className="st-input" value={addM.role} onChange={e => setAddM(p => ({ ...p, role: e.target.value }))} placeholder="e.g. Engineer" /></>)}
              {field(<>{label('Email')}<input className="st-input" value={addM.email} onChange={e => setAddM(p => ({ ...p, email: e.target.value }))} placeholder="email@example.com" /></>)}
              {field(<>{label('Skills')}<input className="st-input" value={addM.skills} onChange={e => setAddM(p => ({ ...p, skills: e.target.value }))} placeholder="python,react,debugging" /></>)}
              {field(<>{label('Available')}<select className="st-select" value={addM.available ? 'Yes' : 'No'} onChange={e => setAddM(p => ({ ...p, available: e.target.value === 'Yes' }))}><option>Yes</option><option>No</option></select></>)}
              <button type="submit" className="st-btn st-btn-primary" style={{ width: '100%' }}>Add Team Member</button>
            </form>
          </>)}

          {formCard(<>
            <div style={{ fontSize: 15, fontWeight: 700, color: '#FAFAFA', marginBottom: 14 }}>Update Team Availability</div>
            {members.length === 0 ? <div style={{ color: '#71717A', fontSize: 14 }}>No team members available.</div> : (
              <form onSubmit={handleUpdateMember}>
                {field(<>{label('Select Team Member')}<select className="st-select" value={updMemberId ?? ''} onChange={e => { const m = members.find(m => m.id === Number(e.target.value)); setUpdMemberId(Number(e.target.value)); setUpdAvail(m?.available === true || m?.available === 1 ? 'Available' : 'Unavailable') }}>{members.map(m => <option key={m.id} value={m.id}>{m.id} - {m.name}</option>)}</select></>)}
                {field(<>{label('Availability')}<select className="st-select" value={updAvail} onChange={e => setUpdAvail(e.target.value)}><option>Available</option><option>Unavailable</option></select></>)}
                <button type="submit" className="st-btn st-btn-primary" style={{ width: '100%' }}>Update Availability</button>
              </form>
            )}
          </>)}

          {formCard(<>
            <div style={{ fontSize: 15, fontWeight: 700, color: '#FAFAFA', marginBottom: 14 }}>Delete Team Member</div>
            {members.length === 0 ? <div style={{ color: '#71717A', fontSize: 14 }}>No team members available.</div> : (
              <form onSubmit={handleDeleteMember}>
                {field(<>{label('Select Team Member To Delete')}<select className="st-select" value={delMemberId ?? ''} onChange={e => setDelMemberId(Number(e.target.value))}>{members.map(m => <option key={m.id} value={m.id}>{m.id} - {m.name}</option>)}</select></>)}
                {field(<>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 14, color: '#A1A1AA' }}>
                    <input type="checkbox" className="st-checkbox" checked={confirmDelMember} onChange={e => setConfirmDelMember(e.target.checked)} />
                    ⚠️ I understand this will be permanently deleted
                  </label>
                </>)}
                <button type="submit" className="st-btn" style={{ width: '100%', color: '#FF6A63', borderColor: 'rgba(255,106,99,0.25)' }}>Delete Team Member</button>
              </form>
            )}
          </>)}
        </div>
      </div>

      <div style={{ background: 'rgba(0,0,0,0.40)', border: '1px solid rgba(255,255,255,0.10)', borderRadius: 12, padding: '14px 18px', backdropFilter: 'blur(10px)', marginTop: 4 }}>
        <div style={{ fontSize: 15, color: '#A1A1AA', lineHeight: 1.75 }}>
          All changes are applied immediately. Deleted items cannot be recovered, so please review carefully before confirming.
        </div>
      </div>
    </div>
  )
}
