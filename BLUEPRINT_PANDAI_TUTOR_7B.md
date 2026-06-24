# BLUEPRINT PANDAI-Tutor-7B

Tanggal: 2026-06-24
Status: Draft arsitektur awal
Scope: Desain teknis awal untuk membangun "MODEL AI PANDAI" berbasis base model open-weight + adaptasi LoRA, fokus bilingual Indonesia dan Inggris.

---

## 1. Ringkasan Eksekutif

`PANDAI-Tutor-7B` tidak disarankan dibangun dari nol pada tahap ini. Pendekatan yang paling sehat secara engineering adalah:

1. memilih base model open-weight yang sudah kuat untuk reasoning dan multilingual instruction
2. membangun lapisan identitas PANDAI melalui data dan fine-tuning bertahap
3. melakukan adaptasi lokal memakai LoRA/QLoRA agar tetap realistis untuk hardware tim pengembang
4. mengintegrasikan model hasil adaptasi ke `PAN-AI` melalui `LLMHandler`, bukan lewat jalur terpisah

Target akhirnya bukan hanya "model yang bisa menjawab", tetapi model tutor yang:

- konsisten dengan persona guru PANDAI
- kuat di Bahasa Indonesia dan Inggris
- aman untuk konteks edukasi
- efisien untuk deployment lokal kelas menengah sampai high-end

---

## 2. Tujuan Produk Model

### 2.1 Tujuan Utama

`PANDAI-Tutor-7B` dirancang sebagai model tutor edukasi bilingual untuk:

- chat tutor harian
- koreksi grammar dan fluency
- penjelasan konsep dalam dua bahasa
- pembuatan latihan/quiz terstruktur
- feedback belajar yang personal, tegas, dan hangat
- adaptasi respons terhadap konteks siswa dan memori belajar

### 2.2 Non-Goal Tahap Awal

Pada fase blueprint ini, model tidak ditujukan untuk:

- full-scale general-purpose AGI
- pretraining dari corpus internet mentah
- voice model / TTS model
- multimodal vision/audio training
- fine-tuning besar yang memerlukan cluster GPU enterprise

---

## 3. Keputusan Arsitektur Utama

### 3.1 Keputusan A - Bukan Training from Scratch

Keputusan:

- Tidak melatih model dari nol.

Alasan:

- biaya komputasi sangat tinggi
- butuh data skala besar dan tim riset khusus
- tidak proporsional dengan kebutuhan produk tahap sekarang
- tidak cocok dengan strategi iteratif PANDAI yang sedang fokus pada pilot product

### 3.2 Keputusan B - Base Model + PANDAI Layer

Keputusan:

- Menggunakan base model open-weight yang sudah matang, lalu menambahkan "PANDAI layer" lewat instruction tuning dan alignment.

Makna "PANDAI layer":

- gaya mengajar
- format respons standar
- disiplin bilingual
- kebijakan tutor
- guardrail edukasi
- adaptasi terhadap konteks siswa

### 3.3 Keputusan C - LoRA/QLoRA Sebagai Jalur Adaptasi Awal

Keputusan:

- Tahap awal fine-tuning memakai LoRA atau QLoRA.

Alasan:

- realistis untuk GPU lokal
- iterasi cepat
- lebih murah dibanding full fine-tune
- memudahkan eksperimen beberapa varian tutor
- mudah rollback bila perilaku model memburuk

### 3.4 Keputusan D - Integrasi Tetap Lewat LLMHandler

Keputusan:

- Model hasil training wajib masuk lewat `neuro_language_tutor/llm_handler.py`.

Alasan:

- menjaga konsistensi routing hybrid yang sudah dibangun
- memanfaatkan fallback, observability, dan selector profile yang sudah ada
- mencegah lahirnya jalur model khusus yang hardcoded seperti masalah pada quiz lama

---

## 4. Kandidat Base Model

### 4.1 Kandidat Utama

Rekomendasi utama tahap awal:

- `Qwen2.5-7B-Instruct`

Alasan pemilihan:

- performa instruction-following kuat
- ekosistem tooling luas
- cukup baik untuk multilingual use case
- kompatibel untuk eksperimen lokal
- sudah sejalan dengan stack yang saat ini dipakai PAN-AI melalui keluarga model Qwen di Ollama

