import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Wifi, GraduationCap, BarChart3, History,
  Settings, FileText, Shield, LogOut,
} from 'lucide-react'

const nav = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/devices', icon: Wifi, label: 'Devices' },
  { to: '/training', icon: GraduationCap, label: 'Training' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/history', icon: History, label: 'History' },
  { to: '/settings', icon: Settings, label: 'Settings' },
  { to: '/documentation', icon: FileText, label: 'Docs' },
  { to: '/privacy', icon: Shield, label: 'Privacy' },
]

export default function Sidebar({ onLogout }: { onLogout: () => void }) {
  return (
    <aside className="w-60 bg-gray-900 border-r border-gray-800 flex flex-col min-h-screen">
      <div className="p-4 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <Wifi className="w-7 h-7 text-brand-400" />
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight">WiSense</h1>
            <p className="text-[10px] text-gray-500 uppercase tracking-widest">Wi-Fi Sensing</p>
          </div>
        </div>
      </div>
      <nav className="flex-1 py-2 px-2 space-y-0.5">
        {nav.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                isActive
                  ? 'bg-brand-600/20 text-brand-400 font-medium'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
              }`
            }
          >
            <Icon className="w-4 h-4" />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="p-3 border-t border-gray-800">
        <button
          onClick={onLogout}
          className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm text-gray-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
        >
          <LogOut className="w-4 h-4" />
          Sign Out
        </button>
      </div>
    </aside>
  )
}