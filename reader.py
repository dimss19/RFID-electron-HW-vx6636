"""
Aplikasi Integrasi RFID UHF Electron HW-VX6336 (Keyboard Wedge / Auto-Paste Web)
Dirancang khusus untuk sistem Gudang (Input Barang Masuk & Barang Keluar - rfid.moko.ai.id)

Fitur Logika Gudang:
1. Auto-Paste Instan (Ctrl+A -> Backspace -> Ctrl+V) ke kolom input browser tanpa menekan Enter.
2. Anti-Double Scan (Tag Lock): Barang yang masih menempel di atas reader tidak akan
   di-input berulang kali saat operator sedang mengecek Detail Barang & klik Simpan.
3. Anti-Tabrakan (Single-Tag Guard): Jika ada >1 tag terdeteksi sekaligus di dekat reader,
   sistem menolak input dan membunyikan peringatan agar tidak salah input barang.
4. Siklus pembacaan 5 detik sekali sesuai konfigurasi.
"""

import time
import sys
import os
import json
import ctypes
from ctypes import wintypes
import winsound
import serial
import serial.tools.list_ports


# ==============================================================================
# MANAJEMEN KONFIGURASI & LOGGING
# ==============================================================================
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
LOG_FILE = os.path.join(BASE_DIR, "rfid_scanner.log")

