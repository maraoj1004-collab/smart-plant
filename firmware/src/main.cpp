#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include "rules.h"
#include "secrets.h"

#define SOIL_PIN 34
#define LIGHT_PIN 35
#define DHT_PIN 4
#define PUMP_PIN 26

// 토양센서 보정값: 시리얼로 마른 흙/젖은 흙 값을 읽어서 바꾸세요
#define SOIL_ADC_DRY 4095
#define SOIL_ADC_WET 1500

const unsigned long INTERVAL_MS = 10000;
const unsigned long PUMP_MS = 3000;

DHT dht(DHT_PIN, DHT22);

float readSoilPercent() {
  int raw = analogRead(SOIL_PIN);
  float pct = (float)(SOIL_ADC_DRY - raw) * 100.0f / (SOIL_ADC_DRY - SOIL_ADC_WET);
  return constrain(pct, 0.0f, 100.0f);
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
  dht.begin();
  connectWiFi();
}

void loop() {
  Reading r;
  r.soil = readSoilPercent();
  r.temp = dht.readTemperature();
  r.hum = dht.readHumidity();
  r.light = analogRead(LIGHT_PIN);

  if (isnan(r.temp) || isnan(r.hum)) {
    Serial.println("DHT read failed");
    delay(2000);
    return;
  }

  Action a = decide(r);
  if (a == WATER) {
    digitalWrite(PUMP_PIN, HIGH);
    delay(PUMP_MS);
    digitalWrite(PUMP_PIN, LOW);
  }

  sendLog(r, a);
  delay(INTERVAL_MS);
}
