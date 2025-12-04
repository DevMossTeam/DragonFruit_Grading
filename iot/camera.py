import cv2
import numpy as np
import os
import sys;
import paho.mqtt.client as mqtt
import threading
from flask import Flask, Response

# =============================
# IMPORT MODEL & MQTT SENDER
# =============================
sys.path.append(r"D:\Programming\Clone Github\DargonFruit_Grading\model")
sys.path.append(r"D:\Programming\Clone Github\DargonFruit_Grading\iot")

from fuzzy_single import predict_single_image
from mqtt_machine_bridge import send_grade
from firebase_uploader import send_to_firebase

# =============================
# GLOBAL STATE
# =============================
latest_weight = None
trigger_capture = False
stream_frame = None  # frame terakhir untuk stream

# =============================
# MQTT CALLBACK
# =============================
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✓ MQTT Kamera Terhubung")
        client.subscribe("iot/machine/weight")
        client.subscribe("iot/camera/capture")
    else:
        print("✗ Gagal koneksi MQTT:", rc)

def on_message(client, userdata, msg):
    global latest_weight, trigger_capture
    topic = msg.topic
    payload = msg.payload.decode()

    if topic == "iot/machine/weight":
        try:
            latest_weight = float(payload)
        except:
            pass
    elif topic == "iot/camera/capture":
        print("📸 Trigger capture diterima")
        trigger_capture = True

def start_mqtt():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("10.204.14.89", 1883, 60)
    client.loop_forever()

threading.Thread(target=start_mqtt, daemon=True).start()

# =============================
# CAMERA SETUP
# =============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(BASE_DIR, "..", "data")
os.makedirs(SAVE_DIR, exist_ok=True)
SAVE_PATH = os.path.join(SAVE_DIR, "photo_latest.jpg")

def remove_black_border(frame, threshold=15):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mask = gray > threshold
    coords = np.column_stack(np.where(mask))
    if coords.size == 0:
        return frame
    y_min, x_min = coords.min(axis=0)
    y_max, x_max = coords.max(axis=0)
    cropped = frame[y_min:y_max, x_min:x_max]
    return cropped if cropped.size > 0 else frame

def resize_keep_ratio(img, target_height=720):
    h, w = img.shape[:2]
    scale = target_height / h
    new_w = int(w * scale)
    return cv2.resize(img, (new_w, target_height))

def make_square(img):
    h, w = img.shape[:2]
    side = min(h, w)
    x1 = (w - side) // 2
    y1 = (h - side) // 2
    return img[y1:y1+side, x1:x1+side]

# === FIX: resize final image to 3060 x 3060 ===
def resize_to_3060_square(img, size=3060):
    return cv2.resize(img, (size, size))

# Cari kamera otomatis
camera_index = -1
for i in range(5):
    test = cv2.VideoCapture(i)
    if test.isOpened():
        print("Kamera ditemukan di index", i)
        camera_index = i
        test.release()
        break

if camera_index == -1:
    print("Tidak ada kamera ditemukan!")
    sys.exit()

cap = cv2.VideoCapture(camera_index)
print("\n=== Sistem Siap, Mode Headless + Streaming ===\n")

# =============================
# FLASK STREAM APP
# =============================
app = Flask(__name__)

def gen_frames():
    global stream_frame
    while True:
        if stream_frame is None:
            continue
        ret, buffer = cv2.imencode('.jpg', stream_frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def start_flask():
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

threading.Thread(target=start_flask, daemon=True).start()

# =============================
# LOOP UTAMA
# =============================
while True:
    ret, frame = cap.read()
    if not ret:
        continue

    frame_clean = remove_black_border(frame)
    stream_frame = resize_keep_ratio(frame_clean, 900)

    # Capture untuk model
    if trigger_capture:
        trigger_capture = False

        # make square first
        model_img = make_square(frame_clean)

        # === FIX: resize ke 3060×3060 ===
        model_img = resize_to_3060_square(model_img)

        # Simpan file
        model_path = os.path.join(BASE_DIR, "temp", "temp_uploaded_image.jpg")
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        cv2.imwrite(model_path, model_img)
        cv2.imwrite(SAVE_PATH, model_img)

        print("[INFO] Gambar disimpan (3060x3060):", SAVE_PATH)
        print("Memproses grading...")

        try:
            result, err = predict_single_image(model_path)
            if err:
                print("[ERROR] Pipeline gagal:", err)
                continue

            result["actual"] = latest_weight if latest_weight else 0

            print("\nHASIL:")
            print("Grade   :", result["grade"])
            print("Length  :", result["length"])
            print("Diameter:", result["diameter"])
            print("Est. Wt :", result["weight"])
            print("Actual  :", result["actual"])

            send_grade(result["grade"])
            send_to_firebase(result)

        except Exception as e:
            print("TERJADI ERROR:", e)
