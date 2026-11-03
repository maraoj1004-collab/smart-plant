import sqlite3

from flask import Flask, jsonify, render_template_string, request

FIELDS = ("soil", "temp", "hum", "light", "action")

DASHBOARD = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="10">
<title>스마트 반려식물</title>
<style>
  body { font-family: system-ui, sans-serif; margin: 24px; color: #1f2933; background: #f7faf7; }
  h1 { margin: 0 0 4px; }
  .sub { color: #66788a; margin-bottom: 20px; }
  .cards { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 20px; }
  .card { background: #fff; border-radius: 10px; padding: 12px 16px; min-width: 110px;
          box-shadow: 0 1px 3px rgba(0,0,0,.08); }
  .card b { display: block; font-size: 24px; }
  table { border-collapse: collapse; width: 100%; background: #fff; border-radius: 10px; overflow: hidden;
          box-shadow: 0 1px 3px rgba(0,0,0,.08); }
  th, td { padding: 8px 12px; text-align: right; border-bottom: 1px solid #eef2f0; }
  th { background: #eaf3ec; }
  th:first-child, td:first-child, td:last-child, th:last-child { text-align: left; }
  .tag { padding: 2px 8px; border-radius: 6px; font-weight: 600; font-size: 13px; }
  .NONE { background: #e3f4e6; color: #2f7a3e; }
  .WATER { background: #dcebfb; color: #1f5fa8; }
  .HOT { background: #fde4e1; color: #b3372a; }
  .DARK { background: #ebe6f7; color: #5b3fa0; }
</style>
</head>
<body>
<h1>🪴 스마트 반려식물 관리기</h1>
<div class="sub">ESP32 룰셋 판단 로그 · 10초마다 새로고침 · 전체 {{ total }}건</div>
<div class="cards">
  {% for name, label in [("NONE","정상"),("WATER","물 주기"),("HOT","고온"),("DARK","빛 부족")] %}
  <div class="card"><span class="tag {{ name }}">{{ label }}</span><b>{{ counts.get(name, 0) }}</b></div>
  {% endfor %}
</div>
<table>
  <tr><th>시간</th><th>토양수분(%)</th><th>온도(℃)</th><th>습도(%)</th><th>조도</th><th>판단</th></tr>
  {% for r in rows %}
  <tr><td>{{ r.ts }}</td><td>{{ r.soil }}</td><td>{{ r.temp }}</td><td>{{ r.hum }}</td><td>{{ r.light }}</td>
      <td><span class="tag {{ r.action }}">{{ r.action }}</span></td></tr>
  {% else %}
  <tr><td colspan="6">아직 로그가 없습니다.</td></tr>
  {% endfor %}
</table>
</body>
</html>"""


def create_app(db_path="plant.db"):
    app = Flask(__name__)

    def db():
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("""CREATE TABLE IF NOT EXISTS logs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts DATETIME DEFAULT (datetime('now', 'localtime')),
            soil REAL, temp REAL, hum REAL, light INTEGER, action TEXT)""")
        return conn

    @app.post("/logs")
    def add_log():
        d = request.get_json(silent=True) or {}
        missing = [f for f in FIELDS if f not in d]
        if missing:
            return jsonify(ok=False, missing=missing), 400
        conn = db()
        with conn:
            conn.execute(
                "INSERT INTO logs(soil,temp,hum,light,action) VALUES(?,?,?,?,?)",
                tuple(d[f] for f in FIELDS),
            )
        conn.close()
        return jsonify(ok=True), 201

    @app.get("/logs")
    def list_logs():
        conn = db()
        rows = conn.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 50").fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])

    @app.get("/")
    def dashboard():
        conn = db()
        rows = conn.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 50").fetchall()
        counts = dict(conn.execute("SELECT action, COUNT(*) FROM logs GROUP BY action").fetchall())
        conn.close()
        return render_template_string(
            DASHBOARD, rows=rows, counts=counts, total=sum(counts.values())
        )

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=5000)
