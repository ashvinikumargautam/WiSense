import { useState, useEffect, useCallback } from 'react'
import { api } from '../api/client'
import type { DetectionRecord } from '../types'

const PREDICTION_COLORS: Record<string, string> = {
  NO_MOVEMENT: 'text-green-400 bg-green-500/10 border-green-500/20',
  MOVEMENT: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
  WALKING: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
  UNKNOWN: 'text-gray-400 bg-gray-500/10 border-gray-500/20',
}

export default function History() {
  const [detections, setDetections] = useState<DetectionRecord[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [filter, setFilter] = useState<string>('')

  const fetchHistory = useCallback(async () => {
    try {
      const params = new URLSearchParams({ page: String(page), page_size: '50' })
      if (filter) params.set('prediction', filter)
      const d = await api.get<{ detections: DetectionRecord[]; total: number }>(`/history?${params}`)
      setDetections(d.detections)
      setTotal(d.total)
    } catch { /* ignore */ }
  }, [page, filter])

  useEffect(() => { fetchHistory() }, [fetchHistory])

  const totalPages = Math.ceil(total / 50)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Detection History</h1>
          <p className="text-sm text-gray-500 mt-0.5">{total} total detections</p>
        </div>
        <select value={filter} onChange={e => { setFilter(e.target.value); setPage(1) }}
          className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300">
          <option value="">All Classes</option>
          <option value="NO_MOVEMENT">No Movement</option>
          <option value="MOVEMENT">Movement</option>
          <option value="WALKING">Walking</option>
          <option value="UNKNOWN">Unknown</option>
        </select>
      </div>

      <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 text-gray-500 text-xs">
              <th className="text-left py-3 px-4 font-medium">Time</th>
              <th className="text-left py-3 px-4 font-medium">Device</th>
              <th className="text-left py-3 px-4 font-medium">Prediction</th>
              <th className="text-left py-3 px-4 font-medium">Confidence</th>
              <th className="text-left py-3 px-4 font-medium">RSSI</th>
              <th className="text-left py-3 px-4 font-medium">Source</th>
            </tr>
          </thead>
          <tbody>
            {detections.length === 0 ? (
              <tr><td colSpan={6} className="text-center py-8 text-gray-600">No detections yet</td></tr>
            ) : detections.map(d => (
              <tr key={d.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                <td className="py-2.5 px-4 text-gray-400 text-xs font-mono">
                  {d.created_at ? new Date(d.created_at).toLocaleString() : '—'}
                </td>
                <td className="py-2.5 px-4 text-gray-300 text-xs">{d.device_id}</td>
                <td className="py-2.5 px-4">
                  <span className={`text-xs px-2 py-0.5 rounded-full border ${PREDICTION_COLORS[d.prediction] || PREDICTION_COLORS.UNKNOWN}`}>
                    {d.prediction.replace('_', ' ')}
                  </span>
                </td>
                <td className="py-2.5 px-4 text-gray-300 text-xs">{(d.confidence * 100).toFixed(1)}%</td>
                <td className="py-2.5 px-4 text-gray-400 text-xs">{d.rssi != null ? `${d.rssi} dBm` : '—'}</td>
                <td className="py-2.5 px-4 text-gray-500 text-xs uppercase">{d.data_source}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1}
            className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 disabled:opacity-40 text-gray-300 rounded-lg text-xs">Prev</button>
          <span className="text-xs text-gray-500">Page {page} of {totalPages}</span>
          <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page >= totalPages}
            className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 disabled:opacity-40 text-gray-300 rounded-lg text-xs">Next</button>
        </div>
      )}
    </div>
  )
}