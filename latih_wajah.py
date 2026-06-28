"""
Latih Wajah (v2.0 - Deep Learning)
===================================
Menggantikan LBPH training dengan face_recognition encoding generation.
Menghasilkan file 'encodings/face_encodings.pkl' berisi 128D face embeddings.
"""

import face_recognition
import numpy as np
import pickle
import os

# Path ke folder dataset
path = 'dataset'
output_dir = 'encodings'
output_path = os.path.join(output_dir, 'face_encodings.pkl')

def generate_encodings(dataset_path):
    """Generate face encodings dari semua gambar di folder dataset."""
    
    all_encodings = []
    all_ids = []
    gagal_count = 0
    
    image_files = [f for f in os.listdir(dataset_path) if f.endswith('.jpg')]
    total_files = len(image_files)
    
    print(f"[INFO] Memproses {total_files} gambar dari '{dataset_path}'...")
    
    for i, filename in enumerate(image_files):
        try:
            user_id = int(filename.split(".")[1])
            filepath = os.path.join(dataset_path, filename)
            
            # Skip file yang terlalu kecil (kemungkinan corrupt)
            if os.path.getsize(filepath) < 2000:
                print(f"  [SKIP] {filename} - file terlalu kecil ({os.path.getsize(filepath)} bytes)")
                gagal_count += 1
                continue
            
            # Load gambar (face_recognition otomatis handle grayscale & color)
            img = face_recognition.load_image_file(filepath)
            h, w = img.shape[:2]
            
            # Coba deteksi wajah otomatis dulu
            face_locations = face_recognition.face_locations(img, model='hog')
            
            if len(face_locations) == 0:
                # Gambar kemungkinan sudah berupa crop wajah → pakai seluruh gambar
                face_locations = [(0, w, h, 0)]  # (top, right, bottom, left)
            
            encodings = face_recognition.face_encodings(img, face_locations)
            
            if len(encodings) > 0:
                all_encodings.append(encodings[0])
                all_ids.append(user_id)
                
                if (i + 1) % 10 == 0:
                    print(f"  [{i+1}/{total_files}] Berhasil memproses {filename}")
            else:
                gagal_count += 1
                print(f"  [GAGAL] {filename} - tidak bisa generate encoding")
                
        except Exception as e:
            gagal_count += 1
            print(f"  [ERROR] {filename}: {e}")
            continue
    
    return all_encodings, all_ids, gagal_count


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  FACE ENCODING GENERATOR (Deep Learning)")
    print("="*60)
    
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"[ERROR] Folder '{path}' kosong! Ambil dataset terlebih dahulu.")
        exit()
    
    encodings, ids, gagal = generate_encodings(path)
    
    if len(ids) > 0:
        # Simpan ke pickle
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        data = {
            'encodings': encodings,
            'ids': ids
        }
        
        with open(output_path, 'wb') as f:
            pickle.dump(data, f)
        
        unique_users = len(set(ids))
        print(f"\n{'='*60}")
        print(f"  ✅ SUKSES!")
        print(f"  📊 {unique_users} user, {len(ids)} encoding berhasil di-generate")
        if gagal > 0:
            print(f"  ⚠️  {gagal} gambar gagal diproses")
        print(f"  💾 Tersimpan di: {output_path}")
        print(f"{'='*60}")
    else:
        print("\n[ERROR] Tidak ada data yang berhasil diproses!")