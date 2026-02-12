'use client'

import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { WifiOff, RefreshCw } from 'lucide-react'

interface ErrorStateProps {
  message?: string
  onRetry?: () => void
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  const isNetworkError =
    message?.toLowerCase().includes('network') ||
    message?.toLowerCase().includes('connection') ||
    message?.toLowerCase().includes('fetch')

  return (
    <Card>
      <CardContent className="py-12 text-center">
        <WifiOff className="h-10 w-10 text-muted-foreground/30 mx-auto mb-4" />
        <p className="text-sm font-medium text-foreground mb-1">
          {isNetworkError ? 'Backend Unavailable' : 'Something went wrong'}
        </p>
        <p className="text-xs text-muted-foreground mb-4 max-w-sm mx-auto">
          {isNetworkError
            ? 'The API server is not reachable. Make sure the backend is running or check your connection.'
            : message || 'An unexpected error occurred.'}
        </p>
        {onRetry && (
          <Button size="sm" variant="outline" onClick={onRetry}>
            <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
            Retry
          </Button>
        )}
      </CardContent>
    </Card>
  )
}
