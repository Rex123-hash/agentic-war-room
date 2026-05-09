import { useAppStore } from '../../stores/appStore'
import type { NavPage } from '../../types'

const NAV_LABELS: NavPage[] = ['Home', 'Agents', 'Tasks', 'Team', 'Action Log', 'Manage Data', 'About']

export default function TopNav() {
  const { page, setPage } = useAppStore()

  return (
    <div style={{ background: 'rgba(0,0,0,0.20)', border: '1px solid rgba(255,255,255,0.10)', borderRadius: 12, padding: 8, backdropFilter: 'blur(10px)', margin: '8px 0 24px' }}>
      <div style={{ display: 'grid', gridTemplateColumns: `repeat(${NAV_LABELS.length}, 1fr)`, gap: 4 }}>
        {NAV_LABELS.map((label) => {
          const active = page === label
          return (
            <button
              key={label}
              onClick={() => setPage(label)}
              style={{
                width: '100%', height: 42, borderRadius: 8, fontFamily: 'inherit',
                border: active ? '1px solid rgba(255,255,255,0.22)' : '1px solid rgba(255,255,255,0.10)',
                background: active ? 'rgba(0,0,0,0.72)' : 'rgba(255,255,255,0.05)',
                color: active ? '#fff' : '#9CA3AF',
                fontSize: 14, fontWeight: 600, cursor: 'pointer', whiteSpace: 'nowrap',
                boxShadow: 'none', outline: 'none', padding: '0 16px',
                transition: 'background 0.15s ease, border-color 0.15s ease, color 0.15s ease',
              }}
              onMouseEnter={e => {
                if (!active) {
                  const btn = e.currentTarget as HTMLButtonElement
                  btn.style.background = 'rgba(255,255,255,0.10)'
                  btn.style.borderColor = 'rgba(255,255,255,0.16)'
                  btn.style.color = '#fff'
                }
              }}
              onMouseLeave={e => {
                if (!active) {
                  const btn = e.currentTarget as HTMLButtonElement
                  btn.style.background = 'rgba(255,255,255,0.05)'
                  btn.style.borderColor = 'rgba(255,255,255,0.10)'
                  btn.style.color = '#9CA3AF'
                }
              }}
            >
              {label}
            </button>
          )
        })}
      </div>
    </div>
  )
}
