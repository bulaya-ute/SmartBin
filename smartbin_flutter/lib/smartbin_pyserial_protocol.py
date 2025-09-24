#!/usr/bin/env python3
"""
SmartBin PySerial Protocol (Flutter bundle copy)
This is a copy of the project's protocol script placed under the Flutter lib folder
for reference or desktop execution via an external process.
Note: Flutter does not execute Python directly; invoke this with a Process if needed.
"""

import serial
import subprocess
import threading
import time
import base64
import io
from PIL import Image
from typing import Tuple

class SmartBinPySerialProtocol:
    def __init__(self, esp32_mac: str = "EC:E3:34:15:F2:62", rfcomm_device: str = "/dev/rfcomm0", baudrate: int = 115200):
        self.esp32_mac = esp32_mac
        self.rfcomm_device = rfcomm_device
        self.baudrate = baudrate
        self.ser = None
        self.running = False
        self.connected = False
        self.rfcomm_bound = False
        self.waiting_for_image = False
        self.image_metadata = {}
        self.image_parts = {}
        self.expected_parts = 0
        self.reader_thread = None

    def start(self):
        print("🚀 Starting SmartBin PySerial Protocol Communication")
        if not self._setup_rfcomm_binding():
            return False
        if not self._setup_serial():
            return False
        self.running = True
        self._start_reader_thread()
        self._main_loop()
        return True

    def stop(self):
        print("🛑 Stopping SmartBin communication")
        self.running = False
        self.connected = False
        if self.reader_thread:
            self.reader_thread.join(timeout=2)
        self._cleanup_serial()
        self._cleanup_rfcomm_binding()

    def _setup_rfcomm_binding(self) -> bool:
        try:
            print(f"🔗 Binding RFCOMM to {self.esp32_mac}...")
            try:
                subprocess.run(["sudo", "rfcomm", "release", "0"], capture_output=True, text=True, timeout=5)
            except Exception:
                pass
            res = subprocess.run(["sudo", "rfcomm", "bind", "0", self.esp32_mac, "1"], capture_output=True, text=True, timeout=10)
            if res.returncode != 0:
                print(f"❌ Failed to bind RFCOMM: {res.stderr}")
                return False
            self.rfcomm_bound = True
            print(f"✅ RFCOMM bound to {self.rfcomm_device}")
            time.sleep(1)
            return True
        except Exception as e:
            print(f"❌ RFCOMM setup error: {e}")
            return False

    def _cleanup_rfcomm_binding(self):
        if self.rfcomm_bound:
            try:
                subprocess.run(["sudo", "rfcomm", "release", "0"], capture_output=True, text=True, timeout=5)
                print("✅ RFCOMM released")
            except Exception as e:
                print(f"⚠️ RFCOMM release warning: {e}")
            self.rfcomm_bound = False

    def _setup_serial(self) -> bool:
        try:
            print(f"📡 Opening serial {self.rfcomm_device}...")
            self.ser = serial.Serial(
                port=self.rfcomm_device,
                baudrate=self.baudrate,
                timeout=1,
                write_timeout=1,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
            )
            self.ser.flushInput(); self.ser.flushOutput()
            print("✅ Serial open")
            return True
        except Exception as e:
            print(f"❌ Serial error: {e}")
            return False

    def _cleanup_serial(self):
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
                print("✅ Serial closed")
            except Exception as e:
                print(f"⚠️ Serial close warning: {e}")

    def _start_reader_thread(self):
        self.reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self.reader_thread.start()

    def _reader_loop(self):
        print("📖 Reader active")
        while self.running and self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        self._process_line(line)
                else:
                    time.sleep(0.01)
            except Exception as e:
                if self.running:
                    print(f"❌ Reader error: {e}")
                break
        print("📖 Reader stopped")

    def _process_line(self, line: str):
        if self._is_protocol_message(line):
            code, content = self._extract_code_content(line)
            self._handle_protocol_message(code, content)
        else:
            print(f"📝 ESP32: {line}")

    def _send_message(self, code: str, content: str = "") -> bool:
        try:
            if not self.ser or not self.ser.is_open:
                print("❌ Serial not open")
                return False
            msg = f"{code} {content}".strip()
            self.ser.write((msg + "\n").encode("utf-8"))
            self.ser.flush()
            print(f"📤 Sent: {msg}")
            return True
        except Exception as e:
            print(f"❌ Send error: {e}")
            return False

    def _is_protocol_message(self, line: str) -> bool:
        if len(line) < 6:
            return False
        code = line[:5]
        if line[5] != ' ':
            return False
        return (code in ['RTC00', 'RTC01', 'RTC02', 'CLS01'] or
                code.startswith('PA') or code.startswith('PX') or
                code.startswith('ERR'))

    def _extract_code_content(self, line: str) -> Tuple[str, str]:
        code = line[:5]
        content = line[6:] if len(line) > 6 else ""
        return code, content

    def _handle_protocol_message(self, code: str, content: str):
        print(f"📥 Protocol: {code} {content}")
        if code == 'RTC00':
            print("🤝 ESP32 requesting connection")
            self._send_message('RTC01', 'Laptop ready')
        elif code == 'RTC02':
            print("🎉 Connection established")
            self.connected = True
        elif code == 'PA000':
            self._handle_image_metadata(content)
        elif code.startswith('PA'):
            self._handle_image_part(int(code[2:]), content)
        elif code.startswith('PX'):
            self._handle_final_image_part(int(code[2:]), content)
        elif code.startswith('ERR'):
            print(f"⚠️ ESP32 Error: {content}")

    def _handle_image_metadata(self, content: str):
        print(f"📷 Image metadata: {content}")
        self.image_metadata = {}
        self.image_parts = {}
        for item in content.split(','):
            item = item.strip()
            if ':' in item:
                k, v = item.split(':', 1)
                self.image_metadata[k.strip()] = v.strip()
        self.expected_parts = int(self.image_metadata.get('parts', '0'))
        self.waiting_for_image = True
        print(f"📊 Expecting {self.expected_parts} parts")

    def _handle_image_part(self, part_num: int, content: str):
        if not self.waiting_for_image:
            print("⚠️ Part received unexpectedly")
            return
        self.image_parts[part_num] = content
        print(f"📦 Received part {part_num}/{self.expected_parts}")

    def _handle_final_image_part(self, part_num: int, content: str):
        if not self.waiting_for_image:
            print("⚠️ Final part received unexpectedly")
            return
        self.image_parts[part_num] = content
        print(f"🏁 Final part {part_num}/{self.expected_parts}")
        self._process_complete_image()

    def _process_complete_image(self):
        try:
            print("🔄 Processing complete image...")
            base64_data = "".join(self.image_parts.get(i, "") for i in range(1, self.expected_parts + 1))
            image_data = base64.b64decode(base64_data)
            image = Image.open(io.BytesIO(image_data))
            print(f"🖼️ Image decoded: {image.size}, {image.format}")
            print("📸 Classification handled externally")
        except Exception as e:
            print(f"❌ Image processing error: {e}")
            self._send_message('ERR04', 'image_processing_failed')
        finally:
            self.waiting_for_image = False
            self.image_metadata = {}
            self.image_parts = {}
            self.expected_parts = 0

if __name__ == '__main__':
    p = SmartBinPySerialProtocol()
    try:
        p.start()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    finally:
        p.stop()

