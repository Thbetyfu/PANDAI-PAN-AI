# Dataset PANDAI Tutor v1

Folder ini menyimpan dataset awal untuk eksperimen `PANDAI-Tutor-7B`.

## Target Isi

- instruction bilingual tutor
- grammar correction pairs
- structured quiz generation
- feedback belajar
- refusal/safety examples

## File Awal

- `sample_schema.jsonl`: contoh format data satu baris per sampel
- `gold_samples_tutor_basic_v1.jsonl`: batch pertama 50 gold samples untuk fondasi tutor dasar
- `gold_samples_feedback_refusal_quiz_v1.jsonl`: batch kedua untuk feedback, refusal, dan quiz structured

## Catatan

- gunakan JSONL UTF-8
- satu objek JSON per baris
- hindari karakter kontrol yang merusak parsing
- setiap sampel harus punya `task_type` dan `language`
