FROM python:3.11-slim

WORKDIR /app

COPY m2_simulador.py .

CMD ["python", "-u", "m2_simulador.py"]
