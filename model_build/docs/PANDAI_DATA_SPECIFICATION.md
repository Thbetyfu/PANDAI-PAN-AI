# PANDAI Data Specification

Versi: v1
Tanggal: 2026-06-24
Status: Draft operasional awal
Scope: Spesifikasi resmi untuk dataset bilingual `PANDAI-Tutor-7B`

---

## 1. Tujuan Dokumen

Dokumen ini mendefinisikan kontrak data untuk seluruh sampel yang akan dipakai dalam:

- supervised fine-tuning (SFT)
- structured task tuning
- evaluasi internal
- audit kualitas data

Tujuan utamanya adalah memastikan bahwa semua data untuk `PANDAI-Tutor-7B`:

- konsisten
- mudah divalidasi
- aman untuk konteks edukasi
- siap dipakai lintas eksperimen tanpa format yang berubah-ubah

---

## 2. Unit Data

Unit dasar dataset adalah satu objek JSON per baris dalam file JSONL.

Setiap objek mewakili satu interaksi terarah antara:

- instruksi sistem
- input pengguna
- respons ideal asisten

Satu baris harus cukup untuk dipakai langsung pada pipeline training tanpa perlu interpretasi manual tambahan.

---

## 3. Format File

### 3.1 Format Wajib

- encoding: UTF-8
- ekstensi: `.jsonl`
- satu objek JSON valid per baris
- tanpa trailing comma
- tanpa komentar inline

### 3.2 Aturan Parsing

- semua key memakai snake_case
- field string tidak boleh berisi karakter kontrol yang merusak parser
- newline di dalam string diperbolehkan bila valid sebagai JSON
- field kosong tidak boleh diisi string kosong jika secara semantik berarti "tidak ada"; gunakan field opsional dan omit bila perlu

---

## 4. Schema Wajib

Setiap sampel minimal harus memiliki field berikut:

```json
{
  "id": "sample_0001",
  "task_type": "grammar_correction",
  "language": "en",
  "student_level": "beginner",
  "persona": "strict_warm",
  "difficulty": "easy",
  "curriculum_tag": "english.past_tense",
  "safety_label": "safe",
  "response_style": "explanatory",
  "system": "You are PANDAI Tutor...",
  "user": "i go to school yesterday",
  "assistant": "Kalimat yang benar adalah 'I went to school yesterday.' ..."
}
```

### 4.1 Field Wajib

| Field | Tipe | Wajib | Deskripsi |
| --- | --- | --- | --- |
| `id` | string | ya | ID unik sampel |
| `task_type` | string | ya | jenis tugas pedagogis |
| `language` | string | ya | bahasa utama input |
| `student_level` | string | ya | level target siswa |
| `persona` | string | ya | persona tutor PANDAI |
| `difficulty` | string | ya | tingkat kesulitan |
| `curriculum_tag` | string | ya | label kurikulum / topik |
| `safety_label` | string | ya | label keamanan sampel |
| `response_style` | string | ya | gaya keluaran yang diinginkan |
| `system` | string | ya | instruksi sistem |
| `user` | string | ya | input pengguna |
| `assistant` | string | ya | jawaban target ideal |

### 4.2 Field Opsional yang Direkomendasikan

| Field | Tipe | Deskripsi |
| --- | --- | --- |
| `source_type` | string | asal data: synthetic, human_authored, public_dataset |
| `source_name` | string | nama sumber dataset bila ada |
| `review_status` | string | status review internal |
| `reviewer_notes` | string | catatan reviewer |
| `split_hint` | string | preferensi split bila diperlukan |
| `locale` | string | locale spesifik seperti `id_ID`, `en_US` |
| `metadata` | object | metadata tambahan yang tidak kritikal untuk training |

---

## 5. Definisi Nilai per Field

### 5.1 `task_type`

Nilai yang diizinkan pada fase awal:

- `instruction_tutor_bilingual`
- `grammar_correction`
- `teaching_explanation`
- `quiz_generation_structured`
- `student_feedback`
- `safe_refusal`
- `translation_reformulation`

