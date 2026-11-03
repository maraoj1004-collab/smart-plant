#pragma once

// 룰셋 모델: 센서값 -> 행동. 하드웨어와 분리된 순수 함수라 PC(native)에서 테스트 가능.
enum Action { NONE, WATER, ALERT_HOT, ALERT_DARK };

struct Reading {
  float soil;   // 토양수분 (%)
  float temp;   // 온도 (C)
  float hum;    // 습도 (%)
  int light;    // 조도 (ADC 0~4095)
};

const float SOIL_DRY = 30.0f;  // 이 값 미만이면 물 주기
const float TEMP_HOT = 32.0f;  // 이 값 초과면 고온 경고
const int LIGHT_DARK = 200;    // 이 값 미만이면 빛 부족

// 우선순위: 물 부족 > 고온 > 빛 부족
inline Action decide(const Reading& r) {
  if (r.soil < SOIL_DRY) return WATER;
  if (r.temp > TEMP_HOT) return ALERT_HOT;
  if (r.light < LIGHT_DARK) return ALERT_DARK;
  return NONE;
}

inline const char* actionName(Action a) {
  switch (a) {
    case WATER: return "WATER";
    case ALERT_HOT: return "HOT";
    case ALERT_DARK: return "DARK";
    default: return "NONE";
  }
}
