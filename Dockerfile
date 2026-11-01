FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    HOST=0.0.0.0 \
    PORT=5000 \
    DB_PATH=/data/smartcampus.db \
    GUNICORN_WORKERS=2

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Usuario no root; /data es donde vive SQLite (se monta como volumen)
RUN useradd --system --uid 1001 --no-create-home appuser \
    && mkdir -p /data && chown appuser /data
USER appuser

EXPOSE 5000
VOLUME ["/data"]

HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import os,urllib.request as u; u.urlopen('http://127.0.0.1:%s/health' % os.environ['PORT'], timeout=2)" || exit 1

CMD ["sh", "-c", "exec gunicorn --bind ${HOST}:${PORT} --workers ${GUNICORN_WORKERS} --access-logfile - 'app.main:create_app()'"]
