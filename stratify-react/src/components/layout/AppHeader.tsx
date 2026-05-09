import { ShieldIcon } from '../../utils/icons'

export default function AppHeader() {
  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16, marginBottom: 24 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <div style={{
          width: 48, height: 48, borderRadius: 8,
          border: '1px solid rgba(255,255,255,0.20)',
          background: 'rgba(255,255,255,0.10)',
          backdropFilter: 'blur(10px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: '#fff', flexShrink: 0,
        }}>
          {/* @ts-ignore */}
          <ShieldIcon size={28} />
        </div>
        <div>
          <div style={{ fontSize: 40, fontWeight: 800, lineHeight: 1.1, color: '#fff', letterSpacing: 0 }}>
            Stratify
          </div>
          <div style={{ marginTop: 5, fontSize: 16, color: '#9CA3AF', lineHeight: 1.6 }}>
            Multi-agent workspace for project monitoring, risk analysis, and operational response.
          </div>
        </div>
      </div>
    </div>
  )
}
