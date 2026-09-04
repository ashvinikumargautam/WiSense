export default function Documentation() {
  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-white">Documentation</h1>
        <p className="text-sm text-gray-500 mt-0.5">Architecture, concepts, and usage guide</p>
      </div>

      <div className="space-y-4">
        <DocSection title="Architecture Overview" id="architecture">
          <pre className="bg-gray-800 rounded-lg p-4 text-xs text-green-300 overflow-x-auto font-mono">{`
DATA SOURCE
    │
    ├── SimulatorDataSource (laptop, now)
    └── ESP32CSIDataSource    (hardware, later)
    │
    ▼
Signal Preprocessing
    ├── Amplitude extraction
    ├── Hampel outlier removal
    ├── Butterworth low-pass filter
    ├── Moving average smoothing
    └── Standardization
    │
    ▼
Feature Extraction (29 features)
    ├── Time-domain (11): mean, std, var, RMS, min, max, range, median, skew, kurtosis, ZCR
    ├── Frequency-domain (4): spectral energy, dominant freq, entropy, centroid
    └── CSI-specific (14): subcarrier stats, spatial variance, correlation
    │
    ▼
ML Classifier (Random Forest / Logistic Regression / SVM)
    │
    ▼
Movement Prediction (NO_MOVEMENT / MOVEMENT / WALKING / UNKNOWN)
    │
    ▼
WebSocket → React Dashboard
          `}</pre>
        </DocSection>

        <DocSection title="What is CSI?" id="csi">
          <p className="text-sm text-gray-300">Channel State Information (CSI) represents how a Wi-Fi signal transforms as it travels from transmitter to receiver. It captures amplitude and phase information for each OFDM subcarrier. When a person moves in the environment, they alter the multipath propagation, causing measurable changes in CSI. This is the physical basis for Wi-Fi-based human sensing.</p>
        </DocSection>

        <DocSection title="Simulation Mode" id="simulation">
          <p className="text-sm text-gray-300">The simulator generates synthetic CSI-like signals with distinct characteristics for each activity:</p>
          <ul className="list-disc list-inside text-sm text-gray-400 mt-2 space-y-1">
            <li><strong className="text-gray-300">NO_MOVEMENT:</strong> Stable amplitudes, very low temporal variance, no periodic structure</li>
            <li><strong className="text-gray-300">MOVEMENT:</strong> Random amplitude fluctuations, medium variance, no clear periodicity</li>
            <li><strong className="text-gray-300">WALKING:</strong> Periodic modulation at ~1.5 Hz (step frequency), harmonics at 3 Hz, subcarrier-dependent phase variation</li>
          </ul>
          <p className="text-sm text-gray-400 mt-2">The simulated signals pass through the exact same preprocessing, feature extraction, and ML inference pipeline as real ESP32 CSI data would.</p>
        </DocSection>

        <DocSection title="Getting Started" id="getting-started">
          <ol className="list-decimal list-inside text-sm text-gray-300 space-y-2">
            <li>Register an account and log in</li>
            <li>Go to Dashboard and click "Start Simulator"</li>
            <li>A default ML model is auto-generated on first startup from synthetic data</li>
            <li>Switch between NO_MOVEMENT, MOVEMENT, and WALKING to see predictions change</li>
            <li>Go to Training to collect custom data and retrain the model</li>
          </ol>
        </DocSection>

        <DocSection title="ESP32 Integration (Future)" id="esp32">
          <p className="text-sm text-gray-300">When you purchase an ESP32:</p>
          <ol className="list-decimal list-inside text-sm text-gray-400 mt-2 space-y-1">
            <li>Flash the firmware from <code className="bg-gray-800 px-1 rounded">firmware/esp32_csi/</code></li>
            <li>Configure Wi-Fi credentials and backend URL in the firmware</li>
            <li>Register the ESP32 as a device in the Devices page</li>
            <li>Select "ESP32" as data source</li>
            <li>The same pipeline processes real CSI data — no code changes needed</li>
          </ol>
        </DocSection>

        <DocSection title="API Reference" id="api">
          <div className="bg-gray-800 rounded-lg p-4 text-xs font-mono text-gray-300 overflow-x-auto space-y-1">
            <div><span className="text-green-400">POST</span> /api/auth/register</div>
            <div><span className="text-green-400">POST</span> /api/auth/login</div>
            <div><span className="text-blue-400">GET</span>  /api/health</div>
            <div><span className="text-blue-400">GET</span>  /api/devices</div>
            <div><span className="text-green-400">POST</span> /api/devices</div>
            <div><span className="text-blue-400">GET</span>  /api/sensing/status</div>
            <div><span className="text-green-400">POST</span> /api/sensing/simulation/start</div>
            <div><span className="text-green-400">POST</span> /api/sensing/simulation/stop</div>
            <div><span className="text-green-400">POST</span> /api/sensing/simulation/activity</div>
            <div><span className="text-green-400">POST</span> /api/training/start</div>
            <div><span className="text-green-400">POST</span> /api/training/stop</div>
            <div><span className="text-green-400">POST</span> /api/training/train</div>
            <div><span className="text-green-400">POST</span> /api/training/generate-default</div>
            <div><span className="text-blue-400">GET</span>  /api/training/status</div>
            <div><span className="text-blue-400">GET</span>  /api/training/model/status</div>
            <div><span className="text-blue-400">GET</span>  /api/history</div>
            <div><span className="text-yellow-400">WS</span>   /ws/sensing?token=JWT</div>
            <div><span className="text-yellow-400">WS</span>   /ws/device/{'{'}device_id{'}'}?token=JWT</div>
          </div>
        </DocSection>
      </div>
    </div>
  )
}

function DocSection({ title, id, children }: { title: string; id: string; children: React.ReactNode }) {
  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-5" id={id}>
      <h2 className="text-base font-semibold text-white mb-3">{title}</h2>
      {children}
    </div>
  )
}