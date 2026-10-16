"""
Navegador e Extrator Web Semântico em Duas Camadas para o piDots.
Utiliza HTTPX assíncrono com Trafilatura para extração leve em Markdown (< 20MB RAM, sem Chromium).
"""

import asyncio
import socket
import ipaddress
import httpx
import logging
import trafilatura
from typing import Any
from urllib.parse import urlparse, urljoin

logger = logging.getLogger("pidots.tools.web_reader")

MAX_MARKDOWN_CHARS = 24000  # Teto de caracteres extraídos para proteger memória e tokens
MAX_DOWNLOAD_BYTES = 5 * 1024 * 1024  # Limite de 5MB de download para proteger a RAM do Raspberry Pi


def _is_safe_host(hostname: str) -> tuple[bool, str]:
    """Valida se o hostname não resolve para rede privada, loopback ou link-local (prevenção SSRF)."""
    try:
        addr_infos = socket.getaddrinfo(hostname, None)
        for _, _, _, _, sockaddr in addr_infos:
            ip_str = sockaddr[0]
            ip = ipaddress.ip_address(ip_str)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                return False, f"Acesso bloqueado por segurança: endereço IP de rede interna/loopback ({ip_str})."
        return True, ""
    except Exception as err:
        return False, f"Falha na resolução de DNS para '{hostname}': {str(err)}"


class WebReader:
    """Extrai conteúdo textual limpo de URLs da internet sem sobrecarga de navegador gráfico."""

    @staticmethod
    def _extract_sync(html_content: str, netloc: str) -> tuple[str, str]:
        """Executa o parsing CPU-bound do Trafilatura fora do loop de eventos principal."""
        extracted_text = trafilatura.extract(
            html_content,
            include_links=True,
            include_images=False,
            include_tables=True,
            output_format="markdown",
            favor_precision=True
        )
        if not extracted_text:
            extracted_text = trafilatura.baseline(html_content) or "Não foi possível extrair texto legível desta página."

        metadata = trafilatura.extract_metadata(html_content)
        title = metadata.title if metadata and metadata.title else netloc
        return extracted_text, title

    @classmethod
    async def read_url(cls, url: str, timeout_seconds: float = 20.0) -> dict[str, Any]:
        """
        Baixa o HTML via HTTPX assíncrono e extrai o texto principal em Markdown com Trafilatura.
        Aplica verificação anti-SSRF e limite estrito de download.
        """
        parsed = urlparse(url)
        if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
            return {"error": f"URL inválida ou esquema não suportado: '{url}'"}

        hostname = parsed.hostname or ""
        if not hostname:
            return {"error": f"Hostname ausente na URL: '{url}'"}

        # Verificação rigorosa anti-SSRF fora da thread de eventos
        is_safe, ssrf_err = await asyncio.to_thread(_is_safe_host, hostname)
        if not is_safe:
            return {"url": url, "error": ssrf_err}

        current_url = url
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux aarch64; rv:130.0) Gecko/20100101 Firefox/130.0 (piDots/1.5)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        try:
            html_content = ""
            async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=False) as client:
                max_hops = 5
                for _ in range(max_hops):
                    # Validação anti-SSRF para a URL atual (hop inicial ou redirecionado)
                    curr_parsed = urlparse(current_url)
                    if curr_parsed.scheme.lower() not in ("http", "https") or not curr_parsed.netloc:
                        return {"url": current_url, "error": f"URL inválida ou esquema não suportado: '{current_url}'"}
                    curr_host = curr_parsed.hostname or ""
                    if not curr_host:
                        return {"url": current_url, "error": f"Hostname ausente na URL: '{current_url}'"}

                    is_safe, ssrf_err = await asyncio.to_thread(_is_safe_host, curr_host)
                    if not is_safe:
                        return {"url": current_url, "error": f"Redirecionamento bloqueado por segurança: {ssrf_err}"}

                    async with client.stream("GET", current_url, headers=headers) as response:
                        if response.status_code in (301, 302, 303, 307, 308):
                            location = response.headers.get("location")
                            if not location:
                                return {"url": current_url, "error": f"Redirecionamento HTTP {response.status_code} sem cabeçalho Location."}
                            current_url = urljoin(current_url, location)
                            continue

                        if response.status_code != 200:
                            return {
                                "url": current_url,
                                "status_code": response.status_code,
                                "error": f"O servidor retornou HTTP {response.status_code}"
                            }

                        # Verifica Content-Length se informado pelo cabeçalho
                        cl = response.headers.get("content-length")
                        if cl and cl.isdigit() and int(cl) > MAX_DOWNLOAD_BYTES:
                            return {
                                "url": current_url,
                                "error": f"Tamanho do conteúdo excede o limite permitido de {MAX_DOWNLOAD_BYTES // (1024*1024)}MB."
                            }

                        chunks: list[bytes] = []
                        total_bytes = 0
                        async for chunk in response.aiter_bytes():
                            total_bytes += len(chunk)
                            if total_bytes > MAX_DOWNLOAD_BYTES:
                                return {
                                    "url": current_url,
                                    "error": f"Download interrompido: excedeu o limite máximo de {MAX_DOWNLOAD_BYTES // (1024*1024)}MB."
                                }
                            chunks.append(chunk)

                        raw_bytes = b"".join(chunks)
                        html_content = raw_bytes.decode(response.encoding or "utf-8", errors="replace")
                        break
                else:
                    return {"url": url, "error": "Número excessivo de redirecionamentos HTTP (> 5 hops)."}

            # Extração semântica limpa via Trafilatura em thread worker para não bloquear o uvloop
            extracted_text, title = await asyncio.to_thread(cls._extract_sync, html_content, parsed.netloc)

            # Trunca para limite seguro
            truncated = len(extracted_text) > MAX_MARKDOWN_CHARS
            final_text = extracted_text[:MAX_MARKDOWN_CHARS]

            return {
                "url": url,
                "title": title,
                "status": "success",
                "character_count": len(final_text),
                "is_truncated": truncated,
                "content_markdown": final_text
            }

        except httpx.ConnectError:
            return {"url": url, "error": "Falha de conexão com o servidor de destino."}
        except httpx.TimeoutException:
            return {"url": url, "error": f"Timeout de conexão excedido ({timeout_seconds}s)."}
        except Exception as e:
            logger.error("Erro ao ler URL %s: %s", url, str(e), exc_info=True)
            return {"url": url, "error": f"Exceção durante a leitura da página: {str(e)}"}
