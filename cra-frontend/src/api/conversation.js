// api/conversations.js
import api from './client'

export const fetchConversations = () =>
  api.get('conversations/').then((r) => r.data)

export const createConversation = (title = 'Nouvelle conversation') =>
  api.post(`conversations/?title=${encodeURIComponent(title)}`).then((r) => r.data)

export const deleteConversation = (conversationId) =>
  api.delete(`conversations/${conversationId}`).then((r) => r.data)

export const updateConversationTitle = (conversationId, title) =>
  api.patch(`conversations/${conversationId}/title?new_title=${encodeURIComponent(title)}`).then((r) => r.data)