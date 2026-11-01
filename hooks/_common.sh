#!/bin/sh
# Utilidades compartidas por los hooks. Localiza el interprete de Python del proyecto.
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT" || exit 1

find_python() {
    for candidate in \
        "$ROOT/.venv/Scripts/python.exe" "$ROOT/.venv/bin/python" \
        "$HOME/.venvs/smartcampus/Scripts/python.exe" "$HOME/.venvs/smartcampus/bin/python"; do
        if [ -x "$candidate" ]; then echo "$candidate"; return; fi
    done
    for name in python3 python; do
        if command -v "$name" >/dev/null 2>&1; then command -v "$name"; return; fi
    done
}

PY="${PYTHON:-$(find_python)}"
if [ -z "$PY" ]; then
    echo "❌ No se encontro Python. Define la variable PYTHON o crea el entorno virtual."
    exit 1
fi
