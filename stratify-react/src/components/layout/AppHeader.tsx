import { ShieldIcon } from '../../utils/icons'

export default function AppHeader() {
  return (
    <div className="flex items-start justify-between gap-4 mb-6">
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 rounded-lg border border-white/20 bg-white/10 backdrop-blur-sm flex items-center justify-center text-white flex-shrink-0">
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
