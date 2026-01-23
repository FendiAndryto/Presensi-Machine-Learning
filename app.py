from flask import Flask, render_template, request, redirect, url_for, flash, Response, jsonify, session
import cv2
import os
import psycopg2
import math
from datetime import datetime
from werkzeug.utils import secure_filename
import numpy as np 
from PIL import Image

# Variabel Global untuk menyimpan frame terakhir
global_frame = None

# --- GLOBAL VARIABLES ---
last_detected_id = 0 
last_detected_name = "Unknown"

app = Flask(__name__)
app.secret_key = 'rahasia_skripsi_pendi' # Kunci untuk Session & Flash

# --- KONFIGURASI DATABASE ---
DB_NAME = "skripsi_db"
DB_USER = "postgres"
DB_PASS = "12345"  # <--- PASTIKAN PASSWORD BENAR
DB_HOST = "localhost"

# --- DATABASE CONNECTION ---
def get_db_connection():
    return psycopg2.connect(database=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)

# --- SETUP COMPUTER VISION (YANG SUDAH DIPERBAIKI) ---

cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
face_detector = cv2.CascadeClassifier(cascade_path)
recognizer = cv2.face.LBPHFaceRecognizer_create()

# Cek apakah file otak AI ada? Kalau ada, muat.
if os.path.exists('trainer/trainer.yml'):
    recognizer.read('trainer/trainer.yml')

# Gunakan Dictionary {} bukan List [] agar lebih aman & cepat
names = {} 

def load_user_names():
    """
    Fungsi ini bertugas mengambil daftar nama terbaru dari Database PostgreSQL.
    Dipanggil saat aplikasi mulai, atau setelah Training selesai.
    """
    global names
    names = {} # Reset memori dulu
    
    try:
        # Buka koneksi database (Pastikan fungsi get_db_connection ada di file ini)
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Ambil semua ID dan Nama Lengkap
        cur.execute("SELECT id, nama_lengkap FROM users")
        rows = cur.fetchall()
        
        for row in rows:
            user_id = row[0]
            nama_user = row[1]
            # Simpan ke memori: { 1: 'Admin', 2: 'Budi' }
            names[user_id] = nama_user
        
        # Tambahkan default untuk ID 0 (Unknown)
        names[0] = "Unknown"
        
        conn.close()
        print(f"[INFO] Berhasil memuat {len(names)} nama user dari Database.")
        
    except Exception as e:
        print(f"[ERROR] Gagal memuat nama user: {e}")
        # Jika database error, set default minimal agar tidak crash
        names = {0: "Unknown", 1: "Admin"}

# PANGGIL FUNGSI INI SEKALI SAAT STARTUP
load_user_names()

# Setup Kamera
camera = cv2.VideoCapture(0)

# --- FUNGSI BANTUAN ---

def hitung_jarak(lat1, lon1, lat2, lon2):
    R = 6371e3 
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# --- FITUR DATASET WEB ---

