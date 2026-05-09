import { useAppStore } from '../../stores/appStore'
import { TasksIcon, TeamIcon, LogIcon } from '../../utils/icons'
import type { NavPage } from '../../types'

const shortcuts = [
  {
    page: 'Tasks' as NavPage,
    icon: TasksIcon,
    color: '#5A93FF',
    title: 'Tasks',
    copy: 'Review active work, priorities, owners, and deadlines.',
    btn: 'Open Tasks',
  },
  {
    page: 'Team' as NavPage,
    icon: TeamIcon,
    color: '#47D46B',
    title: 'Team',
    copy: 'Check roles, skills, and who is currently available.',
    btn: 'Open Team',
  },
  {
    page: 'Action Log' as NavPage,
    icon: LogIcon,
    color: '#FF6A63',
    title: 'Action Log',
    copy: 'Audit recent operations and recorded system actions.',
    btn: 'Open Action Log',
  },
]

export default function Home() {
  const setPage = useAppStore(s => s.setPage)

  return (
    <div className="page-fade">
      {/* Hero */}
      <div
        style={{
          background: 'rgba(0,0,0,0.40)', border: '1px solid rgba(255,255,255,0.10)',
          borderRadius: 12, padding: '34px 32px', backdropFilter: 'blur(10px)',
          boxShadow: '0 18px 40px rgba(0,0,0,0.18)', marginBottom: 26,
        }}
      >
        <div style={{ fontSize: 28, fontWeight: 700, color: '#FAFAFA', marginBottom: 10, lineHeight: 1.25 }}>
          Welcome to Stratify
        </div>
        <div style={{ fontSize: 16, color: '#A1A1AA', lineHeight: 1.75, maxWidth: 900 }}>
          Built for project leads who need clarity without digging through scattered updates.
          Stratify brings tasks, team capacity, and recent actions into one focused workspace,
          so you can understand what is moving, what is blocked, and where your attention is needed next.
        </div>
      </div>

      {/* Shortcut cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 16 }}>
        {shortcuts.map(({ page, icon: Icon, color, title, copy, btn }) => (
          <div key={page}>
            <div
              style={{
                minHeight: 190, padding: 22, borderRadius: 14,
                background: 'linear-gradient(145deg, rgba(255,255,255,0.06), rgba(255,255,255,0.015)), rgba(0,0,0,0.40)',
                border: '1px solid rgba(255,255,255,0.10)',
                boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.06), 0 18px 40px rgba(0,0,0,0.18)',
                marginBottom: 10,
              }}
            >
              <div
                style={{
                  width: 56, height: 56, borderRadius: 16, display: 'flex',
                  alignItems: 'center', justifyContent: 'center', marginBottom: 18,
                  border: `1px solid ${color}`,
                  background: `color-mix(in srgb, ${color} 14%, transparent)`,
                  boxShadow: `0 12px 28px color-mix(in srgb, ${color} 15%, transparent)`,
                  color,
                }}
              >
                {/* @ts-ignore */}
                <Icon size={28} />
              </div>
              <div style={{ fontSize: 15, fontWeight: 700, color, marginBottom: 8 }}>{title}</div>
              <div style={{ fontSize: 15, color: '#A1A1AA', lineHeight: 1.75 }}>{copy}</div>
            </div>
            <button className="st-btn st-btn-primary" style={{ width: '100%' }} onClick={() => setPage(page)}>
              {btn}
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
