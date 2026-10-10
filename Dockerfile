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
    mkdir -p /app/data /app/workspaces && \
    chown -R pidots:pidots /app

# Copia código fonte da aplicação e arquivos estáticos
COPY --chown=pidots:pidots pidots/ /app/pidots/
COPY --chown=pidots:pidots pidots_spa_prototype.html /app/pidots_spa_prototype.html
COPY --chown=pidots:pidots relatorio_estudo_pidots.html /app/relatorio_estudo_pidots.html

USER pidots

EXPOSE 8000

# Healthcheck do container com baixo impacto
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/health || exit 1

# Inicialização com Worker Único e uvloop para preservação de RAM (< 60MB)
CMD ["uvicorn", "pidots.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--loop", "uvloop", "--no-access-log"]
