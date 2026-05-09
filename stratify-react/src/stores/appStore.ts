import { create } from 'zustand'
import type { NavPage } from '../types'

interface AppState {
  page: NavPage
  setPage: (page: NavPage) => void
}

export const useAppStore = create<AppState>((set) => ({
  page: 'Home',
  setPage: (page) => set({ page }),
}))
