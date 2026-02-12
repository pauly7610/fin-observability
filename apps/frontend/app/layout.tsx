import './globals.css'
import { ClerkProvider } from '@clerk/nextjs'
import { ReactQueryProvider } from './react-query-provider'
import { ThemeProvider } from '@/components/ThemeProvider'
import { AuthTokenProvider } from '@/components/AuthTokenProvider'
import type { ReactNode } from 'react'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'FinAI Observability',
  description: 'Financial AI Observability Platform',
}

const clerkPubKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
const hasClerk = clerkPubKey && !clerkPubKey.includes('placeholder')

export default function RootLayout({ children }: { children: ReactNode }) {
  const content = (
    <ThemeProvider
      attribute="class"
      defaultTheme="dark"
      enableSystem
      disableTransitionOnChange
    >
      <ReactQueryProvider>
        {hasClerk ? <AuthTokenProvider>{children}</AuthTokenProvider> : children}
      </ReactQueryProvider>
    </ThemeProvider>
  )

  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased">
        {hasClerk ? <ClerkProvider>{content}</ClerkProvider> : content}
      </body>
    </html>
  )
}
