import type { SensingMessage } from '../types'

interface Props {
  entries: { time: string; prediction: string; confidence: number }[]
}

const PREDICTION_COLORS: Record<string, string> = {
  NO_MOVEMENT: 'bg-green-500/20 text-green-400 border-green-500/30',
  MOVEMENT: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  WALKING: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  UNKNOWN: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
}

export default function ActivityTimeline({ entries }: Props) {
  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
      <h3 className="text-sm font-medium text-gray-300 mb-3 uppercase tracking-wider">Activity Timeline</h3>
      <div className="space-y-1.5 max-h-64 overflow-y-auto">
        {entries.length === 0 && (
          <p className="text-gray-600 text-sm py-4 text-center">Waiting for predictions...</p>
        )}
        {entries.map((entry, i) => {
          const colorClass = PREDICTION_COLORS[entry.prediction] || PREDICTION_COLORS.UNKNOWN
          return (
            <div key={i} className="flex items-center justify-between py-1.5 px-2 rounded-lg hover:bg-gray-800/30">
              <span className="text-xs font-mono text-gray-500">{entry.time}</span>
              <span className={`text-xs font-medium px-2.5 py-0.5 rounded-full border ${colorClass}`}>
                {entry.prediction.replace('_', ' ')}
              </span>
              <span className="text-xs text-gray-500">{Math.round(entry.confidence * 100)}%</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}