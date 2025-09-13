```
sortir-jagung/
│
├── dataset/                         # Data untuk PCV & AI
│   ├── grade_a/                     # Gambar jagung kualitas bagus (Grade A)
│   ├── grade_b/                     # Gambar jagung kualitas sedang (Grade B)
│   └── grade_c/                     # Gambar jagung kualitas rendah (Grade C)
│
├── preprocessing/                   # Modul PCV
│   ├── preprocess_images.py         # Resize, normalisasi, augmentasi
│   └── segmentation.py              # Segmentasi buah jagung (OpenCV)
│
├── model/                           # Modul Sistem Kecerdasan (AI/DL)
│   ├── train_model.ipynb            # Notebook training CNN/ResNet/MobileNet
│   ├── evaluate_model.py            # Evaluasi akurasi, confusion matrix
│   ├── model.h5                     # Model hasil training (TensorFlow/Keras)
│   └── model.tflite                 # Versi ringan untuk IoT/edge device
│
├── classification/                  # Modul inferensi (real-time klasifikasi)
│   ├── classify_realtime.py         # Klasifikasi buah jagung via webcam
│   └── test_single_image.py         # Tes klasifikasi untuk 1 gambar input
│
├── iot/                             # Modul IoT
│   ├── esp32_iot.ino                # ESP32 code (kirim data via WiFi/MQTT/Firebase)
│   ├── mqtt_publisher.py            # Alternatif publish data dari Python → broker
│   └── mqtt_subscriber.py           # Listener untuk dashboard lokal
│
├── dashboard/                       # Modul monitoring
│   ├── web_dashboard/               # Web-based dashboard
│   │   ├── index.html               # Tampilan utama dashboard
│   │   ├── style.css                # Styling
│   │   └── app.js                   # JS untuk ambil data dari Firebase/MQTT
│   └── mobile_app/                  # (Opsional) App Android
│       └── mit_app_inventor.aia     # File project MIT App Inventor
│
├── actuator/                        # Modul sortir mekanik (opsional)
│   └── servo_control.ino            # Kode servo motor untuk sortir fisik jagung
│
├── docs/                            # Dokumentasi & laporan
│   ├── proposal.docx                # Proposal tugas akhir semester
│   ├── laporan.docx                 # Laporan akhir
│   ├── flowchart.png                # Diagram alur sistem
│   └── architecture.png             # Arsitektur PCV + AI + IoT
│
├── requirements.txt                 # Daftar library Python (OpenCV, TensorFlow, MQTT, dll.)
└── README.md                        # Penjelasan singkat project
```
1. PCV (Pengolahan Citra & Vision)
```
preprocessing/capture_dataset.py
preprocessing/preprocess_images.py
preprocessing/segmentation.py
Fokus: pengambilan gambar buah jagung, segmentasi citra, preprocessing.
```

2. Sistem Kecerdasan (AI/ML)
```
model/train_model.ipynb (training CNN/ResNet/MobileNet)
model/evaluate_model.py (evaluasi akurasi model)
classification/classify_realtime.py (klasifikasi buah jagung real-time menjadi Grade A, B, C)
Fokus: klasifikasi kualitas jagung dengan deep learning.
```
3. IoT
```
iot/esp32_iot.ino (ESP32 kirim hasil sortir ke cloud)
iot/mqtt_publisher.py + mqtt_subscriber.py (komunikasi data)
dashboard/web_dashboard/ (dashboard real-time menampilkan jumlah jagung per grade)
actuator/servo_control.ino (opsional: mekanisme sortir fisik ke wadah A, B, C)
```

## Roadmap Proyek

### Tahap 1 – Perencanaan Sistem
- Menentukan kebutuhan sistem: klasifikasi buah jagung menjadi Grade A, B, C.  
- Menyusun arsitektur sistem: PCV, AI, IoT, aktuator (opsional).  
- Menentukan perangkat keras: kamera, ESP32/Raspberry Pi, motor/servo.

### Tahap 2 – Dataset & Preprocessing
- **Pengumpulan Data**  
  - Foto buah jagung utuh dari berbagai kondisi (Grade A, B, C).  
  - Minimal 300–500 citra per kelas.  

- **Preprocessing (PCV)**  
  - Resize gambar (misal 224×224 px).  
  - Normalisasi piksel (0–1).  
  - Augmentasi data (rotasi, flip, pencahayaan).  
  - (Opsional) Segmentasi citra untuk crop hanya buah jagung.  

- **Output**: Dataset siap latih dalam folder `grade_a/`, `grade_b/`, `grade_c/`.

### Tahap 3 – Training Model AI
- **Pemodelan AI (Sistem Kecerdasan)**  
  - Pilih arsitektur CNN sederhana atau Transfer Learning (ResNet50, MobileNet).  
  - Latih model dengan dataset jagung.  
  - Evaluasi dengan confusion matrix, precision, recall, F1-score.  

- **Optimisasi Model**  
  - Hyperparameter tuning.  
  - Simpan model ke format `.h5` dan `.tflite`.  

- **Output**: Model AI siap pakai untuk klasifikasi jagung Grade A, B, C.

### Tahap 4 – Implementasi Klasifikasi Real-Time
- **Program Real-Time Classification**  
  - Input kamera/webcam.  
  - Jalankan inferensi model secara langsung.  
  - Tampilkan hasil klasifikasi di layar.  

- **Pengujian**  
  - Uji dengan buah jagung nyata.  
  - Catat akurasi real-time.  

- **Output**: Program real-time yang dapat mendeteksi dan menampilkan Grade jagung.

### Tahap 5 – Integrasi IoT
- **Komunikasi IoT**  
  - ESP32/ESP8266 untuk mengirim hasil klasifikasi ke server/cloud.  
  - Alternatif: Python script publish ke MQTT broker/Firebase.  

- **Dashboard Monitoring**  
  - Web dashboard (HTML, CSS, JS).  
  - Menampilkan jumlah jagung per grade (A, B, C).  
  - Grafik tren batch.  

- **Output**: Dashboard real-time untuk memonitor hasil sortir jagung.

### Tahap 6 – Mekanisme Sortir Fisik (Opsional)
- **Kontrol Mekanis**  
  - Servo/motor untuk memisahkan jagung sesuai Grade.  
  - Integrasi dengan ESP32 untuk mengarahkan jagung ke wadah A, B, C.  

- **Pengujian Sistem Lengkap**  
  - Uji coba dengan jagung bergerak di conveyor/wadah.  

- **Output**: Prototipe mesin sortir otomatis (jika diwajibkan).
