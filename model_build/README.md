# Model Build Workspace

Workspace ini dipakai untuk seluruh pekerjaan build model `PANDAI-Tutor-7B` tanpa mencampur eksperimen training dengan runtime service `PAN-AI`.

## Tujuan

- menyimpan dataset training bilingual
- menyimpan data card dan dokumentasi eksperimen
- menyimpan config training/evaluation
- menyimpan script utilitas untuk prepare, validate, train, eval, dan export
- menyimpan artefak hasil eksperimen secara terstruktur

## Struktur

```text
model_build/
  datasets/
  data_cards/
  configs/
    base/
    lora/
    eval/
  scripts/
  artifacts/
  docs/
    adr/
    experiments/
```

## Aturan Kerja

1. Jangan letakkan checkpoint besar langsung di root repo.
2. Semua dataset harus punya dokumentasi singkat dan status lisensi.
3. Semua eksperimen harus punya config yang bisa diulang.
4. Model hasil training untuk runtime PAN-AI tetap harus diintegrasikan lewat `LLMHandler`.

## Urutan Penggunaan

1. Lengkapi schema dan sampel di `datasets/`
2. Dokumentasikan dataset di `data_cards/`
3. Sesuaikan config di `configs/`
4. Jalankan script di `scripts/`
5. Simpan artefak dan laporan di `artifacts/` dan `docs/experiments/`

## Dokumen Referensi

- `docs/PANDAI_DATA_SPECIFICATION.md` sebagai kontrak resmi format dan kualitas data
