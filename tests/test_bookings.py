import pytest

pytestmark = pytest.mark.integration


def payload(aula_id, inicio="10:00", fin="12:00", fecha="2026-11-10"):
    return {
        "aula_id": aula_id,
        "usuario": "ana",
        "fecha": fecha,
        "hora_inicio": inicio,
        "hora_fin": fin,
    }


def test_create_and_list_booking(client, room_id):
    resp = client.post("/bookings", json=payload(room_id))
    assert resp.status_code == 201
    assert resp.get_json()["aula_id"] == room_id

    resp = client.get("/bookings")
    assert resp.status_code == 200
    assert len(resp.get_json()) == 1


def test_delete_booking(client, room_id):
    booking_id = client.post("/bookings", json=payload(room_id)).get_json()["id"]
    assert client.delete(f"/bookings/{booking_id}").status_code == 204
    assert client.get("/bookings").get_json() == []


def test_booking_unknown_room_404(client):
    assert client.post("/bookings", json=payload(999)).status_code == 404


def test_overlapping_booking_409(client, room_id):
    client.post("/bookings", json=payload(room_id, "10:00", "12:00"))
    resp = client.post("/bookings", json=payload(room_id, "11:00", "13:00"))
    assert resp.status_code == 409


def test_contiguous_booking_201(client, room_id):
    client.post("/bookings", json=payload(room_id, "10:00", "12:00"))
    resp = client.post("/bookings", json=payload(room_id, "12:00", "13:00"))
    assert resp.status_code == 201


@pytest.mark.parametrize("inicio,fin", [("12:00", "10:00"), ("10:00", "10:00"), ("xx", "11:00")])
def test_wrong_hours_422(client, room_id, inicio, fin):
    assert client.post("/bookings", json=payload(room_id, inicio, fin)).status_code == 422


def test_wrong_date_422(client, room_id):
    assert client.post("/bookings", json=payload(room_id, fecha="10/11/2026")).status_code == 422


def test_delete_missing_booking_404(client):
    assert client.delete("/bookings/999").status_code == 404
