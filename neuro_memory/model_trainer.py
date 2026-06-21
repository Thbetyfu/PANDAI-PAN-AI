
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import numpy as np

# Machine Learning imports
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib


@dataclass
class TrainingConfig:
    """Konfigurasi training model"""
    model_name: str = "pandai_neuro_memory_v1"
    embedding_dim: int = 384
    # Neural Network config
    hidden_layer_sizes: tuple = (128, 64, 32)  # 3 layer Dense
    activation: str = "relu"
    solver: str = "adam"
    alpha: float = 0.0001  # L2 regularization
    batch_size: int = 32
    learning_rate_init: float = 0.001
    max_iter: int = 500
    early_stopping: bool = True
    # Data config
    test_size: float = 0.2
    random_state: int = 42


class ModelTrainer:
    """
    Pipeline untuk melatih foundation model Neuro-Memory dengan neural network.
    Menggunakan MLPRegressor (scikit-learn) untuk regresi prediksi kinerja.
    """

    def __init__(self, storage_path: str = "./neuro_memory_storage/models"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _extract_features(self, chunk: Dict[str, Any]) -> List[float]:
        """
        Ekstrak fitur yang lebih banyak dari memory chunk.
        Fitur mencakup: biometrics, quiz stats, content type, temporal, dll.
        """
        content = chunk.get("content", {})
        content_type = chunk.get("content_type", "")
        timestamp = chunk.get("timestamp", "")
        
        feature_vector = []
        
        # 1. Biometric features (jika ada)
        if content_type == "biometric":
            feature_vector.append(content.get("focus_score", 0.5))  # 0-1
            feature_vector.append(content.get("eye_aspect_ratio", 0.3))
            feature_vector.append(content.get("blink_rate", 10.0))
            # Tambahkan fitur tambahan dari biometrics
            feature_vector.append(content.get("head_movement", 0.0))  # Head movement intensity
            feature_vector.append(content.get("yaw", 0.0))  # Head yaw angle
            feature_vector.append(content.get("pitch", 0.0))  # Head pitch angle
            feature_vector.append(content.get("eye_movement", 0.0))  # Eye movement intensity
        else:
            # Default untuk non-biometric
            feature_vector.extend([0.5, 0.3, 10.0, 0.0, 0.0, 0.0, 0.0])
        
        # 2. Quiz features (jika ada)
        if content_type == "quiz_result":
            feature_vector.append(content.get("score", 0.5))  # Skor kuis 0-1
            feature_vector.append(content.get("duration_seconds", 60.0))  # Durasi pengerjaan
            feature_vector.append(content.get("difficulty_level", 1.0))  # Tingkat kesulitan (1-5)
            feature_vector.append(content.get("attempt_count", 1.0))  # Jumlah percobaan
            # Tambahkan fitur quiz tambahan
            feature_vector.append(content.get("correct_answers", 0.0))
            feature_vector.append(content.get("total_questions", 10.0))
        else:
            feature_vector.extend([0.5, 60.0, 1.0, 1.0, 0.0, 10.0])
        
        # 3. Content type encoding (one-hot sederhana)
        # Encode content_type ke fitur numerik
        content_types = ["biometric", "quiz_result", "study_session", "note", "other"]
        for ct in content_types:
            feature_vector.append(1.0 if content_type == ct else 0.0)
        
        # 4. Temporal features (dari timestamp)
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            feature_vector.append(dt.hour / 24.0)  # Jam 0-1 dinormalisasi
            feature_vector.append(dt.weekday() / 7.0)  # Hari 0-6 dinormalisasi
            feature_vector.append(dt.day / 31.0)  # Tanggal 1-31 dinormalisasi
        except:
            feature_vector.extend([0.5, 0.5, 0.5])
        
        # 5. Additional metadata features
        session_duration = content.get("session_duration_seconds", 300.0)
        feature_vector.append(min(session_duration / 3600.0, 1.0))  # Durasi hingga max 1 jam
        
        return feature_vector

    def prepare_training_data(self, memory_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Siapkan data training dengan fitur ekstraksi yang lebih lengkap"""
        features = []
        labels = []
        
        for chunk in memory_chunks:
            # Ekstrak fitur
            feature_vector = self._extract_features(chunk)
            features.append(feature_vector)
            
            # Label: learning_effectiveness atau score sebagai proxy
            content = chunk.get("content", {})
            label = content.get("learning_effectiveness", content.get("score", 0.5))
            labels.append(label)
        
        # Pastikan semua feature vector memiliki panjang yang sama
        if features:
            feature_dim = len(features[0])
            for i, feat in enumerate(features):
                if len(feat) != feature_dim:
                    features[i] = feat + [0.0] * (feature_dim - len(feat))
        
        return {
            "features": np.array(features),
            "labels": np.array(labels),
            "feature_names": [
                "focus_score", "eye_aspect_ratio", "blink_rate",
                "head_movement", "yaw", "pitch", "eye_movement",
                "quiz_score", "quiz_duration", "quiz_difficulty", "quiz_attempts",
                "quiz_correct", "quiz_total",
                "ct_biometric", "ct_quiz", "ct_study", "ct_note", "ct_other",
                "time_hour", "time_weekday", "time_day",
                "session_duration"
            ],
            "metadata": {
                "total_samples": len(memory_chunks),
                "feature_dim": len(features[0]) if features else 0,
                "prepared_at": datetime.now().isoformat()
            }
        }

    def train_model(self, training_data: Dict[str, Any], config: Optional[TrainingConfig] = None) -> Dict[str, Any]:
        """
        Latih model neural network dengan MLPRegressor.
        Termasuk training loop, scaling fitur, dan evaluasi dengan metrik lengkap.
        """
        config = config or TrainingConfig()
        
        X = training_data["features"]
        y = training_data["labels"]
        
        # Split data dengan stratifikasi (jika memungkinkan)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=config.test_size,
            random_state=config.random_state
        )
        
        # Normalisasi fitur dengan StandardScaler
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Inisialisasi neural network (MLPRegressor)
        model = MLPRegressor(
            hidden_layer_sizes=config.hidden_layer_sizes,
            activation=config.activation,
            solver=config.solver,
            alpha=config.alpha,
            batch_size=config.batch_size,
            learning_rate_init=config.learning_rate_init,
            max_iter=config.max_iter,
            early_stopping=config.early_stopping,
            random_state=config.random_state,
            verbose=True
        )
        
        # Training loop dengan backpropagation (ditangani internal oleh scikit-learn)
        print(f"[Neuro-Memory] Training model dengan {len(X_train)} samples...")
        model.fit(X_train_scaled, y_train)
        print(f"[Neuro-Memory] Training selesai dalam {model.n_iter_} iterasi")
        
        # Evaluasi dengan metrik lengkap
        y_train_pred = model.predict(X_train_scaled)
        y_test_pred = model.predict(X_test_scaled)
        
        metrics = {
            "train": {
                "mae": float(mean_absolute_error(y_train, y_train_pred)),
                "rmse": float(np.sqrt(mean_squared_error(y_train, y_train_pred))),
                "r2": float(r2_score(y_train, y_train_pred))
            },
            "test": {
                "mae": float(mean_absolute_error(y_test, y_test_pred)),
                "rmse": float(np.sqrt(mean_squared_error(y_test, y_test_pred))),
                "r2": float(r2_score(y_test, y_test_pred))
            },
            "n_train_samples": len(X_train),
            "n_test_samples": len(X_test),
            "feature_dim": X_train.shape[1],
            "n_iter": model.n_iter_
        }
        
        # Cetak metrik
        print(f"\n[Neuro-Memory] Evaluasi Model:")
        print(f"  Train MAE: {metrics['train']['mae']:.4f}")
        print(f"  Train RMSE: {metrics['train']['rmse']:.4f}")
        print(f"  Train R²: {metrics['train']['r2']:.4f}")
        print(f"  Test MAE: {metrics['test']['mae']:.4f}")
        print(f"  Test RMSE: {metrics['test']['rmse']:.4f}")
        print(f"  Test R²: {metrics['test']['r2']:.4f}")
        
        # Simpan model, scaler, dan config dengan joblib (production-ready format)
        model_package = {
            "model": model,
            "scaler": scaler,
            "config": asdict(config),
            "metrics": metrics,
            "feature_names": training_data.get("feature_names", []),
            "trained_at": datetime.now().isoformat()
        }
        
        # Simpan model utama
        model_path = self.storage_path / f"{config.model_name}.joblib"
        joblib.dump(model_package, model_path)
        
        # Simpan juga sebagai pickle untuk kompatibilitas
        model_path_pkl = self.storage_path / f"{config.model_name}.pkl"
        joblib.dump(model_package, model_path_pkl)
        
        # Simpan metrik dalam JSON untuk monitoring
        metrics_path = self.storage_path / f"{config.model_name}_metrics.json"
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)
        
        print(f"\n[Neuro-Memory] Model disimpan ke: {model_path}")
        
        return model_package

    def load_model(self, model_name: str = "pandai_neuro_memory_v1") -> Optional[Dict[str, Any]]:
        """Muat model yang sudah dilatih (joblib format)"""
        model_path = self.storage_path / f"{model_name}.joblib"
        if not model_path.exists():
            # Coba fallback ke pickle
            model_path = self.storage_path / f"{model_name}.pkl"
            if not model_path.exists():
                return None
        
        print(f"[Neuro-Memory] Memuat model dari: {model_path}")
        return joblib.load(model_path)

    def predict(self, model_package: Dict[str, Any], features: List[float]) -> float:
        """Lakukan prediksi dengan model yang dimuat (dengan scaling)"""
        model = model_package["model"]
        scaler = model_package["scaler"]
        
        # Reshape dan scale fitur
        features_np = np.array(features).reshape(1, -1)
        features_scaled = scaler.transform(features_np)
        
        # Prediksi
        prediction = model.predict(features_scaled)
        return float(prediction[0])

    def anonymize_data(self, memory_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Anonimkan data untuk kebutuhan riset dan sharing.
        Menghapus semua informasi identifikasi pribadi.
        """
        anonymized = []
        for chunk in memory_chunks:
            safe_chunk = {
                "content_type": chunk.get("content_type"),
                "timestamp": chunk.get("timestamp"),
                "content": {
                    k: v for k, v in chunk.get("content", {}).items()
                    if k not in ["student_name", "student_email", "student_nisn", "student_id"]
                }
            }
            anonymized.append(safe_chunk)
        return anonymized

