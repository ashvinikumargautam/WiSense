import { useState, useEffect, useCallback } from 'react'
import { Play, Square, Brain, CheckCircle, AlertCircle } from 'lucide-react'
import { api } from '../api/client'
import type { TrainingStatus, ModelStatus, TrainingResults, TrainingSession } from '../types'

export default function Training() {
  const [trainingStatus, setTrainingStatus] = useState<TrainingStatus | null>(null)
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null)
  const [trainingResults, setTrainingResults] = useState<TrainingResults | null>(null)
  const [training, setTraining] = useState(false)
  const [error, setError] = useState('')

  const fetchTrainingStatus = useCallback(async () => {
    try {
      const s = await api.get<TrainingStatus>('/training/status')
      setTrainingStatus(s)
      setTraining(s.collecting)
    } catch { /* ignore */ }
  }, [])

  const fetchModelStatus = useCallback(async () => {
    try {
      const s = await api.get<ModelStatus>('/training/model/status')
      setModelStatus(s)
    } catch { /* ignore */ }
  }, [])

  useEffect(() => { fetchTrainingStatus(); fetchModelStatus() }, [fetchTrainingStatus, fetchModelStatus])
  useEffect(() => {
    const interval = setInterval(() => { fetchTrainingStatus(); fetchModelStatus() }, training ? 1000 : 3000)
    return () => clearInterval(interval)
  }, [training, fetchTrainingStatus, fetchModelStatus])

  const startCollection = async (activity: string) => {
    setError('')
    try {
      await api.post('/training/start', { activity })
      await fetchTrainingStatus()
    } catch (e: any) { setError(e.message) }
  }

  const stopCollection = async () => {
    try {
      await api.post('/training/stop')
      await fetchTrainingStatus()
    } catch (e: any) { setError(e.message) }
  }

  const trainModel = async () => {
    setError('')
    setTraining(true)
    try {
      const r = await api.post<{ results: TrainingResults }>('/training/train')
      setTrainingResults(r.results)
      await fetchModelStatus()
    } catch (e: any) { setError(e.message) }
    finally { setTraining(false) }
  }

  const generateDefault = async () => {
    setError('')
    setTraining(true)
    try {
      const r = await api.post<{ results: TrainingResults }>('/training/generate-default')
      setTrainingResults(r.results)
      await fetchModelStatus()
    } catch (e: any) { setError(e.message) }
    finally { setTraining(false) }
  }

  const sessionsByActivity = (activity: string): TrainingSession[] => {
    return trainingStatus?.sessions.filter(s => s.activity === activity && s.status === 'completed') || []
  }

  const totalSamples = () => {
    return trainingStatus?.sessions.filter(s => s.status === 'completed').reduce((sum, s) => sum + s.samples_collected, 0) || 0
  }

  const activities = ['NO_MOVEMENT', 'MOVEMENT', 'WALKING']

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Model Training</h1>
          <p className="text-sm text-gray-500 mt-0.5">Collect data and train movement classifiers</p>
        </div>
        <button onClick={generateDefault} disabled={training}
          className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors">
          <Brain className="w-4 h-4" /> Generate Default Model
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2 text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-2">
          <AlertCircle className="w-4 h-4" /> {error}
        </div>
      )}

      {/* Current model status */}
      {modelStatus && (
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
          <h3 className="text-sm font-medium text-gray-300 mb-3">Current Model</h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div>
              <div className="text-xs text-gray-500">Status</div>
              <div className={`text-sm font-medium ${modelStatus.model_loaded ? 'text-green-400' : 'text-red-400'}`}>
                {modelStatus.model_loaded ? 'Loaded' : 'Not Available'}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Type</div>
              <div className="text-sm font-medium text-white">{modelStatus.model_type || '—'}</div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Classes</div>
              <div className="text-sm font-medium text-white">{modelStatus.classes.join(', ') || '—'}</div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Training Samples</div>
              <div className="text-sm font-medium text-white">{modelStatus.n_training_samples || '—'}</div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Default</div>
              <div className="text-sm font-medium text-white">{modelStatus.is_default ? 'Yes (Synthetic)' : 'No (Custom)'}</div>
            </div>
          </div>
          {modelStatus.metrics && Object.keys(modelStatus.metrics).length > 0 && (
            <div className="grid grid-cols-4 gap-4 mt-4 pt-4 border-t border-gray-800">
              <div>
                <div className="text-xs text-gray-500">Accuracy</div>
                <div className="text-lg font-bold text-green-400">{(modelStatus.metrics.accuracy * 100).toFixed(1)}%</div>
              </div>
              <div>
                <div className="text-xs text-gray-500">Precision</div>
                <div className="text-lg font-bold text-blue-400">{(modelStatus.metrics.precision * 100).toFixed(1)}%</div>
              </div>
              <div>
                <div className="text-xs text-gray-500">Recall</div>
                <div className="text-lg font-bold text-amber-400">{(modelStatus.metrics.recall * 100).toFixed(1)}%</div>
              </div>
              <div>
                <div className="text-xs text-gray-500">F1 Score</div>
                <div className="text-lg font-bold text-purple-400">{(modelStatus.metrics.f1_score * 100).toFixed(1)}%</div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Collection controls */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-gray-300">Data Collection</h3>
          <div className="text-xs text-gray-500">Total samples: {totalSamples()}</div>
        </div>

        {trainingStatus?.collecting && (
          <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg px-4 py-2 mb-4 flex items-center justify-between">
            <span className="text-blue-300 text-sm">Collecting: {trainingStatus.activity?.replace('_', ' ')} — {trainingStatus.samples_collected} samples</span>
            <button onClick={stopCollection} className="flex items-center gap-1.5 px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded-lg text-xs font-medium">
              <Square className="w-3 h-3" /> Stop
            </button>
          </div>
        )}

        <div className="space-y-2">
          {activities.map(act => {
            const sessions = sessionsByActivity(act)
            const count = sessions.reduce((s, sess) => s + sess.samples_collected, 0)
            return (
              <div key={act} className="flex items-center justify-between py-2.5 px-3 bg-gray-800/50 rounded-lg">
                <div className="flex items-center gap-3">
                  {count > 0 ? (
                    <CheckCircle className="w-4 h-4 text-green-400" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border-2 border-gray-600" />
                  )}
                  <span className="text-sm text-white font-medium">{act.replace('_', ' ')}</span>
                  <span className="text-xs text-gray-500">{count} samples ({sessions.length} sessions)</span>
                </div>
                <button
                  onClick={() => startCollection(act)}
                  disabled={trainingStatus?.collecting || false}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 disabled:opacity-40 text-white rounded-lg text-xs font-medium transition-colors"
                >
                  <Play className="w-3 h-3" /> Collect
                </button>
              </div>
            )
          })}
        </div>

        <button
          onClick={trainModel} disabled={training || totalSamples() < 30}
          className="mt-4 w-full flex items-center justify-center gap-2 px-4 py-3 bg-brand-600 hover:bg-brand-700 disabled:opacity-40 text-white rounded-lg text-sm font-medium transition-colors"
        >
          <Brain className="w-4 h-4" />
          {training ? 'Training...' : `Train Model (${totalSamples()} samples)`}
        </button>
      </div>

      {/* Training results */}
      {trainingResults && (
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
          <h3 className="text-sm font-medium text-gray-300 mb-4">Training Results — {trainingResults.best_model}</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div>
              <div className="text-xs text-gray-500">Accuracy</div>
              <div className="text-lg font-bold text-green-400">{(trainingResults.best_f1 * 100).toFixed(1)}%</div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Samples</div>
              <div className="text-lg font-bold text-white">{trainingResults.n_samples}</div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Features</div>
              <div className="text-lg font-bold text-white">{trainingResults.n_features}</div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Classes</div>
              <div className="text-lg font-bold text-white">{trainingResults.classes.length}</div>
            </div>
          </div>

          {/* Confusion matrix for best model */}
          {trainingResults.models[trainingResults.best_model]?.confusion_matrix && (
            <div>
              <h4 className="text-xs text-gray-400 mb-2">Confusion Matrix ({trainingResults.best_model})</h4>
              <ConfusionMatrix
                matrix={trainingResults.models[trainingResults.best_model].confusion_matrix}
                labels={trainingResults.confusion_matrix_labels}
              />
            </div>
          )}

          {/* Per-model comparison */}
          <div className="mt-4">
            <h4 className="text-xs text-gray-400 mb-2">Model Comparison</h4>
            <table className="w-full text-xs">
              <thead>
                <tr className="text-gray-500 border-b border-gray-800">
                  <th className="text-left py-2 pr-4">Model</th>
                  <th className="text-right py-2 px-2">Accuracy</th>
                  <th className="text-right py-2 px-2">Precision</th>
                  <th className="text-right py-2 px-2">Recall</th>
                  <th className="text-right py-2 px-2">F1</th>
                  <th className="text-right py-2 pl-2">CV Acc</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(trainingResults.models).map(([name, m]) => (
                  <tr key={name} className={`border-b border-gray-800/50 ${name === trainingResults.best_model ? 'text-brand-400' : 'text-gray-300'}`}>
                    <td className="py-2 pr-4 font-medium">{name} {name === trainingResults.best_model && '★'}</td>
                    <td className="text-right py-2 px-2">{(m.accuracy * 100).toFixed(1)}%</td>
                    <td className="text-right py-2 px-2">{(m.precision * 100).toFixed(1)}%</td>
                    <td className="text-right py-2 px-2">{(m.recall * 100).toFixed(1)}%</td>
                    <td className="text-right py-2 px-2">{(m.f1_score * 100).toFixed(1)}%</td>
                    <td className="text-right py-2 pl-2">{(m.cv_accuracy_mean * 100).toFixed(1)}±{(m.cv_accuracy_std * 100).toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

function ConfusionMatrix({ matrix, labels }: { matrix: number[][]; labels: string[] }) {
  const maxVal = Math.max(...matrix.flat(), 1)
  return (
    <div className="overflow-x-auto">
      <table className="text-xs">
        <thead>
          <tr>
            <th className="py-1 pr-2 text-gray-600"></th>
            {labels.map(l => (
              <th key={l} className="py-1 px-2 text-gray-500 font-normal">{l.replace('_', ' ')}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.map((row, i) => (
            <tr key={i}>
              <td className="py-1 pr-2 text-gray-500 font-normal text-right">{labels[i]?.replace('_', ' ')}</td>
              {row.map((val, j) => {
                const intensity = val / maxVal
                return (
                  <td key={j} className="py-1 px-2">
                    <div
                      className="w-10 h-7 flex items-center justify-center rounded text-white font-medium"
                      style={{ backgroundColor: `rgba(59, 130, 246, ${intensity * 0.8 + 0.05})` }}
                    >
                      {val}
                    </div>
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}