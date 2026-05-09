import { icons } from '../../utils/icons'

interface Props { title: string; subtitle: string; icon: string }

export default function PageHeader({ title, subtitle, icon }: Props) {
  const Icon = icons[icon]
  return (
    <div style={{ padding: '2px 0 24px', borderBottom: '1px solid rgba(255,255,255,0.10)', marginBottom: 28 }}>
      <div className="flex items-start gap-3.5">
        <div
          style={{
            width: 44, height: 44, border: '1px solid rgba(255,255,255,0.10)',
            borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#A1A1AA', background: 'rgba(0,0,0,0.40)', flexShrink: 0,
          }}
        >
          {/* @ts-ignore */}
          <Icon size={20} />
        </div>
        <div>
          <div style={{ fontSize: 34, fontWeight: 800, color: '#FAFAFA', lineHeight: 1.08 }}>{title}</div>
          <div style={{ fontSize: 15, color: '#A1A1AA', marginTop: 6, lineHeight: 1.7, maxWidth: 820 }}>{subtitle}</div>
        </div>
      </div>
    </div>
  )
}
