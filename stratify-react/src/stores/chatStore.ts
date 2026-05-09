import { create } from 'zustand'

interface Message { role: 'user' | 'assistant'; content: string }

interface ChatState {
  history: Message[]
  sessionToken: string
  draftPrompt: string
  addMessage: (msg: Message) => void
  setDraftPrompt: (prompt: string) => void
  clearChat: () => void
  newSession: () => string
}

const makeToken = () => Math.random().toString(36).slice(2, 18)

export const useChatStore = create<ChatState>((set) => ({
  history: [],
  sessionToken: makeToken(),
  draftPrompt: '',
  addMessage: (msg) => set((s) => ({ history: [...s.history, msg] })),
  setDraftPrompt: (prompt) => set({ draftPrompt: prompt }),
  clearChat: () => set({ history: [], draftPrompt: '', sessionToken: makeToken() }),
  newSession: () => { const t = makeToken(); set({ sessionToken: t }); return t },
}))
