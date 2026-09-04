import { Shield } from 'lucide-react'

export default function Privacy() {
  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-center gap-3">
        <Shield className="w-8 h-8 text-brand-400" />
        <div>
          <h1 className="text-2xl font-bold text-white">Privacy</h1>
          <p className="text-sm text-gray-500 mt-0.5">How WiSense handles your data</p>
        </div>
      </div>

      <div className="bg-gray-900 rounded-xl border border-gray-800 p-6 space-y-5 text-sm text-gray-300 leading-relaxed">
        <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-4">
          <h3 className="text-green-400 font-medium mb-2">WiSense does NOT use a camera.</h3>
          <h3 className="text-green-400 font-medium mb-2">WiSense does NOT use a microphone.</h3>
          <h3 className="text-green-400 font-medium">WiSense does NOT identify faces or individuals.</h3>
        </div>

        <div>
          <h3 className="text-white font-medium mb-2">What WiSense Does</h3>
          <p>WiSense is a Wi-Fi sensing research and engineering application. It analyzes Channel State Information (CSI) — a byproduct of normal Wi-Fi communication — to detect movement patterns in an environment.</p>
        </div>

        <div>
          <h3 className="text-white font-medium mb-2">Data Processing</h3>
          <p>All signal processing and ML inference runs locally on your machine. No data is sent to external cloud services for analysis. Your CSI data, training samples, and detection history are stored in a local database.</p>
        </div>

        <div>
          <h3 className="text-white font-medium mb-2">Simulation Mode</h3>
          <p>In simulation mode (the current default), no real Wi-Fi data is used at all. The application generates synthetic CSI-like signals for testing and development purposes.</p>
        </div>

        <div>
          <h3 className="text-white font-medium mb-2">Limitations</h3>
          <ul className="list-disc list-inside space-y-1 text-gray-400">
            <li>Movement detection depends on signal conditions, hardware, room geometry, interference, and training data quality.</li>
            <li>WiSense does not recognize or identify specific individuals.</li>
            <li>Accuracy varies significantly based on environment and configuration.</li>
            <li>This is a research/engineering tool, not a commercial security product.</li>
          </ul>
        </div>

        <div>
          <h3 className="text-white font-medium mb-2">Browser Limitation</h3>
          <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-4 text-amber-200">
            A normal web browser cannot directly access raw Wi-Fi CSI from the laptop's Wi-Fi adapter. Browser APIs do not expose this data. Laptop mode therefore uses simulated or replayed CSI data. Real Wi-Fi sensing requires compatible hardware and firmware, such as an ESP32 with CSI-capable configuration.
          </div>
        </div>
      </div>
    </div>
  )
}