import client from './client'
import type { Task, TeamMember, ActionLog, Metrics, SummaryResponse } from '../types'

// ── Analysis ─────────────────────────────────────────────────────────────────
export const analyze = (goal: string, sessionId: string) =>
  client.post<SummaryResponse>('/analyze', { goal, session_id: sessionId }).then(r => r.data)

export const analyzeDaily = () =>
  client.post<SummaryResponse>('/analyze-daily').then(r => r.data)

export const analyzeMCP = (goal: string, sessionId: string) =>
  client.post<SummaryResponse>('/analyze-mcp', { goal, session_id: sessionId }).then(r => r.data)

// ── Tasks ─────────────────────────────────────────────────────────────────────
export const getTasks = () => client.get<Task[]>('/tasks').then(r => r.data)

export const addTask = (body: {
  title: string; assignee: string; status: string
  priority: string; deadline: string; description: string
}) => client.post('/tasks', body).then(r => r.data)

export const updateTask = (id: number, body: { assignee: string; status: string }) =>
  client.put(`/tasks/${id}`, body).then(r => r.data)

export const deleteTask = (id: number) =>
  client.delete(`/tasks/${id}`).then(r => r.data)

// ── Team ──────────────────────────────────────────────────────────────────────
export const getTeam = () => client.get<TeamMember[]>('/team').then(r => r.data)

export const addTeamMember = (body: {
  name: string; role: string; email: string; skills: string; available: boolean
}) => client.post('/team', body).then(r => r.data)

export const updateMemberAvailability = (id: number, available: boolean) =>
  client.put(`/team/${id}`, { available }).then(r => r.data)

export const deleteTeamMember = (id: number) =>
  client.delete(`/team/${id}`).then(r => r.data)

// ── Logs & Metrics ────────────────────────────────────────────────────────────
export const getActionLogs = (limit = 20) =>
  client.get<ActionLog[]>('/action-logs', { params: { limit } }).then(r => r.data)

export const getMetrics = () => client.get<Metrics>('/metrics').then(r => r.data)
