#pragma once
#include "esp_camera.h"

// XIAO ESP32S3 Sense 카메라를 조도 센서로 사용: 흑백 사진의 평균 밝기를 조도값으로 변환

bool initCameraLight() {
  camera_config_t c = {};
  c.pin_pwdn = -1;
  c.pin_reset = -1;
  c.pin_xclk = 10;
  c.pin_sccb_sda = 40;
  c.pin_sccb_scl = 39;
  c.pin_d7 = 48;
  c.pin_d6 = 11;
  c.pin_d5 = 12;
  c.pin_d4 = 14;
  c.pin_d3 = 16;
  c.pin_d2 = 18;
  c.pin_d1 = 17;
  c.pin_d0 = 15;
  c.pin_vsync = 38;
  c.pin_href = 47;
  c.pin_pclk = 13;
  c.xclk_freq_hz = 20000000;
  c.ledc_timer = LEDC_TIMER_0;
  c.ledc_channel = LEDC_CHANNEL_0;
  c.pixel_format = PIXFORMAT_GRAYSCALE;
  c.frame_size = FRAMESIZE_QQVGA;  // 160x120, 밝기만 볼 거라 작게
  c.fb_count = 2;
  c.fb_location = CAMERA_FB_IN_PSRAM;
  c.grab_mode = CAMERA_GRAB_LATEST;
  if (esp_camera_init(&c) != ESP_OK) return false;

  // 자동 노출/자동 게인을 끄고 고정해야 어두우면 실제로 어둡게 찍힘
  sensor_t* s = esp_camera_sensor_get();
  s->set_exposure_ctrl(s, 0);
  s->set_aec_value(s, 300);
  s->set_gain_ctrl(s, 0);
  s->set_agc_gain(s, 0);
  return true;
}

// 평균 밝기(0~255)를 조도 센서와 같은 0~4095 범위로 변환, 실패하면 -1
int readCameraLight() {
  camera_fb_t* fb = esp_camera_fb_get();  // 오래된 프레임 버리기
  if (fb) esp_camera_fb_return(fb);
  fb = esp_camera_fb_get();
  if (!fb) return -1;

  uint32_t sum = 0;
  for (size_t i = 0; i < fb->len; i++) sum += fb->buf[i];
  int avg = sum / fb->len;
  esp_camera_fb_return(fb);

  Serial.printf("camera brightness %d/255\n", avg);
  return avg * 16;
}
