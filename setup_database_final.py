import psycopg2
from psycopg2 import sql
from werkzeug.security import generate_password_hash # TAMBAHAN: Import untuk keamanan password

# --- KONFIGURASI DATABASE ---
DB_NAME = "skripsi_db"
DB_USER = "postgres"
DB_PASS = "12345"       
DB_HOST = "localhost"

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
            durasi_kerja VARCHAR(20),
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
        """,

        # 5. Tabel PENGAJUAN IZIN
        """
        CREATE TABLE IF NOT EXISTS pengajuan_izin (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            tanggal_mulai DATE NOT NULL,
            tanggal_selesai DATE NOT NULL,
            tipe_izin VARCHAR(20),
            keterangan TEXT,
            bukti_foto VARCHAR(255),
            status_approval VARCHAR(20) DEFAULT 'Pending',
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
        """
    )

    conn = None
    try:
        conn = psycopg2.connect(database=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cur = conn.cursor()
        
        print("[INFO] Menghapus tabel lama (KECUALI lokasi_kantor) agar bersih...")
        # Urutan drop penting karena Foreign Key!
        cur.execute("DROP TABLE IF EXISTS pengajuan_izin")
        cur.execute("DROP TABLE IF EXISTS absensi")
        cur.execute("DROP TABLE IF EXISTS users")
        cur.execute("DROP TABLE IF EXISTS divisi")
        # NOTE: DROP TABLE lokasi_kantor KITA HAPUS agar koordinat aman.

        print("[INFO] Membuat struktur tabel baru...")
        for command in commands:
            cur.execute(command)
        
        # --- SEEDING DATA (Isi Data Awal) ---
        print("[INFO] Mengisi data default...")
        
        # 1. Isi Divisi
        cur.execute("INSERT INTO divisi (nama_divisi) VALUES ('IT'), ('Marketing'), ('Keuangan'), ('HRD')")
        
        # 2. Isi Lokasi Kantor (Dihapus/Dicoment)
        # Kita tidak melakukan INSERT lagi agar data koordinat yang sudah ada di database tidak double/tertimpa.
        # Jika tabelnya ternyata kosong, kamu bisa input manual di DBeaver/pgAdmin.

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