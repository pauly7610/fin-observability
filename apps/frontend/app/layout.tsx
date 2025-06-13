import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Financial Observability Dashboard',
  description: 'An observability dashboard for financial transactions.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        {/* We can add a ThemeProvider here later if we want dark mode toggle */}
        {children}
      </body>
    </html>
  )
}