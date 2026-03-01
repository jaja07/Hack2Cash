/**
 * App.jsx
 * Root component — renders LoginPage or Dashboard based on auth state.
 */
import { AuthProvider, useAuth } from './context/AuthContext'
import LoginPage from './components/LoginPage'
import Dashboard from './components/Dashboard'

function AppRouter() {
  const { user } = useAuth()
  return user ? <Dashboard /> : <LoginPage />
}

export default function App() {
  return (
    <AuthProvider>
      <AppRouter />
    </AuthProvider>
  )
}
