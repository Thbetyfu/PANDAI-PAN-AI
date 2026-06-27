# Dokumentasi Status dan Rencana Pengembangan PAN-AI

Dokumen ini dibuat sebagai referensi kerja untuk memahami kondisi PAN-AI saat ini, bagian yang belum selesai, integrasi API yang belum masuk, evaluasi teknis terhadap TTS, struktur folder, fungsi file/folder utama, dan pendekatan arsitektur yang sedang dipakai.

Tanggal pembaruan: 2026-06-23

---

## 1. Ringkasan Eksekutif

PAN-AI saat ini sudah berkembang menjadi layanan FastAPI yang berfungsi sebagai pusat orkestrasi untuk:

- Neuro-Language-Tutor
- Hermes Memory v2
- Neuro-Memory
- skill OpenClaw
- UI interaktif siswa dengan maskot
- pemilihan mode LLM lokal/cloud
- pemilihan mode TTS local/api/auto

Secara umum, fondasi sistem sudah berjalan dan sudah cukup untuk tahap pilot/internal testing. Namun, masih ada beberapa area yang belum selesai atau masih bersifat template, terutama pada:

- orkestrasi skill yang belum benar-benar agentic penuh
- integrasi provider cloud yang belum aktif
- kualitas TTS yang masih belum natural
- sinkronisasi dokumentasi lama dengan implementasi baru
- standardisasi arsitektur agar semua modul memakai jalur konfigurasi yang sama

---

## 2. Kondisi Sistem Saat Ini

### 2.1 Yang Sudah Berjalan

Berikut bagian yang saat ini sudah ada dan aktif di codebase:

1. FastAPI gateway terpusat di `server.py`
2. UI siswa berbasis `ui.html`
3. Neuro-Language-Tutor untuk chat, latihan vocab, grammar, progress, TTS, dan STT
4. LLM routing yang mendukung:
   - Ollama lokal
   - OpenAI-compatible cloud API
   - fallback mode
5. Hermes Memory v2 berbasis file JSON dengan metadata dan version history
6. Neuro-Memory untuk cognitive profile, memory chunks, embeddings, similarity search, dan training model
7. Skill layer untuk feedback, memory retrieval, mascot, quiz, biometrics, dan tutor
8. Selector mode TTS:
   - `local`
   - `api`
   - `auto`
9. Selector mode LLM:
   - local/gpu
   - api/cloud
   - auto

### 2.2 Status Operasional Singkat

- LLM lokal via Ollama: sudah bisa dipakai
- LLM cloud via OpenAI-compatible API: jalur kodenya sudah ada, tetapi API key belum dimasukkan
- TTS local: sudah jalan memakai `pyttsx3`
- TTS API/cloud: masih template generik HTTP, belum diikat ke provider final
- STT: sudah ada lewat Whisper
- Memory personalisasi: sudah aktif melalui Hermes summary dan Neuro-Memory
- UI: sudah ada dan usable, tetapi masih single-file dan belum modular

---

## 3. Bagian yang Belum Selesai

Bagian di bawah ini penting dicatat karena berpengaruh langsung ke roadmap teknis berikutnya.

### 3.1 Skill Orchestrator Belum Selesai Penuh

File: `skills/skill_orchestrator.py`

Status saat ini:

- intent recognition masih berbasis regex/keyword matching
- hasil orkestrasi masih berupa rekomendasi skill
- belum ada chaining skill yang benar-benar dinamis dan context-aware
- belum ada penilaian confidence score berbasis model
- belum ada memory-aware planning yang matang

Artinya, modul ini sudah cukup untuk demo sederhana, tetapi belum bisa disebut orchestrator agent penuh.

### 3.2 Integrasi TTS Masih Tahap Fondasi

File utama: `neuro_language_tutor/speech_handler.py`

Status saat ini:

- local TTS memakai `pyttsx3`
- api TTS masih template generic HTTP
- belum ada voice cloning
- belum ada persona voice tuning
- belum ada fallback bertingkat yang cerdas per kualitas dan latency
- belum ada streaming TTS

### 3.3 Kualitas TTS Saat Ini Belum Memuaskan

Ini perlu dicatat secara eksplisit:

- suara TTS saat ini masih terdengar terlalu sintetis / terlalu "AI"
- kualitas ini masih cukup untuk fallback offline atau testing internal
- kualitas ini belum ideal untuk pengalaman tutor yang hangat, natural, dan premium

