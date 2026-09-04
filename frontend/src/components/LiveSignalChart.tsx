import { useMemo } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'

interface Props {
  signalHistory: { time: number; values: number[] }[]
  subcarrierIndex?: number
  showFiltered?: boolean
}

export default function LiveSignalChart({ signalHistory, subcarrierIndex = 0, showFiltered = false }: Props) {
  const data = useMemo(() => {
    return signalHistory.map((entry, i) => ({
      t: i,
      val: entry.values[subcarrierIndex] ?? 0,
    }))
  }, [signalHistory, subcarrierIndex])

  const avg = useMemo(() => {
    if (data.length === 0) return 0
    return data.reduce((s, d) => s + d.val, 0) / data.length
  }, [data])

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-gray-300">CSI Amplitude — Subcarrier {subcarrierIndex}</h3>
        <span className="text-xs text-gray-500">{data.length} points</span>
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey="t" tick={false} axisLine={{ stroke: '#334155' }} />
          <YAxis tick={{ fontSize: 10, fill: '#64748b' }} axisLine={{ stroke: '#334155' }} width={40} />
          <Tooltip
            contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8, fontSize: 12 }}
            labelStyle={{ color: '#94a3b8' }}
            itemStyle={{ color: '#60a5fa' }}
            formatter={(v: number) => [v.toFixed(4), 'Amplitude']}
          />
          <ReferenceLine y={avg} stroke="#475569" strokeDasharray="5 5" />
          <Line
            type="monotone"
            dataKey="val"
            stroke="#3b82f6"
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}