import requests

# Ganti URL ini dengan IP Laptop kamu jika tes dari HP, 
# atau localhost jika tes di laptop yang sama.
url = 'http://127.0.0.1:5000/api/login'

# Data yang mau dikirim 
data_login = {
    'username': 'admin',      
    'password': '123' 
}

try:
    # Kirim request POST ke server
    response = requests.post(url, json=data_login)
    
    # Baca balasannya
    print("Status Code:", response.status_code)
    print("Respon Server:", response.json())
    
except Exception as e:
    print("Gagal connect:", e)