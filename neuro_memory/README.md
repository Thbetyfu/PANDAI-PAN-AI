
# Neuro-Memory Foundation Model
Modul Neuro-Memory untuk PANDAI Neurolearn - Foundation Model untuk personalisasi pembelajaran berbasis biometrik.

## Struktur Folder
```
neuro_memory/
├── __init__.py          # Package initialization
├── memory_engine.py     # Core memory logic dan profil kognitif
├── embedding_store.py   # Vector database untuk similarity search
├── model_trainer.py     # Training pipeline untuk foundation model
└── README.md            # Dokumentasi ini
```

## Komponen Utama

### 1. MemoryEngine
- Mengelola profil kognitif siswa
- Menyimpan dan mengambil memory chunks
- Analisis pola belajar
- **Sync dengan Neuro-Client-Siswa**:
  - Auto-import dari database `local_memory.db` saat pertama kali dijalankan
  - Import manual dari arsip `.csv.gz`
  - Import dari database via API endpoint

### 2. EmbeddingStore
- Menggunakan **sentence-transformers all-MiniLM-L6-v2** untuk embedding nyata
- Menggunakan **FAISS IndexFlatIP** untuk pencarian similarity yang cepat (optimized untuk ribuan/milyaran chunk)
- Fallback ke cosine similarity dasar jika FAISS tidak terinstall
- Fallback ke dummy embedding jika model tidak tersedia (offline mode)
- Persistensi index FAISS ke disk (`faiss_index.bin` + `faiss_metadata.json`), dengan JSONL sebagai backup

### 3. ModelTrainer
- **Neural Network (MLPRegressor)** dengan 3 layer Dense (128 → 64 → 32)
- Ekstraksi fitur yang lebih banyak (23 fitur): biometrics, quiz stats, content type encoding, temporal, dll
- Training loop dengan backpropagation (ditangani scikit-learn)
- **Evaluasi metrik lengkap**: MAE, RMSE, R² (untuk train & test set)
- StandardScaler untuk normalisasi fitur
- Early stopping untuk mencegah overfitting
- Simpan model dalam format **joblib/pickle** (production-ready)
- Anonimkan data untuk riset

## Endpoint API (di PAN-AI/server.py)
| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| POST | /api/neuro-memory/store | Simpan memory chunk baru |
| GET | /api/neuro-memory/profile/{student_id} | Dapatkan profil kognitif |
| POST | /api/neuro-memory/analyze/{student_id} | Analisis pola belajar |
| GET | /api/neuro-memory/recommendations/{student_id} | Rekomendasi personalisasi |
| GET | /api/neuro-memory/chunks/{student_id} | Riwayat memory chunks |
| POST | /api/neuro-memory/train | Latih model Neuro-Memory |
| POST | /api/neuro-memory/predict | Prediksi kinerja belajar |
| POST | /api/neuro-memory/import-database | Impor dari Neuro-Client-Siswa database |
| POST | /api/neuro-memory/import-archive | Impor dari arsip Neuro-Client-Siswa (.csv.gz) |

## Sync dengan Neuro-Client-Siswa
Neuro-Memory dapat mengimpor data lama dari Neuro-Client-Siswa dengan dua cara:

### 1. Auto-Import (Saat Pertama Kali Dijalankan)
MemoryEngine akan otomatis mencari database di path berikut:
- `../Siswa/Neuro-Client-Siswa/db/local_memory.db`
- `../../Siswa/Neuro-Client-Siswa/db/local_memory.db`
- `db/local_memory.db`

Jika database ditemukan, semua data `biometric_logs` dan `intervention_history` akan diimpor sebagai `MemoryChunk`. Setelah import selesai, file `.import_complete` dibuat di `neuro_memory_storage/` untuk menandakan import selesai.

### 2. Manual Import via API
Anda dapat mengimpor secara manual via endpoint API:

#### Impor dari Database
```bash
curl -X POST http://localhost:3002/api/neuro-memory/import-database \
  -H "Content-Type: application/json" \
  -d '{
    "db_path": "../Siswa/Neuro-Client-Siswa/db/local_memory.db",
    "student_id": "user_123"
  }'
```

#### Impor dari Arsip
```bash
curl -X POST http://localhost:3002/api/neuro-memory/import-archive \
  -H "Content-Type: application/json" \
  -d '{
    "archive_path": "../Siswa/Neuro-Client-Siswa/db/.archive/ready/ARCHIVE_20240101_120000.csv.gz",
    "student_id": "user_123"
  }'
```

## Penggunaan Client (Neuro-Client-Siswa)
```python
from ai.neuro_memory_client import NeuroMemoryClient

# Inisialisasi client
client = NeuroMemoryClient(student_id="12345")

# Simpan data biometrik
client.store_biometric_data(
    focus_score=0.85,
    ear=0.32,
    blink_rate=12,
    session_id="session_abc123"
)

# Dapatkan rekomendasi
recommendations = client.get_recommendations()

# Analisis pola belajar
analysis = client.analyze_patterns()
```

## Cara Instalasi Dependensi
Untuk menggunakan model embedding nyata, FAISS, dan neural network, install dependensi:
```bash
cd PAN-AI
pip install -r requirements.txt
```

- Model `all-MiniLM-L6-v2` akan otomatis di-download saat pertama kali dijalankan (sekitar 80MB)
- FAISS akan otomatis digunakan untuk pencarian similarity yang cepat

## Cara Training Model
1. Jalankan server PAN-AI: `python server.py`
2. Panggil endpoint `/api/neuro-memory/train` via POST request
3. Model akan disimpan ke `neuro_memory_storage/models/` sebagai `pandai_neuro_memory_v1.joblib`

## Catatan Backward Compatibility
- Data lama di `vectors.jsonl` tetap dapat dibaca
- FAISS index otomatis di-rebuild dari JSONL saat pertama kali dijalankan
- JSONL selalu disimpan sebagai backup untuk keamanan

## Roadmap Pengembangan
- [x] Integrasi model embedding nyata (sentence-transformers)
- [x] Upgrade ke FAISS untuk performa lebih baik
- [x] Neural network untuk prediksi kinerja
- [x] Sync dengan Neuro-Storage archive_manager.py
- [ ] Dashboard untuk visualisasi profil kognitif
