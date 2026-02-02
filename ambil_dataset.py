import cv2
import os

# --- KONFIGURASI ---
cam = cv2.VideoCapture(0)
cam.set(3, 640) # Lebar kamera
cam.set(4, 480) # Tinggi kamera

face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Pastikan folder dataset ada
if not os.path.exists('dataset'):
    os.makedirs('dataset')

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

            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                count_total += 1
                count_sesi += 1
                
                # Simpan ke folder dataset
                # Format: User.ID.Urutan.jpg
                cv2.imwrite(f"dataset/User.{face_id}.{count_total}.jpg", gray[y:y+h, x:x+w])
                
                # Tampilkan Progress
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