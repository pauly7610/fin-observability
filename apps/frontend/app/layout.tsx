import './globals.css'
import { ReactQueryProvider } from './react-query-provider' // see step 10
import { Header } from '@/components/Header'
import type { ReactNode } from 'react'

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <ReactQueryProvider>
          <Header />
          <main className="container mx-auto py-6">{children}</main>
        </ReactQueryProvider>
      </body>
    </html>
  )
}
