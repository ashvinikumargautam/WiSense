import { useEffect, useState } from 'react'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { api } from '../api/client'

interface ChartData {
  time: string
  confidence: number
}

export default function MovementChart() {
  const [data, setData] = useState<ChartData[]>([])

  useEffect(() => {
    // Fetch historical data when component loads
    api.get<ChartData[]>('/analytics/timeseries').then(res => {
      setData(res)
    })
  }, [])

  return (
    <div className="w-full h-[300px] bg-gray-900 rounded-xl border border-gray-800 p-4">
      <h3 className="text-gray-300 text-sm font-medium mb-4">Movement Activity Over Time</h3>
      
      {data.length === 0 ? (
        <div className="flex items-center justify-center h-full text-gray-600 text-sm">
          Waiting for detection data...
        </div>
      ) : (
        <ResponsiveContainer width="100%" height="85%">
          <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorMovement" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="time" stroke="#9ca3af" fontSize={12} />
            <YAxis domain={[0, 1]} stroke="#9ca3af" fontSize={12} />
            <Tooltip 
              contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px', color: '#fff' }}
              formatter={(value: number) => [`${(value * 100).toFixed(0)}% Confidence`, 'Movement']}
            />
            <Area 
              type="monotone" 
              dataKey="confidence" 
              stroke="#3b82f6" 
              strokeWidth={2}
              fillOpacity={1} 
              fill="url(#colorMovement)" 
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}