from flask import Flask, render_template, Response, request, redirect, url_for, flash, session, jsonify 
import cv2
import os
import psycopg2
import math
from datetime import datetime
from werkzeug.utils import secure_filename
import numpy as np 
from PIL import Image
from werkzeug.security import generate_password_hash, check_password_hash
import threading
import base64
from flask import send_file, flash, get_flashed_messages
from io import BytesIO
import pandas as pd

global_frame = None
last_detected_id = 0 
last_detected_name = "Unknown"
frame_lock = threading.Lock() # <-- TAMBAHKAN INI

app = Flask(__name__)
app.secret_key = 'rahasia_skripsi_pendi' # Kunci untuk Session & Flash

# --- KONFIGURASI DATABASE ---
DB_NAME = "skripsi_db"
DB_USER = "postgres"
DB_PASS = "12345"  
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
        except Exception as e: 
            print(f"[WARNING] Gagal memproses gambar {imagePath}: {e}")
            continue # Lanjut ke foto berikutnya
            
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
            # --- KODE BARU: Validasi menggunakan check_password_hash ---
            # user[3] adalah password dari database
            if check_password_hash(user[3], password):
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

    # 2. Profil User
    cur.execute("""
        SELECT u.nama_lengkap, d.nama_divisi
        FROM users u
        LEFT JOIN divisi d ON u.divisi_id = d.id
        WHERE u.id = %s
    """, (user_id,))
    user_data = cur.fetchone()
    nama_lengkap = user_data[0] if user_data else session.get('nama', '')
    nama_divisi  = user_data[1] if user_data and user_data[1] else "Staff Umum"

    # 3. Absensi hari ini (jam masuk, jam pulang, durasi_kerja)
    cur.execute("""
        SELECT jam_masuk,
               jam_pulang,
               durasi_kerja
        FROM absensi
        WHERE user_id = %s
          AND tanggal = CURRENT_DATE
    """, (user_id,))
    data = cur.fetchone()
    conn.close()

    # 4. Format nilai untuk template
    jam_masuk = data[0].strftime("%H:%M") if data and data[0] else "--:--"
    jam_pulang = data[1].strftime("%H:%M") if data and data[1] else "--:--"

    # durasi_kerja sudah berupa interval (timedelta di psycopg2)
    if data and data[2]:
        total_seconds = data[2].total_seconds()
        hours   = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        durasi_kerja = f"{hours:02d}:{minutes:02d}"
    else:
        durasi_kerja = "--:--"

    # 5. Render template
    return render_template(
        'dashboard.html',
        jam_masuk=jam_masuk,
        jam_pulang=jam_pulang,
        durasi_kerja=durasi_kerja,
        nama_lengkap=nama_lengkap,
        nama_divisi=nama_divisi
    )


@app.route('/riwayat')
def riwayat():
    if 'user_id' not in session: 
        return redirect(url_for('index'))
    
    # 1. Setup Konfigurasi Waktu Real-time
    now = datetime.now()
    nama_bulan = {
        1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
        5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
        9: "September", 10: "Oktober", 11: "November", 12: "Desember"
    }

    # 2. Ambil parameter dari URL, default ke bulan & tahun saat ini
    # type=int memastikan data dikonversi ke angka untuk query database
    bln = request.args.get('bulan', default=now.month, type=int)
    thn = request.args.get('tahun', default=now.year, type=int)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 3. Query PostgreSQL menggunakan EXTRACT
    # Kita memfilter data berdasarkan user_id, bulan, dan tahun
    query = """
        SELECT tanggal, jam_masuk, jam_pulang, status_kehadiran, lokasi_masuk, durasi_kerja 
        FROM absensi 
        WHERE user_id = %s 
        AND EXTRACT(MONTH FROM tanggal) = %s 
        AND EXTRACT(YEAR FROM tanggal) = %s
        ORDER BY tanggal DESC
    """
    
    cur.execute(query, (session['user_id'], bln, thn))
    data = cur.fetchall()
    conn.close()

    # Membuat daftar pilihan tahun (misal: 3 tahun kebelakang)
    years = range(now.year, now.year - 3, -1) 

    return render_template(
        'riwayat.html',
        data_absen=data,
        bln=bln,
        thn=thn,
        nama_bulan=nama_bulan,
        years=years
    )

