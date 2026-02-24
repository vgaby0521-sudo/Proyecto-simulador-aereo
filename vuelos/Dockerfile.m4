FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir flask flask-socketio

COPY m4_mapa.py .
COPY templates/ templates/

EXPOSE 5000

CMD ["python", "-u", "m4_mapa.py"]
