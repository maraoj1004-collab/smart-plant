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
  .charts { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 12px; margin-bottom: 20px; }
  .chart { background: #fff; border-radius: 10px; padding: 12px 16px; position: relative;
           box-shadow: 0 1px 3px rgba(0,0,0,.08); }
  .chart h2 { font-size: 15px; margin: 0 0 6px; }
  .chart svg { display: block; width: 100%; height: 180px; touch-action: none; }
  .chart text { font-size: 11px; fill: #66788a; }
  .chart text.halo { paint-order: stroke; stroke: #fff; stroke-width: 4px; fill: #52606d; }
  .tip { position: absolute; pointer-events: none; background: #1f2933; color: #fff; font-size: 12px;
         padding: 6px 8px; border-radius: 6px; white-space: nowrap; display: none; }
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
<div class="charts">
  <div class="chart"><h2>토양수분 (%)</h2><svg id="soil-chart"></svg><div class="tip"></div></div>
  <div class="chart"><h2>온도 (℃)</h2><svg id="temp-chart"></svg><div class="tip"></div></div>
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
<script>
const LOGS = {{ chart | tojson }};  // 오래된 순
const NS = "http://www.w3.org/2000/svg";

function el(tag, attrs, parent) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  parent.appendChild(e);
  return e;
}

// 한 측정값의 선 그래프 + 룰 기준선 + 마우스를 올리면 값 표시
function lineChart(id, key, unit, lo, hi, limit, limitLabel, color) {
  const svg = document.getElementById(id);
  const tip = svg.nextElementSibling;
  if (LOGS.length < 2) {
    el("text", { x: 0, y: 90 }, svg).textContent = "로그가 2건 이상 쌓이면 그래프가 표시됩니다.";
    return;
  }
  const W = svg.clientWidth, H = 180, m = { l: 34, r: 8, t: 10, b: 22 };
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  const vals = LOGS.map(d => d[key]);
  lo = Math.min(lo, ...vals); hi = Math.max(hi, ...vals);
  const x = i => m.l + (W - m.l - m.r) * i / (LOGS.length - 1);
  const y = v => m.t + (H - m.t - m.b) * (1 - (v - lo) / (hi - lo));

  for (let k = 0; k <= 4; k++) {  // 옅은 격자와 y축 눈금
    const v = lo + (hi - lo) * k / 4;
    el("line", { x1: m.l, x2: W - m.r, y1: y(v), y2: y(v), stroke: "#eef2f0" }, svg);
    el("text", { x: m.l - 6, y: y(v) + 4, "text-anchor": "end" }, svg).textContent = Math.round(v);
  }
  const t = s => s.slice(11, 16);
  el("text", { x: m.l, y: H - 4 }, svg).textContent = t(LOGS[0].ts);
  el("text", { x: W - m.r, y: H - 4, "text-anchor": "end" }, svg).textContent = t(LOGS[LOGS.length - 1].ts);

  el("line", { x1: m.l, x2: W - m.r, y1: y(limit), y2: y(limit), stroke: "#8a96a3",
               "stroke-dasharray": "4 4" }, svg);
  el("path", { d: vals.map((v, i) => (i ? "L" : "M") + x(i) + " " + y(v)).join(""),
               fill: "none", stroke: color, "stroke-width": 2, "stroke-linejoin": "round" }, svg);
  el("text", { x: W - m.r, y: y(limit) - 5, "text-anchor": "end", class: "halo" }, svg).textContent = limitLabel;

  const cross = el("line", { y1: m.t, y2: H - m.b, stroke: "#9aa5b1", visibility: "hidden" }, svg);
  const dot = el("circle", { r: 4.5, fill: color, stroke: "#fff", "stroke-width": 2, visibility: "hidden" }, svg);
  svg.addEventListener("pointermove", e => {
    const px = (e.clientX - svg.getBoundingClientRect().left) * W / svg.clientWidth;
    const i = Math.max(0, Math.min(LOGS.length - 1,
      Math.round((px - m.l) / (W - m.l - m.r) * (LOGS.length - 1))));
    const d = LOGS[i];
    cross.setAttribute("x1", x(i)); cross.setAttribute("x2", x(i));
    dot.setAttribute("cx", x(i)); dot.setAttribute("cy", y(d[key]));
    cross.setAttribute("visibility", "visible"); dot.setAttribute("visibility", "visible");
    tip.textContent = `${d.ts.slice(11)} · ${d[key]}${unit} · ${d.action}`;
    tip.style.display = "block";
    const left = x(i) * svg.clientWidth / W + 16;
    tip.style.left = Math.min(left, svg.clientWidth - tip.offsetWidth + 16) + "px";
    tip.style.top = "36px";
  });
  svg.addEventListener("pointerleave", () => {
    cross.setAttribute("visibility", "hidden"); dot.setAttribute("visibility", "hidden");
    tip.style.display = "none";
  });
}

lineChart("soil-chart", "soil", "%", 0, 100, 30, "물 주기 기준 30%", "#2a78d6");
lineChart("temp-chart", "temp", "℃", 20, 40, 32, "고온 기준 32℃", "#eb6834");
</script>
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
        chart = [dict(r) for r in reversed(rows)]
        return render_template_string(
            DASHBOARD, rows=rows, chart=chart, counts=counts, total=sum(counts.values())
        )

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=5000)
