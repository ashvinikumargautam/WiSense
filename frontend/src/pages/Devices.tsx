import { useState, useEffect } from 'react'
import { Wifi, Plus, Trash2, Signal } from 'lucide-react'
import { api } from '../api/client'
import type { Device } from '../types'

export default function Devices() {
  const [devices, setDevices] = useState<Device[]>([])
  const [showAdd, setShowAdd] = useState(false)
  const [newId, setNewId] = useState('')
  const [newName, setNewName] = useState('')
  const [error, setError] = useState('')

  const fetchDevices = async () => {
    try {
      const d = await api.get<Device[]>('/devices')
      setDevices(d)
    } catch { /* ignore */ }
  }

  useEffect(() => { fetchDevices() }, [])

  const addDevice = async () => {
    setError('')
    if (!newId.trim()) return
    try {
      await api.post('/devices', { device_id: newId.trim(), device_name: newName.trim(), device_type: 'esp32', data_source: 'esp32' })
      setNewId(''); setNewName(''); setShowAdd(false)
      await fetchDevices()
    } catch (e: any) { setError(e.message) }
  }

  const removeDevice = async (id: string) => {
    try {
      await api.delete(`/devices/${id}`)
      await fetchDevices()
    } catch { /* ignore */ }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Devices</h1>
          <p className="text-sm text-gray-500 mt-0.5">Manage sensing devices</p>
        </div>
        <button onClick={() => setShowAdd(!showAdd)} className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-sm font-medium transition-colors">
          <Plus className="w-4 h-4" /> Add Device
        </button>
      </div>

      {showAdd && (
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 space-y-3">
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-400 mb-1">Device ID</label>
              <input value={newId} onChange={e => setNewId(e.target.value)} placeholder="ESP32-001"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-brand-500" />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Name (optional)</label>
              <input value={newName} onChange={e => setNewName(e.target.value)} placeholder="Living Room Sensor"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-brand-500" />
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={addDevice} className="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-sm">Add</button>
            <button onClick={() => setShowAdd(false)} className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm">Cancel</button>
          </div>
        </div>
      )}

      <div className="grid gap-4">
        {devices.map(device => (
          <div key={device.id} className="bg-gray-900 rounded-xl border border-gray-800 p-5">
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-4">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                  device.device_type === 'simulator' ? 'bg-amber-500/20' : 'bg-brand-500/20'
                }`}>
                  <Wifi className={`w-5 h-5 ${device.device_type === 'simulator' ? 'text-amber-400' : 'text-brand-400'}`} />
                </div>
                <div>
                  <h3 className="font-semibold text-white">{device.device_id}</h3>
                  <p className="text-sm text-gray-500">{device.device_name || 'Unnamed device'}</p>
                  <div className="flex items-center gap-3 mt-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full border ${
                      device.data_source === 'simulation'
                        ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                        : 'bg-brand-500/10 text-brand-400 border-brand-500/20'
                    }`}>
                      {device.data_source.toUpperCase()}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded-full border ${
                      device.status === 'online'
                        ? 'bg-green-500/10 text-green-400 border-green-500/20'
                        : 'bg-gray-500/10 text-gray-400 border-gray-500/20'
                    }`}>
                      <Signal className="w-3 h-3 inline mr-1" />
                      {device.status.toUpperCase()}
                    </span>
                  </div>
                </div>
              </div>
              {device.device_type !== 'simulator' && (
                <button onClick={() => removeDevice(device.device_id)} className="p-2 text-gray-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors">
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </div>
            {device.last_seen && (
              <p className="text-xs text-gray-600 mt-3">Last seen: {new Date(device.last_seen).toLocaleString()}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}