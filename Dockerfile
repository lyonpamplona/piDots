# ==============================================================================
# piDots Core - Dockerfile Otimizado para Edge / Raspberry Pi 4B (ARM64)
# Imagem base Python slim, sem compilações desnecessárias, com worker único uvloop
# ==============================================================================

FROM python:3.13-slim

# Evita criação de arquivos .pyc e garante logs em tempo real sem buffer
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Instalação de ferramentas essenciais mínimas: bubblewrap (sandbox) e curl (healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    bubblewrap \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia e instala dependências Python enxutas
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Cria usuário não-root para execução segura do container
RUN useradd -u 1000 -m -s /bin/bash pidots && \
    mkdir -p /app/data/locales /app/data/backups /app/workspaces /app/static /app/pages && \
    chown -R pidots:pidots /app

# Copia código fonte da aplicação, páginas modulares, ativos estáticos e dicionários i18n
COPY --chown=pidots:pidots pidots/ /app/pidots/
COPY --chown=pidots:pidots static/ /app/static/
COPY --chown=pidots:pidots pages/ /app/pages/
COPY --chown=pidots:pidots data/locales/ /app/data/locales/
COPY --chown=pidots:pidots data/changelog.json /app/data/changelog.json

USER pidots

EXPOSE 8000

# Healthcheck do container com baixo impacto
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/health || exit 1

# Inicialização com Worker Único e uvloop para preservação de RAM (< 60MB)
CMD ["uvicorn", "pidots.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--loop", "uvloop", "--no-access-log"]
