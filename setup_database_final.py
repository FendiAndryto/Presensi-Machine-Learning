import psycopg2
from psycopg2 import sql
from werkzeug.security import generate_password_hash # TAMBAHAN: Import untuk keamanan password
import os
from dotenv import load_dotenv

# Load env variables from .env if present
load_dotenv()

# --- KONFIGURASI DATABASE ---
DB_NAME = os.environ.get("DB_NAME", "skripsi_db")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASS = os.environ.get("DB_PASS", "12345")       
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")

def create_tables():
    commands = (
        # 1. Tabel DIVISI
        """
        CREATE TABLE IF NOT EXISTS divisi (
            id SERIAL PRIMARY KEY,
            nama_divisi VARCHAR(50) UNIQUE NOT NULL
        )
        """,
        
        # 2. Tabel USERS
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            nama_lengkap VARCHAR(100) NOT NULL,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL, -- Sekarang diisi dengan Hash
            role VARCHAR(20) DEFAULT 'Staff',
            divisi_id INTEGER,
            foto_wajah VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (divisi_id) REFERENCES divisi (id) ON DELETE SET NULL
        )
        """,
        
        # 3. Tabel LOKASI KANTOR (Aman, tidak akan dihapus)
        """
        CREATE TABLE IF NOT EXISTS lokasi_kantor (
            id SERIAL PRIMARY KEY,
            nama_lokasi VARCHAR(100),
            latitude DECIMAL(10,8),
            longitude DECIMAL(11,8),
            radius_meter INTEGER DEFAULT 50
        )
        """,

        # 4. Tabel ABSENSI
        """
        CREATE TABLE IF NOT EXISTS absensi (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            tanggal DATE DEFAULT CURRENT_DATE,
            jam_masuk TIME,
            jam_pulang TIME,
            foto_masuk VARCHAR(255),
            foto_pulang VARCHAR(255),
            lokasi_masuk VARCHAR(100),
            lokasi_pulang VARCHAR(100),
            status_kehadiran VARCHAR(20),
            durasi_kerja INTERVAL GENERATED ALWAYS AS (jam_pulang - jam_masuk) STORED,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
        """
    )

    conn = None
    try:
        conn = psycopg2.connect(database=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)
        cur = conn.cursor()
        
        print("[INFO] Menghapus tabel lama agar bersih...")
        # Urutan drop penting karena Foreign Key!
        cur.execute("DROP TABLE IF EXISTS absensi")
        cur.execute("DROP TABLE IF EXISTS users")
        cur.execute("DROP TABLE IF EXISTS divisi")
        cur.execute("DROP TABLE IF EXISTS lokasi_kantor")
        # NOTE: DROP TABLE lokasi_kantor KITA HAPUS agar koordinat aman.

        print("[INFO] Membuat struktur tabel baru...")
        for command in commands:
            cur.execute(command)
        
        # --- SEEDING DATA (Isi Data Awal) ---
        print("[INFO] Mengisi data default...")
        
        # 1. Isi Divisi
        cur.execute("INSERT INTO divisi (nama_divisi) VALUES ('IT'), ('Marketing'), ('Keuangan'), ('HRD')")
        
        # 2. Isi Lokasi Kantor
        cur.execute("""
            INSERT INTO lokasi_kantor (id, nama_lokasi, latitude, longitude, radius_meter)
            VALUES (1, 'Kantor Pusat', -6.179389, 106.607972, 50)
        """)

        # --- GENERATE PASSWORD SECARA AMAN ---
        # Password '123' diubah menjadi format acak (Hash) agar bisa login di web
        hashed_password_admin = generate_password_hash('123')
        hashed_password_staff = generate_password_hash('123')

        # 3. Isi User Admin (ID 1)
        cur.execute("""
            INSERT INTO users (nama_lengkap, username, password, role, divisi_id) 
            VALUES ('Super Admin', 'admin', %s, 'Admin', 1)
        """, (hashed_password_admin,))
        
        # 4. Isi User Staff Marketing (ID 2)
        cur.execute("""
            INSERT INTO users (nama_lengkap, username, password, role, divisi_id) 
            VALUES ('Fendi Andriyanto', 'fendi', %s, 'Staff', 2)
        """, (hashed_password_staff,))

        cur.close()
        conn.commit()
        print("[INFO] SELESAI! Database skripsi_db berhasil direset dengan password yang sudah aman.")
        
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"[ERROR] {error}")
    finally:
        if conn is not None:
            conn.close()

if __name__ == '__main__':
    create_tables()