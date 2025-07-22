# Use Python 3.11 oficial
FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Criar usuário não-root para segurança
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Criar estrutura de diretórios necessária
RUN mkdir -p /app/src/database && \
    mkdir -p /app/database && \
    mkdir -p /app/logs

# Definir permissões corretas
RUN chown -R appuser:appuser /app
USER appuser

# Expor porta 5000
EXPOSE 5000

# Variáveis de ambiente
ENV FLASK_APP=app.py
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Script de inicialização
COPY docker-entrypoint.sh /
USER root
RUN chmod +x /docker-entrypoint.sh
USER appuser

# Comando de inicialização
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["python", "app.py"]