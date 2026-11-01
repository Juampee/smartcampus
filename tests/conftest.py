import pytest

from app.db import connect, init_db
from app.main import create_app


@pytest.fixture
def conn(tmp_path):
    connection = connect(str(tmp_path / "unit.db"))
    init_db(connection)
    yield connection
    connection.close()


@pytest.fixture
def app(tmp_path):
    return create_app({"TESTING": True, "DB_PATH": str(tmp_path / "test.db")})


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def room_id(client):
    resp = client.post(
        "/rooms",
        json={
            "nombre": "Aula 101",
            "edificio": "A",
            "capacidad": 30,
            "equipamiento": ["proyector"],
        },
    )
    return resp.get_json()["id"]
