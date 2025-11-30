import cv2
import numpy as np
import os

TARGET_SIZE = 3060

# =========================
# Folder penyimpanan foto
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(BASE_DIR, "..", "raw_data")
os.makedirs(SAVE_DIR, exist_ok=True)

def get_next_filename():
    existing = [f for f in os.listdir(SAVE_DIR) if f.startswith("photo_3060x3060")]
    numbers = []
    for f in existing:
        try:
            numbers.append(int(f.replace("photo_3060x3060_", "").replace(".jpg", "")))
        except:
            pass
    next_num = max(numbers) + 1 if numbers else 1
    return os.path.join(SAVE_DIR, f"photo_3060x3060_{next_num}.jpg")


# =========================
# Hilangkan bingkai hitam (simple & aman)
# =========================
def remove_black_border(frame, threshold=15):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mask = gray > threshold
    coords = np.column_stack(np.where(mask))

    if coords.size == 0:
        return frame  # fail-safe

    y_min, x_min = coords.min(axis=0)
    y_max, x_max = coords.max(axis=0)

    cropped = frame[y_min:y_max, x_min:x_max]

    if cropped.size == 0:
        return frame  # fail-safe

    return cropped


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


# =========================
# LOOP UTAMA
# =========================
while True:
    ret, frame = cap.read()
    if not ret:
        print("Frame tidak terbaca")
        break

    # --- Hapus bingkai hitam ---
    frame_clean = remove_black_border(frame)

    h, w = frame_clean.shape[:2]
    if h == 0 or w == 0:
        continue

    # --- Crop kotak 1:1 ---
    side = min(h, w)
    x1 = (w - side) // 2
    y1 = (h - side) // 2

    square = frame_clean[y1:y1+side, x1:x1+side]

    if square.size == 0:
        continue

    # --- Resize ke 3060 x 3060 ---
    output = cv2.resize(square, (TARGET_SIZE, TARGET_SIZE))

    cv2.imshow("Camera 1:1 (3060x3060)", output)

    key = cv2.waitKey(1)

    # --- Save ---
    if key == ord('s'):
        filename = get_next_filename()
        cv2.imwrite(filename, output)
        print("✔ Saved:", filename)

    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
