"""
Skrip Penulisan / Encode EPC Tag RFID UHF Electron HW-VX6336
Digunakan untuk menulis atau mengubah nomor EPC pada kartu / tag UHF Gen2 (ISO18000-6C).
"""

import sys
import time
import serial
import serial.tools.list_ports


def calculate_crc16(data: bytes) -> tuple[int, int]:
    """Menghitung CRC-16 (Preset: 0xFFFF, Polynomial: 0x8408)"""
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


class HWVX6336Writer:
    def __init__(self, port: str, baudrate: int = 57600, address: int = 0x00):
        self.port = port
        self.baudrate = baudrate
        self.address = address
        self.ser: serial.Serial | None = None

    def connect(self) -> bool:
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1.5
            )
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            return True
        except Exception as e:
            print(f"[ERROR] Gagal membuka port {self.port}: {e}")
            return False

    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()

    def _send_command(self, cmd: int, data: bytes = b"") -> bytes | None:
        if not self.ser or not self.ser.is_open:
            return None

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

    def beep(self, times: int = 1, active_ms: int = 80):
        active_t = max(1, min(255, active_ms // 50))
        data = bytes([active_t, 1, times])
        self._send_command(0x33, data)

    def read_current_epc(self) -> str | None:
        """Membaca EPC tag yang saat ini berada di atas reader"""
        resp = self._send_command(0x01)
        if not resp:
            return None
        status = resp[3]
        if status in (0x01, 0x02, 0x03, 0x04):
            data_block = resp[4:-2]
            if data_block and data_block[0] >= 1:
                epc_len = data_block[1]
                epc_bytes = data_block[2:2 + epc_len]
                return epc_bytes.hex().upper()
        return None

    def write_epc(self, new_epc_hex: str, password_hex: str = "00000000") -> tuple[bool, str]:
        """
        Menuliskan nomor EPC baru ke tag UHF (Cmd 0x04: Write EPC).
        Panjang EPC harus berupa kelipatan kata (1 word = 2 byte / 4 karakter hex).
        Standar umum EPC adalah 12 byte (24 karakter hex).
        """
        clean_epc = new_epc_hex.replace(" ", "").strip()
        if len(clean_epc) % 4 != 0:
            return False, "Panjang EPC harus genap dalam satuan word (kelipatan 4 karakter HEX, misal 24 karakter)"

        try:
            wepc_bytes = bytes.fromhex(clean_epc)
            pwd_bytes = bytes.fromhex(password_hex.zfill(8))
        except ValueError:
            return False, "Format karakter HEX tidak valid! Gunakan angka 0-9 dan huruf A-F"

        enum = len(wepc_bytes) // 2  # Jumlah word (16-bit)
        if enum < 1 or enum > 15:
            return False, f"Jumlah word EPC ({enum}) di luar rentang yang diizinkan (1-15 word)"

        # Parameter Cmd 0x04: [ENum (1B)] [Password (4B)] [WEPC (Variable)]
        cmd_data = bytes([enum]) + pwd_bytes + wepc_bytes
        resp = self._send_command(0x04, cmd_data)

        if not resp:
            return False, "Tidak ada respons dari reader (pastikan tag menempel stabil)"

        status = resp[3]
        if status == 0x00:
            return True, "Berhasil menulis EPC baru ke tag"
        elif status == 0xFB:
            return False, "Tidak ada tag di jangkauan reader (No Tag Operable)"
        elif status == 0x05:
            return False, "Access Password salah"
        elif status == 0xFC:
            return False, "Tag mengembalikan error code (mungkin memori tag terkunci/write-protected)"
        else:
            return False, f"Gagal menulis dengan kode status reader: 0x{status:02X}"


def main():
    print("=" * 65)
    print("      PROGRAM PENULIS / ENCODER EPC RFID ELECTRON HW-VX6336")
    print("=" * 65)

    ports = [p.device for p in serial.tools.list_ports.comports()]
    if not ports:
        print("[!] Tidak ada COM port terdeteksi. Pastikan reader terhubung.")
        selected_port = input("Ketik port manual (misal COM3): ").strip()
        if not selected_port:
            sys.exit(0)
    else:
        selected_port = ports[0] if len(ports) == 1 else ports[int(input(f"Pilih port (1-{len(ports)}): ")) - 1]

    writer = HWVX6336Writer(port=selected_port)
    print(f"\n[INFO] Menghubungkan ke {selected_port}...")
    if not writer.connect():
        sys.exit(1)

    print("[SUCCESS] Reader siap.\n")
    print("-" * 65)
    print("PETUNJUK:")
    print("1. Tempelkan HANYA 1 buah kartu/tag di atas reader.")
    print("2. Jangan menggerakkan kartu selama proses penulisan.")
    print("-" * 65 + "\n")

    input("Tekan Enter untuk mendeteksi kartu yang ada di atas reader...")

    current_epc = writer.read_current_epc()
    if not current_epc:
        print("[!] Kartu tidak terdeteksi! Pastikan kartu ditempelkan tepat di atas reader.")
        writer.disconnect()
        sys.exit(1)

    print(f"\n[INFO] Kartu terdeteksi saat ini:")
    print(f"       EPC Lama: {current_epc} ({len(current_epc) // 2} Byte)")
    writer.beep(1, 60)

    print("\nMasukkan EPC Baru:")
    print("Contoh standar (12 byte / 24 hex): E28011700000020B776C92A1")
    new_epc = input("EPC Baru: ").strip().upper()

    if not new_epc:
        print("[!] Penulisan dibatalkan.")
        writer.disconnect()
        sys.exit(0)

    print(f"\n[PROSES] Menulis {new_epc} ke tag...")
    success, msg = writer.write_epc(new_epc)

    if success:
        writer.beep(2, 80)
        print(f"[BERHASIL] {msg}")

        # Verifikasi pembacaan ulang
        time.sleep(0.3)
        verified_epc = writer.read_current_epc()
        print(f"[VERIFIKASI] EPC terbaca setelah ditulis: {verified_epc}")
        if verified_epc == new_epc:
            print("[VALID] EPC berhasil diverifikasi 100% cocok!")
        else:
            print("[WARN] Nilai terbaca berbeda, silakan cek kembali.")
    else:
        print(f"[GAGAL] {msg}")

    writer.disconnect()
    print("\n[INFO] Selesai.")


if __name__ == "__main__":
    main()
