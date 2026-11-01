"""Logica de negocio, independiente de HTTP (testeable con una conexion SQLite)."""

import json
from datetime import datetime

from app.models import Booking, Room


class ServiceError(Exception):
    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ValidationError(ServiceError):
    status_code = 422


class NotFoundError(ServiceError):
    status_code = 404


class ConflictError(ServiceError):
    status_code = 409


# ---------- validaciones ----------


def validate_capacity(capacidad) -> int:
    if isinstance(capacidad, bool) or not isinstance(capacidad, int):
        raise ValidationError("La capacidad debe ser un entero")
    if capacidad <= 0:
        raise ValidationError("La capacidad debe ser mayor que 0")
    return capacidad


def _require_text(value, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"'{name}' es obligatorio")
    return value.strip()


def parse_time(value, name: str = "hora") -> str:
    """Devuelve la hora normalizada HH:MM o lanza ValidationError."""
    try:
        return datetime.strptime(value, "%H:%M").strftime("%H:%M")
    except (TypeError, ValueError):
        raise ValidationError(f"'{name}' debe tener formato HH:MM") from None


def parse_date(value) -> str:
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        raise ValidationError("'fecha' debe tener formato YYYY-MM-DD") from None


def validate_time_range(hora_inicio, hora_fin) -> tuple[str, str]:
    inicio = parse_time(hora_inicio, "hora_inicio")
    fin = parse_time(hora_fin, "hora_fin")
    if inicio >= fin:
        raise ValidationError("hora_inicio debe ser anterior a hora_fin")
    return inicio, fin


def overlaps(inicio_a: str, fin_a: str, inicio_b: str, fin_b: str) -> bool:
    """Dos franjas solapan si inicio_A < fin_B y inicio_B < fin_A (contiguas no solapan)."""
    return inicio_a < fin_b and inicio_b < fin_a


# ---------- aulas ----------


def create_room(conn, nombre, edificio, capacidad, equipamiento=None) -> Room:
    nombre = _require_text(nombre, "nombre")
    edificio = _require_text(edificio, "edificio")
    capacidad = validate_capacity(capacidad)
    equipamiento = [] if equipamiento is None else equipamiento
    if not isinstance(equipamiento, list) or not all(isinstance(e, str) for e in equipamiento):
        raise ValidationError("'equipamiento' debe ser una lista de textos")
    cur = conn.execute(
        "INSERT INTO rooms (nombre, edificio, capacidad, equipamiento) VALUES (?, ?, ?, ?)",
        (nombre, edificio, capacidad, json.dumps(equipamiento)),
    )
    conn.commit()
    return get_room(conn, cur.lastrowid)


def list_rooms(conn) -> list[Room]:
    rows = conn.execute("SELECT * FROM rooms ORDER BY id").fetchall()
    return [Room.from_row(r) for r in rows]


def get_room(conn, room_id: int) -> Room:
    row = conn.execute("SELECT * FROM rooms WHERE id = ?", (room_id,)).fetchone()
    if row is None:
        raise NotFoundError(f"Aula {room_id} no encontrada")
    return Room.from_row(row)


def delete_room(conn, room_id: int) -> None:
    get_room(conn, room_id)
    conn.execute("DELETE FROM rooms WHERE id = ?", (room_id,))
    conn.commit()


# ---------- reservas ----------


def create_booking(conn, aula_id, usuario, fecha, hora_inicio, hora_fin) -> Booking:
    usuario = _require_text(usuario, "usuario")
    fecha = parse_date(fecha)
    inicio, fin = validate_time_range(hora_inicio, hora_fin)
    if isinstance(aula_id, bool) or not isinstance(aula_id, int):
        raise ValidationError("'aula_id' debe ser un entero")
    get_room(conn, aula_id)  # 404 si no existe

    existing = conn.execute(
        "SELECT hora_inicio, hora_fin FROM bookings WHERE aula_id = ? AND fecha = ?",
        (aula_id, fecha),
    ).fetchall()
    for row in existing:
        if overlaps(inicio, fin, row["hora_inicio"], row["hora_fin"]):
            raise ConflictError(
                f"El aula {aula_id} ya esta reservada entre "
                f"{row['hora_inicio']} y {row['hora_fin']} el {fecha}"
            )

    cur = conn.execute(
        "INSERT INTO bookings (aula_id, usuario, fecha, hora_inicio, hora_fin) "
        "VALUES (?, ?, ?, ?, ?)",
        (aula_id, usuario, fecha, inicio, fin),
    )
    conn.commit()
    return get_booking(conn, cur.lastrowid)


def list_bookings(conn) -> list[Booking]:
    rows = conn.execute("SELECT * FROM bookings ORDER BY fecha, hora_inicio, id").fetchall()
    return [Booking.from_row(r) for r in rows]


def get_booking(conn, booking_id: int) -> Booking:
    row = conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
    if row is None:
        raise NotFoundError(f"Reserva {booking_id} no encontrada")
    return Booking.from_row(row)


def delete_booking(conn, booking_id: int) -> None:
    get_booking(conn, booking_id)
    conn.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
    conn.commit()
