/**
 * PIDOTS GUIA DIDATICO - SCRIPTS OPERACIONAIS E FERRAMENTAS INTERATIVAS
 * =====================================================================
 * Gerencia: Barra Mecanica de Leitura, Omnisearch Ctrl+K em memoria,
 * Mini API Tester Playground (Passo 06), Simulador de Risco HITL,
 * Drawer Retratil com Scrollspy e Destaque, PWA do Guia Tecnico.
 * ZERO EMOJIS // Vanilla JS Puro // Alta Performance ARM64
 * =====================================================================
 */

(function(window) {
    "use strict";

        /* =====================================================================
           SCRIPTS OPERACIONAIS DO GUIA DIDATICO PIDOTS (INTERFACE TECNICA MINIMALISTA)
           - Barra Mecanica de Leitura (0 a 100%)
           - Omnisearch Client-Side em Memoria (Ctrl+K e /)
           - Mini API Tester Interativo (Passo 06)
           - Drawer Retratil com Scrollspy e Destaque
           - Simulador Interativo HITL
           - Alternador de Tema Dark Noir vs Blueprint
           ===================================================================== */
        const drawer = document.getElementById('retractableDrawer');
        const drawerBackdrop = document.getElementById('drawerBackdrop');
        const toggleDrawerBtn = document.getElementById('toggleDrawerBtn');
        const drawerSearch = document.getElementById('drawerSearchInput');
        const btnBackToTop = document.getElementById('btnBackToTop');
        const drawerLinks = document.querySelectorAll('.drawer-link');
        const stepModules = document.querySelectorAll('.step-module');
        const readingProgressThumb = document.getElementById('readingProgressThumb');

        // 1. Barra Mecanica de Progresso de Leitura Vertical
        window.addEventListener('scroll', () => {
            const winScroll = document.documentElement.scrollTop || document.body.scrollTop;
            const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
            const scrolled = height > 0 ? (winScroll / height) * 100 : 0;
            if (readingProgressThumb) {
                readingProgressThumb.style.width = scrolled.toFixed(1) + '%';
            }

            // Controle do botao voltar ao topo
            if (winScroll > 300) {
                btnBackToTop.style.display = 'flex';
            } else {
                btnBackToTop.style.display = 'none';
            }
        });

        // Gerenciador de Bloqueio de Rolagem Resiliente (Consome núcleo central de scroll-lock.js)
        const ScrollLockManager = window.ScrollLockManager || {
            bloquear() {},
            desbloquear() {}
        };

        // 2. Controle do Drawer Retratil a Direita (Menu Lateral Direito Abre/Fecha)
        function openDrawer() {
            if (!drawer) return;
            drawer.classList.add('is-open', 'open');
            if (drawerBackdrop) drawerBackdrop.classList.add('is-active', 'open');
            document.body.classList.add('drawer-open');
            if (toggleDrawerBtn) {
                toggleDrawerBtn.setAttribute('aria-expanded', 'true');
            }
            if (window.innerWidth <= 1024) {
                ScrollLockManager.bloquear();
            }
            if (drawerSearch) {
                setTimeout(() => drawerSearch.focus(), 50);
            }
        }

        function closeDrawer(restoreScroll = true) {
            if (drawer) drawer.classList.remove('is-open', 'open');
            if (drawerBackdrop) drawerBackdrop.classList.remove('is-active', 'open');
            document.body.classList.remove('drawer-open');
            if (toggleDrawerBtn) {
                toggleDrawerBtn.setAttribute('aria-expanded', 'false');
            }
            ScrollLockManager.desbloquear(false, restoreScroll);
        }

        if (toggleDrawerBtn) {
            toggleDrawerBtn.addEventListener('click', () => {
                if (drawer && (drawer.classList.contains('is-open') || drawer.classList.contains('open'))) {
                    closeDrawer();
                } else {
                    openDrawer();
                }
            });
        }

        // Fechamento da Gaveta via Tecla Escape e Atalho Global Alt+I
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && drawer && (drawer.classList.contains('is-open') || drawer.classList.contains('open'))) {
                closeDrawer();
            } else if ((e.altKey && (e.key === 'i' || e.key === 'I')) && !e.ctrlKey && !e.metaKey) {
                e.preventDefault();
                if (drawer && (drawer.classList.contains('is-open') || drawer.classList.contains('open'))) {
                    closeDrawer();
                } else {
                    openDrawer();
                }
            }
        });

        // 3. Navegacao Suave para Passos
        function scrollToStep(stepId) {
            const target = document.getElementById(stepId);
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }

        function handleDrawerNav(e, stepId) {
            if (e) e.preventDefault();
            closeDrawer(false);
            requestAnimationFrame(() => {
                scrollToStep(stepId);
            });
        }

        // Destaque Ativo Resiliente (ScrollSpy Híbrido para Seções do Manual)
        function setActiveStepHighlight(id) {
            if (!id) return;
            drawerLinks.forEach(link => {
                if (link.getAttribute('href') === '#' + id) {
                    link.classList.add('active');
                } else {
                    link.classList.remove('active');
                }
            });
        }

        function updateActiveStepByScroll() {
            if (!stepModules || stepModules.length === 0) return;
            let activeId = stepModules[0].id;
            const offsetThreshold = 140;
            for (let i = 0; i < stepModules.length; i++) {
                const rect = stepModules[i].getBoundingClientRect();
                if (rect.top <= offsetThreshold) {
                    activeId = stepModules[i].id;
                } else {
                    break;
                }
            }
            setActiveStepHighlight(activeId);
        }

        window.addEventListener('scroll', updateActiveStepByScroll, { passive: true });
        document.addEventListener('DOMContentLoaded', updateActiveStepByScroll);

        // 4. Mecanismo de Busca no Drawer (Oculta itens e também cabeçalhos de trilha vazios)
        function filtrarDrawer(query) {
            const q = (query || '').trim().toLowerCase();
            const items = document.querySelectorAll('.drawer-item');

            items.forEach(item => {
                const text = item.innerText.toLowerCase();
                const keywords = (item.getAttribute('data-keywords') || '').toLowerCase();
                if (!q || text.includes(q) || keywords.includes(q)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });

            const trackHeaders = document.querySelectorAll('.drawer-track-header');
            trackHeaders.forEach(header => {
                if (!q) {
                    header.style.display = '';
                    return;
                }
                let next = header.nextElementSibling;
                let hasVisibleItem = false;
                while (next && !next.classList.contains('drawer-track-header')) {
                    if (next.classList.contains('drawer-item') && next.style.display !== 'none') {
                        hasVisibleItem = true;
                        break;
                    }
                    next = next.nextElementSibling;
                }
                header.style.display = hasVisibleItem ? '' : 'none';
            });
        }

        if (drawerSearch) {
            drawerSearch.addEventListener('input', (e) => {
                filtrarDrawer(e.target.value);
            });
        }

        // 5. Copia de Comandos com Fallback Resiliente para HTTP LAN (.code-paper-box, .terminal-block, .terminal-card)
        function copyToClipboardFallback(text) {
            if (window.PixelSystem && window.PixelSystem.copyToClipboard) {
                return window.PixelSystem.copyToClipboard(text);
            }
            return new Promise((resolve, reject) => {
                if (navigator.clipboard && window.isSecureContext) {
                    navigator.clipboard.writeText(text).then(resolve).catch(() => {
                        execCommandCopy(text, resolve, reject);
                    });
                } else {
                    execCommandCopy(text, resolve, reject);
                }
            });
        }

        function execCommandCopy(text, resolve, reject) {
            try {
                const ta = document.createElement('textarea');
                ta.value = text;
                ta.setAttribute('readonly', '');
                ta.style.position = 'fixed';
                ta.style.top = '-9999px';
                ta.style.left = '-9999px';
                document.body.appendChild(ta);
                ta.select();
                ta.setSelectionRange(0, text.length);
                const ok = document.execCommand('copy');
                document.body.removeChild(ta);
                if (ok) resolve();
                else reject(new Error('execCommand copy failed'));
            } catch (e) {
                reject(e);
            }
        }

        function copiarTextoPixel(btn) {
            if (!btn) return;
            const box = btn.closest('.code-paper-box, .terminal-block, .terminal-card');
            if (!box) return;
            const codeEl = box.querySelector('.code-paper-content, .terminal-pre code, .terminal-pre');
            if (!codeEl) return;
            const code = codeEl.innerText || codeEl.textContent || '';
            copyToClipboardFallback(code).then(() => {
                const labelSpan = btn.querySelector('span');
                const originalText = labelSpan ? labelSpan.textContent : '';
                if (labelSpan) {
                    labelSpan.textContent = 'Copiado';
                }
                btn.classList.add('btn-green');
                setTimeout(() => {
                    if (labelSpan && originalText) {
                        labelSpan.textContent = originalText;
                    }
                    btn.classList.remove('btn-green');
                }, 2000);
            }).catch(() => {});
        }

        // 6. Mini API Tester Interativo (Passo 06)
        let currentApiPayload = '';

        function selecionarEndpointApi(metodo, rota, payload, btnElement) {
            currentApiPayload = (payload !== undefined && payload !== null) ? payload : '';
            const chips = document.querySelectorAll('.api-chip-btn');
            chips.forEach(c => c.classList.remove('active'));
            
            let target = btnElement;
            if (!target && typeof event !== 'undefined' && event) {
                target = event.currentTarget || event.target;
            }
            if (target && target.classList) {
                target.classList.add('active');
            } else {
                chips.forEach(c => {
                    if (c.textContent.includes(rota)) c.classList.add('active');
                });
            }

            const methodBadge = document.getElementById('apiTestMethod');
            const urlInput = document.getElementById('apiTestUrlInput');
            if (methodBadge) methodBadge.innerText = metodo;
            if (urlInput) urlInput.value = rota;
        }

        async function executarTesteApi() {
            const methodBadge = document.getElementById('apiTestMethod');
            const urlInput = document.getElementById('apiTestUrlInput');
            const statusBadge = document.getElementById('apiTestStatusBadge');
            const latencyBadge = document.getElementById('apiTestLatency');
            const titleElem = document.getElementById('apiTestTerminalTitle');
            const outputElem = document.getElementById('apiTestJsonOutput');
            const runBtn = document.getElementById('btnRunApiTest');
            const runBtnLabel = runBtn ? runBtn.querySelector('span') : null;
            const originalLabel = runBtnLabel ? runBtnLabel.textContent : 'Testar Rota HTTP';

            const metodo = methodBadge ? methodBadge.innerText.trim() : 'GET';
            const rota = urlInput ? urlInput.value.trim() : '/health';

            if (runBtn) {
                runBtn.disabled = true;
                if (runBtnLabel) runBtnLabel.textContent = 'Enviando requisição...';
            }

            const t0 = performance.now();

            try {
                let options = { method: metodo, headers: { 'Accept': 'application/json' } };
                if (metodo === 'POST' || metodo === 'PUT') {
                    if (typeof currentApiPayload === 'string' && currentApiPayload.trim().length > 0) {
                        options.headers['Content-Type'] = 'application/json';
                        // Evita double-stringify quando currentApiPayload ja e uma string JSON valida
                        try {
                            const parsed = JSON.parse(currentApiPayload);
                            options.body = JSON.stringify(parsed);
                        } catch (_) {
                            options.body = currentApiPayload;
                        }
                    } else if (currentApiPayload && typeof currentApiPayload === 'object') {
                        options.headers['Content-Type'] = 'application/json';
                        options.body = JSON.stringify(currentApiPayload);
                    } else if (rota === '/api/threads') {
                        options.headers['Content-Type'] = 'application/json';
                        options.body = JSON.stringify({
                            dot_id: 'dot-supervisor',
                            title: 'Sessao Interativa Mini Tester ' + new Date().toLocaleTimeString('pt-BR')
                        });
                    }
                }

                const resp = await fetch(rota, options);
                const t1 = performance.now();
                const latency = Math.round(t1 - t0);
                const json = await resp.json();

                if (statusBadge) {
                    statusBadge.innerText = resp.status + ' ' + (resp.status === 200 ? 'OK' : 'RESPONSE');
                    statusBadge.className = 'api-status-badge ' + (resp.ok ? 'status-200' : 'status-err');
                }
                if (latencyBadge) latencyBadge.innerText = latency + ' ms';
                if (titleElem) titleElem.innerText = 'RESPOSTA DO SERVIDOR // HTTP ' + resp.status;
                if (outputElem) outputElem.innerText = JSON.stringify(json, null, 2);

            } catch (err) {
                const t1 = performance.now();
                const latency = Math.round(t1 - t0);

                // Fallback informativo demonstrativo
                if (statusBadge) {
                    statusBadge.innerText = '200 OK (SIMULADO)';
                    statusBadge.className = 'api-status-badge status-200';
                }
                if (latencyBadge) latencyBadge.innerText = latency + ' ms';
                if (titleElem) titleElem.innerText = 'RESPOSTA SIMULADA // ' + rota;
                
                let fallbackPayload = {
                    endpoint: rota,
                    method: metodo,
                    node: "pidots-core",
                    arch: "aarch64 / x86_64 (Linux Edge Node)",
                    status: "healthy",
                    timestamp: new Date().toISOString(),
                    note: "Conexão local ativa via IPC/HTTP."
                };
                if (outputElem) outputElem.innerText = JSON.stringify(fallbackPayload, null, 2);
            } finally {
                if (runBtn) {
                    runBtn.disabled = false;
                    if (runBtnLabel) runBtnLabel.textContent = originalLabel;
                }
            }
        }

        // 7. Base de Conhecimento e Indexacao do Omnisearch Client-Side
        const OMNISEARCH_INDEX = [
            {
                id: 'passo-1',
                step: 'PASSO 01',
                title: 'O Que É o piDots & Especialistas Autônomos',
                keywords: 'arquetipos supervisor coder desenvolvedor arquiteto auditor conceitos edge react persistencia modular arm64',
                desc: 'Estacao de trabalho soberana para Raspberry Pi 4B. Quatro arquetipos especializados: Supervisor, Desenvolvedor (@coder), Arquiteto (@arquiteto) e Auditor.'
            },
            {
                id: 'passo-2',
                step: 'PASSO 02',
                title: 'Chat Multi-Bot & Logs Internos de Raciocínio',
                keywords: 'multi-bot mencao delegate handoff logs internos raciocinio inter-agente visibilidade internal threads',
                desc: 'Diálogos colaborativos com menções @dot, delegação de subtarefas sem poluir a thread principal e transcrições expansivas de raciocínio.'
            },
            {
                id: 'passo-3',
                step: 'PASSO 03',
                title: 'Autonomia Proativa (Dot Heartbeat) & Diretriz de Silêncio',
                keywords: 'heartbeat proativo cron croniter heartbeat_ok tarefas tasks agendamento segundo plano economia tokens',
                desc: 'Agendador cron assincrono em background. Diretriz vital HEARTBEAT_OK para operacao 100% silenciosa e economia de tokens.'
            },
            {
                id: 'passo-4',
                step: 'PASSO 04',
                title: 'Gateway de Mensageria Unificada & Salas Temáticas',
                keywords: 'gateway mensageria telegram whatsapp evolution api webhooks canais salas antirecursao hop_count',
                desc: 'Integracao com Telegram, WhatsApp e Webhooks HTTP. Salas tematicas com trava rigida antirecursao (hop_count <= 3).'
            },
            {
                id: 'passo-5',
                step: 'PASSO 05',
                title: 'Arsenal de Ferramentas & Poda Dinâmica (Tool Pruning)',
                keywords: 'ferramentas tools arsenal hitl pruning economia poda shell python workspace permissions',
                desc: 'Mais de 15 ferramentas nativas. Poda dinamica de esquemas que reduz em mais de 75% o consumo de tokens de entrada.'
            },
            {
                id: 'passo-6',
                step: 'PASSO 06',
                title: 'Passo a Passo Operacional, Endpoints REST & Preservação Flash',
                keywords: 'deploy docker docker-compose env curl rest endpoints health tasks channels computer state save-as-space mcp microsd wal synchronous normal activity rail',
                desc: 'Configuracao de ambiente, deploy via Docker Compose, Mini API Tester com rotas de CoAgents State e Computador de Borda, e diretrizes PRAGMA do MicroSD.'
            },
            {
                id: 'passo-7',
                step: 'PASSO 07',
                title: 'Memória Hierárquica Autônoma (Padrão MemGPT / Letta)',
                keywords: 'memoria hierarquica core memory archival recall fts5 bm25 embeddings 64d unificado memoria longa duracao persona fatos',
                desc: 'Tres camadas de memoria: Core Memory editavel, Recall Memory e Archival Memory com motor de embedding 64D deterministico unificado e FTS5/BM25.'
            },
            {
                id: 'passo-8',
                step: 'PASSO 08',
                title: 'Self-Healing Harness & Planejamento em Dois Estágios',
                keywords: 'self-healing auto-correcao traceback goals milestones metas planejamento checkpoints ast fluxo fechado coagents state_snapshot state_delta',
                desc: 'Diagnostico cirurgico de tracebacks (teto 2 tentativas) e Planejamento em 2 Estagios sincronizado via CoAgents Shared State (STATE_SNAPSHOT / STATE_DELTA).'
            },
            {
                id: 'passo-9',
                step: 'PASSO 09',
                title: 'Conselho Consultivo & Debate Dialético Multi-Bot',
                keywords: 'conselho consultivo debate dialetica propositor auditor supervisor fitas internas resolucao tripartite early consensus exit',
                desc: 'Deliberacao formal entre Propositor (@coder), Auditor Critico (@auditor) e Supervisor (@supervisor) com Early Consensus Exit.'
            },
            {
                id: 'passo-10',
                step: 'PASSO 10',
                title: 'Espaço de Conhecimento Compartilhado & Dot Packs Portáveis',
                keywords: 'shared space knowledge quadro colaborativo save thread as space dot packs v1.1 sha-256 templates manifestos import export json portabilidade',
                desc: 'Quadro compartilhado sincronizado por thread, conversao de conversa em Space (/save-space) e empacotamento criptografico Dot Packs v1.1 (SHA-256).'
            },
            {
                id: 'passo-11',
                step: 'PASSO 11',
                title: 'Triggers de Hardware Edge & Manutenção do MicroSD',
                keywords: 'hardware triggers temperatura broadcom bcm2711 process_rss_mb microsd manutencao noturna vacuum wal truncate protecao fisica',
                desc: 'Telemetria fisica com process_rss_mb real do processo FastAPI, monitoramento termico BCM2711 e rotina noturna WAL TRUNCATE + VACUUM INTO.'
            },
            {
                id: 'passo-12',
                step: 'PASSO 12',
                title: 'Micro-Motor de Internacionalização (i18n) & Dicionários JSON de Borda',
                keywords: 'internacionalizacao i18n bilingue portugues ingles pt en locale traducao dicionario data-i18n client-side static pidots-i18n',
                desc: 'Alternancia instantanea PT/EN sem frameworks pesados, dicionarios atomicos JSON com cache estatico e seguranca estrita via textContent.'
            },
            {
                id: 'passo-13',
                step: 'PASSO 13',
                title: 'Protocolo de 34 Slash Commands (/) & Interface de Borda de Alta Velocidade',
                keywords: 'slash commands barra popover autocomplete catalogo 34 comandos teletipo slips levenshtein export pack hitl telemetry coagents computer save-space mcp clear theme',
                desc: 'Catalogo unificado de 34 comandos em 6 categorias (incluindo /coagents, /computer, /save-space e /mcp), execucao no cliente em < 16ms e recibos tatis.'
            },
            {
                id: 'passo-14',
                step: 'PASSO 14',
                title: 'Desacoplamento por Portas & Cloudflare Tunnel (8081, 8082, 8083)',
                keywords: 'cloudflare tunnel cloudflared desacoplamento portas 8081 8082 8083 nginx reverse proxy zero trust nat traversal ingress arm64',
                desc: 'Exposicao remota segura de nós Raspberry Pi sem abertura de portas no roteador, mapeamento de subdominios dedicados e protecao Zero Trust no Workspace.'
            }
        ];

        let omnisearchSelectedIndex = 0;
        let omnisearchCurrentMatches = [];
        let omnisearchDomIndexed = false;

        function indexarConteudoDomOmnisearch() {
            if (omnisearchDomIndexed) return;
            OMNISEARCH_INDEX.forEach(item => {
                const stepEl = document.getElementById(item.id);
                if (stepEl) {
                    item.bodyText = (stepEl.innerText || stepEl.textContent || '')
                        .replace(/\s+/g, ' ')
                        .trim();
                } else {
                    item.bodyText = '';
                }
            });
            omnisearchDomIndexed = true;
        }

        function extrairSnippetOmnisearch(item, query) {
            if (!query) return item.desc;
            const q = query.toLowerCase();
            const headerHit = (item.title + ' ' + item.desc + ' ' + item.keywords + ' ' + item.step)
                .toLowerCase()
                .includes(q);
            if (headerHit || !item.bodyText) {
                return item.desc;
            }
            const bodyLower = item.bodyText.toLowerCase();
            const matchIdx = bodyLower.indexOf(q);
            if (matchIdx === -1) return item.desc;
            const start = Math.max(0, matchIdx - 48);
            const end = Math.min(item.bodyText.length, matchIdx + query.length + 72);
            const prefix = start > 0 ? '...' : '';
            const suffix = end < item.bodyText.length ? '...' : '';
            return prefix + item.bodyText.slice(start, end).trim() + suffix;
        }

        function abrirOmnisearch() {
            indexarConteudoDomOmnisearch();
            const modal = document.getElementById('omnisearchModal');
            const backdrop = document.getElementById('omnisearchBackdrop');
            const input = document.getElementById('omnisearchInput');

            if (modal && backdrop) {
                modal.classList.add('is-active');
                backdrop.classList.add('is-active');
                ScrollLockManager.bloquear();
                if (input) {
                    input.value = '';
                    input.focus();
                }
                renderizarResultadosOmnisearch('');
            }
        }

        function fecharOmnisearch() {
            const modal = document.getElementById('omnisearchModal');
            const backdrop = document.getElementById('omnisearchBackdrop');
            if (modal) modal.classList.remove('is-active');
            if (backdrop) backdrop.classList.remove('is-active');
            ScrollLockManager.desbloquear();
        }

        function destacarTermo(texto, termo) {
            if (!termo) return texto;
            const regex = new RegExp('(' + termo.replace(/[-/\\^$*+?.()|[\]{}]/g, '\\$&') + ')', 'gi');
            return texto.replace(regex, '<mark>$1</mark>');
        }

        function renderizarResultadosOmnisearch(query) {
            indexarConteudoDomOmnisearch();
            const container = document.getElementById('omnisearchResults');
            const counter = document.getElementById('omnisearchCounter');
            const totalMatches = document.getElementById('omnisearchTotalMatches');
            const q = query.trim().toLowerCase();

            omnisearchCurrentMatches = OMNISEARCH_INDEX.filter(item => {
                if (!q) return true;
                const fullText = (
                    item.title + ' ' +
                    item.desc + ' ' +
                    item.keywords + ' ' +
                    item.step + ' ' +
                    (item.bodyText || '')
                ).toLowerCase();
                return fullText.includes(q);
            });

            omnisearchSelectedIndex = 0;

            if (counter) counter.innerText = omnisearchCurrentMatches.length + ' RESULTADOS';
            if (totalMatches) totalMatches.innerText = omnisearchCurrentMatches.length + ' PASSOS ENCONTRADOS';

            if (!container) return;
            container.innerHTML = '';

            if (omnisearchCurrentMatches.length === 0) {
                container.innerHTML = '<div style="padding: 24px; text-align: center; color: var(--ink-muted); font-family: var(--font-pixel); font-size: 9px;">NENHUM PASSO ENCONTRADO PARA O TERMO CONSULTADO.</div>';
                return;
            }

            omnisearchCurrentMatches.forEach((item, index) => {
                const el = document.createElement('div');
                el.className = 'omnisearch-item' + (index === omnisearchSelectedIndex ? ' is-selected' : '');
                el.onclick = () => {
                    fecharOmnisearch();
                    scrollToStep(item.id);
                };

                const snippet = extrairSnippetOmnisearch(item, q);
                el.innerHTML = `
                    <div class="omnisearch-item-top">
                        <span class="omnisearch-item-title">${destacarTermo(item.title, q)}</span>
                        <span class="omnisearch-item-step">${item.step}</span>
                    </div>
                    <div class="omnisearch-item-desc">${destacarTermo(snippet, q)}</div>
                `;
                container.appendChild(el);
            });
        }

        function atualizarSelecaoOmnisearch() {
            const items = document.querySelectorAll('.omnisearch-item');
            items.forEach((item, idx) => {
                if (idx === omnisearchSelectedIndex) {
                    item.classList.add('is-selected');
                    item.scrollIntoView({ block: 'nearest' });
                } else {
                    item.classList.remove('is-selected');
                }
            });
        }

        const omnisearchInput = document.getElementById('omnisearchInput');
        if (omnisearchInput) {
            omnisearchInput.addEventListener('input', (e) => {
                renderizarResultadosOmnisearch(e.target.value);
            });

            omnisearchInput.addEventListener('keydown', (e) => {
                if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    if (omnisearchCurrentMatches.length > 0) {
                        omnisearchSelectedIndex = (omnisearchSelectedIndex + 1) % omnisearchCurrentMatches.length;
                        atualizarSelecaoOmnisearch();
                    }
                } else if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    if (omnisearchCurrentMatches.length > 0) {
                        omnisearchSelectedIndex = (omnisearchSelectedIndex - 1 + omnisearchCurrentMatches.length) % omnisearchCurrentMatches.length;
                        atualizarSelecaoOmnisearch();
                    }
                } else if (e.key === 'Enter') {
                    e.preventDefault();
                    if (omnisearchCurrentMatches.length > 0 && omnisearchCurrentMatches[omnisearchSelectedIndex]) {
                        const targetId = omnisearchCurrentMatches[omnisearchSelectedIndex].id;
                        fecharOmnisearch();
                        scrollToStep(targetId);
                    }
                } else if (e.key === 'Escape') {
                    fecharOmnisearch();
                }
            });
        }

        // Atalho Global de Teclado (Ctrl+K, Cmd+K ou /)
        window.addEventListener('keydown', (e) => {
            const isInputFocused = ['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName);

            // Ctrl+K ou Cmd+K
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
                e.preventDefault();
                abrirOmnisearch();
                return;
            }

            // Tecla / quando nenhum campo estiver em foco
            if (e.key === '/' && !isInputFocused) {
                e.preventDefault();
                abrirOmnisearch();
                return;
            }

            // Tecla Escape para fechar modal ou drawer
            if (e.key === 'Escape') {
                fecharOmnisearch();
                closeDrawer();
            }
        });

        // 8. Simulador Interativo do Analisador HITL
        function analisarComandoHITL() {
            const cmd = document.getElementById('hitlTestInput').value.trim();
            const cmdDisplay = document.getElementById('hitlCmdDisplay');
            const riskBadge = document.getElementById('hitlRiskBadge');
            const reqBadge = document.getElementById('hitlReqBadge');

            if (cmdDisplay) cmdDisplay.innerText = cmd || '(vazio)';
            const lower = cmd.toLowerCase();

            const criticos = [
                'rm -rf', 'reboot', 'shutdown', 'mkfs', 'dd ', ':(){ :|:& };:',
                'chmod 777 /', 'chown', '> /dev/sda', 'kill -9 1'
            ];
            const medios = ['pip install', 'npm install', 'git pull', 'systemctl', 'docker stop'];

            let ehCritico = criticos.some(c => lower.includes(c));
            let ehMedio = medios.some(m => lower.includes(m));

            if (ehCritico) {
                if (riskBadge) {
                    riskBadge.className = 'pixel-stamp stamp-critical';
                    riskBadge.innerText = 'CRITICAL (CRITICO)';
                }
                if (reqBadge) {
                    reqBadge.className = 'pixel-stamp stamp-critical';
                    reqBadge.innerText = 'BLOQUEADO ATE APROVACAO';
                }
            } else if (ehMedio) {
                if (riskBadge) {
                    riskBadge.className = 'pixel-stamp stamp-amber';
                    riskBadge.innerText = 'MEDIUM (MEDIO)';
                }
                if (reqBadge) {
                    reqBadge.className = 'pixel-stamp stamp-notice';
                    reqBadge.innerText = 'REGISTRADO EM AUDITORIA';
                }
            } else {
                if (riskBadge) {
                    riskBadge.className = 'pixel-stamp stamp-approved';
                    riskBadge.innerText = 'LOW (BAIXO RISCO)';
                }
                if (reqBadge) {
                    reqBadge.className = 'pixel-stamp stamp-approved';
                    reqBadge.innerText = 'EXECUCAO IMEDIATA';
                }
            }
        }

        // 9. Alternador de Tema Dark Noir vs Blueprint Tecnico
        function toggleTheme() {
            if (window.PixelSystem && window.PixelSystem.ThemeManager) {
                return window.PixelSystem.ThemeManager.toggleTheme(false);
            }
            const current = document.documentElement.getAttribute('data-theme');
            const next = current === 'blueprint' ? 'noir' : 'blueprint';
            
            if (next === 'blueprint') {
                document.documentElement.setAttribute('data-theme', 'blueprint');
                localStorage.setItem('pidots-theme', 'blueprint');
            } else {
                document.documentElement.removeAttribute('data-theme');
                localStorage.setItem('pidots-theme', 'noir');
            }
        }

        // Carregar tema salvo
        (function initSavedTheme() {
            const saved = localStorage.getItem('pidots-theme');
            if (saved === 'blueprint') {
                document.documentElement.setAttribute('data-theme', 'blueprint');
            }
        })();

        // Navegacao Global por Teclado e Resolucao de Superficies delegada ao CrossSurfaceRouter (static/js/core/cross-surface-router.js)

        // Integracao PWA & Service Worker no Guia Operacional Didatico
        const PiDotsDocsPWA = (function() {
            let deferredPrompt = null;

            function init() {
                if ('serviceWorker' in navigator) {
                    window.addEventListener('load', () => {
                        navigator.serviceWorker.register('/sw.js').catch((err) => {
                            console.warn('[piDots Docs] Falha ao registrar Service Worker:', err);
                        });
                    });
                }

                window.addEventListener('beforeinstallprompt', (e) => {
                    e.preventDefault();
                    deferredPrompt = e;
                    const btn = document.getElementById('btnDocsPwaInstall');
                    if (btn) btn.style.display = 'inline-flex';
                });

                window.addEventListener('appinstalled', () => {
                    deferredPrompt = null;
                    const btn = document.getElementById('btnDocsPwaInstall');
                    if (btn) btn.style.display = 'none';
                });

                // Deteccao do iOS Safari
                const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
                const isStandalone = window.navigator.standalone === true;
                if (isIOS && !isStandalone) {
                    const btn = document.getElementById('btnDocsPwaInstall');
                    if (btn) {
                        btn.style.display = 'inline-flex';
                        btn.onclick = () => {
                            const isEn = window.PiDotsI18n && window.PiDotsI18n.getLanguage() === 'en';
                            const msg = isEn
                                ? 'To install on iOS Safari: tap the Share button and select "Add to Home Screen".'
                                : 'Instalação no iOS Safari: toque no botão Compartilhar e selecione "Adicionar à Tela de Início".';
                            if (window.PixelSystem && window.PixelSystem.toast) {
                                window.PixelSystem.toast(msg, 'info', 5000);
                            } else {
                                console.info(msg);
                            }
                        };
                    }
                }
            }

            async function install() {
                if (!deferredPrompt) return;
                deferredPrompt.prompt();
                const { outcome } = await deferredPrompt.userChoice;
                if (outcome === 'accepted') {
                    console.log('[piDots Docs] Instalacao PWA aceita.');
                }
                deferredPrompt = null;
                const btn = document.getElementById('btnDocsPwaInstall');
                if (btn) btn.style.display = 'none';
            }

            return {
                init: init,
                install: install
            };
        })();

        document.addEventListener('DOMContentLoaded', () => {
            PiDotsDocsPWA.init();
        });

    // Exportacao Global para manipuladores de evento inline
    window.openDrawer = openDrawer;
    window.closeDrawer = closeDrawer;
    window.scrollToStep = scrollToStep;
    window.handleDrawerNav = handleDrawerNav;
    window.filtrarDrawer = filtrarDrawer;
    window.copiarTextoPixel = copiarTextoPixel;
    window.selecionarEndpointApi = selecionarEndpointApi;
    window.executarTesteApi = executarTesteApi;
    window.abrirOmnisearch = abrirOmnisearch;
    window.fecharOmnisearch = fecharOmnisearch;
    window.destacarTermo = destacarTermo;
    window.renderizarResultadosOmnisearch = renderizarResultadosOmnisearch;
    window.atualizarSelecaoOmnisearch = atualizarSelecaoOmnisearch;
    window.analisarComandoHITL = analisarComandoHITL;
    window.toggleTheme = toggleTheme;
    window.PiDotsDocsPWA = PiDotsDocsPWA;
})(typeof window !== "undefined" ? window : this);
