# 📸 Sistem Presensi Face Recognition & Machine Learning

Sistem presensi modern berbasis web yang mengintegrasikan teknologi **Computer Vision** (Face Detection & Face Recognition) dan **Geofencing** (sistem pembatasan radius koordinat lokasi) untuk merekam kehadiran staff secara realtime, aman, dan efisien.

---

## 📌 Deskripsi Proyek

Aplikasi ini dikembangkan menggunakan **Python Flask** sebagai framework web utama, **PostgreSQL** untuk manajemen database relasional yang andal, dan **OpenCV (Haar Cascade & LBPH)** untuk proses pendeteksian serta pengenalan wajah pengguna secara realtime baik dari webcam server/desktop maupun dari browser perangkat mobile (HP). 

Sistem ini juga dilengkapi dengan mekanisme **Geo-fencing** yang membatasi jarak presensi karyawan berdasarkan koordinat kantor yang ditentukan, dengan pengecualian fleksibilitas khusus untuk divisi tertentu (seperti Divisi *Marketing*).

---

## 🚀 Fitur Utama

### 1. 🛡️ Sistem Autentikasi Keamanan Tinggi
* Login aman menggunakan enkripsi password dengan metode **PBKDF2/SHA256 Hash** (`werkzeug.security`).
* Pembagian otorisasi akses (role-based access) antara **Super Admin** dan **Staff**.

### 2. 👤 Face Recognition Pintar (LBPH)
* **Pengambilan Dataset Wajah Terpandu**: Alur pengambilan dataset wajah terbagi menjadi 4 sesi terarah (Wajah Datar, Wajah Senyum, Serong Kiri, dan Serong Kanan) untuk akurasi data.
* **Pelatihan Model Langsung (Online Training)**: Admin dapat melatih sistem mengenali wajah pengguna baru langsung dari dasbor web.
* **Face Recognition Real-Time**: Verifikasi kehadiran menggunakan kamera laptop/PC maupun kamera perangkat mobile via WebRTC.

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
* **Computer Vision:** OpenCV (Haar Cascades untuk deteksi wajah, Local Binary Patterns Histograms / LBPH untuk pengenalan wajah)
* **Sistem Database:** PostgreSQL (`psycopg2`)
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
├── trainer/                    # Model latih pengenalan wajah hasil training (trainer.yml)
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

## ⚙️ Panduan Instalasi & Konfigurasi

### 1. Prasyarat Sistem
Pastikan Anda sudah menginstal beberapa software berikut:
* **Python 3.8 - 3.11**
* **PostgreSQL Database Server**
* **Kamera/Webcam Aktif**

### 2. Kloning Repositori
```bash
git clone https://github.com/FendiAndryto/Presensi-Machine-Learning.git
cd Presensi-Machine-Learning
```

### 3. Setup Virtual Environment
```bash
python -m venv .venv
```
Aktifkan virtual environment:
* **Windows:**
  ```powershell
  .venv\Scripts\activate
  ```
* **macOS / Linux:**
  ```bash
  source .venv/bin/activate
  ```

### 4. Instalasi Dependency
Instal pustaka-pustaka Python yang diperlukan:
```bash
pip install flask opencv-python opencv-contrib-python psycopg2 numpy pillow pandas openpyxl requests
```
> [!IMPORTANT]
> Pastikan menginstal `opencv-contrib-python` karena modul `cv2.face` (pengenal LBPH) berada di paket kontribusi tersebut, bukan di paket OpenCV standar.

### 5. Setup Database PostgreSQL
1. Buat database baru di PostgreSQL dengan nama `skripsi_db`.
2. Buka berkas `setup_database_final.py` dan sesuaikan kredensial koneksi berikut dengan server lokal Anda:
   ```python
   DB_NAME = "skripsi_db"
   DB_USER = "postgres"
   DB_PASS = ""
   DB_HOST = "localhost"
   ```
3. Jalankan script inisialisasi tabel & data seeder:
   ```bash
   python setup_database_final.py
   ```
   *Script ini otomatis akan membuat struktur tabel `divisi`, `users`, `lokasi_kantor`, dan `absensi`, serta menambahkan data akun bawaan untuk pengujian.*

### 6. Jalankan Aplikasi
Jalankan server aplikasi Flask:
```bash
python app.py
```
Buka browser Anda dan akses halaman login di alamat:
[http://127.0.0.1:5000](http://127.0.0.1:5000)

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

1. **Inisialisasi Awal**: Jalankan script `setup_database_final.py` untuk mengeset PostgreSQL.
2. **Pendaftaran Karyawan**: Admin masuk ke panel admin, menu **Kelola User**, dan mendaftarkan staff baru.
3. **Perekaman Dataset Wajah**:
   * Admin menekan tombol **Ambil Dataset** untuk staff bersangkutan.
   * Ikuti arahan kamera untuk merekam wajah staff dalam 4 sesi gerakan agar variasi wajah terekam dengan baik.
4. **Model Training (Pelatihan Otak AI)**: Setelah selesai mengambil data wajah, klik **Train Model** pada halaman Admin untuk memperbarui model pengenal (`trainer.yml`).
5. **Proses Presensi**:
   * Staff login ke dasbor masing-masing, sistem akan mendeteksi koordinat lokasi staff.
   * Kamera pada dasbor (atau fitur mobile absensi) diaktifkan untuk mencocokkan wajah staff bersangkutan dengan model.
   * Jika wajah terdeteksi cocok dengan akun login dan posisi koordinat valid (berada di dalam geofence kantor / pengecualian marketing), presensi **Masuk** atau **Pulang** akan tercatat secara otomatis ke database.

---

## 📖 Tujuan Proyek

Proyek ini dibuat sebagai implementasi riset terapan di bidang Machine Learning dan Computer Vision untuk meningkatkan integritas, akurasi, dan efisiensi pencatatan kehadiran karyawan di era digital.