Aturan:

- jangan membuat `task_type` baru tanpa memperbarui spesifikasi ini
- satu sampel hanya boleh punya satu `task_type` utama

### 5.2 `language`

Nilai yang diizinkan:

- `id`
- `en`
- `mixed`

Definisi:

- `id`: input utama berbahasa Indonesia
- `en`: input utama berbahasa Inggris
- `mixed`: input memang sengaja bilingual atau code-switching

### 5.3 `student_level`

Nilai yang diizinkan:

- `beginner`
- `elementary`
- `intermediate`
- `upper_intermediate`

Catatan:

- tahap awal sebaiknya fokus pada `beginner` sampai `intermediate`

### 5.4 `persona`

Nilai default fase awal:

- `strict_warm`

Varian tambahan boleh ditambahkan nanti jika alignment sudah matang, misalnya:

- `gentle_supportive`
- `concise_coach`

Namun fase awal harus dominan satu persona agar identitas model tidak kabur.

### 5.5 `difficulty`

Nilai yang diizinkan:

- `easy`
- `medium`
- `hard`

### 5.6 `safety_label`

Nilai yang diizinkan:

- `safe`
- `sensitive_but_allowed`
- `refusal_required`

Aturan:

- mayoritas data fase awal sebaiknya `safe`
- data `refusal_required` harus tetap ada untuk melatih boundary

### 5.7 `response_style`

Nilai yang diizinkan:

- `concise`
- `explanatory`
- `step_by_step`
- `structured_json`
- `encouraging`

---

## 6. Aturan Penulisan Konten

### 6.1 Aturan untuk `system`

Field `system` harus:

- mendefinisikan peran tutor dengan jelas
- konsisten dengan identitas PANDAI
- tidak terlalu panjang
- tidak bertentangan dengan `response_style`

### 6.2 Aturan untuk `user`

Field `user` harus:

- realistis seperti interaksi siswa nyata
- sesuai dengan `language`
- sesuai dengan `student_level`
- tidak berisi noise yang tidak perlu kecuali memang disengaja untuk simulasi typo

### 6.3 Aturan untuk `assistant`

Field `assistant` harus:

- benar secara pedagogis
- konsisten dengan persona PANDAI
- tidak berhalusinasi
- jelas dan mudah dipahami siswa
- mematuhi `response_style`

Untuk task `structured_json`, output `assistant` wajib:

- valid JSON
- tanpa markdown fence
- tanpa teks pembuka atau penutup

---

## 7. Rubrik Kualitas Data

Setiap sampel harus lolos rubrik berikut.

### 7.1 Ketepatan Pedagogis

Checklist:

- koreksi benar
- penjelasan relevan
- tingkat bahasa sesuai target siswa
- tidak terlalu teknis untuk level awal

### 7.2 Konsistensi Persona

Checklist:

- nada tegas tapi hangat
- tidak sarkastik
- tidak terlalu kaku
- tidak terlalu panjang bila tidak perlu

### 7.3 Kepatuhan Format

Checklist:

- field lengkap
- label benar
- JSON valid
- `task_type` cocok dengan isi sampel

### 7.4 Keamanan

Checklist:

- tidak ada konten berbahaya untuk siswa
- tidak ada bias kasar atau ujaran merendahkan
- refusal contoh ditulis dengan aman dan edukatif

---

## 8. Komposisi Dataset

Target awal komposisi yang direkomendasikan:

- 45% `language = id`
- 45% `language = en`
- 10% `language = mixed`

Target awal komposisi `task_type`:

- 25% `instruction_tutor_bilingual`
- 20% `grammar_correction`
- 20% `teaching_explanation`
- 15% `quiz_generation_structured`
- 10% `student_feedback`
- 5% `safe_refusal`
- 5% `translation_reformulation`

Catatan:

- komposisi ini bukan aturan absolut, tetapi baseline awal agar data tidak berat sebelah

