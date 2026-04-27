import psycopg2
# Import fungsi koneksi dari app.py kamu
from app import get_db_connection 

def intip_kolom():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Kita minta 0 data, cuma buat lihat 'Header' tabelnya
        cur.execute("SELECT * FROM absensi LIMIT 0")
        
        # Ambil nama-nama kolom
        nama_kolom = [desc[0] for desc in cur.description]
        
        print("\n=== STRUKTUR TABEL ABSENSI KAMU ===")
        print(nama_kolom)
        print("===================================\n")
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    intip_kolom()