@app.route('/riwayat/export')
def export_riwayat_excel():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    now = datetime.now()

    nama_bulan = {
        1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
        5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
        9: "September", 10: "Oktober", 11: "November", 12: "Desember"
    }

    bln = request.args.get('bulan', default=now.month, type=int)
    thn = request.args.get('tahun', default=now.year, type=int)

    conn = get_db_connection()
    cur = conn.cursor()

    query = """
        SELECT tanggal, jam_masuk, jam_pulang, status_kehadiran, lokasi_masuk, durasi_kerja
        FROM absensi
        WHERE user_id = %s
        AND EXTRACT(MONTH FROM tanggal) = %s
        AND EXTRACT(YEAR FROM tanggal) = %s
        ORDER BY tanggal DESC
    """

    cur.execute(query, (session['user_id'], bln, thn))
    data = cur.fetchall()

    laporan_data = []

    for row in data:
        tanggal = row[0].strftime('%d-%m-%Y')

        jam_masuk = row[1].strftime('%H:%M') if row[1] else '--:--'
        jam_pulang = row[2].strftime('%H:%M') if row[2] else '--:--'

        status = row[3]
        lokasi = row[4] if row[4] else '-'

        # Format durasi kerja
        if row[5]:
            total_seconds = row[5].total_seconds()

            jam = int(total_seconds // 3600)
            menit = int((total_seconds % 3600) // 60)

            durasi = f"{jam} Jam {menit} Menit"
        else:
            durasi = "--:--"

        laporan_data.append({
            'Tanggal': tanggal,
            'Jam Masuk': jam_masuk,
            'Jam Pulang': jam_pulang,
            'Durasi Kerja': durasi,
            'Status': status,
            'Lokasi': lokasi
        })

    conn.close()

    # ================= EXPORT EXCEL =================
    df = pd.DataFrame(laporan_data)

    output = BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Riwayat Absensi')

        worksheet = writer.sheets['Riwayat Absensi']

        # Auto width kolom
        for column_cells in worksheet.columns:
            length = max(len(str(cell.value)) if cell.value else 0 for cell in column_cells)
            worksheet.column_dimensions[column_cells[0].column_letter].width = length + 5

    output.seek(0)

    filename = f"Riwayat_Absensi_{nama_bulan[bln]}_{thn}.xlsx"

    return send_file(
        output,
        download_name=filename,
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# --- ROUTES ADMIN ---

@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'Admin':
        flash('Akses Ditolak!', 'danger')
        return redirect(url_for('index'))

    conn = get_db_connection()
    cur = conn.cursor()

    # ---------- Filter ----------
    tanggal = request.form.get('tanggal')
    bln     = request.form.get('bulan')
    thn     = request.form.get('tahun')

    where_clause = ""
    params = []

    if tanggal:
        where_clause = "DATE(a.tanggal) = %s"
        params.append(tanggal)
    elif bln and thn:
        where_clause = "EXTRACT(MONTH FROM a.tanggal) = %s AND EXTRACT(YEAR FROM a.tanggal) = %s"
        params.extend([bln, thn])
    elif thn:
        where_clause = "EXTRACT(YEAR FROM a.tanggal) = %s"
        params.append(thn)
    else:
        today = datetime.today().strftime('%Y-%m-%d')
        where_clause = "DATE(a.tanggal) = %s"
        params.append(today)

    # ---------- Statistik ----------
    cur.execute("SELECT COUNT(*) FROM users WHERE role = 'Staff'")
    total_user = cur.fetchone()[0]

    cur.execute(f"SELECT COUNT(*) FROM absensi a WHERE {where_clause} AND status_kehadiran = 'Hadir'", params)
    hadir = cur.fetchone()[0]

    stats = {'total_user': total_user, 'hadir': hadir}

    # ---------- Data absensi (tambahkan durasi_kerja) ----------
    query_absen = f"""
        SELECT u.nama_lengkap,
               a.jam_masuk,
               a.jam_pulang,
               a.durasi_kerja,          -- ← baru
               d.nama_divisi,
               a.tanggal
        FROM absensi a
        JOIN users u ON a.user_id = u.id
        LEFT JOIN divisi d ON u.divisi_id = d.id
        WHERE {where_clause}
        ORDER BY a.tanggal DESC, a.jam_masuk DESC
    """
    cur.execute(query_absen, params)
    live_absen = cur.fetchall()          # setiap baris = (nama, masuk, pulang, durasi, divisi, tanggal)

    conn.close()

    nama_bulan = {
        1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
        5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
        9: "September", 10: "Oktober", 11: "November", 12: "Desember"
    }

    tgl_input   = datetime.today().strftime('%Y-%m-%d')
    tgl_sekarang = datetime.now().strftime('%d %B %Y')

    return render_template(
        'admin_dashboard.html',
        stats=stats,
        live_absen=live_absen,
        tgl_sekarang=tgl_sekarang,
        tanggal=tanggal,
        bln=int(bln) if bln else None,
        thn=int(thn) if thn else None,
        nama_bulan=nama_bulan,
        tgl_input=tgl_input
    )


@app.route('/video_feed')
def video_feed():
    # [PROTEKSI] Cek apakah yang akses itu localhost atau dari luar (Cloudflared)
    host = request.host
    is_local = "localhost" in host or "127.0.0.1" in host

    def generate_frames():
        global global_frame, last_detected_id, last_detected_name
        
        # JANGAN buka kamera laptop kalau diakses dari luar (Cloudflared/HP lain)
        if not is_local:
            print(f"[INFO] Akses luar terdeteksi ({host}). Kamera laptop tetap mati.")
            return

        # Hanya jalankan ini kalau dibuka langsung di laptop server (localhost)
        cap = cv2.VideoCapture(0) 

        if not cap.isOpened():
            print("[ERROR] Tidak dapat mengakses kamera laptop.")
            return

        while True:
            try:
                success, frame = cap.read()
                if not success:
                    continue 
                
                with frame_lock:
                    global_frame = frame.copy()

                # --- Logika Deteksi Wajah ---
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_detector.detectMultiScale(gray, 1.2, 5)
                
                if len(faces) == 0:
                    with frame_lock:
                        last_detected_id = 0
                        last_detected_name = "Unknown"
                
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    try:
                        id_pred, confidence = recognizer.predict(gray[y:y+h, x:x+w])
                        if confidence < 60: 
                            with frame_lock:
                                last_detected_id = id_pred
                                last_detected_name = names.get(id_pred, f"User {id_pred}")
                        else:
                            with frame_lock:
                                last_detected_id = 0
                                last_detected_name = "Unknown"
                        
                        cv2.putText(frame, last_detected_name, (x+5, y-5), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    except Exception as e:
                        pass
                
                ret, buffer = cv2.imencode('.jpg', frame)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            
            except Exception as e:
                break

        cap.release()
        print("[INFO] Kamera laptop dimatikan.")

    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/cek_jarak', methods=['POST'])
def cek_jarak_realtime():
    try:
        data = request.get_json()
        
        # Validasi input biar gak error pas diproses
        if not data or 'latitude' not in data or 'longitude' not in data:
            return jsonify({'error': 'Data lokasi tidak lengkap'}), 400

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT latitude, longitude, radius_meter FROM lokasi_kantor WHERE id = 1")
        kantor = cur.fetchone()
        cur.close() # Tutup cursor biar rapi
        conn.close()
        
        if not kantor:
            return jsonify({'error': 'Data lokasi kantor belum diset'}), 404
        
        jarak = hitung_jarak(data['latitude'], data['longitude'], float(kantor[0]), float(kantor[1]))
        
        # Penentuan status (Logic lo tetap dipertahankan)
        status_text = "Di Dalam Jangkauan" if jarak <= kantor[2] else "Di Luar Jangkauan"
        status_class = "alert-success" if jarak <= kantor[2] else "alert-danger"
        icon = "fa-circle-check" if jarak <= kantor[2] else "fa-circle-xmark"
        
        return jsonify({
            'jarak': int(jarak), 
            'status_text': status_text, 
            'status_class': status_class, 
            'icon': icon
        })
    except Exception as e:
        print(f"[ERROR API] Cek Jarak Gagal: {e}")
        return jsonify({'error': 'Gagal mengambil data lokasi'}), 500

@app.route('/proses_absen', methods=['POST'])
def proses_absen():
    global last_detected_id, last_detected_name
    
    with frame_lock:
        current_id   = last_detected_id
        current_name = last_detected_name
    
    if current_id == 0:
        return jsonify({'status': 'error',
                        'pesan': 'Wajah tidak dikenali! Harap posisikan wajah dengan benar.'})
    
    if 'user_id' not in session:
        return jsonify({'status': 'error',
                        'pesan': 'Sesi habis. Silakan login ulang.'})
    if session['user_id'] != current_id:
        return jsonify({'status': 'error',
                        'pesan': f'Wajah tidak cocok! Anda login sebagai {session["nama"]}, '
                                 f'tapi terdeteksi wajah {current_name}.'})

    data = request.get_json()
    user_lat  = float(data['latitude'])
    user_long = float(data['longitude'])

    try:
        conn = get_db_connection()
        cur  = conn.cursor()

        # ---- GEO‑FENCING -------------------------------------------------
        cur.execute("SELECT latitude, longitude, radius_meter FROM lokasi_kantor WHERE id = 1")
        kantor = cur.fetchone()
        jarak = hitung_jarak(user_lat, user_long,
                             float(kantor[0]), float(kantor[1]))
        radius_max = int(kantor[2])
        is_marketing = (session.get('divisi_id') == 2)

        if jarak > radius_max and not is_marketing:
            cur.close(); conn.close()
            return jsonify({'status': 'error',
                            'pesan': f'Gagal! Lokasi terlalu jauh. Jarak: {int(jarak)}m (Max: {radius_max}m)'})

        # ---- CEK ABSENSI HARI INI ---------------------------------------
        cur.execute("""
            SELECT id, jam_masuk, jam_pulang
            FROM absensi
            WHERE user_id = %s AND tanggal = CURRENT_DATE
        """, (current_id,))
        data_absen = cur.fetchone()
        waktu_sekarang = datetime.now().strftime('%H:%M:%S')

        # -------- A: BELUM ABSEN (MASUK) ---------------------------------
        if data_absen is None:
            cur.execute("""
                INSERT INTO absensi (user_id, jam_masuk, lokasi_masuk, status_kehadiran)
                VALUES (%s, %s, %s, %s)
            """, (current_id, waktu_sekarang,
                  f"{user_lat},{user_long}", "Hadir"))
            conn.commit()
            pesan = f"Absen MASUK Berhasil! Semangat, {session['nama']}."

        # -------- B: SUDAH MASUK, BELUM PULANG (PULANG) ------------------
        elif data_absen[2] is None:
            cur.execute("""
                UPDATE absensi
                SET jam_pulang = %s,
                    lokasi_pulang = %s
                WHERE id = %s
            """, (waktu_sekarang,
                  f"{user_lat},{user_long}",
                  data_absen[0]))
            conn.commit()
            # durasi_kerja ter‑generate otomatis oleh DB
            pesan = f"Absen PULANG Berhasil! Hati-hati di jalan, {session['nama']}."

        # -------- C: SUDAH LENGKAP ---------------------------------------
        else:
            cur.close(); conn.close()
            return jsonify({'status': 'error',
                            'pesan': 'Anda sudah selesai absen hari ini.'})

        cur.close(); conn.close()
        return jsonify({'status': 'success',
                        'pesan': pesan,
                        'jarak': f"{int(jarak)} Meter"})

    except Exception as e:
        print(f"[ERROR DB] Absensi gagal: {e}")
        return jsonify({'status': 'error',
                        'pesan': 'Terjadi kesalahan sistem database.'})

    
# capture via javascript WebRTC
@app.route('/proses_absen_mobile', methods=['POST'])
def proses_absen_mobile():
    try:
        data = request.get_json()
        img_data   = data['image']               # base64
        user_lat   = float(data['latitude'])
        user_long  = float(data['longitude'])

        # ---- Decode foto -------------------------------------------------
        img_bytes = base64.b64decode(img_data.split(',')[1])
        nparr     = np.frombuffer(img_bytes, np.uint8)
        frame     = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        gray      = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # ---- Deteksi wajah -----------------------------------------------
        faces = face_detector.detectMultiScale(gray, 1.2, 5)
        if len(faces) == 0:
            return jsonify({'status': 'error',
                            'pesan': 'Wajah tidak terdeteksi! Pastikan wajah terlihat jelas di HP.'})

        for (x, y, w, h) in faces:
            id_wajah, confidence = recognizer.predict(gray[y:y+h, x:x+w])
            if confidence > 60:
                return jsonify({'status': 'error',
                                'pesan': 'Wajah tidak dikenali!'})
            if session.get('user_id') != id_wajah:
                return jsonify({'status': 'error',
                                'pesan': f'Bukan wajah {session["nama"]}!'})

            # ---- Logika yang sama dengan /proses_absen ------------------
            conn = get_db_connection()
            cur  = conn.cursor()

            # Geo‑fencing
            cur.execute("SELECT latitude, longitude, radius_meter FROM lokasi_kantor WHERE id = 1")
            kantor = cur.fetchone()
            jarak = hitung_jarak(user_lat, user_long,
                                 float(kantor[0]), float(kantor[1]))
            radius_max = int(kantor[2])
            is_marketing = (session.get('divisi_id') == 2)

            if jarak > radius_max and not is_marketing:
                cur.close(); conn.close()
                return jsonify({'status': 'error',
                                'pesan': f'Gagal! Lokasi terlalu jauh. Jarak: {int(jarak)}m'})

            # Cek data hari ini
            cur.execute("""
                SELECT id, jam_masuk, jam_pulang
                FROM absensi
                WHERE user_id = %s AND tanggal = CURRENT_DATE
            """, (id_wajah,))
            data_absen = cur.fetchone()
            waktu_sekarang = datetime.now().strftime('%H:%M:%S')

            # ---- A: Masuk -------------------------------------------------
            if data_absen is None:
                cur.execute("""
                    INSERT INTO absensi (user_id, jam_masuk, lokasi_masuk, status_kehadiran)
                    VALUES (%s, %s, %s, %s)
                """, (id_wajah, waktu_sekarang,
                      f"{user_lat},{user_long}", "Hadir"))
                pesan = f"Absen MASUK via HP Berhasil! Semangat, {session['nama']}."
            # ---- B: Pulang ------------------------------------------------
            elif data_absen[2] is None:
                cur.execute("""
                    UPDATE absensi
                    SET jam_pulang = %s,
                        lokasi_pulang = %s
                    WHERE id = %s
                """, (waktu_sekarang,
                      f"{user_lat},{user_long}",
                      data_absen[0]))
                pesan = f"Absen PULANG via HP Berhasil! Hati-hati di jalan."
                # durasi_kerja dihitung otomatis oleh DB
            # ---- C: Sudah selesai -----------------------------------------
            else:
                cur.close(); conn.close()
                return jsonify({'status': 'error',
                                'pesan': 'Anda sudah selesai absen hari ini.'})

            conn.commit()
            cur.close(); conn.close()
            return jsonify({'status': 'success',
                            'pesan': pesan,
                            'jarak': f"{int(jarak)}m"})

        return jsonify({'status': 'error', 'pesan': 'Gagal memproses wajah.'})

    except Exception as e:
        print(f"Error Mobile Absen: {e}")
        return jsonify({'status': 'error',
                        'pesan': 'Terjadi kesalahan sistem.'})

    
@app.route('/admin/laporan', methods=['GET', 'POST'])
def laporan():
    if 'user_id' not in session or session.get('role') != 'Admin':
        return redirect(url_for('index'))

    now = datetime.now()
    nama_bulan = {
        1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
        5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
        9: "September", 10: "Oktober", 11: "November", 12: "Desember"
    }

    # --------- ambil bulan & tahun ----------
    if request.method == 'POST':
        selected_month = int(request.form.get('bulan', now.month))
        selected_year  = int(request.form.get('tahun', now.year))
    else:
        selected_month = request.args.get('bulan', default=now.month, type=int)
        selected_year  = request.args.get('tahun', default=now.year, type=int)

    conn = get_db_connection()
    cur  = conn.cursor()

    # --------- daftar staff ----------
    cur.execute("""
        SELECT u.id, u.nama_lengkap, d.nama_divisi
        FROM users u
        LEFT JOIN divisi d ON u.divisi_id = d.id
        WHERE u.role = 'Staff'
        ORDER BY u.nama_lengkap ASC
    """)
    users = cur.fetchall()

    laporan_data = []

    for user in users:
        user_id, nama, divisi = user
        divisi = divisi if divisi else "-"

        # ----- hadir -----
        cur.execute("""
            SELECT COUNT(*)
            FROM absensi
            WHERE user_id = %s
              AND EXTRACT(MONTH FROM tanggal) = %s
              AND EXTRACT(YEAR FROM tanggal) = %s
              AND status_kehadiran = 'Hadir'
        """, (user_id, selected_month, selected_year))
        hadir = cur.fetchone()[0]

        # ----- terlambat -----
        cur.execute("""
            SELECT COUNT(*)
            FROM absensi
            WHERE user_id = %s
              AND EXTRACT(MONTH FROM tanggal) = %s
              AND EXTRACT(YEAR FROM tanggal) = %s
              AND jam_masuk > '08:00:00'
        """, (user_id, selected_month, selected_year))
        telat = cur.fetchone()[0]

        # ----- total jam kerja (interval) -----
        cur.execute("""
            SELECT SUM(durasi_kerja) AS total_interval
            FROM absensi
            WHERE user_id = %s
              AND EXTRACT(MONTH FROM tanggal) = %s
              AND EXTRACT(YEAR FROM tanggal) = %s
              AND status_kehadiran = 'Hadir'
        """, (user_id, selected_month, selected_year))
        total_interval = cur.fetchone()[0]   # None bila tidak ada data

        if total_interval:
            # total_interval adalah datetime.timedelta
            total_seconds = total_interval.total_seconds()
            jam   = int(total_seconds // 3600)                # jam penuh
            menit = int((total_seconds % 3600) // 60)         # sisa menit
            jam_kerja_hm = f"{jam} jam {menit} menit"
            jam_kerja_decimal = round(total_seconds / 3600, 2)   # untuk Excel bila diperlukan
        else:
            jam_kerja_hm = "0 jam 0 menit"
            jam_kerja_decimal = 0.0

        laporan_data.append({
            'nama'            : nama,
            'divisi'          : divisi,
            'hadir'           : hadir,
            'telat'           : telat,
            'jam_kerja_hm'    : jam_kerja_hm,      # <-- dipakai di HTML
            'jam_kerja_dec'   : jam_kerja_decimal # <-- dipakai di export Excel
        })

    conn.close()

    years = range(now.year, now.year - 3, -1)

    return render_template(
        'laporan.html',
        data_laporan=laporan_data,
        bln=selected_month,
        thn=selected_year,
        nama_bulan=nama_bulan,
        years=years,
        tgl_cetak=now.strftime("%d %B %Y")
    )

@app.route('/admin/laporan/export')
def export_laporan_excel():
    if 'user_id' not in session or session.get('role') != 'Admin':
        return redirect(url_for('index'))

    now = datetime.now()

    selected_month = request.args.get('bulan', default=now.month, type=int)
    selected_year  = request.args.get('tahun', default=now.year, type=int)

    nama_bulan = {
        1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
        5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
        9: "September", 10: "Oktober", 11: "November", 12: "Desember"
    }

    conn = get_db_connection()
    cur = conn.cursor()

    # Ambil data staff
    cur.execute("""
        SELECT u.id, u.nama_lengkap, d.nama_divisi
        FROM users u
        LEFT JOIN divisi d ON u.divisi_id = d.id
        WHERE u.role = 'Staff'
        ORDER BY u.nama_lengkap ASC
    """)

    users = cur.fetchall()

    laporan_data = []

    for user in users:
        user_id, nama, divisi = user
        divisi = divisi if divisi else "-"

        # ================= HADIR =================
        cur.execute("""
            SELECT COUNT(*)
            FROM absensi
            WHERE user_id = %s
              AND EXTRACT(MONTH FROM tanggal) = %s
              AND EXTRACT(YEAR FROM tanggal) = %s
              AND status_kehadiran = 'Hadir'
        """, (user_id, selected_month, selected_year))

        hadir = cur.fetchone()[0]

        # ================= TERLAMBAT =================
        cur.execute("""
            SELECT COUNT(*)
            FROM absensi
            WHERE user_id = %s
              AND EXTRACT(MONTH FROM tanggal) = %s
              AND EXTRACT(YEAR FROM tanggal) = %s
              AND jam_masuk > '08:00:00'
        """, (user_id, selected_month, selected_year))

        telat = cur.fetchone()[0]

        # ================= TOTAL JAM KERJA =================
        cur.execute("""
            SELECT SUM(durasi_kerja)
            FROM absensi
            WHERE user_id = %s
              AND EXTRACT(MONTH FROM tanggal) = %s
              AND EXTRACT(YEAR FROM tanggal) = %s
              AND status_kehadiran = 'Hadir'
        """, (user_id, selected_month, selected_year))

        total_interval = cur.fetchone()[0]

        if total_interval:
            total_seconds = total_interval.total_seconds()

            jam = int(total_seconds // 3600)
            menit = int((total_seconds % 3600) // 60)

            jam_kerja = f"{jam} Jam {menit} Menit"
        else:
            jam_kerja = "0 Jam 0 Menit"

        laporan_data.append({
            'Nama Karyawan': nama,
            'Divisi': divisi,
            'Total Hadir': f"{hadir} Hari",
            'Terlambat': f"{telat} Kali",
            'Total Jam Kerja': jam_kerja
        })

    conn.close()

    # ================= DATAFRAME =================
    df = pd.DataFrame(laporan_data)

    # ================= EXPORT EXCEL =================
    output = BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Laporan Absensi')

        worksheet = writer.sheets['Laporan Absensi']

        # Auto width column
        for column_cells in worksheet.columns:
            length = max(len(str(cell.value)) if cell.value else 0 for cell in column_cells)
            worksheet.column_dimensions[column_cells[0].column_letter].width = length + 5

    output.seek(0)

    filename = f"Laporan_Absensi_{nama_bulan[selected_month]}_{selected_year}.xlsx"

    return send_file(
        output,
        download_name=filename,
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

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
        role = request.form['role'] 
        
        # --- KODE BARU: Mengacak password sebelum masuk database ---
        hashed_password = generate_password_hash(password)
        
        try:
            cur.execute("""
                INSERT INTO users (nama_lengkap, username, password, role, divisi_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (nama, username, hashed_password, role, divisi_id)) # Gunakan hashed_password
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

@app.route('/admin/edit_user/<int:id>', methods=['POST'])
def edit_user(id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('index'))

    nama = request.form['nama']
    divisi_id = request.form['divisi']
    role = request.form['role']
    new_password = request.form['password']
    
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        if new_password:  # Jika admin mengisi kolom password
            hashed_password = generate_password_hash(new_password)
            cur.execute("""
                UPDATE users 
                SET nama_lengkap = %s, divisi_id = %s, role = %s, password = %s 
                WHERE id = %s
            """, (nama, divisi_id, role, hashed_password, id))
        else:  # Jika password dikosongkan
            cur.execute("""
                UPDATE users 
                SET nama_lengkap = %s, divisi_id = %s, role = %s 
                WHERE id = %s
            """, (nama, divisi_id, role, id))
            
        conn.commit()
        flash(f'Data {nama} berhasil diperbarui!', 'success')
    except Exception as e:
        flash(f'Gagal update user: {e}', 'danger')
    finally:
        conn.close()

    return redirect(url_for('kelola_users'))

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
    # Tambahkan threaded=True agar streaming tidak terganggu saat tombol ditekan
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)