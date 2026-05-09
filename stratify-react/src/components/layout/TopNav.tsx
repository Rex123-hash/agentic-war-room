import { useAppStore } from '../../stores/appStore'
import type { NavPage } from '../../types'

const NAV_LABELS: NavPage[] = ['Home', 'Agents', 'Tasks', 'Team', 'Action Log', 'Manage Data', 'About']

export default function TopNav() {
  const { page, setPage } = useAppStore()

  return (
    <div>
      {/* nav shell — no visible spacers, just the pill container */}
      <div style={{ background: 'rgba(0,0,0,0.25)', border: '1px solid rgba(255,255,255,0.10)', borderRadius: 12, padding: 6, backdropFilter: 'blur(10px)', margin: '8px 0 24px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: `repeat(${NAV_LABELS.length}, 1fr)`, gap: 4 }}>
          {NAV_LABELS.map((label) => {
            const active = page === label
            return (
              <button
                key={label}
                onClick={() => setPage(label)}
                style={{
                  width: '100%', minHeight: 40, borderRadius: 8, fontFamily: 'inherit',
                  border: active ? '1px solid rgba(255,255,255,0.22)' : '1px solid transparent',
                  background: active ? 'rgba(0,0,0,0.72)' : 'transparent',
                  color: active ? '#fff' : '#9CA3AF',
                  fontSize: 14, fontWeight: 600, cursor: 'pointer', whiteSpace: 'nowrap',
                  boxShadow: 'none', outline: 'none',
                  transition: 'background 0.18s ease, color 0.18s ease, border-color 0.18s ease',
                }}
                onMouseEnter={e => {
                  if (!active) {
                    const btn = e.currentTarget as HTMLButtonElement
                    btn.style.background = 'rgba(255,255,255,0.05)'
                    btn.style.color = '#fff'
                  }
                }}
                onMouseLeave={e => {
                  if (!active) {
                    const btn = e.currentTarget as HTMLButtonElement
                    btn.style.background = 'transparent'
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
    </div>
  )
}