### 4.2 Kandidat Cadangan

Kandidat yang bisa dipertimbangkan sebagai pembanding:

- `Qwen2.5-3B-Instruct`
- `Llama 3.1 8B Instruct` jika lisensi dan deployment cocok
- `Mistral 7B Instruct` untuk pembandingan latency vs quality

### 4.3 Rekomendasi Final Fase 1

Gunakan dua lapisan model:

- `PANDAI-Tutor-7B-Primary`: berbasis `Qwen2.5-7B-Instruct`
- `PANDAI-Tutor-3B-Edge`: varian ringan untuk device yang lebih terbatas

Catatan:

- meskipun nama produk utama tetap `PANDAI-Tutor-7B`, arsitektur produk sebaiknya sejak awal menyiapkan varian edge yang lebih kecil

---

## 5. Spesifikasi Perilaku Model

Model PANDAI harus memiliki perilaku berikut.

### 5.1 Persona Tutor

- tegas tapi hangat
- mendorong belajar aktif
- tidak menghakimi siswa
- memberi koreksi jelas dan bertahap
- menjaga bahasa tetap mudah dipahami

### 5.2 Kemampuan Bilingual

- memahami prompt Indonesia
- memahami prompt Inggris
- mampu menjelaskan Inggris dalam Indonesia
- mampu menjelaskan Indonesia dalam Inggris
- mampu menjaga bahasa output sesuai permintaan user

### 5.3 Gaya Output

- ringkas untuk pertanyaan sederhana
- terstruktur untuk penjelasan kompleks
- konsisten untuk quiz/JSON tasks
- menghindari halusinasi dan klaim palsu
- mengutamakan kejelasan dibanding gaya bombastis

### 5.4 Guardrail Edukasi

- tidak memberi jawaban berbahaya atau tidak pantas untuk siswa
- tidak mengarang fakta saat tidak yakin
- mendorong klarifikasi bila prompt ambigu
- menghindari jawaban terlalu rumit untuk level siswa

---

## 6. Strategi Data

### 6.1 Jenis Dataset

Dataset `PANDAI-Tutor-7B` harus dibagi menjadi beberapa kelompok:

1. `instruction_tutor_bilingual`
2. `grammar_correction_pairs`
3. `teaching_explanations`
4. `quiz_generation_structured`
5. `student_feedback_and_encouragement`
6. `classroom_safety_and_refusal`
7. `translation_and_reformulation`

### 6.2 Sumber Data

Urutan sumber data yang direkomendasikan:

1. data sintetis berkualitas tinggi dari prompt generator internal
2. dataset publik instruction bilingual yang lisensinya aman
3. dataset grammar correction dan education QA publik
4. data domain internal PANDAI yang dibuat manual oleh tim

Catatan penting:

- jangan memakai data tanpa lisensi jelas
- jangan memakai scrape acak yang kualitas pedagogisnya tidak terkontrol
- data internal lebih sedikit tetapi berkualitas biasanya lebih bernilai untuk fase awal

### 6.3 Komposisi Bahasa

Target awal komposisi:

- 45% Bahasa Indonesia
- 45% Bahasa Inggris
- 10% mixed bilingual / translation / switching

Tujuan komposisi ini:

- menjaga keseimbangan
- mencegah model terlalu dominan ke satu bahasa
- melatih transisi penjelasan antar bahasa

### 6.4 Format Data

Format data training direkomendasikan memakai JSONL dengan skema:

```json
{
  "id": "sample_0001",
  "task_type": "grammar_correction",
  "language": "en",
  "student_level": "beginner",
  "system": "You are PANDAI Tutor...",
  "user": "i go to school yesterday",
  "assistant": "Kalimat yang benar adalah 'I went to school yesterday.' ..."
}
```

Field tambahan yang sebaiknya disiapkan:

- `persona`
- `difficulty`
- `curriculum_tag`
- `safety_label`
- `response_style`

### 6.5 Prinsip Kualitas Data

Setiap contoh data harus:

- punya target jawaban yang jelas
- sesuai gaya tutor PANDAI
- bebas kontradiksi
- bebas markdown rusak
- bebas JSON invalid untuk task terstruktur
- konsisten tingkat kesulitan dan target pedagogisnya

---

