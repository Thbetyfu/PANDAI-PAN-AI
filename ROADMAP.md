# Roadmap & Key Performance Indicators (KPIs): PAN-AI Project

Dokumen ini merinci peta jalan pengembangan (roadmap) sistem kecerdasan buatan terpusat PAN-AI, serta Key Performance Indicators (KPIs) untuk mengukur keberhasilan implementasi di setiap fase.

---

## 🗺️ Peta Jalan Pengembangan (Roadmap)

### Fase 1: Proof of Concept & Integrasi Lokal (Status: Selesai)
Fokus fase ini adalah memvalidasi kelayakan konsep arsitektur microservices terdekopel (decoupled), integrasi custom skills OpenClaw Python dengan Express Backend, dan logika pembatasan kuota siswa.
- **Pekerjaan**:
  - Menyusun struktur folder `PAN-AI` dan konfigurasi dasar Gateway.
  - Menulis skrip custom skills: `digital_twin.py` (Hermes memory profile), `generate_quiz.py` (Gemini Quiz Generator), dan `evaluate_biometrics.py` (biometric classification).
  - Membangun FastAPI wrapper untuk menyatukan seluruh modul AI di port 3002.
  - Mengimplementasikan middleware pengecekan dan pengurangan kuota harian (reset 24 jam sejak pemakaian pertama) di backend utama Node.js/Express.
  - Membuat skrip simulasi pengujian kuota dan validasi alur data.
- **KPI Keberhasilan**:
  - Alur data telemetri biometrik dari klien berhasil dievaluasi oleh server FastAPI dengan latensi pemrosesan internal kurang dari 200 ms.
  - Sistem kuota berhasil memblokir request siswa ke-4 (pada batas limit uji coba 3 request) dan mengembalikan respons HTTP 429 yang valid dengan estimasi waktu reset yang akurat.
  - Logika reset otomatis aktif setelah timestamp menunjukkan perbedaan lebih dari 24 jam sejak pemakaian pertama dalam siklus tersebut.

---

### Fase 2: Migrasi Database & Infrastruktur Cloud (Status: Rencana)
Fokus fase ini adalah memindahkan database JSON lokal dan memori berkas siswa ke infrastruktur cloud serverless berkapasitas tinggi untuk menangani konkurensi 1.000+ siswa secara simultan.
- **Pekerjaan**:
  - Menyewa dan melakukan konfigurasi cloud VPS (misal: Linux Ubuntu di Railway, DigitalOcean, atau AWS) untuk menjadi tempat hidup daemon FastAPI PAN-AI.
  - Mengonfigurasi reverse proxy (seperti Nginx) dan SSL (Let's Encrypt) di server untuk keamanan transmisi data API dari klien sekolah.
  - Migrasi database pengguna lokal (`shared_users.json`) ke pangkalan data relasional terpusat (Supabase PostgreSQL / PostgreSQL server).
  - Migrasi profil memori Digital Twin siswa (`USER.md` dan `MEMORY.md` berbasis file) ke tabel relasional terstruktur di PostgreSQL atau vector database untuk performa query yang lebih cepat.
- **KPI Keberhasilan**:
  - Konkurensi server sanggup melayani pengiriman data telemetri simultan dari minimal 500 siswa aktif secara bersamaan tanpa mengalami kegagalan request (0% error rate).
  - Rata-rata latensi API dari klien ke cloud server hingga kembali (Round Trip Time) di bawah 500 ms dalam kondisi jaringan normal.
  - Keamanan koneksi API terenkripsi penuh menggunakan HTTPS (SSL valid).

---

### Fase 3: Kalibrasi Algoritma Biometrik & Sinkronisasi Real-time (Status: Rencana)
Fokus fase ini adalah meningkatkan akurasi pembacaan data biometrik (HR, HRV, GSR, EAR) serta menghadirkan umpan balik intervensi yang responsif dalam hitungan detik.
- **Pekerjaan**:
  - Mengintegrasikan parsing data mentah dari headset EEG secara real-time untuk memperkaya pembacaan status konsentrasi siswa.
  - Melakukan fine-tuning nilai ambang batas (*threshold calibration*) algoritma biometrik berdasarkan data hasil belajar di lapangan untuk menekan angka *false-positive* (deteksi kantuk/stres yang salah).
  - Mengimplementasikan protokol transmisi data real-time berbasis WebSockets atau MQTT pada FastAPI untuk sinkronisasi instan status siswa ke dasbor pemantauan guru secara real-time.
- **KPI Keberhasilan**:
  - Tingkat akurasi deteksi kebingungan (*confusion*) dan kelelahan belajar (*fatigue*) siswa mencapai lebih dari 90% setelah divalidasi dengan kuesioner balik/uji coba lapangan.
  - Keterlambatan (*delay*) pengiriman notifikasi tanda bahaya kognitif (misal: siswa stres berat) dari klien siswa hingga muncul di dasbor guru kurang dari 1,5 detik.

---

### Fase 4: Digital Twin Lanjutan & Integrasi Metaverse (Status: Rencana)
Fokus fase ini adalah menyajikan representasi objek Digital Twin siswa ke dalam metaverse pembelajaran yang hidup dan adaptif secara real-time.
- **Pekerjaan**:
  - Membangun model machine learning prediktif untuk memproyeksikan kurva kejenuhan kognitif siswa berdasarkan riwayat historis memori Hermes mereka.
  - Menghubungkan API state Digital Twin dari server PAN-AI langsung dengan game server metaverse (LMS Metaverse).
  - Mengembangkan sistem pemicu intervensi otomatis di dalam game (dynamic game spawner), seperti memunculkan NPC bantuan kognitif atau membuka gerbang minigame relaksasi secara dinamis saat state Digital Twin siswa menunjukkan kelelahan kognitif.
- **KPI Keberhasilan**:
  - Digital Twin mampu memprediksi waktu kelelahan kognitif (*attention decay*) siswa 5 menit sebelum terjadi dengan tingkat presisi > 85%.
  - Game server metaverse sukses menerima event trigger intervensi kognitif dari PAN-AI dan memunculkan aset visual/mini-game penyeimbang fokus di layar siswa dalam waktu < 200 ms pasca-trigger.

---

## 📈 Matriks Ringkasan KPIs Utama

| Parameter Pengukuran | Target Fase 1 | Target Fase 2 | Target Fase 3 | Target Fase 4 |
| :--- | :--- | :--- | :--- | :--- |
| **Latensi Evaluasi Internal** | < 200 ms | < 100 ms | < 50 ms | < 30 ms |
| **Konkurensi Siswa Aktif** | Uji Coba Lokal | 500+ siswa | 1.000+ siswa | 2.000+ siswa |
| **Akurasi Deteksi Kognitif** | Deteksi Dasar | 75% akurat | 90% akurat | > 92% akurat |
| **Akurasi Prediksi Kejenuhan**| N/A | N/A | 70% akurat | > 85% akurat |
| **Integrasi Ekosistem** | CLI / API | Web LMS | Real-time Dashboard| Live Metaverse |
