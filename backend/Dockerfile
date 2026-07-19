# Backend GameList — Django 5.2 + DRF
# Wheels binários (psycopg[binary], Pillow) já trazem libpq/libjpeg, então
# não é preciso instalar pacotes de sistema (imagem enxuta).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependências primeiro (aproveita o cache de camadas do Docker).
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Código da aplicação.
COPY . .

# O entrypoint espera o Postgres, aplica migrations, popula o seed e sobe o servidor.
EXPOSE 8000
ENTRYPOINT ["sh", "/app/entrypoint.sh"]
