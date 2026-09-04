export interface User {
  id: number
  username: string
  email: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user_id: number
  username: string
}

export interface Device {
  id: number
  device_id: string
  device_name: string
  device_type: string
  data_source: string
  status: string
  last_seen: string | null
  created_at: string
}

export interface SensingStatus {
  is_running: boolean
  data_source: string
  device_id: string
  model_ready: boolean
  stats: {
    total_samples: number
    total_predictions: number
    packets_per_second: number
    elapsed_seconds: number
  }
  simulator_activity: string
  collecting_training: boolean
  training_activity: string | null
  training_samples_collected: number
}

export interface SensingMessage {
  type: string
  timestamp: number
  device_id: string
  prediction: string
  confidence: number
  probabilities: Record<string, number>
  signal: number[]
  rssi: number
  data_source: string
  model_ready: boolean
  stats: {
    total_samples: number
    total_predictions: number
    packets_per_second: number
  }
}

export interface TrainingSession {
  id: number
  activity: string
  samples_collected: number
  status: string
  created_at: string | null
}

export interface TrainingStatus {
  collecting: boolean
  activity: string | null
  samples_collected: number
  sessions: TrainingSession[]
}

export interface ModelStatus {
  model_exists: boolean
  model_loaded: boolean
  model_type: string
  classes: string[]
  is_default: boolean
  metrics: Record<string, number>
  n_features: number
  n_training_samples: number
}

export interface DetectionRecord {
  id: number
  device_id: string
  prediction: string
  confidence: number
  rssi: number | null
  data_source: string
  created_at: string
}

export interface TrainingResults {
  best_model: string
  best_f1: number
  classes: string[]
  n_samples: number
  n_features: number
  models: Record<string, ModelMetrics>
  confusion_matrix_labels: string[]
}

export interface ModelMetrics {
  accuracy: number
  precision: number
  recall: number
  f1_score: number
  confusion_matrix: number[][]
  cv_accuracy_mean: number
  cv_accuracy_std: number
  cv_f1_mean: number
}