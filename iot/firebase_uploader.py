import requests
import datetime

# ============================
# KONFIGURASI FIREBASE
# ============================

FIREBASE_URL = "https://sortir-buah-naga-default-rtdb.firebaseio.com/predictions"

# ============================
# FUNGSI KIRIM DATA KE FIREBASE
# ============================

def send_to_firebase(result):
    """
    Mengirim hasil grading ke Firebase Realtime Database.
    result harus mengandung:
      - grade
      - length
      - diameter
      - weight
      - ratio
      - actual (optional, dari MQTT)
    """

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    data = {
        "timestamp": timestamp,
        "grade": result["grade"],
        "length": round(result["length"], 2),
        "diameter": round(result["diameter"], 2),
        "weight": round(result["weight"], 2),
        "actual": round(result.get("actual", 0), 2),   # 👈 DITAMBAHKAN DI SINI
        "ratio": round(result["ratio"], 2)
    }

    url = FIREBASE_URL + ".json"

    try:
        response = requests.post(url, json=data)

        if response.status_code == 200:
            print("[FIREBASE] Data terkirim:", data)
        else:
            print("[FIREBASE] Gagal mengirim:", response.text)

    except Exception as e:
        print("[FIREBASE ERROR]:", e)
