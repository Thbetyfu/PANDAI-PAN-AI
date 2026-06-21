
import numpy as np
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
import hashlib


@dataclass
class VectorEntry:
    vector_id: str
    chunk_id: str
    student_id: str
    vector: List[float]
    metadata: Dict[str, Any]


class EmbeddingStore:
    """
    Vector database untuk pencarian similarity memori kognitif.
    Menggunakan FAISS IndexFlatIP untuk performa tinggi (jika tersedia),
    fallback ke cosine similarity dasar jika FAISS tidak terinstall.
    """

    def __init__(self, storage_path: str = "./neuro_memory_storage/vectors", model_name: str = "all-MiniLM-L6-v2"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.vectors_path = self.storage_path / "vectors.jsonl"
        self.faiss_index_path = self.storage_path / "faiss_index.bin"
        self.faiss_metadata_path = self.storage_path / "faiss_metadata.json"
        
        # Inisialisasi storage
        self._vectors = {}  # vector_id -> VectorEntry
        self._index_to_id = []  # maps FAISS index position to vector_id
        self.faiss_available = False
        self.faiss_index = None
        
        # Coba load FAISS terlebih dahulu
        self._initialize_faiss()
        self._load_vectors()
        
        # Inisialisasi model embedding
        self.model = None
        self.model_available = False
        self._initialize_model(model_name)

    def _initialize_faiss(self) -> None:
        """Inisialisasi FAISS dengan fallback ke mode dasar jika gagal"""
        try:
            import faiss
            self.faiss_available = True
            print("[Neuro-Memory] FAISS berhasil dimuat!")
        except ImportError:
            self.faiss_available = False
            print("[Neuro-Memory] FAISS tidak ditemukan, menggunakan mode dasar.")

    def _initialize_model(self, model_name: str) -> None:
        """Inisialisasi sentence-transformers model dengan fallback ke dummy jika gagal"""
        try:
            print(f"[Neuro-Memory] Memuat model embedding: {model_name}...")
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
            self.model_available = True
            print("[Neuro-Memory] Model embedding berhasil dimuat!")
        except Exception as e:
            print(f"[Neuro-Memory] Gagal memuat model: {e}")
            print("[Neuro-Memory] Menggunakan fallback ke dummy embedding untuk offline mode.")
            self.model = None
            self.model_available = False

    def _load_vectors(self) -> None:
        """Load vectors dari disk, coba FAISS terlebih dahulu, fallback ke JSONL"""
        if self.faiss_available and self.faiss_index_path.exists() and self.faiss_metadata_path.exists():
            # Load dari FAISS
            try:
                import faiss
                self.faiss_index = faiss.read_index(str(self.faiss_index_path))
                with open(self.faiss_metadata_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                    self._vectors = {k: VectorEntry(**v) for k, v in metadata["vectors"].items()}
                    self._index_to_id = metadata["index_to_id"]
                print(f"[Neuro-Memory] Berhasil load {len(self._vectors)} vector dari FAISS.")
                return
            except Exception as e:
                print(f"[Neuro-Memory] Gagal load FAISS index: {e}, fallback ke JSONL.")
        
        # Fallback ke JSONL
        self._vectors = {}
        self._index_to_id = []
        if self.vectors_path.exists():
            with open(self.vectors_path, "r", encoding="utf-8") as f:
                for line in f:
                    data = json.loads(line.strip())
                    entry = VectorEntry(**data)
                    self._vectors[entry.vector_id] = entry
                    self._index_to_id.append(entry.vector_id)
            # Jika FAISS tersedia, rebuild index dari JSONL
            if self.faiss_available and self._vectors:
                self._rebuild_faiss_index()
            print(f"[Neuro-Memory] Berhasil load {len(self._vectors)} vector dari JSONL.")

    def _save_vectors(self) -> None:
        """Save vectors ke disk: FAISS + metadata (jika tersedia), atau JSONL"""
        # Selalu save JSONL sebagai backup
        with open(self.vectors_path, "w", encoding="utf-8") as f:
            for entry in self._vectors.values():
                f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
        
        # Save FAISS jika tersedia
        if self.faiss_available and self.faiss_index is not None:
            import faiss
            faiss.write_index(self.faiss_index, str(self.faiss_index_path))
            with open(self.faiss_metadata_path, "w", encoding="utf-8") as f:
                json.dump({
                    "vectors": {k: asdict(v) for k, v in self._vectors.items()},
                    "index_to_id": self._index_to_id
                }, f, ensure_ascii=False, indent=2)

    def _rebuild_faiss_index(self) -> None:
        """Rebuild FAISS index dari vector yang sudah ada di memory"""
        if not self.faiss_available or not self._vectors:
            return
        
        import faiss
        
        # Dapatkan dimensi vector dari entry pertama
        first_vector = next(iter(self._vectors.values())).vector
        dim = len(first_vector)
        
        # IndexFlatIP untuk cosine similarity (membutuhkan vector yang dinormalisasi)
        self.faiss_index = faiss.IndexFlatIP(dim)
        
        # Normalisasi semua vector dan add ke index
        vectors_np = np.array([
            self._normalize_vector(entry.vector) 
            for entry in self._vectors.values()
        ], dtype=np.float32)
        self.faiss_index.add(vectors_np)
        
        print(f"[Neuro-Memory] FAISS index berhasil dibangun dengan {len(self._vectors)} vector.")

    def _normalize_vector(self, vector: List[float]) -> np.ndarray:
        """Normalisasi vector L2 untuk cosine similarity dengan IndexFlatIP"""
        vec_np = np.array(vector, dtype=np.float32)
        norm = np.linalg.norm(vec_np)
        if norm == 0:
            return vec_np
        return vec_np / norm

    def _generate_vector_id(self, chunk_id: str) -> str:
        return hashlib.sha256(chunk_id.encode()).hexdigest()

    def add_vector(self, chunk_id: str, student_id: str, vector: List[float], metadata: Dict[str, Any] = None) -> str:
        vector_id = self._generate_vector_id(chunk_id)
        
        # Cegah duplikat
        if vector_id in self._vectors:
            print(f"[Neuro-Memory] Vector {vector_id} sudah ada, melewatkan.")
            return vector_id
        
        # Buat entry baru
        entry = VectorEntry(
            vector_id=vector_id,
            chunk_id=chunk_id,
            student_id=student_id,
            vector=vector,
            metadata=metadata or {}
        )
        
        # Tambah ke storage
        self._vectors[vector_id] = entry
        self._index_to_id.append(vector_id)
        
        # Tambah ke FAISS jika tersedia
        if self.faiss_available:
            if self.faiss_index is None:
                self._rebuild_faiss_index()
            else:
                normalized_vec = self._normalize_vector(vector).reshape(1, -1)
                self.faiss_index.add(normalized_vec)
        
        self._save_vectors()
        return vector_id

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        vec1_arr = np.array(vec1)
        vec2_arr = np.array(vec2)
        dot_product = np.dot(vec1_arr, vec2_arr)
        norm1 = np.linalg.norm(vec1_arr)
        norm2 = np.linalg.norm(vec2_arr)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)

    def search_similar(self, query_vector: List[float], student_id: Optional[str] = None, top_k: int = 10) -> List[Dict[str, Any]]:
        if not self._vectors:
            return []
        
        if self.faiss_available and self.faiss_index is not None:
            # Pencarian cepat dengan FAISS
            normalized_query = self._normalize_vector(query_vector).reshape(1, -1)
            scores, indices = self.faiss_index.search(normalized_query, min(top_k * 3, len(self._vectors)))
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0 or idx >= len(self._index_to_id):
                    continue
                vector_id = self._index_to_id[idx]
                entry = self._vectors.get(vector_id)
                if not entry:
                    continue
                # Filter by student_id jika diperlukan
                if student_id and entry.student_id != student_id:
                    continue
                results.append({
                    "vector_id": entry.vector_id,
                    "chunk_id": entry.chunk_id,
                    "similarity": float(score),
                    "metadata": entry.metadata
                })
                if len(results) >= top_k:
                    break
            return results
        
        # Fallback: pencarian dasar
        results = []
        for entry in self._vectors.values():
            if student_id and entry.student_id != student_id:
                continue
            similarity = self.cosine_similarity(query_vector, entry.vector)
            results.append({
                "vector_id": entry.vector_id,
                "chunk_id": entry.chunk_id,
                "similarity": float(similarity),
                "metadata": entry.metadata
            })
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    def get_vector_by_chunk(self, chunk_id: str) -> Optional[VectorEntry]:
        for entry in self._vectors.values():
            if entry.chunk_id == chunk_id:
                return entry
        return None

    def delete_vector(self, vector_id: str) -> bool:
        if vector_id not in self._vectors:
            return False
        
        del self._vectors[vector_id]
        
        # Rebuild FAISS index jika diperlukan (karena FAISS tidak mendukung delete efisien)
        if self.faiss_available:
            self._index_to_id = [vid for vid in self._index_to_id if vid != vector_id]
            self._rebuild_faiss_index()
        
        self._save_vectors()
        return True

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding menggunakan sentence-transformers jika tersedia,
        fallback ke dummy embedding untuk mode offline.
        Menghasilkan 384 dimensi sesuai all-MiniLM-L6-v2.
        """
        if self.model_available and self.model is not None:
            try:
                # Encode text dengan model nyata
                embedding = self.model.encode(text, convert_to_numpy=True)
                return list(embedding.astype(float))
            except Exception as e:
                print(f"[Neuro-Memory] Gagal generate embedding nyata: {e}, fallback ke dummy")
        
        # Fallback: Dummy embedding untuk offline/testing
        return self._generate_dummy_embedding(text)

    def _generate_dummy_embedding(self, text: str) -> List[float]:
        """
        Generate embedding dummy untuk testing/offline (384 dimensi)
        """
        hash_val = int(hashlib.sha256(text.encode()).hexdigest(), 16)
        np.random.seed(hash_val % (2**32))
        return list(np.random.randn(384).astype(float))

