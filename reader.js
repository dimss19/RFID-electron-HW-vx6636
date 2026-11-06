/**
 * HW-VX6336 (dan varian VX6336) UHF RFID Reader untuk Node.js / Electron
 * Menggunakan protokol bawaan: 57600 baud, 8 data bit, 1 stop bit, no parity (8N1).
 *
 * Persyaratan:
 *   npm install serialport
 *
 * Penggunaan:
 *   node reader.js
 */

const EventEmitter = require('events');
let SerialPort;
try {
  ({ SerialPort } = require('serialport'));
} catch (e) {
  // Ditangani saat runtime jika modul belum di-install
}

function calculateCrc16(buffer) {
  let crc = 0xFFFF;
  const poly = 0x8408; // CCITT Reverse
  for (let i = 0; i < buffer.length; i++) {
    crc ^= buffer[i];
    for (let j = 0; j < 8; j++) {
      if (crc & 1) {
        crc = (crc >> 1) ^ poly;
      } else {
        crc = crc >> 1;
      }
    }
  }
  return { lsb: crc & 0xFF, msb: (crc >> 8) & 0xFF };
}

function buildPacket(cmd, data = Buffer.alloc(0), address = 0x00) {
  // Len = 1(address) + 1(cmd) + data.length + 2(crc) = data.length + 4
  const len = data.length + 4;
  const header = Buffer.from([len, address, cmd]);
  const payload = Buffer.concat([header, data]);
  const { lsb, msb } = calculateCrc16(payload);
  return Buffer.concat([payload, Buffer.from([lsb, msb])]);
}

class HWVX6336Reader extends EventEmitter {
  constructor(portPath, baudRate = 57600, address = 0x00) {
    super();
    this.portPath = portPath;
    this.baudRate = baudRate;
    this.address = address;
    this.port = null;
    this.rxBuffer = Buffer.alloc(0);
    this.scanInterval = null;
    this.lastSeen = new Map();
    this.cooldownMs = 5000; // Cooldown 5 detik untuk tag yang sama
  }

  async connect() {
    if (!SerialPort) {
      throw new Error("Modul 'serialport' belum terinstall. Jalankan: npm install serialport");
    }

    return new Promise((resolve, reject) => {
      this.port = new SerialPort({
        path: this.portPath,
        baudRate: this.baudRate,
        dataBits: 8,
        stopBits: 1,
        parity: 'none',
        autoOpen: false
      });

      this.port.open((err) => {
        if (err) return reject(err);

        this.port.on('data', (chunk) => this._onData(chunk));
        this.port.on('error', (err) => this.emit('error', err));
        this.port.on('close', () => this.emit('close'));

        resolve();
      });
    });
  }

  disconnect() {
    this.stopScanning();
    if (this.port && this.port.isOpen) {
      this.port.close();
    }
  }

  _onData(chunk) {
    this.rxBuffer = Buffer.concat([this.rxBuffer, chunk]);

    while (this.rxBuffer.length > 0) {
      const len = this.rxBuffer[0];
      const packetSize = len + 1;

      // Jika buffer belum lengkap, tunggu chunk berikutnya
      if (this.rxBuffer.length < packetSize) break;

      const packet = this.rxBuffer.subarray(0, packetSize);
      this.rxBuffer = this.rxBuffer.subarray(packetSize);

      // Verifikasi CRC
      const dataToVerify = packet.subarray(0, packetSize - 2);
      const { lsb, msb } = calculateCrc16(dataToVerify);

      if (packet[packetSize - 2] === lsb && packet[packetSize - 1] === msb) {
        this._handlePacket(packet);
      } else {
        // Jika CRC tidak cocok, geser 1 byte untuk resinkronisasi stream
        this.rxBuffer = packet.subarray(1);
      }
    }
  }

