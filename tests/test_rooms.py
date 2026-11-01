import pytest

pytestmark = pytest.mark.integration


def test_create_and_get_room(client):
    resp = client.post(
        "/rooms",
        json={"nombre": "Lab 2", "edificio": "B", "capacidad": 25, "equipamiento": ["pcs"]},
    )
    assert resp.status_code == 201
    room = resp.get_json()
    assert room["equipamiento"] == ["pcs"]

    resp = client.get(f"/rooms/{room['id']}")
    assert resp.status_code == 200
    assert resp.get_json()["nombre"] == "Lab 2"


def test_list_rooms(client, room_id):
    resp = client.get("/rooms")
    assert resp.status_code == 200
    assert [r["id"] for r in resp.get_json()] == [room_id]


def test_delete_room(client, room_id):
    assert client.delete(f"/rooms/{room_id}").status_code == 204
    assert client.get(f"/rooms/{room_id}").status_code == 404


@pytest.mark.parametrize("capacidad", [0, -1, "x"])
def test_invalid_capacity_returns_422(client, capacidad):
    resp = client.post("/rooms", json={"nombre": "X", "edificio": "A", "capacidad": capacidad})
    assert resp.status_code == 422


def test_missing_name_returns_422(client):
    resp = client.post("/rooms", json={"edificio": "A", "capacidad": 5})
    assert resp.status_code == 422


def test_invalid_json_returns_400(client):
    resp = client.post("/rooms", data="no-json", content_type="application/json")
    assert resp.status_code == 400


def test_get_missing_room_404(client):
    assert client.get("/rooms/999").status_code == 404


def test_delete_missing_room_404(client):
    assert client.delete("/rooms/999").status_code == 404
