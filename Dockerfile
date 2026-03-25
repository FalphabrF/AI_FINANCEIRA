# ============================================================

# DOCKERFILE - IMAGEM BASE DO SISTEMA

# ============================================================

# OBJETIVO:

# - Criar ambiente leve e estável

# - Garantir segurança (non-root)

# - Otimizar build e execução

#

# BOAS PRÁTICAS:

# - Uso de python:slim

# - Cache de dependências

# - Separação de camadas

# - Usuário não-root

# ============================================================

# ============================================================

# BASE

# ============================================================

FROM python:3.11-slim

# Evita geração de arquivos .pyc e buffer de logs

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Diretório de trabalho

WORKDIR /app

# ============================================================

# DEPENDÊNCIAS DO SISTEMA

# ============================================================

# Instala libs necessárias para pandas, psycopg2, etc

RUN apt-get update && apt-get install -y  build-essential gcc libpq-dev curl && rm -rf /var/lib/apt/lists/*

# ============================================================

# INSTALAÇÃO DE DEPENDÊNCIAS PYTHON

# ============================================================

# Copia apenas requirements primeiro (cache eficiente)

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# ============================================================

# COPIA DO PROJETO

# ============================================================

COPY . .

# ============================================================

# DIRETÓRIOS NECESSÁRIOS

# ============================================================

RUN mkdir -p /app/data && mkdir -p /app/logs

# ============================================================

# USUÁRIO NÃO-ROOT (SEGURANÇA)

# ============================================================

RUN adduser --disabled-password --gecos "" appuser && chown -R appuser:appuser /app

USER appuser

# ============================================================

# HEALTHCHECK (VALIDAÇÃO DO CONTAINER)

# ============================================================

HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# ============================================================

# COMANDO PADRÃO

# ============================================================

# Pode ser sobrescrito pelo docker-compose

CMD ["python", "main.py"]
