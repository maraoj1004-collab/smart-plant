# 스마트 반려식물 관리기

![CI](https://github.com/OWNER/smart-plant/actions/workflows/ci.yml/badge.svg)

ESP32가 센서값을 읽고 **룰셋 모델**로 행동을 정한 뒤, 로그를 서버의 **SQLite DB**에 저장합니다. **GitHub Actions CI**가 룰 테스트, 펌웨어 빌드, 서버 테스트를 자동으로 실행합니다.

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

## 룰셋 모델
위에서부터 먼저 맞는 룰 하나를 적용합니다.

| 우선순위 | 조건 | 행동 |
|---|---|---|
| 1 | 토양수분 < 30% | `WATER` 펌프 3초 작동 |
| 2 | 온도 > 32℃ | `HOT` 고온 경고 |
| 3 | 조도 < 200 | `DARK` 빛 부족 경고 |
| - | 그 외 | `NONE` |

## 배선
| 부품 | ESP32 핀 |
|---|---|
| 토양수분 센서 (AO) | GPIO 34 |
| 조도 센서 LDR (분압) | GPIO 35 |
| DHT22 (DATA) | GPIO 4 |
| 릴레이 (IN) → 펌프 | GPIO 26 |

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
2. `pio run -e esp32dev -t upload`로 업로드하고 `pio device monitor`로 확인합니다.
3. `pio test -e native`로 룰 테스트를 PC에서 실행합니다.

## API
- `POST /logs` 요청 본문: `{"soil":20,"temp":25,"hum":50,"light":800,"action":"WATER"}`
- `GET /logs` 최근 50개 로그 (최신순)
