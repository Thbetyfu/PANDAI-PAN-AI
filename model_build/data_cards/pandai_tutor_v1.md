# Data Card: PANDAI Tutor v1

## Ringkasan

- Nama dataset: `pandai_tutor_v1`
- Status: draft awal
- Fokus: tutor bilingual Indonesia dan Inggris
- Tujuan: SFT awal untuk `PANDAI-Tutor-7B`

## Komponen Data

- instruction tutor bilingual
- grammar correction
- teaching explanation
- structured generation
- safety/refusal

## Bahasa

- Indonesia
- English
- mixed bilingual

## Sumber Data

- data sintetis internal berkualitas tinggi
- data manual kurasi tim
- dataset publik yang lisensinya aman

## Larangan

- data tanpa lisensi jelas
- scrape mentah tanpa kurasi
- konten berbahaya untuk siswa
- contoh dengan output JSON rusak untuk task terstruktur

## Checklist Kualitas

- tujuan pedagogis jelas
- bahasa input sesuai label
- jawaban konsisten dengan persona PANDAI
- format output valid
- tidak halusinatif

## Catatan Evaluasi

- benchmark internal yang terkait: `PANDAI-EVAL`
- review manusia tetap wajib untuk kualitas pedagogis
