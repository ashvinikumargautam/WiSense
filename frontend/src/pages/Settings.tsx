export default function Settings() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-sm text-gray-500 mt-0.5">Application configuration</p>
      </div>

      <div className="bg-gray-900 rounded-xl border border-gray-800 p-5 space-y-6">
        <div>
          <h3 className="text-sm font-medium text-gray-300 mb-1">Data Source</h3>
          <p className="text-xs text-gray-500 mb-3">Configure how CSI data is obtained</p>
          <div className="space-y-2">
            <label className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-lg cursor-pointer">
              <input type="radio" name="source" defaultChecked disabled className="accent-brand-500" />
              <div>
                <div className="text-sm text-white font-medium">Simulation Mode</div>
                <div className="text-xs text-gray-500">Generate synthetic CSI data for testing (current)</div>
              </div>
            </label>
            <label className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-lg cursor-not-allowed opacity-50">
              <input type="radio" name="source" disabled className="accent-brand-500" />
              <div>
                <div className="text-sm text-white font-medium">ESP32 Real Hardware</div>
                <div className="text-xs text-gray-500">Connect an ESP32 device for real CSI data (requires hardware)</div>
              </div>
            </label>
          </div>
        </div>

        <div className="border-t border-gray-800 pt-4">
          <h3 className="text-sm font-medium text-gray-300 mb-1">Simulation Parameters</h3>
          <p className="text-xs text-gray-500 mb-3">These are configured via environment variables</p>
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div className="bg-gray-800/50 rounded-lg p-3">
              <div className="text-gray-500">Sample Rate</div>
              <div className="text-white font-mono mt-0.5">100 Hz</div>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-3">
              <div className="text-gray-500">Subcarriers</div>
              <div className="text-white font-mono mt-0.5">64</div>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-3">
              <div className="text-gray-500">Noise Level</div>
              <div className="text-white font-mono mt-0.5">0.05</div>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-3">
              <div className="text-gray-500">Movement Intensity</div>
              <div className="text-white font-mono mt-0.5">1.0</div>
            </div>
          </div>
        </div>

        <div className="border-t border-gray-800 pt-4">
          <h3 className="text-sm font-medium text-gray-300 mb-1">ML Pipeline</h3>
          <p className="text-xs text-gray-500 mb-3">Signal processing and model configuration</p>
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div className="bg-gray-800/50 rounded-lg p-3">
              <div className="text-gray-500">Window Size</div>
              <div className="text-white font-mono mt-0.5">100 samples (1.0s)</div>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-3">
              <div className="text-gray-500">Hop Size</div>
              <div className="text-white font-mono mt-0.5">50 samples (0.5s)</div>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-3">
              <div className="text-gray-500">Features</div>
              <div className="text-white font-mono mt-0.5">29 per window</div>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-3">
              <div className="text-gray-500">Confidence Threshold</div>
              <div className="text-white font-mono mt-0.5">0.45</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}