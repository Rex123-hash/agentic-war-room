import { useQuery } from '@tanstack/react-query'
import { getMetrics } from '../../api/services'
import MetricCard from './MetricCard'
import { TasksIcon, ListIcon, AlertIcon, TeamIcon, LogIcon } from '../../utils/icons'

export default function MetricsRow() {
  const { data } = useQuery({ queryKey: ['metrics'], queryFn: getMetrics, refetchInterval: 10000 })

  const metrics = [
    { Icon: TasksIcon, label: 'Total Tasks',    value: data?.total_tasks    ?? '—', sub: 'All tasks in system',          color: '#7DD3FC' },
    { Icon: ListIcon,  label: 'Open Tasks',     value: data?.open_tasks     ?? '—', sub: 'Awaiting action',              color: '#F97316' },
    { Icon: AlertIcon, label: 'Critical Open',  value: data?.critical_open  ?? '—', sub: 'Requires immediate attention', color: '#FF4D4D' },
    { Icon: TeamIcon,  label: 'Available Team', value: data?.available_team ?? '—', sub: 'Ready to contribute',          color: '#10B981' },
    { Icon: LogIcon,   label: 'Logged Actions', value: data?.logged_actions ?? '—', sub: 'Total actions recorded',       color: '#A855F7' },
  ]

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, minmax(0, 1fr))', gap: 12, marginBottom: 28 }}>
      {metrics.map(m => <MetricCard key={m.label} {...m} />)}
    </div>
  )
}
