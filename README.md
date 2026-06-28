# 📸 Sistem Presensi Face Recognition & Machine Learning

Sistem presensi modern berbasis web yang mengintegrasikan teknologi **Computer Vision** (Face Detection & Face Recognition) dan **Geofencing** (sistem pembatasan radius koordinat lokasi) untuk merekam kehadiran staff secara realtime, aman, dan efisien.

---

## 📌 Deskripsi Proyek

Aplikasi ini dikembangkan menggunakan **Python Flask** sebagai framework web utama, **PostgreSQL** untuk manajemen database relasional yang andal, dan **Deep Learning (dlib & face_recognition)** untuk proses pendeteksian serta pengenalan wajah pengguna secara realtime (menggantikan sistem lama OpenCV Haar Cascade & LBPH untuk akurasi lebih tinggi). Aplikasi ini terintegrasi penuh dengan **Docker** untuk mempermudah proses deployment. 

Sistem ini juga dilengkapi dengan mekanisme **Geo-fencing** yang membatasi jarak presensi karyawan berdasarkan koordinat kantor yang ditentukan, dengan pengecualian fleksibilitas khusus untuk divisi tertentu (seperti Divisi *Marketing*).

---

## 🚀 Fitur Utama

### 1. 🛡️ Sistem Autentikasi Keamanan Tinggi
* Login aman menggunakan enkripsi password dengan metode **PBKDF2/SHA256 Hash** (`werkzeug.security`).
* Pembagian otorisasi akses (role-based access) antara **Super Admin** dan **Staff**.

### 2. 👤 Face Recognition Deep Learning (dlib)
* **Pengambilan Dataset Wajah Terpandu**: Alur pengambilan dataset wajah terarah untuk mengekstrak *encoding* (128D embeddings) presisi tinggi.
* **Training & Encoding Cepat**: Dataset wajah langsung diekstraksi menjadi embedding vektor (.pkl) tanpa perlu proses re-training LBPH yang lama.
* **Akurasi Real-Time**: Verifikasi kehadiran menggunakan kamera laptop/PC maupun perangkat mobile (WebRTC) dengan tingkat toleransi (threshold) ketat sebesar 0.45 untuk meminimalisir kesalahan.

### 2.5 📸 Validasi Kualitas Gambar Cerdas
* **Anti-Blur & Anti-Gelap**: Sistem otomatis menolak foto jika kondisi pencahayaan buruk (terlalu gelap / terlalu silau) atau gambar blur (deteksi varians Laplacian).
* **Validasi Jarak Wajah**: Otomatis menolak foto jika wajah pengguna terlalu jauh (< 5% luas layar) atau terlalu dekat (> 60% luas layar).

### 3. 📍 Pembatasan Jarak Geofencing (Geo-Location)
* Mengukur jarak koordinat geografis *real-time* user dengan titik koordinat pusat kantor menggunakan rumus **Haversine**.
* **Kebijakan Fleksibel per Divisi**: Karyawan divisi *IT*, *Keuangan*, dan *HRD* wajib berada di dalam jangkauan radius kantor (misalnya 50 meter) untuk melakukan presensi, sedangkan divisi *Marketing* memiliki dispensasi khusus untuk melakukan absensi dari luar jangkauan radius kantor.



### 5. 📊 Dasbor Admin & Laporan Interaktif
* Statistik kehadiran harian visual dan langsung.
* Riwayat presensi bulanan yang dapat difilter berdasarkan tanggal, bulan, atau tahun.
* Ekspor laporan lengkap ke dalam format spreadsheet Excel (`.xlsx`) secara otomatis menggunakan **Pandas & openpyxl**.

---

## 🛠️ Teknologi yang Digunakan

* **Bahasa Pemrograman:** Python 3.x
* **Web Framework:** Flask
* **Computer Vision:** `dlib` & `face_recognition` (untuk 128D Face Embeddings), OpenCV (untuk pemrosesan citra & validasi kualitas)
* **Sistem Database:** PostgreSQL (`psycopg2`)
* **Environment & Deployment:** Docker & Docker Compose
* **Pengolahan & Ekspor Data:** Pandas & openpyxl
* **UI/UX Design:** Bootstrap 5, FontAwesome, Custom Glassmorphism CSS, LogoGlobal branding integration

---

## 📂 Struktur Folder Proyek

