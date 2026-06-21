
import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

# Optional imports for archive import
try:
    import sqlite3
    import gzip
    import csv
    from cryptography.fernet import Fernet
    ARCHIVE_AVAILABLE = True
except ImportError:
    ARCHIVE_AVAILABLE = False


@dataclass
class CognitiveProfile:
    """Profil kognitif individual siswa"""
    student_id: str
    learning_style: str  # visual, auditory, kinesthetic
    focus_peak_hours: List[str]  # ["08:00-10:00", "14:00-16:00"]
    typical_focus_duration: int  # dalam menit
    difficulty_patterns: Dict[str, float]  # {"aljabar": 0.8, "fisika": 0.3}
    intervention_history: List[Dict[str, Any]]
    last_updated: str


@dataclass
class MemoryChunk:
    """Satu unit memori kognitif"""
    chunk_id: str
    student_id: str
    session_id: Optional[str]
    timestamp: str
    content_type: str  # biometric, interaction, quiz_result
    content: Dict[str, Any]
    embedding: Optional[List[float]] = None


class MemoryEngine:
    """
    Core engine untuk mengelola memori kognitif siswa.
    Memproses data biometrik dan interaksi untuk membuat profil personalisasi.
    """

    def __init__(self, storage_path: str = "./neuro_memory_storage"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.profiles_path = self.storage_path / "profiles"
        self.chunks_path = self.storage_path / "chunks"
        self.import_marker = self.storage_path / ".import_complete"
        self.profiles_path.mkdir(exist_ok=True)
        self.chunks_path.mkdir(exist_ok=True)
        
        # Auto-import on first run
        self._auto_import_on_first_run()

    def _generate_chunk_id(self, content: Dict[str, Any]) -> str:
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()

    def store_memory_chunk(self, chunk: MemoryChunk) -> str:
        """Simpan satu unit memori ke storage"""
        if not chunk.chunk_id:
            chunk.chunk_id = self._generate_chunk_id(chunk.content)
        
        chunk_file = self.chunks_path / f"{chunk.chunk_id}.json"
        with open(chunk_file, "w", encoding="utf-8") as f:
            json.dump(asdict(chunk), f, ensure_ascii=False, indent=2)
        
        return chunk.chunk_id

    def get_student_profile(self, student_id: str) -> Optional[CognitiveProfile]:
        """Dapatkan profil kognitif siswa berdasarkan ID"""
        profile_file = self.profiles_path / f"{student_id}.json"
        if profile_file.exists():
            with open(profile_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return CognitiveProfile(**data)
        return None

    def update_student_profile(self, profile: CognitiveProfile) -> None:
        """Perbarui profil kognitif siswa"""
        profile.last_updated = datetime.now().isoformat()
        profile_file = self.profiles_path / f"{profile.student_id}.json"
        with open(profile_file, "w", encoding="utf-8") as f:
            json.dump(asdict(profile), f, ensure_ascii=False, indent=2)

    def create_initial_profile(self, student_id: str) -> CognitiveProfile:
        """Buat profil kognitif awal untuk siswa baru"""
        return CognitiveProfile(
            student_id=student_id,
            learning_style="unknown",
            focus_peak_hours=[],
            typical_focus_duration=20,
            difficulty_patterns={},
            intervention_history=[],
            last_updated=datetime.now().isoformat()
        )

    def get_memory_chunks(self, student_id: str, limit: int = 100) -> List[MemoryChunk]:
        """Dapatkan riwayat memori untuk siswa tertentu"""
        chunks = []
        for chunk_file in sorted(self.chunks_path.glob("*.json"), reverse=True):
            with open(chunk_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data["student_id"] == student_id:
                    chunks.append(MemoryChunk(**data))
                    if len(chunks) >= limit:
                        break
        return chunks

    def analyze_learning_pattern(self, student_id: str) -> Dict[str, Any]:
        """Analisis pola belajar siswa dari riwayat memori"""
        chunks = self.get_memory_chunks(student_id, limit=200)
        profile = self.get_student_profile(student_id) or self.create_initial_profile(student_id)
        
        # Analisis sederhana - akan diperluas saat training model
        focus_times = {}
        for chunk in chunks:
            if chunk.content_type == "biometric" and "focus_score" in chunk.content:
                hour = chunk.timestamp.split("T")[1].split(":")[0]
                focus_times[hour] = focus_times.get(hour, []) + [chunk.content["focus_score"]]
        
        # Hitung peak hours
        peak_hours = []
        for hour, scores in focus_times.items():
            avg_score = sum(scores) / len(scores)
            if avg_score > 0.7:
                peak_hours.append(f"{hour}:00-{int(hour)+2}:00")
        
        profile.focus_peak_hours = list(set(peak_hours))
        self.update_student_profile(profile)
        
        return {
            "student_id": student_id,
            "peak_focus_hours": peak_hours,
            "total_memories": len(chunks),
            "profile_updated": profile.last_updated
        }

    def _auto_import_on_first_run(self):
        """Auto-import data lama jika belum pernah diimpor sebelumnya"""
        if self.import_marker.exists():
            return
        
        print("[Neuro-Memory] Auto-import data pertama kali...")
        
        # Coba import dari database Neuro-Client-Siswa terlebih dahulu
        import_count = 0
        try:
            # Path database default Neuro-Client-Siswa
            possible_db_paths = [
                Path("../Siswa/Neuro-Client-Siswa/db/local_memory.db"),
                Path("../../Siswa/Neuro-Client-Siswa/db/local_memory.db"),
                Path("db/local_memory.db"),
            ]
            
            for db_path in possible_db_paths:
                if db_path.exists():
                    count = self.import_from_neuro_client_database(db_path)
                    import_count += count
                    if count > 0:
                        break
            
            # Tandai import selesai
            with open(self.import_marker, "w") as f:
                f.write(datetime.now().isoformat())
            
            print(f"[Neuro-Memory] Auto-import selesai: {import_count} chunks diimpor")
        except Exception as e:
            print(f"[Neuro-Memory] Auto-import gagal: {e}")

    def import_from_neuro_client_database(self, db_path: Path, student_id: Optional[str] = None) -> int:
        """
        Impor data dari database Neuro-Client-Siswa (local_memory.db)
        """
        if not ARCHIVE_AVAILABLE:
            print("[Neuro-Memory] Library untuk import tidak tersedia (sqlite3, gzip, csv, cryptography)")
            return 0
        
        if not db_path.exists():
            print(f"[Neuro-Memory] Database tidak ditemukan: {db_path}")
            return 0
        
        # Jika student_id tidak ditentukan, coba dapatkan dari struktur direktori
        if not student_id:
            student_id = "NEURO_CLIENT_USER"
        
        count = 0
        conn = None
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Ambil semua data biometric_logs
            cursor.execute("SELECT id, timestamp, ear_score, attention_index, cognitive_load, heart_rate, emotion_state FROM biometric_logs ORDER BY id ASC")
            rows = cursor.fetchall()
            
            # Dapatkan nama kolom untuk referensi
            col_names = [desc[0] for desc in cursor.description]
            
            for row in rows:
                # Konversi ke MemoryChunk
                chunk_content = {
                    "focus_score": float(row[3]) if row[3] is not None else 0.5,
                    "eye_aspect_ratio": float(row[2]) if row[2] is not None else 0.3,
                    "cognitive_load": float(row[4]) if row[4] is not None else 0.5,
                    "heart_rate": float(row[5]) if row[5] is not None else 75,
                    "emotion_state": str(row[6]) if row[6] is not None else "NORMAL"
                }
                
                timestamp = row[1] if row[1] else datetime.now().isoformat()
                
                # Konversi timestamp ke ISO jika perlu
                if " " in timestamp and "T" not in timestamp:
                    timestamp = timestamp.replace(" ", "T")
                
                chunk = MemoryChunk(
                    chunk_id=f"neuro_client_{row[0]}",
                    student_id=student_id,
                    session_id="NEURO_CLIENT_IMPORT",
                    timestamp=timestamp,
                    content_type="biometric",
                    content=chunk_content
                )
                
                self.store_memory_chunk(chunk)
                count += 1
            
            # Juga impor intervention_history
            cursor.execute("SELECT id, timestamp, trigger_reason, action_taken FROM intervention_history ORDER BY id ASC")
            intervention_rows = cursor.fetchall()
            
            for row in intervention_rows:
                chunk_content = {
                    "trigger_reason": str(row[2]) if row[2] else "",
                    "action_taken": str(row[3]) if row[3] else ""
                }
                
                timestamp = row[1] if row[1] else datetime.now().isoformat()
                if " " in timestamp and "T" not in timestamp:
                    timestamp = timestamp.replace(" ", "T")
                
                chunk = MemoryChunk(
                    chunk_id=f"neuro_client_intervention_{row[0]}",
                    student_id=student_id,
                    session_id="NEURO_CLIENT_IMPORT",
                    timestamp=timestamp,
                    content_type="interaction",
                    content=chunk_content
                )
                
                self.store_memory_chunk(chunk)
                count += 1
            
            print(f"[Neuro-Memory] Berhasil mengimpor {count} chunks dari database")
            return count
        except Exception as e:
            print(f"[Neuro-Memory] Gagal mengimpor dari database: {e}")
            return 0
        finally:
            if conn:
                conn.close()

    def import_from_archive(self, archive_path: Path, student_id: Optional[str] = None) -> int:
        """
        Impor data dari arsip Neuro-Client-Siswa (.csv.gz atau .crypt)
        Catatan: Fungsi ini membutuhkan kunci enkripsi untuk .crypt files
        """
        if not ARCHIVE_AVAILABLE:
            print("[Neuro-Memory] Library untuk import tidak tersedia")
            return 0
        
        if not archive_path.exists():
            print(f"[Neuro-Memory] Arsip tidak ditemukan: {archive_path}")
            return 0
        
        if not student_id:
            student_id = "ARCHIVE_USER"
        
        count = 0
        
        try:
            # Jika file adalah .csv.gz (tidak terenkripsi)
            if archive_path.suffix == ".gz" and archive_path.name.endswith(".csv.gz"):
                with gzip.open(archive_path, "rt", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for idx, csv_row in enumerate(reader):
                        # Konversi dari CSV ke MemoryChunk
                        chunk_content = {}
                        if "ear_score" in csv_row:
                            chunk_content["eye_aspect_ratio"] = float(csv_row["ear_score"]) if csv_row["ear_score"] else 0.3
                        if "attention_index" in csv_row:
                            chunk_content["focus_score"] = float(csv_row["attention_index"]) if csv_row["attention_index"] else 0.5
                        if "cognitive_load" in csv_row:
                            chunk_content["cognitive_load"] = float(csv_row["cognitive_load"]) if csv_row["cognitive_load"] else 0.5
                        if "heart_rate" in csv_row:
                            chunk_content["heart_rate"] = float(csv_row["heart_rate"]) if csv_row["heart_rate"] else 75
                        if "emotion_state" in csv_row:
                            chunk_content["emotion_state"] = str(csv_row["emotion_state"]) if csv_row["emotion_state"] else "NORMAL"
                        
                        timestamp = csv_row.get("timestamp", datetime.now().isoformat())
                        if " " in timestamp and "T" not in timestamp:
                            timestamp = timestamp.replace(" ", "T")
                        
                        chunk = MemoryChunk(
                            chunk_id=f"archive_{archive_path.stem}_{idx}",
                            student_id=student_id,
                            session_id="ARCHIVE_IMPORT",
                            timestamp=timestamp,
                            content_type="biometric",
                            content=chunk_content
                        )
                        
                        self.store_memory_chunk(chunk)
                        count += 1
            
            print(f"[Neuro-Memory] Berhasil mengimpor {count} chunks dari arsip")
            return count
        except Exception as e:
            print(f"[Neuro-Memory] Gagal mengimpor dari arsip: {e}")
            return 0
