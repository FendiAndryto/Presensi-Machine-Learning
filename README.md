# Presensi Machine Learning

Sistem presensi berbasis web menggunakan teknologi Face Recognition dan Machine Learning untuk mendeteksi wajah pengguna secara otomatis melalui kamera.

## 📌 Deskripsi

Project ini dibuat untuk mempermudah proses presensi secara digital dengan memanfaatkan pengenalan wajah menggunakan OpenCV dan algoritma machine learning. Sistem dapat mendeteksi wajah pengguna, melakukan training dataset wajah, serta mencatat kehadiran secara otomatis.

## 🚀 Fitur

* Login Admin
* Kelola Data User
* Presensi Otomatis Menggunakan Kamera
* Face Detection & Face Recognition
* Training Dataset Wajah
* Dashboard Admin
* Riwayat Presensi
* Laporan Presensi
* Export Data Presensi
* Sistem Berbasis Web Flask

## 🛠️ Teknologi Yang Digunakan

* Python
* Flask
* OpenCV
* Machine Learning
* HTML
* CSS
* Bootstrap
* SQLite / MySQL

## 📂 Struktur Folder

```bash
Presensi-Machine-Learning/
│
├── dataset/              # Dataset wajah pengguna
├── templates/            # Tampilan HTML
├── trainer/              # File hasil training
├── static/               # CSS, JS, gambar
├── app.py                # Main aplikasi Flask
├── setup_database.py     # Setup database
└── requirements.txt      # Dependency project
```

## ⚙️ Instalasi

Clone repository:

```bash
git clone https://github.com/FendiAndryto/Presensi-Machine-Learning.git
```

Masuk ke folder project:

```bash
cd Presensi-Machine-Learning
```

Buat virtual environment:

```bash
python -m venv .venv
```

Aktifkan virtual environment:

### Windows

```bash
.venv\Scripts\activate
```

Install dependency:

```bash
pip install -r requirements.txt
```

Jalankan aplikasi:

```bash
python app.py
```

## 📸 Cara Kerja Sistem

1. Admin menambahkan data user
2. Sistem mengambil dataset wajah melalui kamera
3. Dataset wajah akan ditraining
4. Sistem melakukan face recognition secara realtime
5. Presensi tersimpan otomatis ke database

## 📷 Screenshot

Tambahkan screenshot aplikasi di sini.

## 📖 Tujuan Project

Project ini dibuat sebagai media pembelajaran dan implementasi machine learning pada sistem presensi berbasis wajah.