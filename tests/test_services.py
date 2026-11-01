import pytest

from app import services
from app.services import ConflictError, NotFoundError, ValidationError

pytestmark = pytest.mark.unit


def make_room(conn, capacidad=30):
    return services.create_room(conn, "Aula 1", "A", capacidad, ["proyector"])


def book(conn, room, inicio, fin, fecha="2026-11-10"):
    return services.create_booking(conn, room.id, "ana", fecha, inicio, fin)


def test_create_and_get_room(conn):
    room = make_room(conn)
    assert room.id == 1
    assert room.equipamiento == ["proyector"]
    assert services.get_room(conn, room.id).nombre == "Aula 1"


def test_delete_room(conn):
    room = make_room(conn)
    services.delete_room(conn, room.id)
    assert services.list_rooms(conn) == []


def test_delete_missing_room_raises(conn):
    with pytest.raises(NotFoundError):
        services.delete_room(conn, 99)


@pytest.mark.parametrize("capacidad", [0, -5, "10", None, True, 3.5])
def test_invalid_capacity(conn, capacidad):
    with pytest.raises(ValidationError):
        services.create_room(conn, "Aula", "A", capacidad)


def test_valid_capacity():
    assert services.validate_capacity(1) == 1


def test_invalid_equipment(conn):
    with pytest.raises(ValidationError):
        services.create_room(conn, "Aula", "A", 10, "proyector")


@pytest.mark.parametrize("inicio,fin", [("12:00", "10:00"), ("10:00", "10:00")])
def test_invalid_time_range(inicio, fin):
    with pytest.raises(ValidationError):
        services.validate_time_range(inicio, fin)


@pytest.mark.parametrize("value", ["25:00", "abc", "9", None])
def test_invalid_time_format(value):
    with pytest.raises(ValidationError):
        services.parse_time(value)


def test_time_normalization():
    assert services.validate_time_range("9:00", "10:30") == ("09:00", "10:30")


def test_overlaps_function():
    assert services.overlaps("10:00", "12:00", "11:00", "13:00")
    assert services.overlaps("10:00", "12:00", "10:30", "11:00")  # contenida
    assert not services.overlaps("10:00", "12:00", "12:00", "13:00")  # contigua
    assert not services.overlaps("12:00", "13:00", "10:00", "12:00")  # contigua inversa
    assert not services.overlaps("08:00", "09:00", "10:00", "11:00")


def test_create_booking(conn):
    room = make_room(conn)
    booking = book(conn, room, "10:00", "12:00")
    assert booking.aula_id == room.id
    assert (booking.hora_inicio, booking.hora_fin) == ("10:00", "12:00")


def test_booking_unknown_room(conn):
    with pytest.raises(NotFoundError):
        services.create_booking(conn, 42, "ana", "2026-11-10", "10:00", "11:00")


def test_overlapping_booking_conflicts(conn):
    room = make_room(conn)
    book(conn, room, "10:00", "12:00")
    with pytest.raises(ConflictError):
        book(conn, room, "11:00", "13:00")


def test_contiguous_booking_allowed(conn):
    room = make_room(conn)
    book(conn, room, "10:00", "12:00")
    assert book(conn, room, "12:00", "13:00").id == 2


def test_same_time_other_date_or_room_allowed(conn):
    room = make_room(conn)
    other = services.create_room(conn, "Aula 2", "A", 20)
    book(conn, room, "10:00", "12:00")
    book(conn, room, "10:00", "12:00", fecha="2026-11-11")
    book(conn, other, "10:00", "12:00")
    assert len(services.list_bookings(conn)) == 3


def test_delete_booking_and_missing(conn):
    room = make_room(conn)
    booking = book(conn, room, "10:00", "12:00")
    services.delete_booking(conn, booking.id)
    with pytest.raises(NotFoundError):
        services.delete_booking(conn, booking.id)


def test_deleting_room_removes_its_bookings(conn):
    room = make_room(conn)
    book(conn, room, "10:00", "12:00")
    services.delete_room(conn, room.id)
    assert services.list_bookings(conn) == []