## 7. Pipeline Training Bertahap

### 7.1 Fase 0 - Data Foundation

Output:

- dataset schema final
- data cleaning rules
- validasi bahasa
- split train/validation/test

Deliverable:

- `datasets/pandai_tutor_v1/`
- `data_cards/pandai_tutor_v1.md`

### 7.2 Fase 1 - SFT Bilingual Tutor

Tujuan:

- membentuk perilaku dasar tutor PANDAI

Metode:

- SFT memakai LoRA/QLoRA pada base model utama

Fokus:

- chat tutor
- koreksi grammar
- penjelasan konsep
- jawaban bilingual

Output:

- `pandai-tutor-7b-sft-v1`

### 7.3 Fase 2 - Structured Task Tuning

Tujuan:

- meningkatkan kepatuhan format untuk tugas seperti quiz JSON, daftar vocab, dan feedback terstruktur

Fokus:

- JSON discipline
- predictable schema
- minimisasi markdown fence

Output:

- `pandai-tutor-7b-structured-v1`

### 7.4 Fase 3 - Preference Alignment

Tujuan:

- memilih gaya respons terbaik untuk tutor PANDAI

Metode:

- DPO atau metode preference optimization ringan, bila data pair sudah cukup

Fokus:

- warmth vs strictness balance
- verbosity control
- refusal quality
- hallucination suppression

Output:

- `pandai-tutor-7b-aligned-v1`

### 7.5 Fase 4 - Distillation Opsional

Tujuan:

- membuat model kecil yang mewarisi perilaku PANDAI untuk device lebih lemah

Kandidat:

- 3B atau 1.5B

Output:

- `pandai-tutor-3b-edge-v1`

---

## 8. Strategi Evaluasi

### 8.1 Dimensi Evaluasi Wajib

Evaluasi model tidak boleh hanya memakai loss. Minimal harus mengukur:

1. kualitas bilingual
2. ketepatan pedagogis
3. grammar correction quality
4. adherence format JSON
5. safety dan refusal
6. latency lokal
7. konsistensi persona tutor

### 8.2 Benchmark Internal PANDAI

Buat benchmark internal bernama `PANDAI-EVAL` dengan subset berikut:

- `eval_id_tutor_basic`
- `eval_en_tutor_basic`
- `eval_bilingual_switch`
- `eval_grammar_fix`
- `eval_quiz_json`
- `eval_safe_refusal`
- `eval_short_vs_detailed_response`

### 8.3 KPI Awal

Target awal yang realistis:

- valid JSON rate untuk quiz >= 95%
- bilingual instruction success >= 90%
- grammar correction acceptance oleh reviewer manusia >= 85%
- hallucination critical rate <= 3%
- median latency lokal acceptable pada profile quality sesuai target hardware

### 8.4 Human Review

Wajib ada evaluasi manusia untuk:

- naturalness penjelasan
- kualitas pembelajaran
- kecocokan tone tutor
- keamanan untuk siswa

---

## 9. Arsitektur Deployment

### 9.1 Deployment Lokal

Jalur deployment yang direkomendasikan:

1. model base atau adapter hasil training dikonversi ke format deployment yang sesuai
2. disajikan lewat runtime lokal yang bisa diintegrasikan ke PAN-AI
3. `LLMHandler` memilih model berdasarkan `llm_profile` dan `llm_model`

Pilihan runtime yang mungkin:

- Ollama jika pipeline export-nya stabil
- vLLM/TGI untuk server yang lebih kuat
- llama.cpp / GGUF path untuk varian edge

### 9.2 Mapping ke Arsitektur PAN-AI Saat Ini

Integrasi harus mengikuti pola berikut:

- `server.py` tetap menjadi API gateway
- `LLMHandler` menjadi satu-satunya entry point model
- endpoint chat/quiz/orchestrator meneruskan `llm_profile` dan `llm_model`
- profile lokal dapat diarahkan ke model PANDAI saat model siap

### 9.3 Strategi Rollout

Urutan rollout yang disarankan:

1. internal offline eval
2. staging model di mesin lokal tim
3. pilot pada feature terbatas, misalnya tutor chat dahulu
4. baru kemudian dipakai untuk quiz dan orchestrator

Alasan:

