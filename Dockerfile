FROM python:3.11-slim

# Evita geração de bytecode .pyc e bufferiza saída para logs em tempo real
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_URL=sqlite:////app/data/ahsd.db

WORKDIR /app

# Instala dependências do sistema necessárias para healthcheck e utilitários
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependências Python primeiro (aproveita cache de camadas)
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copia a aplicação, os arquivos estáticos e o entrypoint
COPY app /app/app
COPY static /app/static
COPY entrypoint.sh /app/entrypoint.sh

# Garante permissões de execução no entrypoint e cria a pasta de dados persistentes
RUN chmod +x /app/entrypoint.sh && mkdir -p /app/data

EXPOSE 8000

# Executa através do entrypoint para garantir permissões de volume antes de subir o uvicorn
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
