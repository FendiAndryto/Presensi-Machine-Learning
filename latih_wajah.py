import cv2
import numpy as np
import os

# Path ke folder dataset
path = 'dataset'

# Inisialisasi algoritma LBPH (Local Binary Patterns Histograms)
recognizer = cv2.face.LBPHFaceRecognizer_create()

def getImagesAndLabels(path):
    # Ambil semua path file di folder dataset
    imagePaths = [os.path.join(path,f) for f in os.listdir(path)]     
    faceSamples=[]
    ids = []

    for imagePath in imagePaths:
        # Abaikan jika bukan file gambar (misal file sistem hidden)
        if not imagePath.endswith(".jpg"):
            continue

        # Load gambar dan konversi ke array angka (Grayscale)
        # Flag 0 artinya mode grayscale
        img_numpy = cv2.imread(imagePath, 0)

        # Ambil ID dari nama file
        # Contoh: "dataset/User.1.5.jpg"
        # Kita split berdasarkan "." lalu ambil angka "1" (index ke-1)
        id = int(os.path.split(imagePath)[-1].split(".")[1])
        
        faceSamples.append(img_numpy)
        ids.append(id)

    return faceSamples, ids

print("\n[INFO] Sedang membaca data wajah (Training)...")
faces, ids = getImagesAndLabels(path)

print(f"[INFO] Melatih sistem dengan {len(faces)} sampel foto...")
# Proses Training dimulai di sini
recognizer.train(faces, np.array(ids))

# Simpan model (otak) yang sudah jadi ke folder 'trainer'
if not os.path.exists('trainer'):
    os.makedirs('trainer')

recognizer.write('trainer/trainer.yml') 

print("\n[INFO] SUKSES! File 'trainer/trainer.yml' berhasil dibuat.")