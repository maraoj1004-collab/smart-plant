from app import create_app

SAMPLE = {"soil": 20, "temp": 25, "hum": 50, "light": 800, "action": "WATER"}


def make_client(tmp_path):
    return create_app(str(tmp_path / "t.db")).test_client()


def test_post_and_get(tmp_path):
    client = make_client(tmp_path)
    r = client.post("/logs", json=SAMPLE)
    assert r.status_code == 201

    logs = client.get("/logs").get_json()
    assert len(logs) == 1
    assert logs[0]["action"] == "WATER"
    assert logs[0]["soil"] == 20


def test_latest_first(tmp_path):
    client = make_client(tmp_path)
    client.post("/logs", json=SAMPLE)
    client.post("/logs", json={**SAMPLE, "action": "NONE"})
    logs = client.get("/logs").get_json()
    assert [l["action"] for l in logs] == ["NONE", "WATER"]


def test_missing_field_rejected(tmp_path):
    client = make_client(tmp_path)
    r = client.post("/logs", json={"soil": 20})
    assert r.status_code == 400
    assert client.get("/logs").get_json() == []


def test_dashboard(tmp_path):
    client = make_client(tmp_path)
    assert "아직 로그가 없습니다" in client.get("/").get_data(as_text=True)

    client.post("/logs", json=SAMPLE)
    r = client.get("/")
    assert r.status_code == 200
    assert "WATER" in r.get_data(as_text=True)
