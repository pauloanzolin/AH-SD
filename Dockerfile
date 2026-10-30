FROM python:3.11-slim

# Evita geração de bytecode .pyc e bufferiza saída para logs em tempo real
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_URL=sqlite:////app/data/ahsd.db

WORKDIR /app

# Instala dependências do sistema necessárias para compilação mínima e verificação de saúde
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependências Python primeiro (aproveita cache de camadas)
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copia a aplicação e os arquivos estáticos
COPY app /app/app
COPY static /app/static

# Cria o diretório de dados persistentes do SQLite
RUN mkdir -p /app/data

# Cria usuário não-root por segurança
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Executa o servidor Uvicorn com suporte a ASGI e múltiplos workers se necessário
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
