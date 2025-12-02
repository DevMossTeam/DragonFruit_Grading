import paho.mqtt.client as mqtt

# KONFIGURASI MQTT
MQTT_BROKER = "10.204.14.105"     # Samakan dengan ESP32
MQTT_PORT   = 1883
TOPIC_WEIGHT = "iot/machine/weight"   # Data dari load cell

# ✅ Global variable untuk menyimpan weight terbaru
latest_weight_g = None

# CALLBACK KETIKA TERHUBUNG
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✓ Terhubung ke MQTT broker")
        client.subscribe(TOPIC_WEIGHT)
        print(f"✓ Subscribe ke topik: {TOPIC_WEIGHT}")
    else:
        print("✗ Gagal terhubung, kode:", rc)

# CALLBACK KETIKA ADA DATA MASUK
def on_message(client, userdata, msg):
    global latest_weight_g  # ✅ Akses global variable
    
    bobot = msg.payload.decode()
    print(f"[MQTT] Berat diterima: {bobot} gram")
    
    # ✅ SIMPAN ke global variable sehingga camera.py bisa baca
    try:
        latest_weight_g = float(bobot)
        print(f"✓ Weight tersimpan di variabel: {latest_weight_g} g")
    except ValueError:
        print(f"✗ Error: Berat invalid '{bobot}'")

# Initialize client but DON'T connect yet (will be called from main.py)
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

def start_mqtt_connection():
    """Start MQTT connection - call this from app startup, not at import time"""
    try:
        print("Menghubungkan ke MQTT...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()  # Start in background thread instead of blocking
        print("✓ MQTT connection started")
    except Exception as e:
        print(f"✗ MQTT connection failed: {e}")

# Don't connect on import - let the application call start_mqtt_connection() during startup
