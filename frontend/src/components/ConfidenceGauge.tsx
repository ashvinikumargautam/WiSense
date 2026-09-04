interface Props {
  confidence: number
  prediction: string
}

const PREDICTION_ICONS: Record<string, string> = {
  NO_MOVEMENT: '🧍',
  MOVEMENT: '🏃',
  WALKING: '🚶',
  UNKNOWN: '❓',
}

const PREDICTION_COLORS: Record<string, string> = {
  NO_MOVEMENT: '#22c55e',
  MOVEMENT: '#f59e0b',
  WALKING: '#3b82f6',
  UNKNOWN: '#6b7280',
}

export default function ConfidenceGauge({ confidence, prediction }: Props) {
  const color = PREDICTION_COLORS[prediction] || '#6b7280'
  const icon = PREDICTION_ICONS[prediction] || '❓'
  const pct = Math.round(confidence * 100)

  // SVG arc parameters
  const radius = 70
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference - (confidence * circumference)

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-6 flex flex-col items-center">
      <h3 className="text-sm font-medium text-gray-400 mb-4 uppercase tracking-wider">Current Activity</h3>
      <div className="relative w-44 h-44 mb-4">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 160 160">
          <circle cx="80" cy="80" r={radius} fill="none" stroke="#1e293b" strokeWidth="8" />
          <circle
            cx="80" cy="80" r={radius} fill="none"
            stroke={color} strokeWidth="8" strokeLinecap="round"
            strokeDasharray={circumference} strokeDashoffset={strokeDashoffset}
            className="transition-all duration-500 ease-out"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-4xl mb-1">{icon}</span>
          <span className="text-xs font-medium text-gray-400 break-all text-center px-2">{prediction.replace('_', ' ')}</span>
        </div>
      </div>
      <div className="text-center">
        <div className="text-3xl font-bold" style={{ color }}>{pct}%</div>
        <div className="text-xs text-gray-500 mt-1">Confidence</div>
      </div>
    </div>
  )
}