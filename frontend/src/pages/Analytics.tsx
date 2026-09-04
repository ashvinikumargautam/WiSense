import { useState, useEffect, useCallback } from 'react'
// ✅ 1. Added AreaChart and Area to the imports
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend, AreaChart, Area } from 'recharts'
import { api } from '../api/client'
import type { DetectionRecord } from '../types'

const COLORS = ['#22c55e', '#f59e0b', '#3b82f6', '#6b7280']

export default function Analytics() {
  const [detections, setDetections] = useState<DetectionRecord[]>([])
  const [total, setTotal] = useState(0)

  const fetchData = useCallback(async () => {
    try {
      const d = await api.get<{ detections: DetectionRecord[]; total: number }>('/history?page_size=1000')
      setDetections(d.detections)
      setTotal(d.total)
    } catch { /* ignore */ }
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  // Prediction distribution
  const distribution = detections.reduce<Record<string, number>>((acc, d) => {
    acc[d.prediction] = (acc[d.prediction] || 0) + 1
    return acc
  }, {})
  const pieData = Object.entries(distribution).map(([name, value]) => ({ name: name.replace('_', ' '), value }))

  // Average confidence per class
  const confidenceByClass = detections.reduce<Record<string, { sum: number; count: number }>>((acc, d) => {
    if (!acc[d.prediction]) acc[d.prediction] = { sum: 0, count: 0 }
    acc[d.prediction].sum += d.confidence
    acc[d.prediction].count += 1
    return acc
  }, {})
  const confidenceData = Object.entries(confidenceByClass).map(([name, v]) => ({
    name: name.replace('_', ' '),
    confidence: Number(((v.sum / v.count) * 100).toFixed(1)),
  }))

  // Timeline (per minute) - For your existing bar chart
  const timelineMap = new Map<string, Record<string, number>>()
  detections.forEach(d => {
    const minute = d.created_at?.substring(0, 16) || 'unknown'
    if (!timelineMap.has(minute)) timelineMap.set(minute, {})
    const entry = timelineMap.get(minute)!
    entry[d.prediction] = (entry[d.prediction] || 0) + 1
  })
  const timelineData = Array.from(timelineMap.entries()).map(([time, counts]) => ({
    time,
    ...Object.fromEntries(Object.entries(counts).map(([k, v]) => [k.replace('_', ' '), v])),
  }))

  // ✅ 2. NEW: Continuous Time-Series Data for the Area Chart
  // Takes the last 60 detections to show a smooth wave
  const pulseData = detections.slice(-60).reverse().map(d => ({
    time: d.created_at?.substring(11, 19) || '00:00:00', // Extract just HH:MM:SS
    confidence: d.prediction === 'NO_MOVEMENT' ? 0 : (d.confidence * 100)
  }))

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Analytics</h1>
        <p className="text-sm text-gray-500 mt-0.5">Detection statistics and patterns ({total} total)</p>
      </div>

      {detections.length === 0 ? (
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-12 text-center text-gray-500">
          No detection data yet. Start the simulator and let it run for a while.
        </div>
      ) : (
        <div className="space-y-6">
          
          {/* ✅ 3. NEW: The "Level 1" Continuous Wave Chart */}
          {pulseData.length > 0 && (
            <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
              <h3 className="text-sm font-medium text-gray-300 mb-3">Room Movement Pulse (Recent Activity)</h3>
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={pulseData}>
                  <defs>
                    <linearGradient id="colorPulse" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#94a3b8' }} interval="preserveStartEnd" />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: '#94a3b8' }} unit="%" />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8, color: '#fff' }}
                    formatter={(value: number) => [`${value.toFixed(1)}%`, 'Movement']}
                  />
                  <Area type="monotone" dataKey="confidence" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorPulse)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Your existing Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
              <h3 className="text-sm font-medium text-gray-300 mb-3">Prediction Distribution</h3>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label>
                    {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
              <h3 className="text-sm font-medium text-gray-300 mb-3">Avg Confidence by Class</h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={confidenceData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#94a3b8' }} />
                  <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} domain={[0, 100]} unit="%" />
                  <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} formatter={(v: number) => [`${v}%`, 'Confidence']} />
                  <Bar dataKey="confidence" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {timelineData.length > 0 && (
              <div className="lg:col-span-2 bg-gray-900 rounded-xl border border-gray-800 p-4">
                <h3 className="text-sm font-medium text-gray-300 mb-3">Detection Timeline</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={timelineData.slice(-30)}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="time" tick={{ fontSize: 9, fill: '#94a3b8' }} angle={-45} textAnchor="end" height={60} />
                    <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} />
                    <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
                    <Legend />
                    {Object.keys(distribution).map((name, i) => (
                      <Bar key={name} dataKey={name.replace('_', ' ')} stackId="a" fill={COLORS[i % COLORS.length]} />
                    ))}
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}