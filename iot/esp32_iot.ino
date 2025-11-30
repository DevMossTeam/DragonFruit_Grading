#include "HX711.h"
#include <ESP32Servo.h>
#include <WiFi.h>
#include <PubSubClient.h>

// WIFI & MQTT SETUP
const char* ssid = "mqtt";
const char* password = "12345678";
const char* mqtt_server = "10.120.200.21";

WiFiClient espClient;
PubSubClient client(espClient);

// HX711
#define DT  23
#define SCK 22
HX711 scale;

float calibration_factor = 400;

// SERVO & MOTOR
#define SERVO_PENDORONG 13  
#define SERVO_B         12
#define SERVO_C         14
#define PIN_MOTOR       26

Servo servoPendorong;
Servo servoB;
Servo servoC;

// variabel untuk menyimpan grade dari python
char gradePython = 0;

//  FUNGSI DORONG 
void servoDorong() {
  servoPendorong.write(45);
  delay(2000);
  servoPendorong.write(180);
}

//  EKSEKUSI SERVO BERDASARKAN GRADE 
void eksekusiGrade(char grade) {
  switch (grade) {
    case 'A':
      Serial.println("== Grade A (Python/Auto) ==");
      servoDorong();
      digitalWrite(PIN_MOTOR, HIGH);
      delay(4000);
      digitalWrite(PIN_MOTOR, LOW);
      break;

    case 'B':
      Serial.println("== Grade B (Python/Auto) ==");
      servoB.write(55);
      servoDorong();
      digitalWrite(PIN_MOTOR, HIGH);
      delay(3000);
      digitalWrite(PIN_MOTOR, LOW);
      servoB.write(0);
      break;

    case 'C':
      Serial.println("== Grade C (Python/Auto) ==");
      servoC.write(55);
      servoDorong();
      digitalWrite(PIN_MOTOR, HIGH);
      delay(1500);
      digitalWrite(PIN_MOTOR, LOW);
      servoC.write(5);
      break;
  }

  Serial.println("Proses grading selesai.\n");
}

//  CALLBACK MQTT 
void callback(char* topic, byte* payload, unsigned int length) {
  String msg = "";
  for (int i = 0; i < length; i++) msg += (char)payload[i];

  Serial.print("MQTT Masuk [");
  Serial.print(topic);
  Serial.print("] : ");
  Serial.println(msg);

  // jika python mengirim grade: A/B/C
  if (String(topic) == "iot/python/grade") {
    if (msg == "A" || msg == "B" || msg == "C") {
      gradePython = msg[0];
      Serial.println("Grade dari Python diterima: " + msg);
    }
  }
}

//  MQTT RECONNECT 
void reconnect() {
  while (!client.connected()) {
    Serial.print("Menghubungkan MQTT... ");

    if (client.connect("ESP32_Grading")) {
      Serial.println("Terhubung!");

      // subscribe topik dari python
      client.subscribe("iot/python/grade");
      client.subscribe("iot/python/command");

    } else {
      Serial.print("Gagal, rc=");
      Serial.print(client.state());
      Serial.println(" coba ulang 3 detik...");
      delay(3000);
    }
  }
}

//  SETUP =
void setup() {
  Serial.begin(115200);

  // WIFI
  Serial.println("Menghubungkan WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Terhubung!");
  Serial.println(WiFi.localIP());

  // MQTT
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);

  // LOAD CELL
  scale.begin(DT, SCK);
  Serial.println("Menunggu stabilisasi load cell...");
  delay(3000);
  scale.set_scale(calibration_factor);
  scale.tare();
  Serial.println("Load Cell Siap!\n");

  // SERVO
  servoPendorong.attach(SERVO_PENDORONG);
  servoB.attach(SERVO_B);
  servoC.attach(SERVO_C);

  pinMode(PIN_MOTOR, OUTPUT);
  digitalWrite(PIN_MOTOR, LOW);

  // posisi awal
  servoPendorong.write(180);
  servoB.write(0);
  servoC.write(5);

  Serial.println(" Sistem Grading Buah Naga Aktif ");
}

//  LOOP =
void loop() {

  // MQTT reconnect otomatis
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // jika grade dari Python ada → eksekusi langsung
  if (gradePython != 0) {
    char g = gradePython;
    gradePython = 0; // reset
    eksekusiGrade(g);
    return;
  }

  // =
  //  MODE OTOMATIS =
  // =

  if (!scale.is_ready()) {
    delay(200);
    return;
  }

  float weight = scale.get_units(5);
  if (abs(weight) < 1) weight = 0;

  Serial.print("Berat: ");
  Serial.print(weight, 2);
  Serial.println(" gram");

  // Kirim berat ke MQTT
  char msg[10];
  dtostrf(weight, 1, 2, msg);
  client.publish("iot/machine/weight", msg);

  // Jika <100 gram berarti belum ada buah
  if (weight < 100) {
    Serial.println("Belum ada buah...\n");
    delay(500);
    return;
  }

  // Cek stabil
  bool stabil = true;
  float w = weight;
  for (int i = 0; i < 10; i++) {
    float cek = scale.get_units(5);
    if (abs(cek - w) > 5) {
      stabil = false;
      break;
    }
    delay(50);
  }

  if (!stabil) {
    Serial.println("Berat belum stabil...\n");
    return;
  }

  // Tentukan grade otomatis
  char grade;

  if (weight > 350)       grade = 'A';
  else if (weight >= 250) grade = 'B';
  else                    grade = 'C';

  // Kirim grade auto ke MQTT
  char g[2] = {grade, 0};
  client.publish("iot/machine/grade", g);

  // Eksekusi servo
  eksekusiGrade(grade);

  delay(300);
}
