import pytest
import numpy as np
from app.signal_processing.preprocessing import SignalPreprocessor
from app.signal_processing.filtering import hampel_filter, butter_lowpass_filter
from app.signal_processing.features import FeatureExtractor

def test_hampel_removes_outliers():
    d = np.array([1.,1.,1.,100.,1.,1.,1.]).reshape(-1,1)
    f = hampel_filter(d, window_size=5, n_sigmas=3.0)
    assert f[3,0] < 50.0

def test_butter_lowpass():
    t = np.linspace(0,1,1000)
    sig = np.sin(2*np.pi*50*t).reshape(-1,1)
    f = butter_lowpass_filter(sig, cutoff=10.0, sample_rate=1000.0)
    assert np.std(f) < 0.1 * np.std(sig)

def test_preprocessor():
    p = SignalPreprocessor()
    raw = np.random.randn(100,64)*0.1+2.0
    proc = p.process(raw)
    assert proc.shape == raw.shape

def test_features():
    ext = FeatureExtractor()
    data = np.random.randn(100,64)*0.1+2.0
    feat = ext.extract(data)
    assert feat.shape == (ext.n_features,)
    assert not np.any(np.isnan(feat))

def test_features_differ():
    ext = FeatureExtractor()
    np.random.seed(42)
    stable = np.ones((100,64))*2.0 + np.random.randn(100,64)*0.01
    t = np.linspace(0,1,100)
    periodic = np.ones((100,64))*2.0 + np.outer(np.sin(2*np.pi*1.5*t), np.ones(64))*0.5
    fs = ext.extract(stable)
    fp = ext.extract(periodic)
    assert not np.allclose(fs, fp)
