import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Devices from './pages/Devices'
import Training from './pages/Training'
import Analytics from './pages/Analytics'
import History from './pages/History'
import Settings from './pages/Settings'
import Privacy from './pages/Privacy'
import Documentation from './pages/Documentation'

export default function App() {
  // ✅ FIX: Destructure login and register HERE
  const { user, loading, logout, login, register } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-gray-500 text-sm">Loading...</div>
      </div>
    )
  }

  return (
    <Routes>
      {/* ✅ FIX: Use the variables instead of calling the hook again */}
      <Route path="/login" element={user ? <Navigate to="/dashboard" replace /> : <Login onLogin={login} />} />
      <Route path="/register" element={user ? <Navigate to="/dashboard" replace /> : <Register onRegister={register} />} />
      <Route
        element={
          <ProtectedRoute isAuthenticated={!!user}>
            <Layout onLogout={logout} />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/devices" element={<Devices />} />
        <Route path="/training" element={<Training />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/history" element={<History />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/documentation" element={<Documentation />} />
        <Route path="/privacy" element={<Privacy />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}