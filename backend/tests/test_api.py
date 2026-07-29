def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_create_and_read_item(client):
    created = client.post("/items", json={"name": "first", "description": "hello"})
    assert created.status_code == 201
    item_id = created.json()["id"]

    fetched = client.get(f"/items/{item_id}")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "first"


def test_list_is_paginated(client):
    for n in range(3):
        client.post("/items", json={"name": f"item-{n}"})
    assert len(client.get("/items?limit=2").json()) == 2


def test_delete_item(client):
    item_id = client.post("/items", json={"name": "gone"}).json()["id"]
    assert client.delete(f"/items/{item_id}").status_code == 204
    assert client.get(f"/items/{item_id}").status_code == 404


def test_missing_item_is_404(client):
    assert client.get("/items/does-not-exist").status_code == 404


def test_complete_rejects_missing_file(client, monkeypatch):
    """If the browser never actually uploaded, say so immediately."""
    import app.main as main

    monkeypatch.setattr(main, "presigned_put_url", lambda key, **kw: "http://fake/url")
    monkeypatch.setattr(main, "object_exists", lambda key: False)

    upload_id = client.post("/uploads", json={"filename": "ghost.csv"}).json()["upload_id"]
    resp = client.post(f"/uploads/{upload_id}/complete")

    assert resp.status_code == 409
    assert client.get(f"/uploads/{upload_id}").json()["status"] == "failed"
