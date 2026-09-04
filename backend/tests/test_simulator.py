import pytest
import numpy as np
import asyncio
from app.data_sources.simulator import SimulatorDataSource

@pytest.mark.asyncio
async def test_simulator_generates_data():
    sim = SimulatorDataSource()
    await sim.start()
    sample = await sim.get_sample()
    assert sample is not None
    assert sample.device_id == "SIMULATOR-001"
    assert sample.csi.shape == (64,)
    await sim.stop()

@pytest.mark.asyncio
async def test_different_activities():
    sim = SimulatorDataSource()
    await sim.start()
    results = {}
    for act in ["NO_MOVEMENT", "MOVEMENT", "WALKING"]:
        sim.set_activity(act)
        amps = []
        for _ in range(200):
            s = await sim.get_sample()
            if s: amps.append(s.get_amplitudes())
        data = np.array(amps)
        results[act] = np.mean(np.std(data, axis=0))
    assert results["NO_MOVEMENT"] < results["MOVEMENT"]
    await sim.stop()

def test_generate_dataset():
    sim = SimulatorDataSource()
    w2, l = sim.generate_dataset_samples("WALKING", n_windows=10, window_size=100)
    assert w2.shape == (10, 100, 64)
    assert all(x == "WALKING" for x in l)