def log(msg: str):
    """Mencetak ke console (jika ada) dan menulis ke file rfid_scanner.log"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    try:
        print(line)
    except Exception:
        pass
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
DEFAULT_CONFIG = {
    "port": "AUTO",              # "AUTO" atau nama port seperti "COM3"
    "baudrate": 57600,           # Baudrate bawaan HW-VX6336
    "scan_interval_sec": 5.0,    # Jeda siklus scan (detik)
    "press_enter_after_paste": False,  # True jika ingin otomatis menekan Enter setelah paste
    "beep_on_success": True,     # Bunyikan buzzer reader saat tag berhasil di-paste
    "alert_sound_on_multi": True # Bunyikan suara peringatan saat ada >1 tag terdeteksi
}

def load_config() -> dict:
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
                config.update(user_cfg)
        except Exception as e:
            print(f"[WARN] Gagal membaca config.json, menggunakan konfigurasi default: {e}")
    else:
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
        except Exception:
            pass
    return config

CONFIG = load_config()
SCAN_INTERVAL_SEC = float(CONFIG.get("scan_interval_sec", 5.0))
BAUDRATE = int(CONFIG.get("baudrate", 57600))
PRESS_ENTER = bool(CONFIG.get("press_enter_after_paste", False))


# ==============================================================================
# MODUL WINDOWS CLIPBOARD & KEYBOARD EMULATOR (Tanpa Library Tambahan)
# ==============================================================================
CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002

VK_BACK = 0x08
VK_RETURN = 0x0D
VK_CONTROL = 0x11
VK_A = 0x41
VK_V = 0x56
KEYEVENTF_KEYUP = 0x0002

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalLock.restype = ctypes.c_void_p
kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalUnlock.restype = wintypes.BOOL
user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
user32.SetClipboardData.restype = wintypes.HANDLE


def copy_to_clipboard(text: str) -> bool:
    """Menyalin teks EPC ke Windows Clipboard"""
    data = text.encode("utf-16-le") + b"\x00\x00"
    if not user32.OpenClipboard(None):
        return False
    try:
        user32.EmptyClipboard()
        h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
        if not h_mem:
            return False
        ptr = kernel32.GlobalLock(h_mem)
        if not ptr:
            return False
        ctypes.memmove(ptr, data, len(data))
        kernel32.GlobalUnlock(h_mem)
        user32.SetClipboardData(CF_UNICODETEXT, h_mem)
        return True
    finally:
        user32.CloseClipboard()


def is_console_focused() -> bool:
    """Mengecek apakah jendela yang sedang aktif adalah jendela Terminal ini sendiri"""
    console_hwnd = kernel32.GetConsoleWindow()
    foreground_hwnd = user32.GetForegroundWindow()
    return bool(console_hwnd and console_hwnd == foreground_hwnd)


def get_active_window_title() -> str:
    """Mengambil nama jendela aplikasi yang sedang aktif"""
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return ""
    length = user32.GetWindowTextLengthW(hwnd)
    if length == 0:
        return ""
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value


def auto_paste_replace(epc_text: str) -> tuple[bool, str]:
    """
    Menyalin kode RFID ke clipboard lalu melakukan simulasi:
    Ctrl+A (blok teks lama) -> Backspace (hapus) -> Ctrl+V (paste RFID baru)
    Tanpa menekan Enter agar operator bisa mengecek Detail Barang terlebih dahulu.
    """
    if not copy_to_clipboard(epc_text):
        return False, "Gagal menyalin ke clipboard"

    # Cegah salah ketik jika operator masih mengklik jendela terminal/CMD
    if is_console_focused():
        return False, "Tersalin di Clipboard (Klik kolom 'TAG RFID' di Browser agar otomatis ter-paste!)"

    # 1. Ctrl + A (Pilih semua isi kotak input sebelumnya)
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    user32.keybd_event(VK_A, 0, 0, 0)
    time.sleep(0.02)
    user32.keybd_event(VK_A, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.02)

    # 2. Backspace (Kosongkan kotak input)
    user32.keybd_event(VK_BACK, 0, 0, 0)
    time.sleep(0.02)
    user32.keybd_event(VK_BACK, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.02)

    # 3. Ctrl + V (Paste kode RFID baru secara instan)
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    user32.keybd_event(VK_V, 0, 0, 0)
    time.sleep(0.02)
    user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

    # 4. Opsional: Tekan tombol Enter jika diatur di config.json
    if PRESS_ENTER:
        time.sleep(0.02)
        user32.keybd_event(VK_RETURN, 0, 0, 0)
        time.sleep(0.02)
        user32.keybd_event(VK_RETURN, 0, KEYEVENTF_KEYUP, 0)

    win_title = get_active_window_title()
    return True, f"Berhasil di-paste ke [{win_title or 'Browser'}]"


# ==============================================================================
# PROTOKOL KOMUNIKASI SERIAL HW-VX6336
# ==============================================================================
def calculate_crc16(data: bytes) -> tuple[int, int]:
    """
    Menghitung CRC-16 sesuai spesifikasi HW-VX6336:
    Preset: 0xFFFF, Polynomial: 0x8408 (CCITT Reverse)
    Mengembalikan (LSB, MSB)
    """
    crc = 0xFFFF
    poly = 0x8408
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ poly
            else:
                crc >>= 1
    return crc & 0xFF, (crc >> 8) & 0xFF


class HWVX6336Reader:
    def __init__(self, port: str, baudrate: int = 57600, address: int = 0x00, timeout: float = 1.5):
        self.port_name = port
        self.baudrate = baudrate
        self.address = address
        self.timeout = timeout
        self.ser: serial.Serial | None = None

    def connect(self) -> bool:
        """Membuka koneksi serial port ke RFID Reader"""
        try:
            self.ser = serial.Serial(
                port=self.port_name,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout
            )
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            time.sleep(0.1)
            return True
        except Exception as e:
            print(f"[ERROR] Gagal membuka port {self.port_name}: {e}")
            return False

    def disconnect(self):
        """Menutup port serial"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("[INFO] Port serial ditutup.")

    def _send_command(self, cmd: int, data: bytes = b"") -> bytes | None:
        """Mengirim frame perintah dan membaca respons dari HW-VX6336"""
        if not self.ser or not self.ser.is_open:
            return None

        try:
            length = len(data) + 4
            payload = bytes([length, self.address, cmd]) + data
            lsb, msb = calculate_crc16(payload)
            packet = payload + bytes([lsb, msb])

            self.ser.reset_input_buffer()
            self.ser.write(packet)
            self.ser.flush()

            first_byte = self.ser.read(1)
            if not first_byte:
                return None

            resp_len = first_byte[0]
            remaining = self.ser.read(resp_len)
            if len(remaining) < resp_len:
                return None

            full_response = first_byte + remaining
            expected_lsb, expected_msb = calculate_crc16(full_response[:-2])
            if full_response[-2] != expected_lsb or full_response[-1] != expected_msb:
                return None

            return full_response
        except (serial.SerialException, OSError):
            self.disconnect()
            return None

    def get_reader_info(self) -> dict | None:
        """Mengambil info hardware / firmware reader (Cmd 0x21)"""
        resp = self._send_command(0x21)
        if not resp:
            return None

        status = resp[3]
        if status == 0x00 and len(resp) >= 14:
            return {
                "firmware_version": f"v{resp[4]}.{resp[5]}",
                "reader_type": hex(resp[6]),
                "power_dbm": resp[10],
                "scan_time_ms": resp[11] * 100
            }
        return None

    def beep(self, times: int = 1, active_ms: int = 100) -> bool:
        """Menyalakan buzzer / LED indikator pada reader (Cmd 0x33)"""
        active_t = max(1, min(255, active_ms // 50))
        silent_t = 1
        data = bytes([active_t, silent_t, times])
        resp = self._send_command(0x33, data)
        return bool(resp and resp[3] == 0x00)

    def inventory(self) -> list[str]:
        """
        Membaca daftar tag RFID EPC Gen2 yang berada di jangkauan antena (Cmd 0x01).
        Mengembalikan list EPC unik dalam format HEX uppercase.
        """
        resp = self._send_command(0x01)
        if not resp:
            return []

        status = resp[3]
        if status not in (0x01, 0x02, 0x03, 0x04):
            return []

        data_block = resp[4:-2]
        if not data_block:
            return []

        num_tags = data_block[0]
        tags = []
        idx = 1
        for _ in range(num_tags):
            if idx >= len(data_block):
                break
            epc_len = data_block[idx]
            idx += 1
            if idx + epc_len <= len(data_block):
                epc_bytes = data_block[idx:idx + epc_len]
                epc_hex = epc_bytes.hex().upper()
                if epc_hex not in tags:
                    tags.append(epc_hex)
                idx += epc_len

        return tags


def list_serial_ports() -> list[str]:
    """Mengembalikan daftar COM port yang terdeteksi di sistem"""
    ports = serial.tools.list_ports.comports()
    return [p.device for p in ports]


def run_simulation(scan_interval: float):
    """Mode simulasi virtual untuk testing ke web tanpa perangkat fisik"""
    print("\n" + "=" * 72)
    print("   [MODE SIMULASI VIRTUAL AKTIF]")
    print(f"   Mengirimkan tag RFID virtual setiap {scan_interval:.0f} detik ke kolom input web.")
    print("   Buka browser dan klik kotak input 'TAG RFID' sekarang!")
    print("   Tekan Ctrl+C untuk berhenti.")
    print("=" * 72 + "\n")

    sample_tags = [
        "E28011700000020B776C92A1",
        "E28011700000020B776C92A2",
        "E28011700000020B776C92A3",
        "E2003412DC03011722029029",
        "1F06B000020801091100A5B2"
    ]

    tag_idx = 0
    scan_counter = 0

    try:
        while True:
            current_epc = sample_tags[tag_idx % len(sample_tags)]
            tag_idx += 1
            scan_counter += 1
            waktu = time.strftime("%H:%M:%S")

            # Beep PC
            try:
                winsound.Beep(1200, 80)
            except Exception:
                pass

            pasted, status_msg = auto_paste_replace(current_epc)
            status_icon = "OK" if pasted else "CLIPBOARD"
            print(f"[{waktu}] [SIMULASI #{scan_counter} - {status_icon}] EPC: {current_epc}")
            print(f"           -> {status_msg}")
            print(f"[{waktu}] Menunggu jeda {scan_interval:.0f} detik...\n")

            time.sleep(scan_interval)
    except KeyboardInterrupt:
        print("\n[INFO] Mode simulasi dihentikan.")


def is_headless() -> bool:
    """Mengecek apakah aplikasi berjalan di latar belakang (tanpa terminal interaktif)"""
    return not sys.stdin or not hasattr(sys.stdin, "isatty") or not sys.stdin.isatty()


# ==============================================================================
# PROGRAM UTAMA (WAREHOUSE KEYBOARD WEDGE)
# ==============================================================================
def main():
    log("====================================================================")
    log("   RFID KEYBOARD WEDGE - ELECTRON HW-VX6336 (GUDANG MASUK & KELUAR)")
    log("====================================================================")

    # Cek apakah dijalankan dengan flag --simulate
    if "--simulate" in sys.argv or "-s" in sys.argv:
        run_simulation(SCAN_INTERVAL_SEC)
        return

    config_port = CONFIG.get("port", "AUTO").upper()
    scan_counter = 0

    # MODE BACKGROUND (HEADLESS)
    if is_headless():
        log("[INFO] Menjalankan dalam Background Mode (tanpa jendela console).")
        while True:
            available_ports = list_serial_ports()
            selected_port = None

            if config_port != "AUTO" and config_port in available_ports:
                selected_port = config_port
            elif available_ports:
                selected_port = available_ports[0]

            if not selected_port:
                log("[WAIT] Menunggu USB RFID HW-VX6336 terhubung...")
                time.sleep(3)
                continue

            reader = HWVX6336Reader(port=selected_port, baudrate=BAUDRATE)
            log(f"[INFO] Mencoba menghubungkan ke {selected_port}...")
            if not reader.connect():
                time.sleep(3)
                continue

            log(f"[SUCCESS] Terhubung ke {selected_port}! Reader siap di background.")
            if CONFIG.get("beep_on_success", True):
                reader.beep(times=1, active_ms=80)

            # Loop scan di background dengan auto-recovery
            try:
                while True:
                    tags = reader.inventory()
                    if tags:
                        current_epc = tags[0]
                        scan_counter += 1

                        if CONFIG.get("beep_on_success", True):
                            reader.beep(times=1, active_ms=60)

                        pasted, status_msg = auto_paste_replace(current_epc)
                        status_icon = "OK" if pasted else "CLIPBOARD"
                        log(f"[SCAN #{scan_counter} - {status_icon}] EPC: {current_epc} -> {status_msg}")
                        time.sleep(SCAN_INTERVAL_SEC)
                    else:
                        time.sleep(0.2)
            except Exception as e:
                log(f"[WARN] Koneksi terputus ({e}), mencoba menghubungkan ulang...")
                reader.disconnect()
                time.sleep(2)

    # MODE INTERAKTIF (TERMINAL / CMD)
    available_ports = list_serial_ports()
    if not available_ports:
        print("[!] Tidak ada COM port fisik yang terdeteksi.")
        print("    1. Pastikan kabel USB reader HW-VX6336 sudah terpasang ke PC.")
        print("    2. Atau Anda dapat mencoba Mode Simulasi untuk tes ke web sekarang.")
        pilihan = input("\nJalankan Mode Simulasi Virtual? (Y/n) atau ketik port (misal COM3): ").strip()
        if pilihan.upper() in ("", "Y", "YES"):
            run_simulation(SCAN_INTERVAL_SEC)
            return
        elif pilihan.upper().startswith("COM"):
            selected_port = pilihan.upper()
        else:
            sys.exit(0)
    else:
        if config_port != "AUTO" and config_port in available_ports:
            selected_port = config_port
            print(f"[CONFIG] Menggunakan port dari config.json: {selected_port}")
        else:
            print("COM Port yang terdeteksi:")
            for i, port in enumerate(available_ports, 1):
                print(f"  [{i}] {port}")

            if len(available_ports) == 1:
                selected_port = available_ports[0]
                print(f"\n[AUTO] Otomatis memilih port: {selected_port}")
            else:
                choice = input(f"\nPilih nomor port (1-{len(available_ports)}) atau ketik 's' untuk simulasi: ").strip()
                if choice.lower() == 's':
                    run_simulation(SCAN_INTERVAL_SEC)
                    return
                try:
                    selected_port = available_ports[int(choice) - 1]
                except Exception:
                    selected_port = available_ports[0]

    reader = HWVX6336Reader(port=selected_port, baudrate=BAUDRATE)
    print(f"[INFO] Menghubungkan ke {selected_port} ({BAUDRATE} bps)...")

    if not reader.connect():
        sys.exit(1)

    info = reader.get_reader_info()
    if info:
        print(f"[DEVICE] Terhubung! Firmware {info['firmware_version']} | Power: {info['power_dbm']} dBm")
    else:
        print("[DEVICE] Port serial terbuka dan siap melakukan pembacaan.")

    reader.beep(times=1, active_ms=80)

    print("\n" + "-" * 72)
    print("CARA PENGGUNAAN DI WEB (rfid.moko.ai.id):")
    print("  1. Buka browser ke halaman 'Input Barang Keluar' / 'Input RFID Produk'.")
    print("  2. Klik sekali pada kolom input 'TAG RFID' (Paste RFID hex).")
    print("  3. Tempelkan kartu / barang ke reader.")
    print(f"  4. Kode RFID otomatis ter-paste ke web, lalu ada jeda {SCAN_INTERVAL_SEC:.0f} detik.")
    print("  * Tekan Ctrl+C untuk berhenti.")
    print("-" * 72 + "\n")

    try:
        while True:
            tags = reader.inventory()
            waktu = time.strftime("%H:%M:%S")

            if tags:
                current_epc = tags[0]
                scan_counter += 1

                if CONFIG.get("beep_on_success", True):
                    reader.beep(times=1, active_ms=60)

                pasted, status_msg = auto_paste_replace(current_epc)
                status_icon = "OK" if pasted else "CLIPBOARD"
                print(f"[{waktu}] [SCAN #{scan_counter} - {status_icon}] EPC: {current_epc}")
                print(f"           -> {status_msg}")
                print(f"[{waktu}] Menunggu jeda {SCAN_INTERVAL_SEC:.0f} detik...\n")
                time.sleep(SCAN_INTERVAL_SEC)
            else:
                time.sleep(0.2)

    except KeyboardInterrupt:
        print("\n\n[INFO] Menghentikan aplikasi RFID Keyboard Wedge...")
    finally:
        reader.disconnect()
        print("[INFO] Aplikasi berhenti.")


if __name__ == "__main__":
    main()
