#!/usr/bin/env bash
# ==============================================================================
# piDots Edge Core — Script Auxiliar de Configuracao do Cloudflare Tunnel
# Arquitetura de Desacoplamento por Portas no Raspberry Pi 4B (ARM64 / x86_64)
# ==============================================================================
# Este script guia o operador na instalacao e configuracao do daemon cloudflared
# para roteamento seguro sem abertura de portas no firewall ou NAT residencial.
# ==============================================================================

set -euo pipefail

echo "========================================================================"
echo " piDots — Assistente de Configuracao do Cloudflare Tunnel"
echo "========================================================================"

# 1. Deteccao Dinamica de Arquitetura
ARCH=$(uname -m)
PKG_ARCH="arm64"
if [ "$ARCH" = "x86_64" ] || [ "$ARCH" = "amd64" ]; then
    PKG_ARCH="amd64"
    echo "[INFO] Arquitetura detectada: x86_64 / amd64."
elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
    PKG_ARCH="arm64"
    echo "[INFO] Arquitetura detectada: ARM64 (Raspberry Pi 4B)."
else
    echo "[ERRO] Arquitetura nao suportada automaticamente ($ARCH). Instale o cloudflared manualmente."
    exit 1
fi

# 2. Verificacao da instalacao do cloudflared
if ! command -v cloudflared &> /dev/null; then
    echo "[PASSO 1] cloudflared nao encontrado. Baixando pacote oficial ($PKG_ARCH)..."
    curl -L --output /tmp/cloudflared.deb "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${PKG_ARCH}.deb"
    sudo dpkg -i /tmp/cloudflared.deb
    rm -f /tmp/cloudflared.deb
    echo "[OK] cloudflared instalado com sucesso."
else
    echo "[OK] cloudflared ja esta instalado: $(cloudflared --version)"
fi

# 3. Instrucoes de Autenticacao
echo ""
echo "[PASSO 2] Autenticacao na conta Cloudflare:"
echo "Execute o comando abaixo e faca login no navegador para vincular sua zona DNS:"
echo "  cloudflared tunnel login"
echo ""

# 4. Criacao do Tunel
echo "[PASSO 3] Criacao do Tunel Dedicado piDots:"
echo "Execute o comando para criar o tunel e anote o UUID gerado:"
echo "  cloudflared tunnel create pidots-edge"
echo ""

# 5. Mapeamento DNS
echo "[PASSO 4] Roteamento de Subdominios DNS na Cloudflare:"
echo "Execute os comandos substituindo 'seudominio.com':"
echo "  cloudflared tunnel route dns pidots-edge pidots.seudominio.com"
echo "  cloudflared tunnel route dns pidots-edge app.seudominio.com"
echo "  cloudflared tunnel route dns pidots-edge docs.seudominio.com"
echo ""

# 6. Copia das Credenciais e Ajuste do Arquivo de Configuracao
echo "[PASSO 5] Instalacao da Configuracao e Credenciais do Tunel:"
echo "  sudo mkdir -p /etc/cloudflared"
echo "  sudo cp ~/.cloudflared/*.json /etc/cloudflared/"
echo "  sudo cp cloudflared/config.yml.example /etc/cloudflared/config.yml"
echo "Substitua o UUID no arquivo /etc/cloudflared/config.yml e o nome do seu dominio."
echo ""

# 7. Instalacao e Ativacao do Servico Systemd
echo "[PASSO 6] Ativacao do Servico em Segundo Plano (Systemd 24/7):"
echo "  sudo cloudflared service install"
echo "  sudo systemctl enable --now cloudflared"
echo "  sudo systemctl status cloudflared"
echo ""
echo "========================================================================"
echo " Apos a ativacao, o piDots estara acessivel globalmente via HTTPS seguro!"
echo "========================================================================"
