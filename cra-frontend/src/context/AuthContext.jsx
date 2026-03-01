/**
 * context/AuthContext.jsx
 * Global auth state — user object + login/logout helpers.
 */
import { createContext, useContext, useState } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = sessionStorage.getItem('cra_user')
    return saved ? JSON.parse(saved) : null
  })

  const login = (userData, token) => {
    sessionStorage.setItem('cra_user', JSON.stringify(userData))
    sessionStorage.setItem('cra_token', token)
    setUser(userData)
  }

  const logout = () => {
    sessionStorage.clear()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
