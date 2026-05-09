import React from 'react'

interface IconProps { size?: number }

const mkProps = (size = 18) => ({
  viewBox: '0 0 24 24', width: size, height: size,
  fill: 'none', stroke: 'currentColor', strokeWidth: 1.9,
  strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const,
})

export const ShieldIcon = ({ size }: IconProps = {}) => (
  <svg {...mkProps(size)}>
    <path d="M12 3l7 3v6c0 4.8-2.9 7.9-7 9-4.1-1.1-7-4.2-7-9V6l7-3z"/>
    <path d="M12 8v8"/><path d="M8.8 11.5H15.2"/>
  </svg>
)

export const TasksIcon = ({ size }: IconProps = {}) => (
  <svg {...mkProps(size)}>
    <rect x="5" y="4" width="14" height="16" rx="2"/>
    <path d="M9 2.8h6v3H9z"/>
    <path d="M8.5 10.5h7"/><path d="M8.5 14.5h7"/>
  </svg>
)

export const ListIcon = ({ size }: IconProps = {}) => (
  <svg {...mkProps(size)}>
    <path d="M9 6.5h10"/><path d="M9 12h10"/><path d="M9 17.5h10"/>
    <circle cx="5.5" cy="6.5" r="1"/><circle cx="5.5" cy="12" r="1"/><circle cx="5.5" cy="17.5" r="1"/>
  </svg>
)

export const AlertIcon = ({ size }: IconProps = {}) => (
  <svg {...mkProps(size)}>
    <path d="M12 4.5l8 14H4l8-14z"/>
    <path d="M12 9v4.8"/><path d="M12 17.2h.01"/>
  </svg>
)

export const TeamIcon = ({ size }: IconProps = {}) => (
  <svg {...mkProps(size)}>
    <circle cx="9" cy="9" r="3.2"/>
    <circle cx="17" cy="10.5" r="2.4"/>
    <path d="M4.5 18.5c.7-2.8 2.9-4.5 6-4.5s5.3 1.7 6 4.5"/>
    <path d="M15.2 18.2c.4-1.8 1.7-3.1 3.8-3.6"/>
  </svg>
)

export const LogIcon = ({ size }: IconProps = {}) => (
  <svg {...mkProps(size)}>
    <rect x="6" y="4" width="12" height="16" rx="2"/>
    <path d="M9 8.5h6"/><path d="M9 12h6"/><path d="M9 15.5h4.5"/>
  </svg>
)

export const AgentIcon = ({ size }: IconProps = {}) => (
  <svg {...mkProps(size)}>
    <rect x="7" y="8" width="10" height="9" rx="2"/>
    <path d="M12 4v4"/><path d="M9.5 17v2"/><path d="M14.5 17v2"/>
    <circle cx="10" cy="12.5" r=".7" fill="currentColor" stroke="none"/>
    <circle cx="14" cy="12.5" r=".7" fill="currentColor" stroke="none"/>
    <path d="M10 15h4"/>
  </svg>
)

export const InfoIcon = ({ size }: IconProps = {}) => (
  <svg {...mkProps(size)}>
    <circle cx="12" cy="12" r="9"/>
    <path d="M12 10.5v5"/>
    <circle cx="12" cy="7.5" r=".7" fill="currentColor" stroke="none"/>
  </svg>
)

export const icons: Record<string, React.FC> = {
  shield: ShieldIcon, tasks: TasksIcon, list: ListIcon, alert: AlertIcon,
  team: TeamIcon, log: LogIcon, agent: AgentIcon, info: InfoIcon,
}
