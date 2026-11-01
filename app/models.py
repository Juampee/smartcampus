"""Modelos de dominio."""

import json
from dataclasses import asdict, dataclass, field


@dataclass
class Room:
    id: int
    nombre: str
    edificio: str
    capacidad: int
    equipamiento: list = field(default_factory=list)

    @classmethod
    def from_row(cls, row) -> "Room":
        return cls(
            id=row["id"],
            nombre=row["nombre"],
            edificio=row["edificio"],
            capacidad=row["capacidad"],
            equipamiento=json.loads(row["equipamiento"]),
        )

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Booking:
    id: int
    aula_id: int
    usuario: str
    fecha: str
    hora_inicio: str
    hora_fin: str

    @classmethod
    def from_row(cls, row) -> "Booking":
        return cls(**{k: row[k] for k in row.keys()})

    def to_dict(self) -> dict:
        return asdict(self)
