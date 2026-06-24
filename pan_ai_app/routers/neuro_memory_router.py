from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pathlib import Path

from ..deps import embedding_store, memory_engine, model_trainer
from ..schemas import ImportArchivePayload, ImportDatabasePayload, MemoryChunkPayload, PredictPayload, TrainModelPayload


router = APIRouter()


@router.post("/api/neuro-memory/store")
async def store_memory_chunk(payload: MemoryChunkPayload):
    try:
        from neuro_memory.memory_engine import MemoryChunk
        from datetime import datetime

        chunk = MemoryChunk(
            chunk_id="",
            student_id=payload.student_id,
            session_id=payload.session_id,
            timestamp=payload.timestamp or datetime.now().isoformat(),
            content_type=payload.content_type,
            content=payload.content,
        )

        chunk_id = memory_engine.store_memory_chunk(chunk)

        embedding_text = f"{payload.content_type}: {str(payload.content)}"
        embedding = embedding_store.generate_embedding(embedding_text)
        embedding_store.add_vector(
            chunk_id=chunk_id,
            student_id=payload.student_id,
            vector=embedding,
            metadata={
                "content_type": payload.content_type,
                "model_used": "all-MiniLM-L6-v2" if embedding_store.model_available else "dummy",
            },
        )

        return {"success": True, "chunk_id": chunk_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan memory: {str(e)}")


@router.get("/api/neuro-memory/profile/{student_id}")
async def get_cognitive_profile(student_id: str):
    profile = memory_engine.get_student_profile(student_id)
    if not profile:
        profile = memory_engine.create_initial_profile(student_id)
    return {"success": True, "student_id": student_id, "profile": profile}


@router.post("/api/neuro-memory/analyze/{student_id}")
async def analyze_learning_patterns(student_id: str):
    try:
        analysis = memory_engine.analyze_learning_pattern(student_id)
        return {"success": True, **analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal menganalisis pola: {str(e)}")


@router.get("/api/neuro-memory/recommendations/{student_id}")
async def get_personalized_recommendations(student_id: str):
    profile = memory_engine.get_student_profile(student_id) or memory_engine.create_initial_profile(student_id)

    recommendations = []

    if profile.focus_peak_hours:
        recommendations.append(
            {
                "type": "schedule",
                "title": "Waktu Belajar Optimal",
                "content": f"Puncak fokus kamu pada jam {', '.join(profile.focus_peak_hours)}. Gunakan waktu ini untuk materi sulit!",
            }
        )

    if profile.typical_focus_duration < 15:
        recommendations.append(
            {
                "type": "technique",
                "title": "Teknik Pomodoro",
                "content": "Coba teknik Pomodoro: 15 menit fokus, 5 menit istirahat.",
            }
        )

    return {"success": True, "student_id": student_id, "recommendations": recommendations}


@router.get("/api/neuro-memory/chunks/{student_id}")
async def get_memory_chunks(student_id: str, limit: int = 100):
    chunks = memory_engine.get_memory_chunks(student_id, limit=limit)
    return {"success": True, "student_id": student_id, "chunks": chunks}


@router.post("/api/neuro-memory/train")
async def train_neuro_memory_model(payload: TrainModelPayload = TrainModelPayload()):
    try:
        from datetime import datetime, timedelta
        import random

        dummy_chunks = []
        for i in range(200):
            chunk = {
                "content_type": "biometric" if i % 2 == 0 else "quiz_result",
                "timestamp": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                "content": {
                    "focus_score": random.uniform(0.3, 0.95),
                    "eye_aspect_ratio": random.uniform(0.2, 0.4),
                    "blink_rate": random.uniform(5, 25),
                    "head_movement": random.uniform(0, 0.5),
                    "yaw": random.uniform(-0.2, 0.2),
                    "pitch": random.uniform(-0.2, 0.2),
                    "eye_movement": random.uniform(0, 0.6),
                    "score": random.uniform(0.5, 1.0),
                    "duration_seconds": random.uniform(30, 300),
                    "difficulty_level": random.randint(1, 5),
                    "attempt_count": random.randint(1, 3),
                    "correct_answers": random.randint(5, 10),
                    "total_questions": 10,
                    "session_duration_seconds": random.uniform(300, 3600),
                    "learning_effectiveness": random.uniform(0.4, 0.95),
                },
            }
            dummy_chunks.append(chunk)

        print(f"[Neuro-Memory] Training dengan {len(dummy_chunks)} dummy samples")

        training_data = model_trainer.prepare_training_data(dummy_chunks)
        model_package = model_trainer.train_model(training_data)

        return {
            "success": True,
            "model_name": payload.model_name,
            "metrics": model_package["metrics"],
            "trained_at": model_package["trained_at"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal training model: {str(e)}")


@router.post("/api/neuro-memory/import-database")
async def import_from_database(payload: ImportDatabasePayload):
    try:
        db_path = Path(payload.db_path)
        count = memory_engine.import_from_neuro_client_database(db_path, payload.student_id)

        if count > 0:
            chunks = memory_engine.get_memory_chunks(payload.student_id, limit=count)
            for chunk in chunks:
                if "neuro_client" in chunk.chunk_id:
                    embedding_text = f"{chunk.content_type}: {str(chunk.content)}"
                    embedding = embedding_store.generate_embedding(embedding_text)
                    embedding_store.add_vector(
                        chunk_id=chunk.chunk_id,
                        student_id=payload.student_id,
                        vector=embedding,
                        metadata={"content_type": chunk.content_type, "source": "neuro_client_import"},
                    )

        return {"success": True, "imported_count": count, "student_id": payload.student_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mengimpor dari database: {str(e)}")


@router.post("/api/neuro-memory/import-archive")
async def import_from_archive(payload: ImportArchivePayload):
    try:
        archive_path = Path(payload.archive_path)
        count = memory_engine.import_from_archive(archive_path, payload.student_id)

        if count > 0:
            chunks = memory_engine.get_memory_chunks(payload.student_id, limit=count)
            for chunk in chunks:
                if "archive" in chunk.chunk_id:
                    embedding_text = f"{chunk.content_type}: {str(chunk.content)}"
                    embedding = embedding_store.generate_embedding(embedding_text)
                    embedding_store.add_vector(
                        chunk_id=chunk.chunk_id,
                        student_id=payload.student_id,
                        vector=embedding,
                        metadata={"content_type": chunk.content_type, "source": "archive_import"},
                    )

        return {"success": True, "imported_count": count, "student_id": payload.student_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mengimpor dari arsip: {str(e)}")


@router.post("/api/neuro-memory/predict")
async def predict_performance(payload: PredictPayload):
    try:
        model_package = model_trainer.load_model()
        if not model_package:
            raise HTTPException(status_code=404, detail="Model belum dilatih. Silakan training terlebih dahulu.")

        prediction = model_trainer.predict(model_package, payload.features)

        return {
            "success": True,
            "predicted_performance": prediction,
            "feature_names": model_package.get("feature_names", []),
            "model_trained_at": model_package.get("trained_at"),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal prediksi: {str(e)}")