  _handlePacket(packet) {
    const reCmd = packet[2];
    const status = packet[3];

    // Response Inventory (0x01)
    if (reCmd === 0x01) {
      if ([0x01, 0x02, 0x03, 0x04].includes(status)) {
        const numTags = packet[4];
        let offset = 5;
        const now = Date.now();

        for (let i = 0; i < numTags; i++) {
          if (offset >= packet.length - 2) break;
          const epcLen = packet[offset++];
          if (offset + epcLen <= packet.length - 2) {
            const epc = packet.subarray(offset, offset + epcLen).toString('hex').toUpperCase();
            offset += epcLen;

            // Cooldown check
            const lastTime = this.lastSeen.get(epc) || 0;
            if (now - lastTime > this.cooldownMs) {
              this.lastSeen.set(epc, now);
              this.emit('tag', epc);
            }
          }
        }
      }
    }
  }

  sendInventory() {
    if (this.port && this.port.isOpen) {
      const packet = buildPacket(0x01, Buffer.alloc(0), this.address);
      this.port.write(packet);
    }
  }

  beep(times = 1, activeMs = 80) {
    if (this.port && this.port.isOpen) {
      const activeT = Math.min(255, Math.max(1, Math.floor(activeMs / 50)));
      const silentT = 1;
      const data = Buffer.from([activeT, silentT, times]);
      const packet = buildPacket(0x33, data, this.address);
      this.port.write(packet);
    }
  }

  startScanning(intervalMs = 100) {
    if (this.scanInterval) return;
    this.scanInterval = setInterval(() => {
      this.sendInventory();
    }, intervalMs);
  }

  stopScanning() {
    if (this.scanInterval) {
      clearInterval(this.scanInterval);
      this.scanInterval = null;
    }
  }
}

// Eksekusi jika dijalankan secara langsung di CLI
if (require.main === module) {
  (async () => {
    if (!SerialPort) {
      console.log("[ERROR] Modul 'serialport' belum terpasang.");
      console.log("Silakan jalankan perintah:");
      console.log("  npm init -y");
      console.log("  npm install serialport\n");
      return;
    }

    console.log("==================================================");
    console.log("   NODE.JS PEMBACA UHF RFID HW-VX6336 (ELECTRON)");
    console.log("==================================================");

    const ports = await SerialPort.list();
    if (ports.length === 0) {
      console.log("[!] Tidak ada port COM terdeteksi.");
      console.log("    Pastikan perangkat HW-VX6336 sudah terpasang.");
      return;
    }

    console.log("Daftar COM Port:");
    ports.forEach((p, idx) => {
      console.log(`  [${idx + 1}] ${p.path} (${p.friendlyName || p.manufacturer || 'Perangkat Serial'})`);
    });

    const selectedPort = ports[0].path;
    console.log(`\nMenghubungkan ke ${selectedPort}...`);

    const reader = new HWVX6336Reader(selectedPort, 57600);

    reader.on('tag', (epc) => {
      const timeStr = new Date().toLocaleTimeString();
      console.log(`[${timeStr}] TAG TERDETEKSI: ${epc}`);
      reader.beep(1, 50);
    });

    reader.on('error', (err) => {
      console.error("[ERROR]", err.message);
    });

    await reader.connect();
    console.log("[SUCCESS] Port terhubung! Memulai scan...");
    reader.beep(1, 60);
    const SCAN_INTERVAL_MS = 5000; // Scan setiap 5 detik sekali
    reader.startScanning(SCAN_INTERVAL_MS);

    console.log(`Tempelkan Tag RFID ke reader. Reader akan melakukan scan setiap ${SCAN_INTERVAL_MS / 1000} detik.`);
    console.log("Tekan Ctrl+C untuk berhenti.\n");

    process.on('SIGINT', () => {
      console.log("\nMenutup reader...");
      reader.disconnect();
      process.exit(0);
    });
  })();
}

module.exports = { HWVX6336Reader, calculateCrc16, buildPacket };

