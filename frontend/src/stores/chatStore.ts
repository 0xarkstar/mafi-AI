import { create } from 'zustand'
import type { ChatMessage } from '../lib/types'

interface ChatStore {
  messages: ChatMessage[]
  addMessage: (msg: Omit<ChatMessage, 'id' | 'timestamp'>) => void
  addSystemMessage: (text: string, type?: ChatMessage['type']) => void
}

const MAX_MESSAGES = 200

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],

  addMessage: (msg) =>
    set((state) => {
      const newMessage: ChatMessage = {
        ...msg,
        id: `${Date.now()}-${Math.random()}`,
        timestamp: Date.now(),
      }
      const messages = [...state.messages, newMessage]
      return {
        messages: messages.length > MAX_MESSAGES ? messages.slice(-MAX_MESSAGES) : messages,
      }
    }),

  addSystemMessage: (text, type = 'system') =>
    set((state) => {
      const newMessage: ChatMessage = {
        id: `${Date.now()}-${Math.random()}`,
        agent: 'System',
        message: text,
        type,
        timestamp: Date.now(),
      }
      const messages = [...state.messages, newMessage]
      return {
        messages: messages.length > MAX_MESSAGES ? messages.slice(-MAX_MESSAGES) : messages,
      }
    }),
}))
