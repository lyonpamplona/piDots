/**
 * piDots Cross-Surface Router — Roteador Inteligente de Superficies de Produto
 * ==============================================================================
 * Gerencia a navegacao canonica e cruzada entre as diferentes superficies do piDots:
 * 1. Overview / Apresentacao (Landing Page)
 * 2. Workspace / Console Operacional (App SPA / PWA)
 * 3. Docs / Manual Operacional (Guia Didatico e Estudos)
 * 4. Relatorio de Engenharia Reversa
 * 5. Swagger / Contratos OpenAPI (/api/docs)
 *
 * Detecta dinamicamente a topologia de acesso:
 * - Modo Portas Desacopladas (Localhost ou LAN: :8081, :8082, :8083, :8088, :8000)
 * - Modo Cloudflare Tunnel / Subdominios (app.dominio.com, docs.dominio.com, pidots.dominio.com)
 * - Modo Gateway Unificado Path-Based (/, /app, /docs, /relatorio)
 *
 * Tambem gerencia os acordes universais de teclado:
 * - 'g' seguido de 'h' -> Ir para Overview (Home)
 * - 'g' seguido de 'w' -> Ir para Workspace
 * - 'g' seguido de 'd' -> Ir para Documentacao
 * ==============================================================================
 */

(function () {
    "use strict";

    // Mapeamento de portas locais padrao do ecossistema piDots
    var PORT_MAP = {
        LANDING: "8081",
        WORKSPACE: "8082",
        DOCS: "8083",
        GATEWAY: "8088",
        CORE_API: "8000"
    };

    /**
     * Inspeciona o ambiente de execucao e retorna o contexto de rede
     */
    function detectTopology() {
        var loc = window.location;
        var port = loc.port || "";
        var hostname = loc.hostname || "localhost";
        var protocol = loc.protocol || "http:";

        // 1. Verificacao de Modo Portas Desacopladas (8081, 8082, 8083)
        if (port === PORT_MAP.LANDING || port === PORT_MAP.WORKSPACE || port === PORT_MAP.DOCS) {
            return {
                mode: "decoupled-ports",
                port: port,
                hostname: hostname,
                protocol: protocol
            };
        }

        // 2. Verificacao de Subdominios Cloudflare ou Dominios Corporativos
        // Padrões como: app.meudominio.com, docs.meudominio.com, pidots.meudominio.com
        var hostParts = hostname.split(".");
        if (hostParts.length >= 3) {
            var sub = hostParts[0].toLowerCase();
            if (sub === "app" || sub === "docs" || sub === "pidots" || sub === "console" || sub === "guide") {
                var baseDomain = hostParts.slice(1).join(".");
                return {
                    mode: "subdomains",
                    subdomain: sub,
                    baseDomain: baseDomain,
                    hostname: hostname,
                    protocol: protocol,
                    port: port
                };
            }
        }

        // 3. Modo Gateway Unificado Path-Based (Porta 8088, 8000, 80, 443 ou IP direto)
        return {
            mode: "path-based",
            port: port,
            hostname: hostname,
            protocol: protocol
        };
    }

    /**
     * Calcula a URL absoluta ou relativa canonica para a superficie solicitada
     * @param {string} surface - 'overview' | 'workspace' | 'docs' | 'report' | 'swagger'
     * @returns {string} URL de destino resolvida
     */
    function resolveSurfaceUrl(surface) {
        var topo = detectTopology();
        var protocol = topo.protocol;
        var hostname = topo.hostname;

        if (topo.mode === "decoupled-ports") {
            // Em modo portas desacopladas, cada servico roda em sua porta dedicada
            if (surface === "overview") {
                return protocol + "//" + hostname + ":" + PORT_MAP.LANDING + "/";
            }
            if (surface === "workspace") {
                return protocol + "//" + hostname + ":" + PORT_MAP.WORKSPACE + "/";
            }
            if (surface === "docs") {
                return protocol + "//" + hostname + ":" + PORT_MAP.DOCS + "/";
            }
            if (surface === "report") {
                return protocol + "//" + hostname + ":" + PORT_MAP.DOCS + "/relatorio";
            }
            if (surface === "swagger") {
                return protocol + "//" + hostname + ":" + PORT_MAP.GATEWAY + "/api/docs";
            }
        } else if (topo.mode === "subdomains") {
            // Em modo subdominios Cloudflare Tunnel
            var portSuffix = (topo.port && topo.port !== "80" && topo.port !== "443") ? (":" + topo.port) : "";
            var base = topo.baseDomain + portSuffix;

            if (surface === "overview") {
                // landing page no subdominio pidots ou dominio raiz
                return protocol + "//pidots." + base + "/";
            }
            if (surface === "workspace") {
                return protocol + "//app." + base + "/";
            }
            if (surface === "docs") {
                return protocol + "//docs." + base + "/";
            }
            if (surface === "report") {
                return protocol + "//docs." + base + "/relatorio";
            }
            if (surface === "swagger") {
                return protocol + "//" + hostname + "/api/docs";
            }
        }

        // Modo Path-Based padrao (Gateway 8088, rotas nativas FastAPI 8000 ou fallback seguro)
        if (surface === "overview") {
            return "/";
        }
        if (surface === "workspace") {
            return "/app";
        }
        if (surface === "docs") {
            return "/docs";
        }
        if (surface === "report") {
            return "/relatorio";
        }
        if (surface === "swagger") {
            return "/api/docs";
        }

        return "/";
    }

    /**
     * Varre o DOM e atualiza os links do switcher e marcas de navegacao
     */
    function updateDomLinks() {
        var topo = detectTopology();

        // 1. Atualizacao de todos os Comutadores e Links de Superficie
        var overviewLinks = document.querySelectorAll("#tab-overview, [data-surface='overview'], .nav-surface-overview");
        for (var i = 0; i < overviewLinks.length; i++) {
            overviewLinks[i].href = resolveSurfaceUrl("overview");
            overviewLinks[i].setAttribute("data-resolved-target", "overview");
        }

        var workspaceLinks = document.querySelectorAll("#tab-workspace, #heroCtaWorkspace, [data-surface='workspace'], a[href='/app'], a[href='/app/'], a[href='/workspace']");
        for (var j = 0; j < workspaceLinks.length; j++) {
            workspaceLinks[j].href = resolveSurfaceUrl("workspace");
            workspaceLinks[j].setAttribute("data-resolved-target", "workspace");
        }

        var docsLinks = document.querySelectorAll("#tab-docs, #heroCtaDocs, [data-surface='docs'], a[href='/docs'], a[href='/docs/'], a[href='/guia']");
        for (var k = 0; k < docsLinks.length; k++) {
            docsLinks[k].href = resolveSurfaceUrl("docs");
            docsLinks[k].setAttribute("data-resolved-target", "docs");
        }

        // 2. Links de Marcas / Logos (retornam para Landing Page, protegendo ancoras internas como #hero)
        var brandLinks = document.querySelectorAll(".brand-link, .brand-unit, #brand-link, [data-surface='brand']");
        for (var b = 0; b < brandLinks.length; b++) {
            var rawHref = brandLinks[b].getAttribute("href") || "";
            if (!rawHref.startsWith("#")) {
                brandLinks[b].href = resolveSurfaceUrl("overview");
                brandLinks[b].setAttribute("data-resolved-target", "overview");
            }
        }

        // 3. Links do Relatorio de Engenharia Reversa
        var reportLinks = document.querySelectorAll("#navReport, [data-surface='report'], a[href='/relatorio'], a[href='/relatorio/']");
        for (var r = 0; r < reportLinks.length; r++) {
            reportLinks[r].href = resolveSurfaceUrl("report");
            reportLinks[r].setAttribute("data-resolved-target", "report");
        }

        // 4. Links da API Swagger / Docs
        var swaggerLinks = document.querySelectorAll("a[href='/api/docs'], a[href='/docs/api'], [data-surface='swagger']");
        for (var s = 0; s < swaggerLinks.length; s++) {
            swaggerLinks[s].href = resolveSurfaceUrl("swagger");
            swaggerLinks[s].setAttribute("data-resolved-target", "swagger");
        }

        // 5. Destacar a aba ativa com base na superficie atual detectada
        highlightActiveSurface(topo);
    }

    /**
     * Aplica classe .active na aba correspondente a superficie em execucao
     */
    function highlightActiveSurface(topo) {
        var path = window.location.pathname;
        var port = topo.port;
        var sub = topo.subdomain || "";

        var currentSurface = "overview";

        if (topo.mode === "decoupled-ports") {
            if (port === PORT_MAP.WORKSPACE) {
                currentSurface = "workspace";
            } else if (port === PORT_MAP.DOCS) {
                currentSurface = (path.indexOf("/relatorio") !== -1) ? "report" : "docs";
            } else {
                currentSurface = "overview";
            }
        } else if (topo.mode === "subdomains") {
            if (sub === "app" || sub === "console") {
                currentSurface = "workspace";
            } else if (sub === "docs" || sub === "guide") {
                currentSurface = (path.indexOf("/relatorio") !== -1) ? "report" : "docs";
            } else {
                currentSurface = "overview";
            }
        } else {
            // Path-based
            if (path.indexOf("/app") === 0 || path.indexOf("/console") === 0 || path.indexOf("/workspace") === 0) {
                currentSurface = "workspace";
            } else if (path.indexOf("/docs") === 0 || path.indexOf("/guia") === 0) {
                currentSurface = "docs";
            } else if (path.indexOf("/relatorio") === 0) {
                currentSurface = "report";
            } else {
                currentSurface = "overview";
            }
        }

        // Ajusta classes nas abas e seletores data-surface
        var overviewElements = document.querySelectorAll("#tab-overview, [data-surface='overview']");
        for (var i = 0; i < overviewElements.length; i++) {
            overviewElements[i].classList.toggle("active", currentSurface === "overview");
        }

        var workspaceElements = document.querySelectorAll("#tab-workspace, [data-surface='workspace']");
        for (var j = 0; j < workspaceElements.length; j++) {
            workspaceElements[j].classList.toggle("active", currentSurface === "workspace");
        }

        var docsElements = document.querySelectorAll("#tab-docs, [data-surface='docs']");
        for (var k = 0; k < docsElements.length; k++) {
            docsElements[k].classList.toggle("active", currentSurface === "docs" || currentSurface === "report");
        }
    }

    /**
     * Sistema de Acordes de Teclado Universais (Keyboard Chords)
     * 'g' seguido de 'h' -> Overview
     * 'g' seguido de 'w' -> Workspace
     * 'g' seguido de 'd' -> Docs
     */
    var lastKeyGTime = 0;
    var G_CHORD_WINDOW_MS = 1000;

    function initKeyboardChords() {
        window.addEventListener("keydown", function (e) {
            // Ignorar se o usuario estiver digitando em campos de formulario
            var target = e.target;
            var tag = target ? target.tagName.toUpperCase() : "";
            var isInput = tag === "INPUT" || tag === "TEXTAREA" || (target && target.isContentEditable);
            if (isInput) return;

            // Ignorar combinacoes com Ctrl, Alt ou Meta
            if (e.ctrlKey || e.altKey || e.metaKey) return;

            var key = e.key.toLowerCase();
            var now = Date.now();

            if (key === "g") {
                lastKeyGTime = now;
                return;
            }

            if (now - lastKeyGTime <= G_CHORD_WINDOW_MS) {
                if (key === "h") {
                    e.preventDefault();
                    lastKeyGTime = 0;
                    window.location.href = resolveSurfaceUrl("overview");
                } else if (key === "w") {
                    e.preventDefault();
                    lastKeyGTime = 0;
                    window.location.href = resolveSurfaceUrl("workspace");
                } else if (key === "d") {
                    e.preventDefault();
                    lastKeyGTime = 0;
                    window.location.href = resolveSurfaceUrl("docs");
                }
            }
        }, true);
    }

    /**
     * Inicializacao do Roteador Cruzado
     */
    function init() {
        updateDomLinks();
        initKeyboardChords();

        // Ouve mudancas de historico (SPA popstate)
        window.addEventListener("popstate", function () {
            updateDomLinks();
        });
    }

    // Exporta API publica global
    window.CrossSurfaceRouter = {
        init: init,
        detectTopology: detectTopology,
        resolveSurfaceUrl: resolveSurfaceUrl,
        updateDomLinks: updateDomLinks,
        navigateTo: function (surface) {
            window.location.href = resolveSurfaceUrl(surface);
        }
    };

    // Auto-inicializacao quando o DOM estiver pronto
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
