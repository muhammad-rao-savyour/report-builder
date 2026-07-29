"""The feature test: one user story, start to finish."""
import csv
import io

import httpx


def _csv_bytes(rows: int) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["name", "qty"])
    for i in range(rows):
        writer.writerow([f"row{i}", i])
    return buf.getvalue().encode()


def test_upload_a_csv_and_get_a_row_count(client):
    rows = 5000
    data = _csv_bytes(rows)

    # 1. ask for permission
    started = client.post("/uploads", json={"filename": "feature.csv"})
    assert started.status_code == 201
    body = started.json()

    # 2. send the bytes straight to storage, exactly like a browser would
    put = httpx.put(body["upload_url"], content=data, timeout=60)
    assert put.status_code == 200

    # 3. queue the job
    assert client.post(f"/uploads/{body['upload_id']}/complete").status_code == 200

    # 4. the worker did its job against the real file in real storage
    result = client.get(f"/uploads/{body['upload_id']}").json()
    assert result["status"] == "done"
    assert result["row_count"] == rows
    assert result["error"] == ""


def test_completing_without_uploading_is_rejected(client):
    body = client.post("/uploads", json={"filename": "ghost.csv"}).json()
    assert client.post(f"/uploads/{body['upload_id']}/complete").status_code == 409
