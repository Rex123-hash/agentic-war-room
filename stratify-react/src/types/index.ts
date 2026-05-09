export interface Task {
  id: number
  title: string
  assignee: string
  status: string
  priority: string
  deadline: string
  description?: string
  created_at?: string
}

export interface TeamMember {
  id: number
  name: string
  role: string
  email: string
  skills: string
  available: boolean | number | string
}

export interface ActionLog {
  id?: number
  tool: string
  action: string
  details: string
  timestamp: string
}

export interface Metrics {
  total_tasks: number
  open_tasks: number
  critical_open: number
  available_team: number
  logged_actions: number
}

export interface SummaryResponse {
  status: 'success' | 'fallback'
  summary: string
}

export interface ParsedSummary {
  status: string
  red_flags: string[]
  actions: string[]
  recommendations: string[]
}

export type NavPage = 'Home' | 'Agents' | 'Tasks' | 'Team' | 'Action Log' | 'Manage Data' | 'About'
