```markdown
# Attendance App

## Deskripsi
Attendance App adalah aplikasi web untuk mengelola kehadiran siswa. Aplikasi ini memungkinkan walikelas dan sekretaris untuk mencatat kehadiran siswa dan melihat rekap absensi harian dan bulanan.

## Fitur
- Formulir absensi harian
- Rekap absensi harian
- Rekap absensi bulanan
- Daftar siswa dengan fitur pencarian dan pagination
- API endpoint untuk integrasi dengan aplikasi lain
- Logging aktivitas dan kesalahan
- Validasi formulir

## Teknologi
- Flask
- SQLAlchemy
- Flask-Login
- Flask-Principal
- Flask-WTF
- Flask-RESTful
- SQLite
- HTML/CSS (Bootstrap)
- PDFKit

## Instalasi dan Pengaturan Lingkungan

### Prasyarat
Pastikan Anda sudah menginstal:
- Python 3.6 atau lebih baru
- Virtualenv

### Langkah-langkah Instalasi
1. Clone repository ini:
   ```bash
   git clone https://github.com/hamidabdul003/attendance_app.git
   cd attendance_app
   ```

2. Buat dan aktifkan virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Untuk pengguna Windows: venv\Scripts\activate
   ```

3. Instal dependensi:
   ```bash
   pip install -r requirements.txt
   ```

4. Buat dan inisialisasi database:
   ```bash
   flask db init
   flask db migrate -m "Initial migration."
   flask db upgrade
   ```

5. Jalankan aplikasi:
   ```bash
   flask run
   ```

### Konfigurasi Logging
Untuk mengaktifkan logging, pastikan konfigurasi logging di `app.py` sesuai dengan kebutuhan Anda. Logging akan mencatat aktivitas dan kesalahan ke file `error.log`.

## Penggunaan

### Login
Akses aplikasi di `http://127.0.0.1:5000` dan login dengan akun yang telah disediakan oleh administrator.

### Mencatat Kehadiran
1. Pilih menu "Formulir Absensi".
2. Isi status kehadiran siswa dan klik tombol "Submit".

### Melihat Rekap Absensi
1. Pilih menu "Rekap Harian" untuk melihat rekap absensi harian.
2. Pilih menu "Rekap Bulanan" untuk melihat rekap absensi bulanan.

### Mengelola Data Siswa
1. Pilih menu "Daftar Siswa".
2. Gunakan fitur pencarian atau pagination untuk mencari dan melihat daftar siswa.

### API Endpoint
Untuk mengambil data siswa, gunakan endpoint berikut:
- Semua siswa: `GET /api/students`
- Siswa tertentu: `GET /api/students/<student_id>`

## Deployment
Untuk melakukan deployment ke server produksi menggunakan Apache2 di Ubuntu Server, ikuti langkah-langkah berikut:

### Prasyarat
Pastikan Anda sudah menginstal:
- Apache2
- mod_wsgi

### Langkah-langkah Deployment
1. Install `mod_wsgi`:
   ```bash
   sudo apt-get install libapache2-mod-wsgi-py3
   ```

2. Buat file konfigurasi untuk aplikasi Anda di Apache:
   ```bash
   sudo nano /etc/apache2/sites-available/attendance_app.conf
   ```

3. Tambahkan konfigurasi berikut:
   ```apache
   <VirtualHost *:80>
       ServerName yourdomain.com

       WSGIDaemonProcess attendance_app python-path=/path/to/attendance_app:/path/to/attendance_app/venv/lib/python3.8/site-packages
       WSGIProcessGroup attendance_app
       WSGIScriptAlias / /path/to/attendance_app/attendance_app.wsgi

       <Directory /path/to/attendance_app>
           Require all granted
       </Directory>

       Alias /static /path/to/attendance_app/static
       <Directory /path/to/attendance_app/static/>
           Require all granted
       </Directory>

       ErrorLog ${APACHE_LOG_DIR}/attendance_app_error.log
       CustomLog ${APACHE_LOG_DIR}/attendance_app_access.log combined
   </VirtualHost>
   ```

4. Buat file WSGI untuk aplikasi Anda:
   ```bash
   nano /path/to/attendance_app/attendance_app.wsgi
   ```

5. Tambahkan konfigurasi berikut:
   ```python
   import sys
   import logging
   import os

   logging.basicConfig(stream=sys.stderr)
   sys.path.insert(0, "/path/to/attendance_app")

   from app import app as application

   if __name__ == "__main__":
       application.run()
   ```

6. Aktifkan konfigurasi dan restart Apache:
   ```bash
   sudo a2ensite attendance_app.conf
   sudo systemctl restart apache2
   ```

## Kontribusi
Jika Anda ingin berkontribusi pada proyek ini, silakan fork repository ini dan buat pull request dengan perubahan Anda.

## Lisensi
Proyek ini dilisensikan di bawah lisensi MIT.

## Kontak
Untuk pertanyaan atau bantuan lebih lanjut, silakan hubungi:
- Email: hamidabdul003@gmail.com
```
