"""
Skrip Pengaturan Otomatis Windows Startup untuk RFID HW-VX6336
"""

import os
import sys
import subprocess


def get_startup_dir() -> str:
    appdata = os.environ.get("APPDATA", "")
    return os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs\Startup")


def pasang_startup(silent: bool = False):
    startup_dir = get_startup_dir()
    lnk_path = os.path.join(startup_dir, "RFID_Reader.lnk")
    current_dir = os.path.dirname(os.path.abspath(__file__))

    target_file = os.path.join(
        current_dir,
        "Jalankan_RFID_Silent.vbs" if silent else "Jalankan_RFID.bat"
    )

    # Buat shortcut menggunakan PowerShell WScript.Shell
    ps_script = (
        f"$ws = New-Object -ComObject WScript.Shell; "
        f"$s = $ws.CreateShortcut('{lnk_path}'); "
        f"$s.TargetPath = '{target_file}'; "
        f"$s.WorkingDirectory = '{current_dir}'; "
        f"$s.Description = 'RFID HW-VX6336 Reader'; "
        f"$s.Save()"
    )

    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            check=True,
            capture_output=True,
            text=True
        )
        mode_str = "Latar Belakang (Silent tanpa jendela)" if silent else "Jendela Terminal (Terlihat)"
        print("=" * 60)
        print("[BERHASIL] Shortcut berhasil dipasang ke Startup Windows!")
        print(f"Mode    : {mode_str}")
        print(f"Target  : {target_file}")
        print(f"Lokasi  : {lnk_path}")
        print("=" * 60)
        print("\nAplikasi akan otomatis berjalan setiap komputer dinyalakan.")
    except Exception as e:
        print(f"[ERROR] Gagal memasang startup: {e}")


def hapus_startup():
    startup_dir = get_startup_dir()
    lnk_path = os.path.join(startup_dir, "RFID_Reader.lnk")

    if os.path.exists(lnk_path):
        try:
            os.remove(lnk_path)
            print("=" * 60)
            print("[BERHASIL] Shortcut RFID Reader telah dihapus dari Startup.")
            print("=" * 60)
        except Exception as e:
            print(f"[ERROR] Gagal menghapus file shortcut: {e}")
    else:
        print("[INFO] Shortcut tidak ditemukan di Startup Windows (sudah nonaktif).")


def main():
    print("=" * 60)
    print("      PENGATURAN WINDOWS STARTUP - RFID HW-VX6336")
    print("=" * 60)
    print("\nPilih aksi:")
    print("  [1] Pasang ke Startup (Tampilkan Jendela Terminal - Direkomendasikan)")
    print("  [2] Pasang ke Startup (Mode Tersembunyi / Latar Belakang)")
    print("  [3] Hapus dari Startup (Nonaktifkan Auto-Start)")
    print("  [4] Keluar")

    pilihan = input("\nMasukkan pilihan (1/2/3/4): ").strip()
    if pilihan == "1":
        pasang_startup(silent=False)
    elif pilihan == "2":
        pasang_startup(silent=True)
    elif pilihan == "3":
        hapus_startup()
    else:
        print("Dibatalkan.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ("--install", "-i"):
            pasang_startup(silent=False)
        elif arg in ("--silent", "-s"):
            pasang_startup(silent=True)
        elif arg in ("--remove", "-r"):
            hapus_startup()
        else:
            main()
    else:
        main()

