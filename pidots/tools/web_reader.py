"""
Navegador e Extrator Web Semântico em Duas Camadas para o piDots.
Utiliza HTTPX assíncrono com Trafilatura para extração leve em Markdown (< 20MB RAM, sem Chromium).
"""

import httpx
import logging
import trafilatura
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger("pidots.tools.web_reader")

MAX_MARKDOWN_CHARS = 24000  # Teto de caracteres extraídos para proteger memória e tokens


class WebReader:
    """Extrai conteúdo textual limpo de URLs da internet sem sobrecarga de navegador gráfico."""

    @staticmethod
    async def read_url(url: str, timeout_seconds: float = 20.0) -> dict[str, Any]:
        """
        Baixa o HTML via HTTPX assíncrono e extrai o texto principal em Markdown com Trafilatura.
        """
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return {"error": f"URL inválida: '{url}'"}

        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux aarch64; rv:130.0) Gecko/20100101 Firefox/130.0 (piDots/0.1)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        try:
            async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                if response.status_code != 200:
                    return {
                        "url": url,
                        "status_code": response.status_code,
                        "error": f"O servidor retornou HTTP {response.status_code}"
                    }

                html_content = response.text

            # Extração semântica limpa via Trafilatura
            extracted_text = trafilatura.extract(
                html_content,
                include_links=True,
                include_images=False,
                include_tables=True,
                output_format="markdown",
                favor_precision=True
            )

            if not extracted_text:
                # Fallback para extração simplificada se a página tiver pouca estrutura
                extracted_text = trafilatura.baseline(html_content) or "Não foi possível extrair texto legível desta página."

            # Trunca para limite seguro
            truncated = len(extracted_text) > MAX_MARKDOWN_CHARS
            final_text = extracted_text[:MAX_MARKDOWN_CHARS]

            # Metadados da página
            metadata = trafilatura.extract_metadata(html_content)
            title = metadata.title if metadata and metadata.title else parsed.netloc

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