Kesimpulan jujur:

> TTS sekarang berfungsi secara teknis, tetapi belum memenuhi standar pengalaman suara yang diinginkan untuk produk PAN-AI.

### 3.4 Integrasi LLM Belum Sepenuhnya Seragam

Catatan:

- `neuro_language_tutor/llm_handler.py` sudah memakai pendekatan hybrid lokal/cloud
- tetapi `skills/generate_quiz.py` masih memanggil Ollama secara langsung lewat URL hardcoded
- ini berarti belum semua fitur memakai jalur routing LLM yang sama

Dampaknya:

- konfigurasi menjadi tidak sepenuhnya konsisten
- maintenance lebih sulit
- fallback behavior berbeda antar fitur

### 3.5 Dokumentasi Lama Belum Sinkron

File terdampak:

- `README.md`
- `ROADMAP.md`

Masalah:

- masih menampilkan gambaran arsitektur lama
- masih merujuk backend Express sebagai bagian utama alur, sementara repo ini sekarang berpusat pada FastAPI service
- belum memuat status hybrid LLM
- belum memuat status hybrid TTS
- belum memuat UI siswa terbaru
- belum memuat endpoint dan struktur runtime terbaru

### 3.6 Testing Masih Terbatas

File yang ada:

- `test_language_tutor.py`

Kondisi:

- ada test dasar
- belum ada coverage menyeluruh untuk:
  - TTS mode switching
  - LLM provider switching
  - orchestrator execute flow
  - Hermes v2 endpoint regression
  - UI integration behavior

### 3.7 UI Masih Monolitik

File:

- `ui.html`

Status:

- mudah dijalankan
- cocok untuk prototyping cepat
- tetapi semakin sulit dipelihara jika fitur bertambah besar

Belum ada:

- pemisahan komponen
- asset pipeline frontend
- state management yang rapi
- struktur design system terpisah

---

## 4. API dan Integrasi yang Belum Dimasukkan

Bagian ini menjawab langsung pertanyaan: API apa saja yang belum masuk ke sistem.

### 4.1 TTS Cloud Provider Final Belum Diintegrasikan

Saat ini yang ada baru template generik:

- `PANDAI_TTS_API_URL`
- `PANDAI_TTS_API_KEY`
- `PANDAI_TTS_API_VOICE`
- `PANDAI_TTS_API_FORMAT`

Artinya, provider final belum benar-benar dimasukkan.

Contoh provider yang belum diintegrasikan secara spesifik:

- ElevenLabs
- Google Cloud Text-to-Speech
- Azure Speech
- Cartesia
- Deepgram Aura

Catatan arah saat ini:

- rekomendasi paling kuat untuk kualitas tutor premium tetap mengarah ke ElevenLabs
- tetapi implementasi resminya belum dilakukan

### 4.2 API Key LLM Cloud Belum Dimasukkan

Jalur kode sudah ada untuk provider OpenAI-compatible, tetapi saat ini belum teraktivasi penuh karena API key belum diisi.

