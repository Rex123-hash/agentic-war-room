import type { FC } from 'react'

interface Props {
  Icon: FC
  label: string
  value: number | string
  sub: string
  color: string
}

export default function MetricCard({ Icon, label, value, sub, color }: Props) {
  return (
    <div
      style={{
        background: 'rgba(0,0,0,0.40)', border: '1px solid rgba(255,255,255,0.10)',
        borderRadius: 12, padding: 16, minHeight: 128, display: 'flex', flexDirection: 'column',
        justifyContent: 'space-between', backdropFilter: 'blur(10px)',
        boxShadow: '0 18px 40px rgba(0,0,0,0.18)',
        transition: 'box-shadow 0.2s ease, border-color 0.2s ease',
      }}
    >
      {/* Top row: glowing icon + label + value */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12, minHeight: 44 }}>
        <div
          style={{
            width: 40, height: 40, borderRadius: 999, display: 'flex',
            alignItems: 'center', justifyContent: 'center', color, flexShrink: 0,
            background: `color-mix(in srgb, ${color} 22%, transparent)`,
            border: `2px solid color-mix(in srgb, ${color} 58%, transparent)`,
            boxShadow: `0 0 0 1px color-mix(in srgb, ${color} 18%, transparent), 0 12px 26px color-mix(in srgb, ${color} 18%, transparent)`,
          }}
        >
          <Icon />
        </div>
        <div>
          <p style={{ margin: 0, fontSize: 11, letterSpacing: '0.06em', textTransform: 'uppercase', color: '#71717A', whiteSpace: 'nowrap' }}>
            {label}
          </p>
          <p style={{ margin: 0, fontSize: 30, fontWeight: 800, color: '#FAFAFA', lineHeight: 1.1 }}>
            {value}
          </p>
        </div>
      </div>
      {/* Subtitle */}
      <div style={{ color: '#A1A1AA', fontSize: 14, lineHeight: 1.5, minHeight: 34 }}>{sub}</div>
    </div>
  )
}
