import cv2
import numpy as np
import os

TARGET_SIZE = 3060

# =========================
# Folder penyimpanan foto
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # posisi file Python
SAVE_DIR = os.path.join(BASE_DIR, "..", "raw_data")     # keluar 1 folder → raw_data

# Buat folder jika belum ada
os.makedirs(SAVE_DIR, exist_ok=True)

def get_next_filename():
    """Cari nomor file berikutnya"""
    existing = [f for f in os.listdir(SAVE_DIR) if f.startswith("photo_3060x3060")]
    numbers = []

    for f in existing:
        try:
            num = int(f.replace("photo_3060x3060_", "").replace(".jpg", ""))
            numbers.append(num)
        except:
            pass

    next_num = max(numbers) + 1 if numbers else 1
    return os.path.join(SAVE_DIR, f"photo_3060x3060_{next_num}.jpg")


# =========================
# Cari kamera otomatis
# =========================
camera_index = -1
for i in range(5):
    cap_test = cv2.VideoCapture(i)
    if cap_test.isOpened():
        print("Kamera ditemukan pada index", i)
        camera_index = i
        cap_test.release()
        break

if camera_index == -1:
    print("Tidak ada kamera ditemukan!")
    exit()

cap = cv2.VideoCapture(camera_index)

if not cap.isOpened():
    print("Gagal membuka kamera index", camera_index)
    exit()


# =========================
# Fungsi Auto Crop
# =========================
def auto_crop_no_black(frame, threshold=10):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mask = gray > threshold
    coords = np.column_stack(np.where(mask))

    if len(coords) == 0:
        return frame

    y_min, x_min = coords.min(axis=0)
    y_max, x_max = coords.max(axis=0)

    return frame[y_min:y_max, x_min:x_max]


# =========================
# LOOP UTAMA
# =========================
while True:
    ret, frame = cap.read()
    if not ret:
        print("Frame tidak terbaca!")
        break

    frame_no_black = auto_crop_no_black(frame)

    h, w = frame_no_black.shape[:2]

    side = min(h, w)
    x1 = (w - side) // 2
    y1 = (h - side) // 2
    square = frame_no_black[y1:y1+side, x1:x1+side]

    output = cv2.resize(square, (TARGET_SIZE, TARGET_SIZE), interpolation=cv2.INTER_AREA)

    cv2.imshow("AutoCrop 1:1 Full 3060x3060", output)

    key = cv2.waitKey(1)

    # =========================
    # Simpan foto ke raw_data/
    # =========================
    if key == ord('s'):
        filename = get_next_filename()
        cv2.imwrite(filename, output)
        print("✔ Disimpan:", filename)

    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