- chat tutor adalah use case paling mudah diamati kualitasnya
- quiz dan orchestration lebih sensitif terhadap format dan konsistensi

---

## 10. Kebutuhan Infrastruktur

### 10.1 Kebutuhan Training Awal

Untuk fase eksperimen awal, target realistis:

- training LoRA/QLoRA di GPU cloud sewaan atau workstation kuat
- dataset relatif kecil tetapi berkualitas
- artefak training tersimpan terstruktur dan versioned

### 10.2 Kebutuhan Lokal Tim

Untuk inference dan smoke test:

- laptop mid-high cukup untuk menjalankan varian ringan/quantized
- model 7B penuh mungkin lebih cocok untuk desktop kuat atau GPU cloud

Kesimpulan praktis:

- jangan mengasumsikan semua laptop pengembang mampu men-training 7B
- pisahkan jelas kebutuhan training dan kebutuhan inference

---

## 11. Risiko Utama

### 11.1 Risiko Kualitas Data

Risiko:

- data sintetis terlalu generik
- gaya tutor tidak konsisten
- bilingual quality timpang

Mitigasi:

- buat rubric data
- lakukan sampling audit manual
- batasi generator prompt agar tidak menghasilkan pola slop

### 11.2 Risiko Overfitting Persona

Risiko:

- model terlalu kaku
- semua jawaban terdengar sama

Mitigasi:

- variasikan format respons
- simpan persona inti tetapi fleksibel dalam ekspresi

### 11.3 Risiko Deployment Gap

Risiko:

- model bagus saat training tetapi buruk di runtime lokal

Mitigasi:

- evaluasi dengan format deployment final sejak awal
- ukur latency dan memory usage pada hardware nyata

### 11.4 Risiko Scope Creep

Risiko:

- proyek berubah menjadi riset model umum, bukan tutor produk

Mitigasi:

- pertahankan fokus pada use case tutor
- setiap dataset dan eksperimen harus diikat ke kebutuhan fitur nyata PAN-AI

---

## 12. Struktur Folder yang Direkomendasikan

Blueprint ini menyarankan penambahan workspace training terpisah dari runtime service utama.

```text
PAN-AI/
  model_build/
    README.md
    datasets/
      pandai_tutor_v1/
    data_cards/
      pandai_tutor_v1.md
    configs/
      base/
      lora/
      eval/
    scripts/
      prepare_data.py
      validate_data.py
      train_sft.py
      run_eval.py
      export_adapter.py
    artifacts/
      checkpoints/
      adapters/
      eval_reports/
    docs/
      adr/
      experiments/
```

Catatan:

- workspace ini sengaja dipisah agar `PAN-AI` runtime tidak tercampur dengan eksperimen training

---

## 13. Rencana Implementasi Setelah Blueprint Ini

Langkah berikutnya yang paling sehat:

### Langkah 1

Bangun folder `model_build/` beserta template data dan config training.

### Langkah 2

Tulis `data specification` resmi untuk sampel tutor bilingual.

### Langkah 3

Buat minimal 200-500 sampel berkualitas tinggi untuk eksperimen SFT pertama.

### Langkah 4

Siapkan pipeline training LoRA sederhana dan satu benchmark internal.

### Langkah 5

Setelah adapter pertama layak, sambungkan ke `LLMHandler` sebagai model eksperimental.

---

## 14. Rekomendasi Final

Jika tujuan kita adalah membangun "MODEL AI PANDAI" yang nyata dan bisa dikembangkan bertahap, maka jalur terbaik adalah:

1. pakai `Qwen2.5-7B-Instruct` sebagai base utama
2. bangun identitas tutor lewat data internal + SFT bilingual
3. gunakan LoRA/QLoRA untuk iterasi awal
4. siapkan benchmark internal `PANDAI-EVAL`
5. integrasikan hasilnya lewat `LLMHandler`
6. baru setelah itu pertimbangkan alignment lanjutan, distillation, atau varian edge

Kesimpulan singkat:

> `PANDAI-Tutor-7B` sebaiknya diperlakukan sebagai produk model terarah untuk tutor edukasi bilingual, bukan proyek pretraining raksasa. Kemenangan terbesarnya akan datang dari kualitas data, disiplin evaluasi, dan integrasi yang rapi dengan arsitektur PAN-AI yang sudah ada.
