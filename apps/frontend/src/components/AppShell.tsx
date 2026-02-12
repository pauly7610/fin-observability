'use client'

import { Sidebar } from '@/components/Sidebar'
import type { ReactNode } from 'react'

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <div className="container max-w-7xl mx-auto py-6 px-6">
          {children}
        </div>
      </main>
    </div>
  )
}
