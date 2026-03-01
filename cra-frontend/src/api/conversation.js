// src/api/conversation.js
import api from './client'

// Remplace 'conversations/' par 'chats/' pour correspondre au backend
export const fetchConversations = () =>
  api.get('chats/').then((r) => r.data)

export const createConversation = (title = 'Nouvelle conversation') =>
  api.post(`chats/?title=${encodeURIComponent(title)}`).then((r) => r.data)

export const deleteConversation = (conversationId) =>
  api.delete(`chats/${conversationId}`).then((r) => r.data)

export const updateConversationTitle = (conversationId, title) =>
  api.patch(`chats/${conversationId}/title?title=${encodeURIComponent(title)}`).then((r) => r.data)