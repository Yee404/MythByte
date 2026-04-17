import cv2
import time
import os
import subprocess
import serial

base = os.path.dirname(os.path.abspath(__file__))

# ── CAPTURA ──────────────────────────────────────────────────────────────────
def capture(name):
    path = os.path.join(base, name)
    subprocess.run([
        "rpicam-jpeg", "-o", path,
        "--width", "320", "--height", "240",
        "--timeout", "1000", "--nopreview"
    ], check=True)
    return path

print("Capturando left.jpg...")
capture("left.jpg")
time.sleep(1)
print("Capturando right.jpg...")
capture("right.jpg")

# ── PIPELINE ─────────────────────────────────────────────────────────────────
start_total = time.time()

left  = cv2.imread(os.path.join(base, "left.jpg"))
right = cv2.imread(os.path.join(base, "right.jpg"))

if left is None:
    raise RuntimeError("left.jpg no encontrado")
if right is None:
    print("right.jpg no encontrado, duplicando left")
    right = left.copy()

left  = cv2.resize(left,  (320, 240))
right = cv2.resize(right, (320, 240))

print(left.shape)
print(right.shape)

# ── ANAGLIFO ROJO/CIAN ────────────────────────────────────────────────────────
start_proc = time.time()

# Canal R de left → ojo izquierdo (rojo)
# Canales G y B de right → ojo derecho (cian)
anaglyph = left.copy()
anaglyph[:, :, 0] = right[:, :, 0]  # B → right
anaglyph[:, :, 1] = right[:, :, 1]  # G → right
anaglyph[:, :, 2] = left[:, :, 2]   # R → left

output_path = os.path.join(base, "stereo.jpg")
cv2.imwrite(output_path, anaglyph, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
print("Guardado en:", output_path)
end_proc = time.time()

# ── LECTURA BINARIA ───────────────────────────────────────────────────────────
with open(output_path, "rb") as f:
    data = f.read()

print(f"Tamaño: {len(data)} bytes")
print(f"Procesamiento: {(end_proc - start_proc)*1000:.1f}ms")

# ── FRAGMENTACIÓN ─────────────────────────────────────────────────────────────
CHUNK_SIZE = 200

def build_packet(seq, payload):
    header = f"{seq:05d}|".encode()
    chk    = (sum(payload) & 0xFF).to_bytes(1, "big")
    return header + payload + chk

chunks  = [data[i:i+CHUNK_SIZE] for i in range(0, len(data), CHUNK_SIZE)]
packets = [build_packet(i, c) for i, c in enumerate(chunks)]
print(f"Chunks: {len(chunks)} paquetes de ~{CHUNK_SIZE}B")

# ── VALIDACIÓN LOCAL ──────────────────────────────────────────────────────────
reconstructed = b"".join(chunks)
rec_path = os.path.join(base, "reconstructed.jpg")
with open(rec_path, "wb") as f:
    f.write(reconstructed)
assert reconstructed == data, "ERROR: reconstrucción no coincide"
print("Validación local: OK")

# ── UART ──────────────────────────────────────────────────────────────────────
UART_PORT = "/dev/serial0"
BAUD      = 115200

try:
    ser = serial.Serial(UART_PORT, BAUD, timeout=1)
    time.sleep(2)
    ser.write(b"START\n")
    for pkt in packets:
        ser.write(pkt)
        time.sleep(0.005)   # 5ms entre paquetes — evita desborde buffer ESP32
    ser.write(b"END\n")
    ser.close()
    print("UART: transmisión completa")
except serial.SerialException as e:
    print(f"UART no disponible ({e}) — modo solo fragmentación")

end_total = time.time()
print(f"Total: {(end_total - start_total)*1000:.1f}ms")