"""
Script Evaluasi Model Face Recognition (Deep Learning)
======================================================
Script ini akan membaca foto-foto wajah di folder `dataset_uji/`
dan membandingkannya dengan data latih di `../encodings/face_encodings.pkl`.

Menghasilkan:
1. Laporan Metrik (Akurasi, Presisi, dll)
2. Gambar Confusion Matrix
"""

import face_recognition
import os
import pickle
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# --- KONFIGURASI ---
ENCODINGS_PATH = '../encodings/face_encodings.pkl'
TEST_DATASET_PATH = 'dataset_uji'
FACE_TOLERANCE = 0.45  # Jarak maksimal untuk dianggap cocok (sama dengan aplikasi utama)
OUTPUT_PLOT_PATH = 'confusion_matrix.png'

def evaluasi():
    print("="*60)
    print("  EVALUASI MODEL PENGENALAN WAJAH")
    print("="*60)

    # 1. Load Data Latih (Encodings)
    if not os.path.exists(ENCODINGS_PATH):
        print(f"[ERROR] File '{ENCODINGS_PATH}' tidak ditemukan!")
        print("[INFO] Pastikan model sudah dilatih terlebih dahulu.")
        return

    with open(ENCODINGS_PATH, 'rb') as f:
        data = pickle.load(f)
        known_encodings = data['encodings']
        known_ids = data['ids']
    
    print(f"[INFO] Data latih dimuat: {len(known_ids)} wajah diketahui dari {len(set(known_ids))} user.")

    # 2. Persiapan Data Uji
    if not os.path.exists(TEST_DATASET_PATH):
        os.makedirs(TEST_DATASET_PATH)
        print(f"[ERROR] Folder '{TEST_DATASET_PATH}' tidak ditemukan, sudah dibuat otomatis.")
        print("[INFO] Silakan isi folder tersebut dengan foto uji berformat 'User.<ID>.<Angka>.jpg'")
        return

    test_images = [f for f in os.listdir(TEST_DATASET_PATH) if f.endswith('.jpg') or f.endswith('.png')]
    if len(test_images) == 0:
        print(f"[WARNING] Tidak ada foto uji di folder '{TEST_DATASET_PATH}'!")
        print("[INFO] Silakan tambahkan beberapa foto untuk diuji.")
        return

    print(f"[INFO] Memproses {len(test_images)} foto uji...\n")

    y_true = []
    y_pred = []
    gagal_deteksi = 0

    # 3. Proses Pengujian
    for filename in test_images:
        filepath = os.path.join(TEST_DATASET_PATH, filename)
        
        # Ekstrak Label Asli (ID) dari nama file: User.ID.Angka.jpg
        try:
            parts = filename.split(".")
            true_id = int(parts[1])
        except Exception:
            print(f"  [SKIP] Nama file '{filename}' tidak valid. Format harus: User.<ID>.<Angka>.jpg")
            continue
            
        y_true.append(true_id)
        
        # Proses Pengenalan Wajah
        img = face_recognition.load_image_file(filepath)
        face_locations = face_recognition.face_locations(img, model='hog')
        face_encodings = face_recognition.face_encodings(img, face_locations)
        
        if len(face_encodings) == 0:
            print(f"  [GAGAL] Tidak ada wajah terdeteksi di foto: {filename}")
            # Jika tidak terdeteksi, kita anggap prediksinya -1 (Unknown)
            y_pred.append(-1) 
            gagal_deteksi += 1
            continue
            
        # Ambil wajah pertama (asumsi 1 foto 1 wajah)
        test_encoding = face_encodings[0]
        
        # Hitung Jarak (Distance)
        distances = face_recognition.face_distance(known_encodings, test_encoding)
        best_idx = int(np.argmin(distances))
        min_distance = distances[best_idx]
        
        if min_distance <= FACE_TOLERANCE:
            predicted_id = known_ids[best_idx]
            status = "BENAR" if predicted_id == true_id else "SALAH"
            print(f"  [TES] {filename} -> Ditebak: {predicted_id} ({status}, Jarak: {min_distance:.2f})")
            y_pred.append(predicted_id)
        else:
            print(f"  [TES] {filename} -> Ditebak: Tidak Dikenal (Jarak: {min_distance:.2f} > {FACE_TOLERANCE})")
            y_pred.append(-1) # -1 untuk Unknown

    # 4. Hitung Metrik & Confusion Matrix
    print("\n" + "="*60)
    print("  HASIL EVALUASI")
    print("="*60)
    
    if len(y_true) > 0:
        akurasi = accuracy_score(y_true, y_pred)
        print(f"Akurasi Keseluruhan: {akurasi * 100:.2f}%\n")
        
        print("Detail Laporan Klasifikasi:")
        # Mapping unik ID yang muncul
        labels = sorted(list(set(y_true + y_pred)))
        target_names = [f"User {lbl}" if lbl != -1 else "Wajah Tidak Dikenal!" for lbl in labels]
        
        print(classification_report(y_true, y_pred, labels=labels, target_names=target_names, zero_division=0))
        
        # 5. Gambar Confusion Matrix
        cm = confusion_matrix(y_true, y_pred, labels=labels)
        
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                    xticklabels=target_names, yticklabels=target_names)
        plt.title('Confusion Matrix - Pengenalan Wajah')
        plt.ylabel('Label Asli (Kenyataan)')
        plt.xlabel('Prediksi Aplikasi')
        
        plt.tight_layout()
        plt.savefig(OUTPUT_PLOT_PATH)
        print(f"\n[INFO] Grafik Confusion Matrix disimpan sebagai '{OUTPUT_PLOT_PATH}'")
        plt.close()
        
        # 6. Gambar Bar Chart Metrik (Precision, Recall, F1)
        report_dict = classification_report(y_true, y_pred, labels=labels, target_names=target_names, zero_division=0, output_dict=True)
        
        metrics = ['precision', 'recall', 'f1-score']
        x = np.arange(len(target_names))
        width = 0.25
        
        plt.figure(figsize=(10, 6))
        for i, metric in enumerate(metrics):
            values = [report_dict[name][metric] for name in target_names]
            plt.bar(x + i*width, values, width, label=metric.capitalize())
            
        plt.xlabel('Users')
        plt.ylabel('Skor (0.0 - 1.0)')
        plt.title('Grafik Metrik Evaluasi per User')
        plt.xticks(x + width, target_names, rotation=45)
        plt.ylim(0, 1.1)
        plt.legend(loc='lower right')
        plt.tight_layout()
        plt.savefig('grafik_laporan_metrik.png')
        print("[INFO] Grafik Bar Chart Metrik disimpan sebagai 'grafik_laporan_metrik.png'")
        plt.close()

        # 7. Gambar Pie Chart Akurasi
        benar = sum(1 for t, p in zip(y_true, y_pred) if t == p)
        salah = len(y_true) - benar
        
        plt.figure(figsize=(6, 6))
        if salah == 0: # Handle pie chart if all are correct
            plt.pie([benar], labels=['Benar'], autopct='%1.1f%%', colors=['#4CAF50'], startangle=90)
        else:
            plt.pie([benar, salah], labels=['Benar', 'Salah / Tidak Dikenal'], autopct='%1.1f%%', 
                    colors=['#4CAF50', '#F44336'], startangle=90, explode=(0.1, 0))
        plt.title('Persentase Akurasi Keseluruhan')
        plt.tight_layout()
        plt.savefig('grafik_akurasi_pie.png')
        print("[INFO] Grafik Pie Chart Akurasi disimpan sebagai 'grafik_akurasi_pie.png'")
        plt.close()
    else:
        print("[WARNING] Tidak ada data valid yang dievaluasi.")

if __name__ == "__main__":
    evaluasi()
