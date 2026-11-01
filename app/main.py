"""Aplicacion Flask (patron app factory)."""

import logging

from flask import Flask, jsonify, request

from app import services
from app.config import load_config
from app.db import close_db, connect, get_db, init_db


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(load_config())
    if test_config:
        app.config.update(test_config)
    logging.basicConfig(level=app.config["LOG_LEVEL"])

    with connect(app.config["DB_PATH"]) as conn:
        init_db(conn)
    app.teardown_appcontext(close_db)

    @app.errorhandler(services.ServiceError)
    def handle_service_error(err):
        return jsonify(error=err.message), err.status_code

    @app.errorhandler(404)
    def handle_404(_err):
        return jsonify(error="Recurso no encontrado"), 404

    @app.errorhandler(405)
    def handle_405(_err):
        return jsonify(error="Metodo no permitido"), 405

    def json_body() -> dict:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise services.ServiceError("El cuerpo debe ser un objeto JSON valido")
        return data

    @app.get("/health")
    def health():
        return jsonify(status="ok", env=app.config["APP_ENV"])

    @app.get("/rooms")
    def list_rooms():
        return jsonify([r.to_dict() for r in services.list_rooms(get_db())])

    @app.post("/rooms")
    def create_room():
        data = json_body()
        room = services.create_room(
            get_db(),
            data.get("nombre"),
            data.get("edificio"),
            data.get("capacidad"),
            data.get("equipamiento"),
        )
        return jsonify(room.to_dict()), 201

    @app.get("/rooms/<int:room_id>")
    def get_room(room_id):
        return jsonify(services.get_room(get_db(), room_id).to_dict())

    @app.delete("/rooms/<int:room_id>")
    def delete_room(room_id):
        services.delete_room(get_db(), room_id)
        return "", 204

    @app.get("/bookings")
    def list_bookings():
        return jsonify([b.to_dict() for b in services.list_bookings(get_db())])

    @app.post("/bookings")
    def create_booking():
        data = json_body()
        booking = services.create_booking(
            get_db(),
            data.get("aula_id"),
            data.get("usuario"),
            data.get("fecha"),
            data.get("hora_inicio"),
            data.get("hora_fin"),
        )
        return jsonify(booking.to_dict()), 201

    @app.delete("/bookings/<int:booking_id>")
    def delete_booking(booking_id):
        services.delete_booking(get_db(), booking_id)
        return "", 204

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(host=application.config["HOST"], port=application.config["PORT"])