Environment yang disiapkan:

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`
- `PANDAI_LLM_ORDER`

Ini berarti:

- fondasi cloud LLM sudah ada
- tetapi integrasi production belum selesai

### 4.3 Model Suara Lokal Lanjutan Belum Masuk

Model suara lokal kualitas tinggi yang sempat didiskusikan belum masuk ke codebase.

Yang sempat dibahas:

- MisoTTS / model sejenis

Catatan penting teknis:

- yang dibahas ini sebenarnya ranah TTS, bukan LLM murni
- sempat disebut sebagai "LLM mimo/miso", tetapi secara teknis tujuan utamanya adalah voice generation, bukan text reasoning
- keputusan final masih belum diambil

Alasan belum dimasukkan:

- risiko bentrok dependency
- kebutuhan Python/runtime yang berbeda
- potensi kebutuhan hardware/VRAM yang tinggi
- belum ada keputusan final apakah tetap memilih local advanced TTS atau cloud premium TTS

### 4.4 API Real-Time Belum Tersedia

Saat ini belum ada endpoint real-time berbasis:

- WebSocket
- Server-Sent Events
- MQTT integration endpoint yang benar-benar aktif di `server.py`

Padahal, untuk tahap lanjut PANDAI, real-time channel akan penting untuk:

- streaming status belajar
- streaming audio response
- sinkronisasi state siswa/guru
- notifikasi biometrik real-time

### 4.5 API Auth dan Quota Belum Ada di Service Ini

Dokumentasi lama masih menyebut backend Express yang menangani:

- auth
- quota
- role management

Tetapi di repo `PAN-AI` saat ini, service FastAPI ini belum memiliki endpoint native untuk:

- login/auth
- quota management
- RBAC
- multi-tenant governance

Artinya, jika PAN-AI ingin berdiri lebih mandiri, bagian ini masih perlu dikembangkan.

---

## 5. Catatan Khusus Tentang TTS

Bagian ini sengaja ditulis eksplisit karena menjadi concern utama.

### 5.1 Kondisi Sekarang

TTS saat ini:

- sudah berjalan
- sudah cukup stabil untuk local fallback
- masih terdengar terlalu AI / robotik
- belum memberikan nuansa suara tutor yang natural

### 5.2 Posisi Keputusan Saat Ini

Keputusan sementara yang paling sehat secara engineering adalah:

1. mempertahankan hybrid TTS
2. local TTS dipakai sebagai fallback/offline mode
3. cloud TTS premium dipakai untuk kualitas pengalaman yang lebih baik

### 5.3 Arah Pengembangan Berikutnya

Pengembangan ke depan untuk area suara akan berfokus pada dua jalur:

#### Jalur A - Cloud Premium TTS

Tujuan:

- suara lebih natural
- cocok untuk persona guru "tegas tapi hangat"
- stabil untuk produksi

Kandidat utama:

- ElevenLabs

#### Jalur B - Eksplorasi Local Advanced Voice Model

Tujuan:

- mengurangi ketergantungan cloud
- menjaga opsi offline/high-privacy deployment

Status:

- masih tahap eksplorasi
- belum menjadi keputusan final
- masih perlu dipikirkan lebih lanjut

Catatan penting:

> Jika nanti ingin mengejar kualitas suara yang benar-benar natural, kemungkinan besar TTS premium cloud akan lebih cepat memberi hasil dibanding memaksa local offline TTS di tahap sekarang.

### 5.4 Catatan Tentang "LLM Mimo/Miso"

Supaya tidak rancu:

- yang dibahas untuk peningkatan suara bukan sekadar LLM biasa
- yang relevan justru model TTS/voice model yang lebih advanced
- opsi seperti MisoTTS atau model sejenis masih akan dipikirkan
- keputusan final belum ditetapkan ke dalam roadmap implementasi aktif

Dengan kata lain:

> Rencana pengembangan suara ke depan masih terbuka, tetapi arah besar saat ini adalah meningkatkan naturalness suara karena TTS sekarang belum memuaskan.

---

## 6. Pendekatan Arsitektur yang Digunakan

### 6.1 Pendekatan Umum

PAN-AI saat ini memakai pendekatan modular service dengan satu gateway utama:

- FastAPI sebagai API gateway/service host
- package terpisah untuk domain utama
- skill layer sebagai adaptor pemanggilan fungsi
- file-based persistence untuk memori dan runtime state
- opsi hybrid lokal/cloud untuk model AI

### 6.2 Pola yang Terlihat di Codebase

#### A. Gateway-Centric Service

Semua endpoint utama dipusatkan di `server.py`.

Kelebihan:

- mudah dijalankan
- cepat untuk prototyping
- sederhana untuk debugging

Kekurangan:

- file gateway menjadi besar
- tanggung jawab banyak terkumpul di satu file

#### B. Domain Modularization

Domain besar dipisah menjadi:

- `neuro_language_tutor/`
- `neuro_memory/`
- `skills/`
- `assets/`
- `memories/`

Ini merupakan pendekatan yang baik untuk scaling bertahap.

#### C. Hybrid AI Routing

Pendekatan yang dipakai:

- local-first bila tersedia
- cloud-capable bila dikonfigurasi
- fallback bila provider utama gagal

Ini adalah pendekatan pragmatis dan cocok untuk kondisi development sekarang.

#### D. File-Based Storage First

Memori dan state masih banyak disimpan dalam:

- JSON
- JSONL
- file audio
- file SVG

Kelebihan:

- cepat dibangun
- transparan untuk debugging
- minim infrastruktur

Kekurangan:

- kurang ideal untuk concurrency tinggi
- akan sulit ketika user bertambah besar

### 6.3 Kesimpulan Pendekatan

Pendekatan yang digunakan saat ini paling tepat disebut:

> modular monolith service dengan hybrid AI integration dan file-based persistence.

Ini bukan microservices penuh, tetapi juga bukan struktur satu file tanpa batas. Untuk tahap sekarang, pendekatan ini masih masuk akal.

---

## 7. Struktur Folder dan Fungsi Folder/File

Bagian ini menjelaskan fungsi folder dan file utama yang ada di repo.

### 7.1 Root Project

#### `server.py`

Fungsi:

- entry point utama FastAPI
- mendefinisikan endpoint API
- menghubungkan skill, memory, tutor, TTS, STT, mascot, orchestrator
- menyediakan endpoint konfigurasi LLM/TTS
- menyajikan UI `ui.html`

#### `ui.html`

Fungsi:

- antarmuka siswa
- chat dengan tutor
- selector mode LLM
- selector mode TTS
- pemanggilan TTS/STT dari browser
- tampilan maskot dan status interaksi

#### `requirements.txt`

Fungsi:

- daftar dependensi Python utama proyek

Dependensi penting:

- `fastapi`
- `uvicorn`
- `requests`
- `sentence-transformers`
- `faiss-cpu`
- `openai-whisper`
- `gTTS`
- `pyttsx3`

#### `README.md`

Fungsi:

- dokumentasi proyek lama / gambaran arsitektur awal

Catatan:

- perlu disinkronkan karena belum merefleksikan implementasi terbaru

#### `ROADMAP.md`

Fungsi:

- roadmap lama tingkat tinggi

Catatan:

- belum memuat detail status implementasi terbaru

#### `test_language_tutor.py`

Fungsi:

- test dasar untuk modul language tutor

#### `PAN_AI_Colab_Setup.py`

Fungsi:

- script setup untuk environment tertentu

#### `pan_ai_experiment.ipynb`

Fungsi:

- notebook eksperimen / eksplorasi

---

### 7.2 Folder `assets/`

Fungsi:

- menyimpan asset visual statis

#### `assets/mascot/siswa/`

Fungsi:

- menyimpan ekspresi maskot siswa dalam format SVG

File utama:

- `Happy.svg`
- `Idle.svg`
- `Menyapa.svg`
- `Bingung.svg`
- `Ngantuk.svg`
- `Nangis.svg`
- `Marah.svg`
- `Suprise.svg`

---

### 7.3 Folder `config/`

#### `config/openclaw_config.yaml`

Fungsi:

- tempat konfigurasi OpenClaw / skill orchestration

---

### 7.4 Folder `memories/`

Fungsi:

- menyimpan memori Hermes per siswa

Contoh:

- `memories/SISWA_001/HERMES_USER.json`
- `memories/SISWA_001/HERMES_LEARNING.json`

Kegunaan:

- personalisasi belajar
- tracking profile siswa
- log pembelajaran

---

### 7.5 Folder `neuro_language_tutor/`

Fungsi:

- domain utama untuk tutor bahasa interaktif

#### `neuro_language_tutor/__init__.py`

Fungsi:

- export package untuk `LanguageChatHandler`, `LessonGenerator`, `ProgressTracker`, `SpeechHandler`, dan `LLMHandler`

#### `neuro_language_tutor/chat_handler.py`

Fungsi:

- menyimpan riwayat chat siswa
- generate response tutor
- menyimpan correction dan explanation
- persist conversation ke JSON

#### `neuro_language_tutor/lesson_generator.py`

Fungsi:

- membuat lesson vocab
- membuat latihan grammar
- menyimpan/menyediakan default vocabulary dataset

#### `neuro_language_tutor/progress_tracker.py`

Fungsi:

- melacak progres vocab
- menghitung lesson completion
- menyimpan summary progres per siswa

#### `neuro_language_tutor/speech_handler.py`

Fungsi:

- STT dengan Whisper
- TTS local/api/auto
- expose status provider TTS ke backend/UI
- menyimpan file audio hasil generate

#### `neuro_language_tutor/llm_handler.py`

Fungsi:

- routing LLM lokal/cloud
- cek ketersediaan Ollama
- panggil OpenAI-compatible API
- bangun prompt tutor
- parse response tutor menjadi:
  - jawaban utama
  - correction
  - explanation

---

### 7.6 Folder `neuro_memory/`

Fungsi:

- fondasi memory intelligence dan personalisasi berbasis cognitive data

#### `neuro_memory/__init__.py`

Fungsi:

- package export untuk modul Neuro-Memory

#### `neuro_memory/README.md`

Fungsi:

- dokumentasi internal domain Neuro-Memory

#### `neuro_memory/memory_engine.py`

Fungsi:

- menyimpan memory chunks
- menyimpan dan memperbarui cognitive profile siswa
- analisis pola belajar sederhana
- auto-import data dari Neuro-Client lama

#### `neuro_memory/embedding_store.py`

Fungsi:

- membuat dan menyimpan embedding memory
- similarity search
- integrasi FAISS
- fallback ke mode non-FAISS

#### `neuro_memory/model_trainer.py`

Fungsi:

- training model prediksi berbasis memory chunks
- ekstraksi fitur
- scaling data
- evaluasi metrik
- simpan model hasil training

---

### 7.7 Folder `neuro_memory_storage/`

Fungsi:

- penyimpanan runtime hasil proses sistem

Isi penting:

- audio hasil TTS
- `conversations.json`
- `default_vocab.json`
- marker import lama

Folder ini adalah storage runtime, bukan source code.

---

### 7.8 Folder `skills/`

Fungsi:

- layer adaptor skill yang menghubungkan logic domain ke endpoint atau orchestration

#### `skills/__init__.py`

Fungsi:

- package initialization

#### `skills/digital_twin.py`

Fungsi:

- versi lama / compatibility layer untuk memory berbasis `USER.md` dan `MEMORY.md`
- load dan update memori siswa format lama

#### `skills/evaluate_biometrics.py`

Fungsi:

- klasifikasi state siswa dari biometrik
- contoh state:
  - `NORMAL`
  - `MENGANTUK`
  - `STRES`
  - `FRUSTRASI`

#### `skills/generate_quiz.py`

Fungsi:

- generate kuis terstruktur lewat Ollama

Catatan:

- masih direct call ke Ollama
- belum mengikuti jalur hybrid LLM router secara penuh

#### `skills/hermes_memory_v2.py`

Fungsi:

- implementasi Hermes Memory v2
- profil siswa JSON
- learning log JSON
- version history
- backward compatibility ke format lama

#### `skills/language_tutor_skill.py`

Fungsi:

- wrapper skill untuk chat tutor
- generate lesson
- update progress
- TTS
- STT
- history management

#### `skills/mascot_skill.py`

Fungsi:

- memetakan state/feedback ke ekspresi maskot
- memilih ekspresi random
- memilih ekspresi untuk jawaban benar/salah

#### `skills/memory_retrieval_skill.py`

Fungsi:

- search memory
- ambil summary memory
- analisis learning pattern
- rekomendasi personal

#### `skills/feedback_generator_skill.py`

Fungsi:

- generate feedback jawaban
- feedback hasil kuis
- feedback progres
- encouragement untuk siswa

#### `skills/skill_orchestrator.py`

Fungsi:

- mengenali intent user
- memetakan intent ke skill recommendation

Catatan:

- belum menjadi orchestrator penuh

---

## 8. Endpoint Utama yang Saat Ini Sudah Ada

Secara singkat, `server.py` saat ini sudah menyediakan kelompok endpoint berikut:

- root/UI:
  - `/`
  - `/ui`

- biometrics:
  - `/api/evaluate-biometrics`

- Hermes v2:
  - `/api/hermes/v2/profile/{student_id}`
  - `/api/hermes/v2/learning-log/{student_id}`
  - `/api/hermes/v2/summary/{student_id}`

- quiz:
  - `/api/generate-quiz`

- Neuro-Memory:
  - `/api/neuro-memory/store`
  - `/api/neuro-memory/profile/{student_id}`
  - `/api/neuro-memory/analyze/{student_id}`
  - `/api/neuro-memory/recommendations/{student_id}`
  - `/api/neuro-memory/chunks/{student_id}`
  - `/api/neuro-memory/train`
  - `/api/neuro-memory/import-database`
  - `/api/neuro-memory/import-archive`
  - `/api/neuro-memory/predict`

- language tutor:
  - `/api/language-tutor/chat`
  - `/api/language-tutor/generate-vocab-lesson`
  - `/api/language-tutor/generate-grammar-lesson`
  - `/api/language-tutor/progress/{student_id}`
  - `/api/language-tutor/text-to-speech`
  - `/api/language-tutor/speech-to-text`

- mascot:
  - `/api/mascot/siswa/expressions`
  - `/api/mascot/siswa/{expression}`

- skill endpoints:
  - `/api/skills/feedback/...`
  - `/api/skills/memory/...`
  - `/api/skills/language-tutor/...`
  - `/api/skills/mascot/...`

- orchestrator:
  - `/api/orchestrator/recognize-intent`
  - `/api/orchestrator/orchestrate`
  - `/api/orchestrator/execute`
  - `/api/orchestrator/get-skills-for-intent`

- config:
  - `/api/config/llm`

---

## 9. Rencana Pengembangan ke Depan

Bagian ini adalah roadmap realistis yang lebih dekat ke kondisi codebase saat ini.

### Prioritas 1 - Rapikan Fondasi dan Dokumentasi

Target:

- sinkronkan `README.md` dengan implementasi sekarang
- sinkronkan `ROADMAP.md` dengan status nyata
- tambahkan health-check dan status endpoint
- kurangi konfigurasi yang tersebar

### Prioritas 2 - Selesaikan Hybrid TTS

Target:

- integrasi provider TTS cloud final
- voice persona yang lebih natural
- opsi pemilihan suara yang jelas
- fallback policy yang stabil

Target kualitas:

- suara tidak lagi terdengar terlalu AI
- cocok untuk tutor edukasi

### Prioritas 3 - Selesaikan Hybrid LLM Secara Konsisten

Target:

- semua fitur memakai satu jalur routing LLM
- quiz generation tidak lagi hardcoded direct ke Ollama
- provider switching seragam antar modul

### Prioritas 4 - Upgrade Skill Orchestrator

Target:

- intent recognition lebih cerdas
- chaining skill nyata
- penggunaan context dari memory
- rekomendasi langkah berikutnya yang lebih agentic

### Prioritas 5 - UI dan Frontend Architecture

Target:

- pecah `ui.html` menjadi struktur frontend yang lebih mudah dirawat
- pisahkan style, script, dan komponen
- rapikan state dan event flow

### Prioritas 6 - Real-Time dan Observability

Target:

- streaming update
- monitoring health service
- logs dan error reporting yang lebih rapi

### Prioritas 7 - Keputusan Final untuk Voice Stack

Target:

- putuskan apakah jalur utama suara masa depan adalah:
  - cloud premium TTS
  - local advanced TTS
  - hybrid permanen

Catatan:

- opsi seperti MisoTTS / model sejenis masih akan dipikirkan
- belum menjadi keputusan implementasi final saat dokumen ini dibuat

---

## 10. Rekomendasi Teknis Saya

Jika ingin pengembangan berjalan rapi, urutan terbaiknya adalah:

1. selesaikan dokumentasi dan standardisasi config
2. tetapkan provider TTS cloud final
3. rapikan seluruh jalur LLM agar konsisten
4. upgrade orchestrator
5. modularisasi UI

Alasan:

- suara adalah gap pengalaman paling terasa saat ini
- orchestrator baru akan benar-benar bernilai jika input/output AI sudah konsisten
- frontend akan lebih mudah dikembangkan setelah kontrak backend stabil

---

## 11. Kesimpulan Akhir

PAN-AI saat ini sudah memiliki fondasi yang kuat untuk:

- tutor bahasa personal
- memory-aware interaction
- hybrid AI routing
- UI siswa interaktif

Namun, sistem ini belum selesai penuh. Area paling penting yang masih harus dikembangkan adalah:

- kualitas TTS
- integrasi API/provider final
- konsistensi routing AI
- orchestrator yang lebih cerdas
- dokumentasi dan struktur maintainability

Catatan yang perlu diingat:

> Saya belum puas dengan TTS yang sekarang karena suaranya masih terlalu AI. Itu akan menjadi fokus pengembangan berikutnya. Opsi lanjutan seperti model suara lokal advanced yang sempat didiskusikan masih akan dipikirkan lebih lanjut sebelum diputuskan menjadi jalur implementasi final.

