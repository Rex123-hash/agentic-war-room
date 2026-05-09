import { useAppStore } from './stores/appStore'
import AppHeader from './components/layout/AppHeader'
import TopNav from './components/layout/TopNav'
import MetricsRow from './components/shared/MetricsRow'
import Home from './components/pages/Home'
import Agents from './components/pages/Agents'
import Tasks from './components/pages/Tasks'
import Team from './components/pages/Team'
import ActionLog from './components/pages/ActionLog'
import ManageData from './components/pages/ManageData'
import About from './components/pages/About'

const pages: Record<string, React.FC> = {
  Home, Agents, Tasks, Team, 'Action Log': ActionLog, 'Manage Data': ManageData, About,
}

export default function App() {
  const page = useAppStore(s => s.page)
  const Page = pages[page] ?? Home

  return (
    <div style={{ maxWidth: 1600, margin: '0 auto', padding: '2rem 1.5rem', minHeight: '100vh' }}>
      <TopNav />
      <AppHeader />
      <MetricsRow />
      <main className="page-fade" key={page}>
        <Page />
      </main>
      <div style={{ textAlign: 'center', color: '#71717A', fontSize: 12, paddingTop: 32, paddingBottom: 16 }}>
        Built with ADK · FastAPI · React · SQLite · Google ADK · MCP
      </div>
    </div>
  )
}
