/**
 * components/Dashboard.jsx
 * Main layout after login: Sidebar + ChatArea.
 */
import { useState } from 'react'
import Sidebar from './Sidebar'
import ChatArea from './ChatArea'

export default function Dashboard() {
  const [section, setSection] = useState('Analyse CRA')
  const [chatKey, setChatKey] = useState(0) // reset chat on "new"

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        activeSection={section}
        onSection={setSection}
        onNewChat={() => { setSection('Analyse CRA'); setChatKey((k) => k + 1) }}
      />
      <main className="flex-1 overflow-hidden">
        <ChatArea key={chatKey} />
      </main>
    </div>
  )
}
