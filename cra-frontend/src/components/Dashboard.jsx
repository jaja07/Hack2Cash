// src/components/Dashboard.jsx
import React, { useState, useEffect } from 'react'
import Sidebar from './Sidebar'
import ChatArea from './ChatArea'
import { useConversations } from '../hooks/useConversations'

export default function Dashboard() {
  const [section, setSection] = useState('Analyse CRA') 
  const { conversations, create, loading } = useConversations()
  const [activeConvId, setActiveConvId] = useState(null)

  // Gère la création d'une nouvelle analyse
  const handleNewChat = async () => {
    try {
      const newConv = await create("Nouvelle Analyse")
      setActiveConvId(newConv.id)
      setSection('Analyse CRA') // Bascule sur le chat après création
    } catch (err) {
      console.error("Erreur création :", err)
    }
  }

  return (
    <div className="flex h-screen overflow-hidden bg-gray-950">
      <Sidebar
        activeSection={section}
        onSection={setSection}
        onNewChat={handleNewChat}
        conversations={conversations}
        onSelectConv={(id) => {
          setActiveConvId(id)
          setSection('Analyse CRA') // Force l'affichage du chat lors d'une sélection
        }}
        activeConvId={activeConvId}
      />
      
      <main className="flex-1 overflow-hidden">
        {/* Vérifiez bien que 'Analyse CRA' correspond au texte envoyé par la Sidebar */}
        {activeConvId && section === 'Analyse CRA' ? (
          <ChatArea conversationId={activeConvId} key={activeConvId} />
        ) : (
          <div className="flex-1 h-full flex items-center justify-center text-gray-500">
            <div className="text-center">
              <p className="text-lg">Select a conversation or create a new one</p>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}