@app.route('/admin/ambil_dataset/<int:user_id>')
def view_ambil_dataset(user_id):
    if 'user_id' not in session or session['role'] != 'Admin': return redirect(url_for('index'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT nama_lengkap FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    conn.close()
    
    return render_template('ambil_dataset.html', user_id=user_id, nama_user=user[0])

# API: Dipanggil oleh Javascript untuk simpan 1 foto
@app.route('/api/simpan_frame', methods=['POST'])
def simpan_frame():
    global global_frame # Panggil variabel global tadi
    
    data = request.get_json()
    user_id = data['user_id']
    urutan = data['urutan']

    # Cek apakah global_frame sudah ada isinya?
    if global_frame is not None:
        # Kita pakai frame dari global, tidak perlu baca kamera lagi
        gray = cv2.cvtColor(global_frame, cv2.COLOR_BGR2GRAY)
        faces = face_detector.detectMultiScale(gray, 1.3, 5)
        
        if len(faces) > 0:
            (x, y, w, h) = faces[0]
            wajah = gray[y:y+h, x:x+w]
            
            path = f"dataset/User.{user_id}.{urutan}.jpg"
            cv2.imwrite(path, wajah)
            return jsonify({'status': 'success', 'pesan': f'Foto {urutan} tersimpan'})
        else:
            return jsonify({'status': 'error', 'pesan': 'Wajah tidak terdeteksi'})
    else:
        return jsonify({'status': 'error', 'pesan': 'Kamera belum siap'})

# --- FITUR TRAINING WEB ---
@app.route('/admin/train_model')
def train_model_web():
    if 'user_id' not in session or session['role'] != 'Admin': return redirect(url_for('index'))
    
    # LOGIKA TRAINING (Copas dari latih_wajah.py tapi versi function)
    path = 'dataset'
    if not os.path.exists(path): os.makedirs(path)
    
    imagePaths = [os.path.join(path, f) for f in os.listdir(path)]
    faceSamples = []
    ids = []
    
    for imagePath in imagePaths:
        try:
            PIL_img = Image.open(imagePath).convert('L')
            img_numpy = np.array(PIL_img, 'uint8')
            id = int(os.path.split(imagePath)[-1].split(".")[1])
            faces = face_detector.detectMultiScale(img_numpy)
            for (x, y, w, h) in faces:
                faceSamples.append(img_numpy[y:y+h, x:x+w])
                ids.append(id)
        except: pass
            
    if len(ids) > 0:
        recognizer.train(faceSamples, np.array(ids))
        recognizer.write('trainer/trainer.yml')
        flash(f'Training Selesai! {len(np.unique(ids))} User telah dipelajari.', 'success')
    else:
        flash('Data dataset kosong! Tidak bisa training.', 'danger')
        
    return redirect(url_for('kelola_users'))

# --- ROUTES AUTHENTICATION (LOGIN/LOGOUT) ---

@app.route('/', methods=['GET', 'POST'])
def index():
    # Jika sudah login, langsung lempar ke dashboard yang sesuai
    if 'user_id' in session:
        if session['role'] == 'Admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Cek Username & Password di Database
        cur.execute("SELECT id, nama_lengkap, role, password, divisi_id FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        conn.close()

        if user:
            # Validasi Password (Sementara Plain Text sesuai setup awal)
            if user[3] == password:
                # LOGIN SUKSES: Simpan data ke Session
                session['user_id'] = user[0]
                session['nama'] = user[1]
                session['role'] = user[2]
                session['divisi_id'] = user[4]
                
                # Cek Role untuk Redirect
                if user[2] == 'Admin':
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('dashboard'))
            else:
                flash('Password salah!', 'danger')
        else:
            flash('Username tidak ditemukan!', 'danger')
            
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.clear() 
    return redirect(url_for('index'))

# --- ROUTES STAFF ---

@app.route('/dashboard')
def dashboard():
    # 1. Proteksi Halaman (Cek Session)
    if 'user_id' not in session or session['role'] == 'Admin':
        return redirect(url_for('index'))

    user_id = session['user_id']
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 2. Ambil Data Profil User (Nama & Divisi)
    # Kita gunakan LEFT JOIN supaya kalau divisinya kosong, tidak error
    cur.execute("""
        SELECT users.nama_lengkap, divisi.nama_divisi 
        FROM users 
        LEFT JOIN divisi ON users.divisi_id = divisi.id 
        WHERE users.id = %s
    """, (user_id,))
    
    user_data = cur.fetchone()
    
    # Simpan ke variabel (Gunakan nilai default jika kosong)
    nama_lengkap = user_data[0] if user_data else session['nama']
    nama_divisi = user_data[1] if user_data and user_data[1] else "Staff Umum"

    # 3. Ambil Data Absensi Hari Ini (Kode Lama)
    cur.execute("SELECT jam_masuk, jam_pulang FROM absensi WHERE user_id = %s AND tanggal = CURRENT_DATE", (user_id,))
    data = cur.fetchone()
    
    conn.close()
    
    jam_masuk = data[0].strftime("%H:%M") if data and data[0] else "--:--"
    jam_pulang = data[1].strftime("%H:%M") if data and data[1] else "--:--"

    # 4. Kirim Data ke HTML (Perhatikan variabel baru: nama_lengkap & nama_divisi)
    return render_template('dashboard.html', 
                           jam_masuk=jam_masuk, 
                           jam_pulang=jam_pulang,
                           nama_lengkap=nama_lengkap,
                           nama_divisi=nama_divisi)

@app.route('/riwayat')
def riwayat():
    if 'user_id' not in session: return redirect(url_for('index'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT tanggal, jam_masuk, jam_pulang, status_kehadiran, lokasi_masuk 
        FROM absensi WHERE user_id = %s ORDER BY tanggal DESC LIMIT 30
    """, (session['user_id'],)) # Pakai ID dari session
    data = cur.fetchall()
    conn.close()
    return render_template('riwayat.html', data_absen=data)

@app.route('/izin', methods=['GET', 'POST'])
def izin():
    if 'user_id' not in session: return redirect(url_for('index'))
    user_id = session['user_id']

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        tgl_mulai = request.form['tgl_mulai']
        tgl_selesai = request.form['tgl_selesai']
        tipe = request.form['tipe_izin']
        ket = request.form['keterangan']
        file = request.files['bukti_foto']
        
        if file:
            filename = secure_filename(file.filename)
            nama_baru = f"izin_{user_id}_{filename}"
            path_simpan = os.path.join('static/uploads', nama_baru)
            file.save(path_simpan)
            
            cur.execute("""
                INSERT INTO pengajuan_izin (user_id, tanggal_mulai, tanggal_selesai, tipe_izin, keterangan, bukti_foto)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, tgl_mulai, tgl_selesai, tipe, ket, nama_baru))
            conn.commit()
            flash('Pengajuan Berhasil!', 'success')
            
    cur.execute("SELECT tanggal_mulai, tanggal_selesai, tipe_izin, keterangan, status_approval FROM pengajuan_izin WHERE user_id = %s ORDER BY id DESC LIMIT 5", (user_id,))
    riwayat = cur.fetchall()
    conn.close()
    return render_template('izin.html', riwayat=riwayat)

# --- ROUTES ADMIN ---

@app.route('/admin/dashboard')
def admin_dashboard():
    # 1. Proteksi Admin
    if 'user_id' not in session or session['role'] != 'Admin':
        flash('Akses Ditolak!', 'danger')
        return redirect(url_for('index'))

    conn = get_db_connection()
    cur = conn.cursor()
    
    # --- A. DATA STATISTIK ---
    # Hitung Total User (Role Staff)
    cur.execute("SELECT COUNT(*) FROM users WHERE role = 'Staff'")
    total_user = cur.fetchone()[0]
    
    # Hitung Yang Hadir Hari Ini
    cur.execute("SELECT COUNT(*) FROM absensi WHERE tanggal = CURRENT_DATE AND status_kehadiran = 'Hadir'")
    hadir = cur.fetchone()[0]
    
    # Hitung Yang Izin/Sakit Hari Ini (Yang sudah di-approve)
    # Note: Status approval 'Disetujui' dan tanggal masuk dalam range izin
    cur.execute("""
        SELECT COUNT(*) FROM pengajuan_izin 
        WHERE status_approval = 'Disetujui' 
        AND CURRENT_DATE BETWEEN tanggal_mulai AND tanggal_selesai
    """)
    izin = cur.fetchone()[0]

    stats = {
        'total_user': total_user,
        'hadir': hadir,
        'izin': izin
    }

    # --- B. DATA PENGAJUAN IZIN (PENDING) ---
    # Ambil daftar izin yang butuh persetujuan
    cur.execute("""
        SELECT p.id, u.nama_lengkap, d.nama_divisi, p.tipe_izin, p.keterangan, p.bukti_foto
        FROM pengajuan_izin p
        JOIN users u ON p.user_id = u.id
        LEFT JOIN divisi d ON u.divisi_id = d.id
        WHERE p.status_approval = 'Pending'
        ORDER BY p.id ASC
    """)
    list_izin = cur.fetchall()

    # --- C. DATA LIVE PRESENSI HARI INI ---
    # Siapa saja yang sudah absen hari ini?
    cur.execute("""
        SELECT u.nama_lengkap, a.jam_masuk, a.jam_pulang, d.nama_divisi
        FROM absensi a
        JOIN users u ON a.user_id = u.id
        LEFT JOIN divisi d ON u.divisi_id = d.id
        WHERE a.tanggal = CURRENT_DATE
        ORDER BY a.jam_masuk DESC
    """)
    live_absen = cur.fetchall()
    
    conn.close()

    tgl_sekarang = datetime.now().strftime('%d %B %Y')

    return render_template('admin_dashboard.html', 
                           stats=stats, 
                           list_izin=list_izin, 
                           live_absen=live_absen,
                           tgl_sekarang=tgl_sekarang)

# --- ROUTE AKSI ADMIN (APPROVE / REJECT) ---

@app.route('/admin/approve/<int:id>')
def approve_izin(id):
    # Proteksi Admin
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('index'))

    conn = get_db_connection()
    cur = conn.cursor()
    
    # Update Status jadi Disetujui
    try:
        cur.execute("UPDATE pengajuan_izin SET status_approval = 'Disetujui' WHERE id = %s", (id,))
        conn.commit()
        flash('Pengajuan Izin berhasil DISETUJUI.', 'success')
    except Exception as e:
        print(e)
        flash('Gagal update database.', 'danger')
        
    cur.close()
    conn.close()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject/<int:id>')
def reject_izin(id):
    # Proteksi Admin
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('index'))

    conn = get_db_connection()
    cur = conn.cursor()
    
    # Update Status jadi Ditolak
    try:
        cur.execute("UPDATE pengajuan_izin SET status_approval = 'Ditolak' WHERE id = %s", (id,))
        conn.commit()
        flash('Pengajuan Izin telah DITOLAK.', 'warning')
    except Exception as e:
        print(e)
        flash('Gagal update database.', 'danger')
        
    cur.close()
    conn.close()
    
    return redirect(url_for('admin_dashboard'))

