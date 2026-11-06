# RFID-electron-HW-vx6636

Program integrasi pembaca **UHF RFID Electron HW-VX6336** (ISO18000-6C / EPC Gen2) berbasis Python dan Node.js yang berfungsi sebagai **Keyboard Wedge (Auto-Paste)** langsung ke form aplikasi web (misal: sistem manajemen gudang barang masuk dan keluar).

---

## Fitur Utama

- **Keyboard Wedge (Auto-Paste Instan)**: Saat tag RFID terdeteksi, program secara otomatis melakukan kombinasi tombol `Ctrl+A` -> `Backspace` -> `Ctrl+V` pada kotak input yang sedang aktif di browser tanpa menekan `Enter` (bisa diaktifkan di konfigurasi jika dibutuhkan).
- **Delay / Cooldown 5 Detik**: Setelah pembacaan berhasil, program memberi jeda 5 detik agar kartu tidak terkirim secara beruntun (*spam*), memberi waktu operator untuk memeriksa data atau klik simpan.
- **Standby Cepat (0.2 detik)**: Saat idle (tidak ada kartu), reader mengecek secara cepat sehingga begitu kartu didekatkan langsung terbaca secara instan.
- **Mode Simulasi Virtual (`--simulate`)**: Memungkinkan pengujian alur web tanpa memerlukan perangkat fisik.
- **Konfigurasi Fleksibel (`config.json`)**: Pengaturan port COM, baudrate, delay, dan tombol Enter dapat diatur dengan mudah.
- **Dua Pilihan Bahasa**: Tersedia dalam versi **Python** (`reader.py`) dan **Node.js** (`reader.js`).

---

## Struktur File

```text
├── reader.py          # Program utama Python (Keyboard Wedge)
├── reader.js          # Program alternatif Node.js / Electron
├── Jalankan_RFID.bat  # Shortcut klik-dua-kali untuk menjalankan di Windows
├── config.json        # File pengaturan konfigurasi aplikasi
└── docs/              # Dokumentasi & Panduan Protokol HW-VX6336
```

---

## Cara Menjalankan

### 1. Menggunakan Python (Disarankan)

1. Pastikan modul `pyserial` terpasang:
   ```bash
   pip install pyserial
   ```
2. Hubungkan reader HW-VX6336 via USB.
3. Jalankan program dengan salah satu cara berikut:
   - Klik 2x file **`Jalankan_RFID.bat`**, ATAU
   - Jalankan via terminal:
     ```bash
     python reader.py
     ```
4. Buka halaman web Anda di browser, klik sekali pada kolom input RFID (contoh: `TAG RFID`).
5. Tempelkan kartu/tag RFID ke reader.

> **Tips Testing Tanpa Alat Fisik:**  
> Jalankan perintah `python reader.py --simulate` untuk menguji alur paste otomatis ke browser menggunakan tag virtual.

---

### 2. Menggunakan Node.js

1. Pasang dependensi serialport:
   ```bash
   npm install serialport
   ```
2. Jalankan:
   ```bash
   node reader.js
   ```

---

## Konfigurasi (`config.json`)

```json
{
    "port": "AUTO",
    "baudrate": 57600,
    "scan_interval_sec": 5.0,
    "press_enter_after_paste": false,
    "beep_on_success": true,
    "alert_sound_on_multi": true
}
```

---

## Lisensi & Spesifikasi Hardware
- **Hardware**: Electron HW-VX6336 Desktop UHF RFID Reader/Writer (902–928 MHz)
- **Komunikasi**: USB Virtual Serial Port (Default Baudrate: 57600, 8N1)
- **Protokol**: ISO18000-6C (EPC Class 1 Gen 2)

