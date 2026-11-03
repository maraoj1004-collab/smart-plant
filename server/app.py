import sqlite3

from flask import Flask, jsonify, request

FIELDS = ("soil", "temp", "hum", "light", "action")


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

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=5000)
