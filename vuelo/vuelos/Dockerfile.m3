FROM python:3.11-slim

WORKDIR /app

RUN mkdir -p /data

COPY m3_base_datos.py .

VOLUME ["/data"]

CMD ["python", "-u", "m3_base_datos.py"]