# --- API & SYSTEM ROUTES ---

@app.route('/video_feed')
def video_feed():
    def generate_frames():
        global global_frame, last_detected_id, last_detected_name
        
        # Pastikan kamera terbuka
        if not camera.isOpened():
            camera.open(0)

        while True:
            try:
                success, frame = camera.read()
                
                # --- PERBAIKAN UTAMA DISINI ---
                if not success:
                    # Jika gagal baca, jangan break (mati). 
                    # Tapi skip loop ini dan coba baca lagi frame berikutnya.
                    continue 
                
                # Simpan ke global untuk fitur ambil foto
                global_frame = frame.copy()

                # --- Logika Deteksi Wajah ---
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_detector.detectMultiScale(gray, 1.2, 5)
                
                if len(faces) == 0:
                    last_detected_id = 0
                    last_detected_name = "Unknown"
                
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    try:
                        # Prediksi ID dan Confidence
                        id, confidence = recognizer.predict(gray[y:y+h, x:x+w])
                        
                        # Ambang batas (Makin kecil makin ketat/mirip)
                        if confidence < 60: 
                            last_detected_id = id
                            
                            # --- PERBAIKAN DISINI (Gunakan Dictionary .get) ---
                            # Artinya: Cari 'id' di kamus 'names'. 
                            # Jika tidak ketemu, kembalikan string "User {id}"
                            last_detected_name = names.get(id, f"User {id}")
                            # --------------------------------------------------
                            
                        else:
                            last_detected_id = 0
                            last_detected_name = "Unknown"
                        
                        # Tampilkan Nama di Layar
                        cv2.putText(frame, last_detected_name, (x+5, y-5), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    except Exception as e:
                        pass
                
                # Encode ke format JPG untuk browser
                ret, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            except Exception as e:
                print(f"Error Streaming: {e}")
                pass

    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/cek_jarak', methods=['POST'])
def cek_jarak_realtime():
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT latitude, longitude, radius_meter FROM lokasi_kantor WHERE id = 1")
    kantor = cur.fetchone()
    conn.close()
    
    jarak = hitung_jarak(data['latitude'], data['longitude'], float(kantor[0]), float(kantor[1]))
    status_text = "Di Dalam Jangkauan" if jarak <= kantor[2] else "Di Luar Jangkauan"
    status_class = "alert-success" if jarak <= kantor[2] else "alert-danger"
    icon = "fa-circle-check" if jarak <= kantor[2] else "fa-circle-xmark"
    
    return jsonify({'jarak': int(jarak), 'status_text': status_text, 'status_class': status_class, 'icon': icon})

@app.route('/proses_absen', methods=['POST'])
def proses_absen():
    global last_detected_id, last_detected_name
    
    # --- VALIDASI 1: APAKAH ADA WAJAH? ---
    if last_detected_id == 0:
        return jsonify({'status': 'error', 'pesan': 'Wajah tidak dikenali! Harap posisikan wajah dengan benar.'})

    # --- VALIDASI 2: ANTI-JOKI (PENTING!) ---
    # Cek apakah ID Wajah (AI) sama dengan ID Akun yang Login (Session)
    # Jangan sampai Budi login tapi yang absen wajahnya Anto.
    if 'user_id' in session:
        if session['user_id'] != last_detected_id:
            return jsonify({
                'status': 'error', 
                'pesan': f'Wajah tidak cocok! Anda login sebagai {session["nama"]}, tapi terdeteksi wajah {last_detected_name}.'
            })
    else:
        return jsonify({'status': 'error', 'pesan': 'Sesi habis. Silakan login ulang.'})

    # --- AMBIL DATA LOKASI ---
    data = request.get_json()
    user_lat = float(data['latitude'])
    user_long = float(data['longitude'])

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # --- VALIDASI 3: GEOFENCING ---
        cur.execute("SELECT latitude, longitude, radius_meter FROM lokasi_kantor WHERE id = 1")
        kantor = cur.fetchone()
        
        jarak = hitung_jarak(user_lat, user_long, float(kantor[0]), float(kantor[1]))
        radius_max = int(kantor[2])
        
        # Logika Pengecualian Marketing (Opsional)
        # Jika user divisi Marketing (ID 2), kita bisa skip validasi jarak
        is_marketing = (session.get('divisi_id') == 2) 

        if jarak > radius_max and not is_marketing:
            cur.close()
            conn.close()
            return jsonify({'status': 'error', 'pesan': f'Gagal! Lokasi terlalu jauh. Jarak: {int(jarak)}m (Max: {radius_max}m)'})

        # --- LOGIKA INTI (SKENARIO A, B, C) ---
        
        # Cek data hari ini
        cur.execute("""
            SELECT id, jam_masuk, jam_pulang FROM absensi 
            WHERE user_id = %s AND tanggal = CURRENT_DATE
        """, (last_detected_id,))
        
        data_absen = cur.fetchone()
        waktu_sekarang = datetime.now().strftime('%H:%M:%S')

        # SKENARIO A: BELUM ABSEN -> MASUK
        if data_absen is None:
            cur.execute("""
                INSERT INTO absensi (user_id, jam_masuk, lokasi_masuk, status_kehadiran)
                VALUES (%s, %s, %s, %s)
            """, (last_detected_id, waktu_sekarang, f"{user_lat},{user_long}", "Hadir"))
            conn.commit()
            pesan = f"Absen MASUK Berhasil! Semangat, {session['nama']}."

        # SKENARIO B: SUDAH MASUK, BELUM PULANG -> PULANG
        elif data_absen[2] is None:
            cur.execute("""
                UPDATE absensi 
                SET jam_pulang = %s, lokasi_pulang = %s 
                WHERE id = %s
            """, (waktu_sekarang, f"{user_lat},{user_long}", data_absen[0]))
            conn.commit()
            pesan = f"Absen PULANG Berhasil! Hati-hati di jalan, {session['nama']}."

        # SKENARIO C: SUDAH LENGKAP -> TOLAK
        else:
            cur.close()
            conn.close()
            return jsonify({'status': 'error', 'pesan': 'Anda sudah selesai absen hari ini.'})

        cur.close()
        conn.close()
        
        return jsonify({
            'status': 'success', 
            'pesan': pesan,
            'jarak': f"{int(jarak)} Meter"
        })

    except Exception as e:
        print(e)
        return jsonify({'status': 'error', 'pesan': 'Terjadi kesalahan sistem database.'})
    
@app.route('/admin/laporan', methods=['GET', 'POST'])
def laporan():
    # 1. Proteksi Admin
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('index'))

    conn = get_db_connection()
    cur = conn.cursor()

    # 2. Tentukan Periode (Default: Bulan & Tahun Sekarang)
    now = datetime.now()
    if request.method == 'POST':
        selected_month = int(request.form['bulan'])
        selected_year = int(request.form['tahun'])
    else:
        selected_month = now.month
        selected_year = now.year

    # 3. Query Super: Ambil semua user staff
    cur.execute("""
        SELECT u.id, u.nama_lengkap, d.nama_divisi 
        FROM users u 
        LEFT JOIN divisi d ON u.divisi_id = d.id 
        WHERE u.role = 'Staff'
        ORDER BY u.nama_lengkap ASC
    """)
    users = cur.fetchall()
    
    laporan_data = []

    # 4. Loop setiap user untuk hitung statistiknya di bulan terpilih
    for user in users:
        user_id = user[0]
        nama = user[1]
        divisi = user[2] if user[2] else "-"
        
        # A. Hitung HADIR
        cur.execute("""
            SELECT COUNT(*) FROM absensi 
            WHERE user_id = %s 
            AND EXTRACT(MONTH FROM tanggal) = %s 
            AND EXTRACT(YEAR FROM tanggal) = %s
            AND status_kehadiran = 'Hadir'
        """, (user_id, selected_month, selected_year))
        hadir = cur.fetchone()[0]

        # B. Hitung TERLAMBAT (Bonus: Misal masuk > 08:00)
        cur.execute("""
            SELECT COUNT(*) FROM absensi 
            WHERE user_id = %s 
            AND EXTRACT(MONTH FROM tanggal) = %s 
            AND EXTRACT(YEAR FROM tanggal) = %s
            AND jam_masuk > '08:00:00'
        """, (user_id, selected_month, selected_year))
        telat = cur.fetchone()[0]

        # C. Hitung IZIN/SAKIT (Approved Only)
        cur.execute("""
            SELECT COUNT(*) FROM pengajuan_izin 
            WHERE user_id = %s 
            AND status_approval = 'Disetujui'
            AND (EXTRACT(MONTH FROM tanggal_mulai) = %s OR EXTRACT(MONTH FROM tanggal_selesai) = %s)
        """, (user_id, selected_month, selected_month))
        izin = cur.fetchone()[0]
        
        # D. Hitung ALPHA (Sederhana: 20 hari kerja - Hadir - Izin)
        # Ini rumus kasar, bisa disesuaikan.
        hari_kerja = 20 
        alpha = hari_kerja - hadir - izin
        if alpha < 0: alpha = 0 # Biar gak minus kalau rajin lembur :D

        laporan_data.append({
            'nama': nama,
            'divisi': divisi,
            'hadir': hadir,
            'telat': telat,
            'izin': izin,
            'alpha': alpha
        })

    conn.close()

    return render_template('laporan.html', 
                           data_laporan=laporan_data, 
                           bln=selected_month, 
                           thn=selected_year,
                           tgl_cetak=now.strftime("%d %B %Y"))

