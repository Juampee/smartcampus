"""Configuracion leida de variables de entorno (nada hardcodeado)."""

import os


def load_config() -> dict:
    return {
        "APP_ENV": os.environ.get("APP_ENV", "development"),
        "HOST": os.environ.get("HOST", "0.0.0.0"),
        "PORT": int(os.environ.get("PORT", "5000")),
        "DB_PATH": os.environ.get("DB_PATH", "./data/smartcampus.db"),
        "LOG_LEVEL": os.environ.get("LOG_LEVEL", "INFO"),
        "SECRET_KEY": os.environ.get("SECRET_KEY", "dev-only-secret"),
    }
