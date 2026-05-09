import PageHeader from '../layout/PageHeader'
import { TasksIcon, AgentIcon, TeamIcon, ShieldIcon, InfoIcon } from '../../utils/icons'

function FeatureCard({ icon: Icon, title, body }: { icon: React.FC; title: string; body: React.ReactNode }) {
  return (
    <div style={{ background: 'rgba(0,0,0,0.40)', border: '1px solid rgba(255,255,255,0.10)', borderRadius: 14, padding: 20, height: '100%', backdropFilter: 'blur(10px)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
        <div style={{ width: 40, height: 40, borderRadius: 12, border: '1px solid rgba(255,255,255,0.10)', background: 'rgba(0,0,0,0.40)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#FAFAFA' }}>
          <Icon />
        </div>
        <div style={{ fontSize: 16, fontWeight: 700, color: '#FAFAFA' }}>{title}</div>
      </div>
      <div style={{ fontSize: 14, color: '#A1A1AA', lineHeight: 1.8 }}>{body}</div>
    </div>
  )
}

export default function About() {
  return (
    <div className="page-fade">
      <PageHeader title="About" subtitle="Understand what the system does today, how it works, and where the product can grow next." icon="info" />

      {/* 3-col cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 16, marginBottom: 24 }}>
        <FeatureCard icon={TasksIcon} title="What You Can Do" body="Analyze delivery risks, review blocked work, monitor team availability, run operational checks, and coordinate urgent responses from a single dashboard." />
        <FeatureCard icon={AgentIcon} title="How It Works" body="The Commander Agent coordinates Data Miner, Context Agent, and Tool Operator to analyze project state and produce structured operational guidance." />
        <FeatureCard icon={TeamIcon} title="Best For" body="Project leads, engineering managers, startup teams, and operations teams that need an AI-powered project operations workflow." />
      </div>

      <hr style={{ borderColor: 'rgba(255,255,255,0.08)', margin: '0 0 20px' }} />

      {/* 2-col cards */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <FeatureCard icon={ShieldIcon} title="Current Implementation" body={
          <ul className="feature-list">
            {['SQLite-backed project data', 'FastAPI and React workflow', 'ADK-based multi-agent orchestration', 'Google Calendar coordination action', 'MCP-based operations mode', 'Action logging and agent activity tracking', 'Interactive and autonomous analysis modes'].map(item => <li key={item}>{item}</li>)}
          </ul>
        } />
        <FeatureCard icon={InfoIcon} title="Future Scope" body={
          <ul className="feature-list">
            {['Slack integration', 'Jira integration', 'Vector-based context retrieval', 'Multi-project workspaces', 'Authentication and access control', 'Cloud-native production hardening'].map(item => <li key={item}>{item}</li>)}
          </ul>
        } />
      </div>
    </div>
  )
}
