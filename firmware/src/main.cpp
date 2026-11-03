#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include "rules.h"
#include "secrets.h"
#include "camera_light.h"

#define SOIL_PIN A0   // D0 (GPIO1)
#define LIGHT_PIN A1  // D1 (GPIO2)
#define DHT_PIN D3    // GPIO4
#define PUMP_PIN D4   // GPIO5
#define STATUS_LED LED_BUILTIN  // 보드 주황 LED (LOW = 켜짐)

// 1이면 센서 없이 시나리오 값으로 동작, 실제 센서를 연결하면 0으로 바꾸세요
#define USE_SIMULATED_SENSORS 1
// 1이면 조도를 보드 카메라 밝기로 실제 측정 (시뮬레이션 모드에서도 적용)
// 빌드만 확인했고 보드 테스트 전이라 기본값은 꺼둠
#define USE_CAMERA_LIGHT 0

// 토양센서 보정값: 시리얼로 마른 흙/젖은 흙 값을 읽어서 바꾸세요
#define SOIL_ADC_DRY 4095
#define SOIL_ADC_WET 1500

const unsigned long INTERVAL_MS = 10000;
const unsigned long PUMP_MS = 3000;

DHT dht(DHT_PIN, DHT22);
bool cameraReady = false;

float readSoilPercent() {
  int raw = analogRead(SOIL_PIN);
  float pct = (float)(SOIL_ADC_DRY - raw) * 100.0f / (SOIL_ADC_DRY - SOIL_ADC_WET);
  return constrain(pct, 0.0f, 100.0f);
}

// 정상 -> 건조 -> 정상 -> 고온 -> 어두움 순서로 돌면서 모든 룰을 보여줌
Reading simulatedReading() {
  static const Reading scenarios[] = {
      {55, 24, 50, 1500},  // NONE
      {22, 25, 45, 1400},  // WATER
      {48, 26, 50, 1300},  // NONE
      {50, 34, 35, 2500},  // HOT
      {52, 23, 55, 120},   // DARK
  };
  static size_t step = 0;
  Reading r = scenarios[step++ % (sizeof(scenarios) / sizeof(scenarios[0]))];
  r.soil += random(-20, 21) / 10.0f;  // 약간의 잡음
  r.temp += random(-5, 6) / 10.0f;
  return r;
}

bool readSensors(Reading& r) {
  if (USE_SIMULATED_SENSORS) {
    r = simulatedReading();
  } else {
    r.soil = readSoilPercent();
    r.temp = dht.readTemperature();
    r.hum = dht.readHumidity();
    r.light = analogRead(LIGHT_PIN);
    if (isnan(r.temp) || isnan(r.hum)) return false;
  }
  if (cameraReady) {
    int light = readCameraLight();
    if (light >= 0) r.light = light;
  }
  return true;
}

void connectWiFi() {
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("WiFi connecting");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.printf("\nWiFi OK: %s\n", WiFi.localIP().toString().c_str());
}

void sendLog(const Reading& r, Action a) {
  if (WiFi.status() != WL_CONNECTED) connectWiFi();

  char body[160];
  snprintf(body, sizeof(body),
           "{\"soil\":%.1f,\"temp\":%.1f,\"hum\":%.1f,\"light\":%d,\"action\":\"%s\"}",
           r.soil, r.temp, r.hum, r.light, actionName(a));

  HTTPClient http;
  http.begin(SERVER_URL);
  http.addHeader("Content-Type", "application/json");
  int code = http.POST(body);
  Serial.printf("%s -> %d\n", body, code);
  http.end();
}

void setup() {
  Serial.begin(115200);
  pinMode(PUMP_PIN, OUTPUT);
  digitalWrite(PUMP_PIN, LOW);
  pinMode(STATUS_LED, OUTPUT);
  digitalWrite(STATUS_LED, HIGH);
  dht.begin();
  if (USE_CAMERA_LIGHT) {
    cameraReady = initCameraLight();
    Serial.println(cameraReady ? "Camera light sensor OK" : "Camera init failed");
  }
  connectWiFi();
  if (USE_SIMULATED_SENSORS) Serial.println("Simulated sensor mode");
}

void loop() {
  Reading r;
  if (!readSensors(r)) {
    Serial.println("DHT read failed");
    delay(2000);
    return;
  }

  Action a = decide(r);
  if (a == WATER) {
    digitalWrite(PUMP_PIN, HIGH);
    digitalWrite(STATUS_LED, LOW);
    delay(PUMP_MS);
    digitalWrite(PUMP_PIN, LOW);
    digitalWrite(STATUS_LED, HIGH);
  }

  sendLog(r, a);
  delay(INTERVAL_MS);
}
