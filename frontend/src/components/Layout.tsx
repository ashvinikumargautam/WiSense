import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'

interface Props {
  onLogout: () => void
}

export default function Layout({ onLogout }: Props) {
  return (
    <div className="flex min-h-screen bg-gray-950">
      <Sidebar onLogout={onLogout} />
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-7xl mx-auto p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}