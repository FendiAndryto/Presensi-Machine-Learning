"""
Kenali Wajah (v2.0 - Deep Learning)
=====================================
Menggantikan LBPH prediction dengan face_recognition embedding comparison.
Memuat encoding dari 'encodings/face_encodings.pkl'.
"""

import face_recognition
import cv2
import numpy as np
import pickle
import os

# --- KONFIGURASI ---
ENCODINGS_PATH = 'encodings/face_encodings.pkl'
FACE_TOLERANCE = 0.45  # Jarak maksimal untuk dianggap cocok

# Load data encoding
if not os.path.exists(ENCODINGS_PATH):
    print(f"[ERROR] File '{ENCODINGS_PATH}' tidak ditemukan!")
    print("[INFO] Jalankan 'python latih_wajah.py' terlebih dahulu.")
    exit()

with open(ENCODINGS_PATH, 'rb') as f:
    data = pickle.load(f)
    known_encodings = data['encodings']
    known_ids = data['ids']

print(f"[INFO] Loaded {len(set(known_ids))} user ({len(known_ids)} encoding)")

# Daftar Nama (load dari database sebaiknya, tapi untuk standalone test pakai dict)
names = {0: 'Unknown'}

# Font untuk tulisan di layar
font = cv2.FONT_HERSHEY_SIMPLEX

# Mulai Kamera
cam = cv2.VideoCapture(0)
cam.set(3, 640)
cam.set(4, 480)

print("[INFO] Kamera dimulai. Tekan 'ESC' untuk berhenti.")

frame_count = 0
cached_results = []  # Cache deteksi terakhir

while True:
    ret, frame = cam.read()
    if not ret:
        continue
    
    frame_count += 1
    
    # Jalankan deteksi setiap 3 frame untuk performa
    if frame_count % 3 == 0:
        # Konversi ke RGB (face_recognition menggunakan RGB, bukan BGR)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Resize untuk performa
        small_frame = cv2.resize(rgb_frame, (0, 0), fx=0.5, fy=0.5)
        
        # Deteksi wajah
        face_locations = face_recognition.face_locations(small_frame, model='hog')
        face_encodings = face_recognition.face_encodings(small_frame, face_locations)
        
        new_results = []
        
        for (top, right, bottom, left), face_enc in zip(face_locations, face_encodings):
            # Scale balik ke ukuran asli
            top *= 2; right *= 2; bottom *= 2; left *= 2
            
            name = "Unknown"
            distance = 1.0
            
            if len(known_encodings) > 0:
                distances = face_recognition.face_distance(known_encodings, face_enc)
                best_idx = int(np.argmin(distances))
                distance = distances[best_idx]
                
                if distance <= FACE_TOLERANCE:
                    user_id = known_ids[best_idx]
                    name = names.get(user_id, f"User {user_id}")
            
            confidence_pct = round((1 - distance) * 100)
            new_results.append((top, right, bottom, left, name, confidence_pct))
        
        cached_results = new_results
    
    # Gambar hasil deteksi (dari cache) pada setiap frame
    for (top, right, bottom, left, name, confidence) in cached_results:
        color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.putText(frame, f"{name}", (left + 5, top - 10), font, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, f"  {confidence}%", (left + 5, bottom + 25), font, 0.7, (255, 255, 0), 1)
    
    cv2.imshow('Kamera Pengenalan Wajah (Deep Learning)', frame)
    
    k = cv2.waitKey(10) & 0xff
    if k == 27:
        break

print("\n[INFO] Program selesai.")
cam.release()
cv2.destroyAllWindows()