```bash
Presensi-Machine-Learning/
│
├── dataset/                    # Foto-foto wajah sampel hasil capture pengguna
├── static/                     # Aset statis (Custom CSS, JS, Gambar, LogoGlobal.png)
├── templates/                  # Template HTML (Dashboard, Laporan, Izin, dll)
├── encodings/                  # Data 128D Face Embeddings (face_encodings.pkl)
│
├── app.py                      # Server aplikasi utama Flask & API Endpoints
├── setup_database_final.py     # Script inisialisasi & seeder database PostgreSQL
├── ambil_dataset.py            # Script standalone untuk mengambil dataset wajah via Webcam
├── latih_wajah.py              # Script standalone untuk melatih model klasifikasi wajah
├── kenali_wajah.py             # Script standalone untuk pengujian akurasi deteksi wajah
├── cek_kolom.py                # Utilitas bantuan untuk memverifikasi struktur tabel DB
└── tes_api.py / tes_upload.py  # Script pembantu untuk pengujian API & upload data
```

---

## ⚙️ Panduan Instalasi & Konfigurasi (Via Docker)

Proyek ini telah dikonfigurasi menggunakan **Docker** & **Docker Compose**. Sangat disarankan untuk menggunakan Docker karena instalasi library `dlib` secara manual (terutama di Windows) memerlukan setup CMake dan C++ Build Tools yang cukup rumit.

### 1. Prasyarat Sistem
* **Docker Desktop** (Windows / macOS) atau **Docker Engine** (Linux)
* Kamera / Webcam aktif

### 2. Kloning Repositori
```bash
git clone https://github.com/FendiAndryto/Presensi-Machine-Learning.git
cd Presensi-Machine-Learning
```

### 3. Setup Environment Variables
Buat salinan konfigurasi dari `.env.example` ke `.env`:
```bash
cp .env.example .env
```
*(Anda dapat mengubah kredensial database di dalam file `.env` jika diperlukan).*

### 4. Build & Jalankan Container
Jalankan perintah berikut di terminal:
```bash
docker-compose up --build -d
```
*Proses ini akan mengunduh base image Python, meng-compile dependensi `dlib` (membutuhkan waktu beberapa menit), melakukan instalasi semua modul, menyiapkan database PostgreSQL, dan menjalankan server Flask.*

### 5. Inisialisasi Database (Hanya 1x Saat Pertama Deploy)
Setelah container berjalan, jalankan perintah ini di terminal untuk membuat tabel dan akun admin default:
```bash
docker exec -it presensi_web python setup_database_final.py
```

### 6. Akses Aplikasi
Buka browser Anda dan akses:
[http://localhost:8000](http://localhost:8000)

---

## 📸 Akun Default untuk Uji Coba

* **Akun Admin:**
  * **Username:** `admin`
  * **Password:** `123`
* **Akun Staff (Divisi Marketing / Tanpa Batas Geofence):**
  * **Username:** `fendi`
  * **Password:** `123`

---

## 📷 Alur Penggunaan Sistem

1. **Inisialisasi Awal**: Jalankan `docker exec -it presensi_web python setup_database_final.py` untuk mengeset tabel PostgreSQL.
2. **Pendaftaran Karyawan**: Admin masuk ke panel admin, menu **Kelola User**, dan mendaftarkan staff baru.
3. **Perekaman Dataset Wajah**:
   * Admin menekan tombol **Ambil Dataset** untuk staff bersangkutan.
   * Ikuti arahan kamera. Sistem akan memvalidasi cahaya dan jarak wajah. Jika lolos validasi, data `face_encodings.pkl` akan otomatis diperbarui (Training otomatis).
4. **Proses Presensi**:
   * Staff login ke dasbor masing-masing, sistem akan mendeteksi koordinat lokasi staff.
   * Kamera pada dasbor (WebRTC) diaktifkan untuk mencocokkan wajah staff dengan model. Wajah harus jelas, cukup cahaya, dan proporsional.
   * Jika wajah dikenali dan posisi koordinat valid (berada di dalam geofence kantor / pengecualian marketing), presensi **Masuk** atau **Pulang** akan tercatat secara otomatis.

---

## 📖 Tujuan Proyek

Proyek ini dibuat sebagai implementasi riset terapan di bidang Machine Learning dan Computer Vision untuk meningkatkan integritas, akurasi, dan efisiensi pencatatan kehadiran karyawan di era digital.