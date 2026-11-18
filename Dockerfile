FROM python:3.11-slim

# Evita archivos .pyc y asegura que los logs salgan en tiempo real en Cloud Run
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencias del sistema necesarias para PostgreSQL y Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del proyecto
COPY . .

# Cloud Run escucha por defecto en el puerto 8080
ENV PORT=8080
EXPOSE 8080

# Al arrancar: recopila estáticos, aplica migraciones en Neon e inicia Gunicorn
# IMPORTANTE: Sustituye 'TU_PROYECTO' por el nombre de la carpeta que contiene wsgi.py
CMD sh -c "python manage.py collectstatic --noinput && python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120"
