import pytest
import numpy as np
import os
import tempfile
from app.ml.training import MLTrainer
from app.ml.inference import MLInference
from app.ml.model_manager import ModelManager

def test_training_pipeline():
    with tempfile.TemporaryDirectory() as tmp:
        mm = ModelManager(model_path=os.path.join(tmp,"m.pkl"), scaler_path=os.path.join(tmp,"s.pkl"))
        trainer = MLTrainer(mm)
        from app.data_sources.simulator import SimulatorDataSource
        sim = SimulatorDataSource()
        aw, al = [], []
        for a in SimulatorDataSource.ACTIVITIES:
            w2, l = sim.generate_dataset_samples(a, n_windows=100, window_size=100)
            aw.append(w2); al.append(l)
        X_w = np.concatenate(aw); y_l = np.concatenate(al)
        feat = trainer.extract_features_from_windows(X_w, fit_preprocessor=True)
        res = trainer.train(feat, y_l)
        assert res["best_f1"] > 0.5
        inf = MLInference(mm)
        assert inf.load_model()
        tw = sim.generate_dataset_samples("WALKING", n_windows=1, window_size=100)[0][0]
        r = inf.predict(tw)
        assert r["prediction"] in ["NO_MOVEMENT","MOVEMENT","WALKING","UNKNOWN"]
        assert r["model_ready"] is True

def test_no_model():
    with tempfile.TemporaryDirectory() as tmp:
        mm = ModelManager(model_path=os.path.join(tmp,"x.pkl"), scaler_path=os.path.join(tmp,"x.pkl"))
        inf = MLInference(mm)
        assert not inf.load_model()
        r = inf.predict(np.random.randn(100,64))
        assert r["prediction"] == "UNKNOWN"