---

## 9. Aturan Data Sourcing

### 9.1 Sumber yang Diizinkan

- data sintetis internal berkualitas tinggi
- data manual yang ditulis tim
- dataset publik dengan lisensi jelas dan aman dipakai

### 9.2 Sumber yang Dilarang

- scrape mentah tanpa lisensi
- konten bajakan atau tidak jelas asalnya
- data yang mengandung informasi pribadi siswa nyata
- data yang tidak bisa diaudit sumbernya

### 9.3 Aturan Privasi

- jangan masukkan nama siswa nyata, email, nomor telepon, atau data sensitif lain
- gunakan entitas generik atau sintetis

---

## 10. Aturan Split Dataset

Setiap dataset final harus dibagi menjadi:

- `train`
- `validation`
- `test`

Prinsip split:

- jangan ada duplikasi hampir-identik lintas split
- contoh dari skenario yang sama jangan bocor ke test jika sudah ada di train
- subset `structured_json` dan `safe_refusal` wajib muncul di validation dan test

Rekomendasi awal:

- train: 80%
- validation: 10%
- test: 10%

---

## 11. Workflow Review Data

Urutan review yang disarankan:

1. penulis membuat sampel
2. validator menjalankan pengecekan schema
3. reviewer manusia menilai kualitas pedagogis
4. sampel diberi `review_status`
5. baru masuk ke split final

Nilai `review_status` yang direkomendasikan:

- `draft`
- `validated_schema`
- `reviewed_human`
- `approved`
- `rejected`

---

## 12. Acceptance Checklist per Sampel

Satu sampel dianggap layak bila:

- ID unik
- semua field wajib ada
- bahasa sesuai label
- persona sesuai PANDAI
- jawaban benar secara pedagogis
- aman untuk konteks edukasi
- valid JSON bila structured task
- tidak mengandung lisensi atau privasi bermasalah

---

## 13. Contoh Kasus yang Baik

### 13.1 Grammar Correction

Ciri sampel baik:

- input realistis
- kesalahan jelas
- perbaikan benar
- penjelasan singkat tapi membantu

### 13.2 Teaching Explanation

Ciri sampel baik:

- menjawab sesuai level siswa
- memakai bahasa sederhana
- contoh mudah dipahami

### 13.3 Structured JSON

Ciri sampel baik:

- schema output jelas
- jawaban murni JSON
- tidak ada variasi format liar

---

## 14. Hubungan Dengan File Lain

Spesifikasi ini terkait langsung dengan:

- [BLUEPRINT_PANDAI_TUTOR_7B.md](file:///d:/0.%20Kerjaan/4.%20PANDAI/PAN-AI/BLUEPRINT_PANDAI_TUTOR_7B.md)
- [sample_schema.jsonl](file:///d:/0.%20Kerjaan/4.%20PANDAI/PAN-AI/model_build/datasets/pandai_tutor_v1/sample_schema.jsonl)
- [pandai_tutor_v1.md](file:///d:/0.%20Kerjaan/4.%20PANDAI/PAN-AI/model_build/data_cards/pandai_tutor_v1.md)

Jika ada konflik antara sampel data dan dokumen ini, maka dokumen spesifikasi ini menjadi referensi utama sampai direvisi resmi.

---

## 15. Rekomendasi Langkah Berikutnya

Setelah dokumen ini selesai, urutan paling sehat adalah:

1. perbarui `sample_schema.jsonl` bila perlu menyesuaikan field opsional
2. buat 50 sampel emas (`gold samples`) sebagai referensi kualitas
3. lanjutkan ke batch pertama 200-500 sampel
4. tambahkan validator schema otomatis di `validate_data.py`

Kesimpulan:

> Kualitas `PANDAI-Tutor-7B` akan sangat ditentukan oleh disiplin spesifikasi data. Dokumen ini harus diperlakukan sebagai kontrak kerja tim, bukan catatan opsional.
