import cv2
import os
import numpy as np

# --- KONFIGURASI ---
cam = cv2.VideoCapture(0)
cam.set(3, 640) # Lebar kamera
cam.set(4, 480) # Tinggi kamera

face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Pastikan folder dataset ada
if not os.path.exists('dataset'):
    os.makedirs('dataset')

def cek_kualitas_foto(gray_frame):
    """Cek kecerahan dan blur dari frame grayscale"""
    kecerahan = np.mean(gray_frame)
    if kecerahan < 40:
        return False, "GELAP! Cari terang"
    if kecerahan > 220:
        return False, "SILAU! Mundur"
        
    blur_score = cv2.Laplacian(gray_frame, cv2.CV_64F).var()
    if blur_score < 80:
        return False, "BLUR! Diam"
        
    return True, ""

print("\n[INFO] Memulai Pengambilan Data Wajah...")
face_id = input('masukkan ID User (Angka, contoh: 1): ')
print("\n[INFO] Pastikan pencahayaan cukup terang.")

# --- SKENARIO PENGAMBILAN DATA ---
instruksi_sesi = [
    "Sesi 1: WAJAH DATAR (SERIUS)",
    "Sesi 2: WAJAH SENYUM (GIGI TERLIHAT)",
    "Sesi 3: SERONG KIRI SEDIKIT",
    "Sesi 4: SERONG KANAN SEDIKIT"
]

total_sesi = len(instruksi_sesi)
foto_per_sesi = 20
count_total = 0

for sesi_ke in range(total_sesi):
    count_sesi = 0
    siap_mulai = False
    
    # Loop Menunggu User Siap (Tekan S)
    while True:
        ret, frame = cam.read()
        frame = cv2.flip(frame, 1) # Mirror effect biar enak ngaca
        
        # Tampilkan Instruksi
        pesan = instruksi_sesi[sesi_ke]
        cv2.putText(frame, f"PERSIAPAN {pesan}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(frame, "Tekan tombol 'S' untuk mulai ambil foto", (50, 400), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Kotak di tengah biar user pas posisinya
        h, w, _ = frame.shape
        cv2.rectangle(frame, (w//2 - 100, h//2 - 120), (w//2 + 100, h//2 + 120), (255, 255, 255), 1)

        cv2.imshow('Ambil Data Wajah', frame)
        
        k = cv2.waitKey(1) & 0xff
        if k == ord('s'): # User tekan 's'
            siap_mulai = True
            break
        elif k == 27: # User tekan ESC
            print("[INFO] Dibatalkan user.")
            cam.release()
            cv2.destroyAllWindows()
            exit()

    # Loop Pengambilan Foto (Otomatis Jepret 20x)
    if siap_mulai:
        print(f"[INFO] Memulai {instruksi_sesi[sesi_ke]}...")
        while count_sesi < foto_per_sesi:
            ret, frame = cam.read()
            frame = cv2.flip(frame, 1)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_detector.detectMultiScale(gray, 1.3, 5)

            h_frame, w_frame = gray.shape
            luas_frame = h_frame * w_frame
            pesan_error = ""

            for (x, y, w, h) in faces:
                # Validasi jarak
                luas_wajah = w * h
                rasio_wajah = luas_wajah / luas_frame

                if rasio_wajah < 0.05:
                    pesan_error = "MAJU! Terlalu Jauh"
                elif rasio_wajah > 0.60:
                    pesan_error = "MUNDUR! Terlalu Dekat"
                else:
                    # Validasi cahaya & blur
                    kualitas_ok, pesan_kualitas = cek_kualitas_foto(gray)
                    if not kualitas_ok:
                        pesan_error = pesan_kualitas
                
                # Gambar kotak wajah
                warna_kotak = (0, 0, 255) if pesan_error else (0, 255, 0)
                cv2.rectangle(frame, (x, y), (x+w, y+h), warna_kotak, 2)
                
                if pesan_error:
                    cv2.putText(frame, pesan_error, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                else:
                    # Foto valid, simpan
                    count_total += 1
                    count_sesi += 1
                    cv2.imwrite(f"dataset/User.{face_id}.{count_total}.jpg", gray[y:y+h, x:x+w])
                    cv2.putText(frame, f"Ambil: {count_sesi}/{foto_per_sesi}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            # Tampilkan Judul Sesi
            cv2.putText(frame, f"SEDANG MEREKAM: {instruksi_sesi[sesi_ke]}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            cv2.imshow('Ambil Data Wajah', frame)
            
            # Delay sedikit biar foto gak sama persis semua (burst mode)
            k = cv2.waitKey(100) & 0xff 
            if k == 27: break

print("\n[INFO] Selesai! Data wajah telah tersimpan.")
cam.release()
cv2.destroyAllWindows()