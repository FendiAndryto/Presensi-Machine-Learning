import cv2
import numpy as np
import os 

# --- KONFIGURASI ---
# Inisialisasi Recognizer dan Load data yang sudah dilatih
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('trainer/trainer.yml')

# Load Haar Cascade (Pendeteksi Wajah)
cascadePath = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
faceCascade = cv2.CascadeClassifier(cascadePath)

# Font untuk tulisan di layar
font = cv2.FONT_HERSHEY_SIMPLEX

# Daftar Nama (ID 0 biasanya kosong, ID 1 adalah Anda)
# Jika nanti ada user ID 2, tambahkan namanya di list ini
names = ['Tidak Tahu', 'Pendi (Saya)', 'User 2', 'User 3'] 

# Mulai Kamera
cam = cv2.VideoCapture(0)
cam.set(3, 640) # Lebar
cam.set(4, 480) # Tinggi

# Tentukan ukuran minimal wajah yang dideteksi
minW = 0.1 * cam.get(3)
minH = 0.1 * cam.get(4)

print("[INFO] Kamera dimulai. Tekan 'ESC' untuk berhenti.")

while True:
    ret, img = cam.read()
    
    # Ubah ke Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Deteksi Wajah
    faces = faceCascade.detectMultiScale( 
        gray,
        scaleFactor = 1.2,
        minNeighbors = 5,
        minSize = (int(minW), int(minH)),
       )

    for(x,y,w,h) in faces:
        # Gambar kotak
        cv2.rectangle(img, (x,y), (x+w,y+h), (0,255,0), 2)
        
        # PREDIKSI SIAPA INI
        # Fungsi predict mengembalikan ID dan Confidence (Jarak kemiripan)
        id, confidence = recognizer.predict(gray[y:y+h,x:x+w])

        # Logika Confidence LBPH:
        # 0 = Cocok Sempurna
        # Semakin kecil angkanya, semakin mirip.
        # Biasanya di bawah 100 dianggap cocok.
        if (confidence < 100):
            nama_user = names[id]
            # Rumus konversi sederhana ke persen
            confidence_text = "  {0}%".format(round(100 - confidence))
        else:
            nama_user = "unknown"
            confidence_text = "  {0}%".format(round(100 - confidence))
        
        # Tampilkan Nama di layar
        cv2.putText(img, str(nama_user), (x+5,y-5), font, 1, (255,255,255), 2)
        # Tampilkan Persentase di layar
        cv2.putText(img, str(confidence_text), (x+5,y+h-5), font, 1, (255,255,0), 1)  

    cv2.imshow('Kamera Pengenalan Wajah', img) 

    # Tekan ESC untuk keluar
    k = cv2.waitKey(10) & 0xff 
    if k == 27:
        break

print("\n[INFO] Program selesai.")
cam.release()
cv2.destroyAllWindows()