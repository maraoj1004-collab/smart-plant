# 스마트 반려식물 관리기

![CI](https://github.com/maraoj1004-collab/smart-plant/actions/workflows/ci.yml/badge.svg)

Seeed XIAO ESP32S3 Sense가 센서값을 읽고 **룰셋 모델**로 행동을 정한 뒤, 로그를 서버의 **SQLite DB**에 저장합니다. **GitHub Actions CI**가 룰 테스트, 펌웨어 빌드, 서버 테스트를 자동으로 실행합니다.

```
[ESP32 + 센서] --(WiFi, HTTP POST JSON)--> [Flask 서버] --> [SQLite DB]
     └ 룰셋 모델 (rules.h)
GitHub Actions CI: 룰 단위테스트 + ESP32 빌드 + 서버 테스트
```

## 과제 조건
| 조건 | 구현 |
|---|---|
| 1. ESP32에 모델 넣기 | [firmware/include/rules.h](firmware/include/rules.h) 룰셋 모델 |
| 2. 로그를 DB에 저장 | [server/app.py](server/app.py) Flask + SQLite |
| 3. CI 구현 | [.github/workflows/ci.yml](.github/workflows/ci.yml) |

## 시뮬레이션 모드
센서 없이 시연할 수 있도록 `USE_SIMULATED_SENSORS 1`(기본값)일 때 정상 → 건조 → 정상 → 고온 → 어두움 시나리오 값을 차례로 생성합니다. 룰 판단과 DB 저장은 실제와 똑같이 동작하고, `WATER`일 때 펌프 대신 보드 LED가 3초 켜집니다. 실제 센서를 연결하면 [main.cpp](firmware/src/main.cpp)에서 값을 `0`으로 바꾸면 됩니다.

## 룰셋 모델
위에서부터 먼저 맞는 룰 하나를 적용합니다.

| 우선순위 | 조건 | 행동 |
|---|---|---|
| 1 | 토양수분 < 30% | `WATER` 펌프 3초 작동 |
| 2 | 온도 > 32℃ | `HOT` 고온 경고 |
| 3 | 조도 < 200 | `DARK` 빛 부족 경고 |
| - | 그 외 | `NONE` |

## 배선
| 부품 | XIAO 핀 |
|---|---|
| 토양수분 센서 (AO) | A0 (D0) |
| 조도 센서 LDR (분압) | A1 (D1) |
| DHT22 (DATA) | D3 |
| 릴레이 (IN) → 펌프 | D4 |

- 센서 전원은 3V3과 GND에 연결합니다. XIAO의 GPIO는 3.3V라 5V 신호를 직접 넣으면 안 됩니다.
- 5V 릴레이 모듈은 VCC를 5V(VBUS) 핀에 연결합니다.
- WiFi를 쓰려면 함께 들어 있는 U.FL 안테나를 꼭 연결해야 합니다.

## 실행 방법
### 서버
```bash
cd server
pip install -r requirements.txt
python app.py          # http://<PC IP>:5000/logs
python -m pytest       # 테스트
```
Windows 방화벽에서 5000번 포트를 허용하세요.

### 펌웨어 (VS Code + PlatformIO)
1. `firmware/include/secrets.example.h`를 `secrets.h`로 복사하고 WiFi와 서버 주소를 채웁니다.
2. `pio run -e xiao_esp32s3 -t upload`로 업로드하고 `pio device monitor`로 확인합니다.
3. `pio test -e native`로 룰 테스트를 PC에서 실행합니다.

## API
- `POST /logs` 요청 본문: `{"soil":20,"temp":25,"hum":50,"light":800,"action":"WATER"}`
- `GET /logs` 최근 50개 로그 (최신순)
