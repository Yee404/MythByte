import cv2
import time
import os

base = os.path.dirname(__file__)

start_total = time.time()

# Cargar imágenes correctamente
left = cv2.imread(os.path.join(base, "left.jpg"))
right = cv2.imread(os.path.join(base, "right.jpg"))

left = cv2.resize(left, (320, 240))
right = cv2.resize(right, (320, 240))

# Validación
if left is None:
    raise Exception("No se encontró left.jpg")

if right is None:
    print("No se encontró right.jpg, duplicando left")
    right = left.copy()

print(left.shape) #resolución de left
print(right.shape)

# Procesamiento
start_proc = time.time()
stereo = cv2.hconcat([left, right])

output_path = os.path.join(base, "stereo.jpg")
cv2.imwrite(output_path, stereo, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
print("Guardado en:", output_path)

end_proc = time.time()

# Lectura binaria
start_bytes = time.time()
with open("Software/raspberry/stereo.jpg", "rb") as f:
    data = f.read()
end_bytes = time.time()

end_total = time.time()

print("Tamaño:", len(data), "bytes")
print("Procesamiento:", end_proc - start_proc)
print("Lectura:", end_bytes - start_bytes)
print("Total:", end_total - start_total)