# --- MANAJEMEN USER (CRUD) ---

@app.route('/admin/users', methods=['GET', 'POST'])
def kelola_users():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cur = conn.cursor()

    # Jika Tambah User Baru
    if request.method == 'POST':
        nama = request.form['nama']
        username = request.form['username']
        password = request.form['password']
        divisi_id = request.form['divisi']
        role = request.form['role'] # 'Staff' atau 'Admin'
        
        try:
            cur.execute("""
                INSERT INTO users (nama_lengkap, username, password, role, divisi_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (nama, username, password, role, divisi_id))
            conn.commit()
            flash('User berhasil ditambahkan! Silakan ambil dataset wajahnya.', 'success')
        except Exception as e:
            flash(f'Gagal menambah user: {e}', 'danger')

    # Ambil Data Users & Divisi
    cur.execute("SELECT u.id, u.nama_lengkap, u.username, u.role, d.nama_divisi FROM users u LEFT JOIN divisi d ON u.divisi_id = d.id ORDER BY u.id DESC")
    users = cur.fetchall()
    
    cur.execute("SELECT * FROM divisi")
    divisi_list = cur.fetchall()
    
    conn.close()
    return render_template('kelola_users.html', users=users, divisi_list=divisi_list)

@app.route('/admin/hapus_user/<int:id>')
def hapus_user(id):
    if 'user_id' not in session or session['role'] != 'Admin': return redirect(url_for('index'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = %s", (id,))
    conn.commit()
    conn.close()
    
    # Hapus juga dataset wajahnya (Opsional tapi bagus untuk kebersihan)
    # Anda bisa tambahkan logic hapus file User.ID.*.jpg disini nanti
    
    flash('User berhasil dihapus.', 'warning')
    return redirect(url_for('kelola_users'))
    
    # --- TAMBAHAN KEAMANAN: NO CACHE ---
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
    # app.run(host='0.0.0.0', port=5000, debug=True)