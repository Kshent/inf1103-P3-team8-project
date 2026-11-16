FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

COPY requirements.txt ./

RUN pip install --no-cache-dir --disable-pip-version-check -r requirements.txt

COPY app.py gui_app.py ./
COPY ai_managerpart2 ./ai_managerpart2
COPY io_manager_part2 ./io_manager_part2
COPY logic_manager_part2 ./logic_manager_part2
COPY data_managerpart2 ./data_managerpart2
COPY gui ./gui
COPY emails ./emails
COPY tests ./tests

WORKDIR /data

# Used only by the web version (gui_app.py).
EXPOSE 8080

CMD ["python", "/app/app.py"]
