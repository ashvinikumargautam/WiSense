import { useEffect, useRef, useState, useCallback } from 'react'
import type { SensingMessage } from '../types'

declare global {
  interface ImportMetaEnv {
    readonly VITE_WS_URL?: string | undefined
  }
}

interface UseWebSocketOptions {
  onMessage?: (msg: SensingMessage) => void
  autoConnect?: boolean
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const { onMessage, autoConnect = false } = options
  const wsRef = useRef<WebSocket | null>(null)
  const [connected, setConnected] = useState(false)
  const [latestMessage, setLatestMessage] = useState<SensingMessage | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>()
  const onMessageRef = useRef(onMessage)
  onMessageRef.current = onMessage

  const connect = useCallback(() => {
    const token = localStorage.getItem('wisense_token')
    if (!token) return

    const env = import.meta.env as {
      readonly VITE_API_URL?: string | undefined
      readonly VITE_WS_URL?: string | undefined
    }
    const wsBase = env.VITE_WS_URL

    let url: string
    if (wsBase) {
      url = `${wsBase}/ws/sensing?token=${token}`
    } else {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = window.location.host
      url = `${protocol}//${host}/ws/sensing?token=${token}`
    }

    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
    }

    ws.onmessage = (event) => {
      try {
        const msg: SensingMessage = JSON.parse(event.data)
        setLatestMessage(msg)
        onMessageRef.current?.(msg)
      } catch {
        // ignore parse errors
      }
    }

    ws.onclose = () => {
      setConnected(false)
      wsRef.current = null
      // Reconnect after 3 seconds
      reconnectTimeoutRef.current = setTimeout(connect, 3000)
    }

    ws.onerror = () => {
      ws.close()
    }
  }, [])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    if (wsRef.current) {
      wsRef.current.onclose = null
      wsRef.current.close()
      wsRef.current = null
    }
    setConnected(false)
  }, [])

  useEffect(() => {
    if (autoConnect) connect()
    return () => disconnect()
  }, [autoConnect, connect, disconnect])

  return { connected, latestMessage, connect, disconnect }
}