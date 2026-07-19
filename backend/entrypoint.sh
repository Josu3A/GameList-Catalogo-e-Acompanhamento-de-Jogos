#!/bin/sh
# Entrypoint do backend: espera o banco, aplica migrations, popula o seed de
# demonstração (idempotente) e sobe o servidor de desenvolvimento do Django.
set -e

echo "Aguardando o PostgreSQL em ${DB_HOST}:${DB_PORT}..."
python <<'PY'
import os
import time
import sys

import psycopg

dsn = (
    f"host={os.environ['DB_HOST']} "
    f"port={os.environ.get('DB_PORT', '5432')} "
    f"dbname={os.environ['DB_NAME']} "
    f"user={os.environ['DB_USER']} "
    f"password={os.environ.get('DB_PASSWORD', '')}"
)
for _ in range(60):
    try:
        psycopg.connect(dsn).close()
        print("Banco disponível.")
        break
    except Exception as exc:  # noqa: BLE001
        print(f"  ...ainda indisponível ({exc}); nova tentativa em 2s")
        time.sleep(2)
else:
    sys.exit("Não foi possível conectar ao PostgreSQL.")
PY

echo "Aplicando migrations..."
python manage.py migrate --noinput

echo "Populando dados de demonstração (seed_demo)..."
python manage.py seed_demo

echo "Subindo o servidor Django em 0.0.0.0:8000..."
exec python manage.py runserver 0.0.0.0:8000
