import requests

# URL API (Pastikan server Flask nyala)
url = 'http://127.0.0.1:5000/api/absen'

# Data user (Pura-puranya User ID 1 sedang login di HP)
# GANTI angka '1' dengan ID user yang wajahnya ada di foto tes_wajah.jpg
payload = {'user_id': '1'} 

# Buka file gambar
files = [
    ('image', ('tes_wajah.jpg', open('tes_wajah.jpg', 'rb'), 'image/jpeg'))
]

try:
    print("Mengirim foto ke server...")
    response = requests.post(url, data=payload, files=files)
    
    print("Status Code:", response.status_code)
    print("Jawaban Server:", response.json())
    
except Exception as e:
    print("Error:", e)