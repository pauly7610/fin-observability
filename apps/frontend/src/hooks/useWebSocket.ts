import { useEffect, useState, useCallback } from 'react'

interface WebSocketHook {
  data: any
  isConnected: boolean
  sendMessage: (message: any) => void
}

export function useWebSocket(path: string): WebSocketHook {
  const [data, setData] = useState<any>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [ws, setWs] = useState<WebSocket | null>(null)

  useEffect(() => {
    const socket = new WebSocket(`${process.env.NEXT_PUBLIC_WS_URL}${path}`)
    
    socket.onopen = () => {
      setIsConnected(true)
    }

    socket.onmessage = (event) => {
      try {
        const parsedData = JSON.parse(event.data)
        setData(parsedData)
      } catch (error) {
        console.error('Error parsing WebSocket message:', error)
      }
    }

    socket.onclose = () => {
      setIsConnected(false)
    }

    socket.onerror = (error) => {
      console.error('WebSocket error:', error)
      setIsConnected(false)
    }

    setWs(socket)

    return () => {
      socket.close()
    }
  }, [path])

  const sendMessage = useCallback((message: any) => {
    if (ws && isConnected) {
      ws.send(JSON.stringify(message))
    }
  }, [ws, isConnected])

  return { data, isConnected, sendMessage }
} 