import cv2
import numpy as np
import os
import sys
import requests
import json
import logging
from datetime import datetime

# =========================
# IMPORT MODEL & MQTT SENDER
# =========================
sys.path.append(r"D:\Programming\Clone Github\DargonFruit_Grading\model")
sys.path.append(r"D:\Programming\Clone Github\DargonFruit_Grading\iot")

from predict_single import predict_single_image
from mqtt_machine_bridge import send_grade   # ← Kirim grade via MQTT

# =========================
# LOGGING SETUP
# =========================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =========================
# CONFIGURATION
# =========================
TARGET_SIZE = 3060
BACKEND_URL = "http://localhost:8000/api"  # ← URL Backend FastAPI
INSERTDATA_ENDPOINT = f"{BACKEND_URL}/insertdata"  # Endpoint untuk insert data
TIMEOUT_REQUEST = 10  # Timeout untuk HTTP request (detik)

# =========================
# Folder & Nama File Fix
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(BASE_DIR, "..", "data")
os.makedirs(SAVE_DIR, exist_ok=True)

SAVE_PATH = os.path.join(SAVE_DIR, "photo_latest.jpg")


# =========================
# Hilangkan bingkai hitam
# =========================
def remove_black_border(frame, threshold=15):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mask = gray > threshold
    coords = np.column_stack(np.where(mask))

    if coords.size == 0:
        return frame

    y_min, x_min = coords.min(axis=0)
    y_max, x_max = coords.max(axis=0)

    cropped = frame[y_min:y_max, x_min:x_max]

    if cropped.size == 0:
        return frame

    return cropped


# =========================
# INSERT DATA KE DATABASE
# =========================
def send_grading_to_backend(grading_result: dict) -> bool:
    """
    Kirim hasil grading ke InsertdataController di backend
    
    Args:
        grading_result: Dictionary dengan keys:
            - grade: 'A', 'B', atau 'C'
            - score: Fuzzy score (0-100)
            - length: Panjang (cm)
            - diameter: Diameter (cm)
            - weight: Berat (g)
            - ratio: Ratio L/D
    
    Returns:
        True jika berhasil, False jika gagal
    """
    try:
        # Prepare data untuk backend (tanpa filename)
        payload = {
            "grade": str(grading_result["grade"]),
            "score": float(grading_result["score"]),
            "length": float(grading_result["length"]),
            "diameter": float(grading_result["diameter"]),
            "weight": float(grading_result["weight"]),
            "ratio": float(grading_result["ratio"])
        }
        
        # Endpoint 1: Set ke buffer
        logger.info("📤 Mengirim data ke backend (buffer)...")
        response = requests.post(
            f"{INSERTDATA_ENDPOINT}/grading-buffer",
            params=payload,
            timeout=TIMEOUT_REQUEST
        )
        response.raise_for_status()
        
        buffer_result = response.json()
        logger.info(f"✓ Data tersimpan di buffer: {buffer_result.get('message')}")
        
        # Step 2: Insert dari buffer ke database
        logger.info("💾 Inserting data ke database...")
        response2 = requests.post(
            f"{INSERTDATA_ENDPOINT}/insert-from-buffer",
            timeout=TIMEOUT_REQUEST
        )
        response2.raise_for_status()
        
        db_result = response2.json()
        logger.info(f"✓ Data berhasil disimpan ke database!")
        logger.info(f"  - ID: {db_result.get('id')}")
        logger.info(f"  - Grade: {db_result.get('final_grade')}")
        
        return True
    
    except requests.exceptions.ConnectionError:
        logger.error("✗ Error: Tidak bisa connect ke backend")
        logger.error(f"  Pastikan FastAPI running di {BACKEND_URL}")
        return False
    
    except requests.exceptions.Timeout:
        logger.error(f"✗ Timeout: Request melebihi {TIMEOUT_REQUEST}s")
        return False
    
    except requests.exceptions.HTTPError as e:
        logger.error(f"✗ HTTP Error: {e.response.status_code}")
        try:
            error_detail = e.response.json()
            logger.error(f"  Detail: {error_detail}")
        except:
            logger.error(f"  {e.response.text}")
        return False
    
    except Exception as e:
        logger.error(f"✗ Error sending data: {e}")
        return False


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
    print("Tidak ada kamera!")
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

    frame_clean = remove_black_border(frame)

    h, w = frame_clean.shape[:2]
    if h == 0 or w == 0:
        continue

    # Crop ke 1:1
    side = min(h, w)
    x1 = (w - side) // 2
    y1 = (h - side) // 2
    square = frame_clean[y1:y1+side, x1:x1+side]

    if square.size == 0:
        continue

    output = cv2.resize(square, (TARGET_SIZE, TARGET_SIZE))

    cv2.imshow("Camera 1:1 (3060x3060)", output)

    key = cv2.waitKey(1)

    # =========================
    # SAVE dan PROSES
    # =========================
    if key == ord('s'):
        cv2.imwrite(SAVE_PATH, output)
        print("[INFO] Gambar disimpan →", SAVE_PATH)

        # Proses gambar untuk grading
        TEMP_DIR = os.path.join(BASE_DIR, "temp")
        os.makedirs(TEMP_DIR, exist_ok=True)

        temp_path = os.path.join(TEMP_DIR, "temp_uploaded_image.jpg")
        cv2.imwrite(temp_path, output)

        print("\nMemproses gambar...")

        try:
            result, err = predict_single_image(temp_path)

            if err:
                print("[ERROR] Pipeline gagal:", err)
            else:
                print("\n" + "="*50)
                print("HASIL ANALISIS GAMBAR")
                print("="*50)
                print("Prediksi Grade :", result["grade"])
                print("Akurasi Fuzzy  :", f"{result['score']:.1f}%")
                print("Panjang        :", f"{result['length']:.2f} cm")
                print("Diameter       :", f"{result['diameter']:.2f} cm")
                print("Berat Estimasi :", f"{result['weight']:.0f} g")
                print("Rasio L/D      :", f"{result['ratio']:.2f}")
                print("="*50 + "\n")

                # =========================
                # INSERT DATA KE BACKEND
                # =========================
                logger.info("🔄 Proses: Insert data ke backend...")
                success = send_grading_to_backend(result)
                
                if success:
                    logger.info("✅ Data berhasil di-insert ke database!")
                else:
                    logger.warning("⚠️ Gagal mengirim data ke backend")
                    logger.warning("   Cek apakah backend running di http://localhost:8000")

                # =========================
                # Kirim via MQTT (tetap dilakukan)
                # =========================
                print("\nMengirm grade via MQTT...")
                send_grade(result["grade"])

        except Exception as e:
            print("Terjadi kesalahan:", e)
            logger.exception("Exception occurred")

    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

