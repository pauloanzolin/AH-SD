#!/bin/sh
set -e

# Garante que o diretório de dados persistentes do SQLite exista e tenha permissões adequadas
mkdir -p /app/data
chmod 777 /app/data 2>/dev/null || true

# Se o banco de dados já existir, garante permissão de leitura/escrita
if [ -f /app/data/ahsd.db ]; then
    chmod 666 /app/data/ahsd.db 2>/dev/null || true
fi

exec "$@"
