FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt ./

RUN pip install --no-cache-dir --disable-pip-version-check -r requirements.txt \
    && useradd --create-home --uid 10001 appuser \
    && mkdir -p /data \
    && chown appuser:appuser /data

COPY --chown=appuser:appuser app.py testScript.py ai_manager.py ai_filter.py data_manager.py IO_manager.py logic_manager.py ./

USER 10001:10001
WORKDIR /data

CMD ["python", "/app/app.py"]