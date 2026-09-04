import { useState, useEffect, useCallback } from 'react'
import { Play, Square, Activity } from 'lucide-react'
import { api } from '../api/client'
import { useWebSocket } from '../hooks/useWebSocket'
import type { SensingStatus, SensingMessage } from '../types'
import ConfidenceGauge from '../components/ConfidenceGauge'
import LiveSignalChart from '../components/LiveSignalChart'
import ActivityTimeline from '../components/ActivityTimeline'

export default function Dashboard() {
  const [status, setStatus] = useState<SensingStatus | null>(null)
  const [prediction, setPrediction] = useState('UNKNOWN')
  const [confidence, setConfidence] = useState(0)
  const [sigHist, setSigHist] = useState<{ time: number; values: number[] }[]>([])
  const [timeline, setTimeline] = useState<{ time: string; prediction: string; confidence: number }[]>([])
  const [sub, setSub] = useState(0)
  const [error, setError] = useState('')

  const handleMsg = useCallback((m: SensingMessage) => {
    if (m.type === 'sensing_update') {
      setPrediction(m.prediction)
      setConfidence(m.confidence)
      setSigHist(p => {
        const n = [...p, { time: m.timestamp, values: m.signal }]
        return n.length > 200 ? n.slice(-200) : n
      })
      setTimeline(p => {
        const t = new Date(m.timestamp * 1000).toLocaleTimeString()
        const n = [{ time: t, prediction: m.prediction, confidence: m.confidence }, ...p]
        return n.length > 50 ? n.slice(0, 50) : n
      })
    }
  }, [])

  const { connected } = useWebSocket({ onMessage: handleMsg, autoConnect: true })

  const fetchStatus = useCallback(async () => {
    try { setStatus(await api.get<SensingStatus>('/sensing/status')) } catch { /* */ }
  }, [])

  useEffect(() => { fetchStatus() }, [fetchStatus])
  useEffect(() => {
    const i = setInterval(fetchStatus, 2000)
    return () => clearInterval(i)
  }, [fetchStatus])

  const startSim = async () => {
    setError('')
    try { await api.post('/sensing/simulation/start', { activity: 'NO_MOVEMENT' }); await fetchStatus() } catch (e: any) { setError(e.message) }
  }

  const stopSim = async () => {
    try { await api.post('/sensing/simulation/stop'); await fetchStatus() } catch { /* */ }
  }

  const setActivity = async (a: string) => {
    try { await api.post('/sensing/simulation/activity', { activity: a }) } catch { /* */ }
  }

  const statCards = [
    { l: 'Data Source', v: status?.data_source?.toUpperCase() || 'NONE', c: status?.data_source === 'simulation' ? 'text-amber-400' : 'text-brand-400' },
    { l: 'Device', v: status?.device_id || '—', c: '' },
    { l: 'Samples', v: status?.stats?.total_samples?.toLocaleString() || '0', c: '' },
    { l: 'Packets/sec', v: String(status?.stats?.packets_per_second || '0'), c: '' },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-sm text-gray-500 mt-0.5">Real-time Wi-Fi movement sensing</p>
        </div>
        <div className="flex items-center gap-3">
          <span className={
            'flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border ' +
            (connected ? 'bg-green-500/20 text-green-400 border-green-500/30' : 'bg-gray-500/20 text-gray-400 border-gray-500/30')
          }>
            <span className={'w-2 h-2 rounded-full ' + (connected ? 'bg-green-400 animate-pulse' : 'bg-gray-400')} />
            {connected ? 'LIVE' : 'OFFLINE'}
          </span>
          {status?.is_running ? (
            <button onClick={stopSim} className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium">
              <Square className="w-4 h-4" /> Stop
            </button>
          ) : (
            <button onClick={startSim} className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-sm font-medium">
              <Play className="w-4 h-4" /> Start Simulator
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-sm rounded-lg px-4 py-2">{error}</div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {statCards.map((s, i) => (
          <div key={i} className="bg-gray-900 rounded-xl border border-gray-800 px-4 py-3">
            <div className="text-xs text-gray-500 mb-0.5">{s.l}</div>
            <div className={'text-sm font-semibold ' + (s.c || 'text-white')}>{s.v}</div>
          </div>
        ))}
      </div>

      {status?.data_source === 'simulation' && (
        <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg px-4 py-2.5 text-amber-300 text-xs font-medium flex items-center gap-2">
          <Activity className="w-3.5 h-3.5" />
          DATA SOURCE: SIMULATION — Synthetic CSI processed through full ML pipeline.
        </div>
      )}

      {status?.is_running && status?.data_source === 'simulation' && (
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
          <h3 className="text-sm font-medium text-gray-300 mb-3">Simulation Activity</h3>
          <div className="flex gap-2">
            {['NO_MOVEMENT', 'MOVEMENT', 'WALKING'].map(a => (
              <button
                key={a}
                onClick={() => setActivity(a)}
                className={
                  'px-4 py-2 rounded-lg text-xs font-medium border ' +
                  (status.simulator_activity === a
                    ? 'bg-brand-600/20 text-brand-400 border-brand-500/30'
                    : 'bg-gray-800 text-gray-400 border-gray-700 hover:text-gray-300')
                }
              >
                {a.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <ConfidenceGauge confidence={confidence} prediction={prediction} />
          {!status?.model_ready && (
            <p className="text-xs text-amber-400 mt-3 text-center bg-amber-500/10 rounded-lg px-3 py-2">
              No ML model loaded. Go to Training.
            </p>
          )}
        </div>
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center gap-2">
            <label className="text-xs text-gray-500">Subcarrier:</label>
            <select
              value={sub}
              onChange={e => setSub(Number(e.target.value))}
              className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-gray-300"
            >
              {Array.from({ length: 64 }, (_, i) => (
                <option key={i} value={i}>#{i}</option>
              ))}
              
            </select>
          </div>
          <LiveSignalChart signalHistory={sigHist} subcarrierIndex={sub} />
        </div>
      </div>

      <ActivityTimeline entries={timeline} />
    </div>
  )
}