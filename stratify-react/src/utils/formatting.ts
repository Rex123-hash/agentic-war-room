import type { ParsedSummary } from '../types'

export function maskEmail(value: string): string {
  if (!value || !value.includes('@')) return ''
  const [local, domain] = value.split('@', 2)
  if (!local) return `***@${domain}`
  if (local.length === 1) return `*@${domain}`
  if (local.length === 2) return `${local[0]}*@${domain}`
  return `${local[0]}${'*'.repeat(local.length - 2)}${local[local.length - 1]}@${domain}`
}

export function parseSummary(summary: string): ParsedSummary {
  const sections: ParsedSummary = { status: '', red_flags: [], actions: [], recommendations: [] }
  const lines = summary.split('\n').map(l => l.trim()).filter(Boolean)
  let current: keyof Pick<ParsedSummary, 'red_flags' | 'actions' | 'recommendations'> | null = null

  for (const line of lines) {
    const stripped = line.replace(/[*#]/g, '').trim()
    if (stripped.includes('Status:')) {
      sections.status = stripped.split('Status:')[1]?.trim() ?? ''
    } else if (/^Red Flags?/i.test(stripped)) {
      current = 'red_flags'
    } else if (/^Actions? Taken/i.test(stripped)) {
      current = 'actions'
    } else if (/^Recommendations?/i.test(stripped)) {
      current = 'recommendations'
    } else if (/^[-*•]/.test(line) || /^\d[.):)]/.test(line)) {
      const value = line.replace(/^[-*•\d.):)\s]+/, '').replace(/[*]/g, '').trim()
      if (current && value && !value.endsWith(':')) {
        sections[current].push(value)
      }
    }
  }
  return sections
}

export function recordsToCsv(rows: Record<string, unknown>[]): string {
  if (!rows.length) return ''
  const headers = Object.keys(rows[0])
  const escape = (v: unknown) => `"${String(v ?? '').replace(/"/g, '""')}"`
  return [headers.join(','), ...rows.map(r => headers.map(h => escape(r[h])).join(','))].join('\n')
}

export function downloadCsv(rows: Record<string, unknown>[], filename: string) {
  const csv = recordsToCsv(rows)
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = filename; a.click()
  URL.revokeObjectURL(url)
}
