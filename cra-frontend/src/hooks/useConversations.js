// hooks/useConversations.js
import { useState, useEffect, useCallback } from 'react'
import { fetchConversations, createConversation, deleteConversation, updateConversationTitle } from '../api/conversation'

export function useConversations() {   // ← plus de paramètre token
  const [conversations, setConversations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    try {
      setLoading(true)
      setConversations(await fetchConversations())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const create = useCallback(async (title) => {
    const conversation = await createConversation(title)
    setConversations((prev) => [conversation, ...prev])
    return conversation
  }, [])

  const remove = useCallback(async (conversationId) => {
    await deleteConversation(conversationId)
    setConversations((prev) => prev.filter((c) => c.id !== conversationId))
  }, [])

  const rename = useCallback(async (conversationId, title) => {
    const updated = await updateConversationTitle(conversationId, title)
    setConversations((prev) => prev.map((c) => (c.id === conversationId ? updated : c)))
  }, [])

  return { conversations, loading, error, create, remove, rename }
}