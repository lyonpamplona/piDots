/**
 * PIDOTS CONSOLE SPA - ORQUESTRADOR CENTRAL E BOOTSTRAP DE UI
 * =====================================================================
 * Controla os eventos globais de tela, atalhos de teclado de acesso rapido,
 * gestao de visoes responsivas (desktop / tablet / smartphone), alternancia
 * de abas do Live Canvas, gavetas tecnicas, transmissao de ordens e bootstrap.
 * ZERO EMOJIS // Vanilla JS Puro // Alta Performance ARM64
 * =====================================================================
 */

(function(window) {
    "use strict";

        function formatDiffHighlight(diffText) {
            if (!diffText) return '';
            const lines = diffText.split('\n');
            return lines.map(line => {
                const escaped = typeof escapeHtml === 'function' ? escapeHtml(line) : line;
                if (escaped.startsWith('+') && !escaped.startsWith('+++')) {
                    return `<div style="color: var(--phosphor-green); background: rgba(0,255,102,0.06); font-family: var(--font-mono); font-size: 11px;">${escaped}</div>`;
                } else if (escaped.startsWith('-') && !escaped.startsWith('---')) {
                    return `<div style="color: var(--stamp-danger); background: rgba(255,51,51,0.06); font-family: var(--font-mono); font-size: 11px;">${escaped}</div>`;
                } else if (escaped.startsWith('---') || escaped.startsWith('+++') || escaped.startsWith('@@')) {
                    return `<div style="color: var(--blueprint-cyan); font-weight: bold; font-family: var(--font-mono); font-size: 11px;">${escaped}</div>`;
                } else {
                    return `<div style="font-family: var(--font-mono); font-size: 11px;">${escaped}</div>`;
                }
            }).join('');
        }

        function openHitlCanvas() {
            const rightCanvas = document.getElementById('rightCanvas');
            if (rightCanvas && rightCanvas.classList.contains('collapsed')) {
                rightCanvas.classList.remove('collapsed');
            }
            const tabBtn = document.getElementById('canvasTabHitl');
            switchCanvasTab('canvas-hitl', tabBtn);
            if (typeof setMobileView === 'function') {
                setMobileView('canvas');
            }
            if (window.PiDotsAPI && typeof PiDotsAPI.loadPendingHitl === 'function') {
                PiDotsAPI.loadPendingHitl();
            }
        }

        async function testProviderConnectionCustom() {
            PixelSystem.toast('Testando conectividade com o provedor de IA...', 'info');
            try {
                const payload = {
                    base_url: (document.getElementById('cfgBaseUrl')?.value || document.getElementById('cfg-ai-url')?.value || '').trim(),
                    model: (document.getElementById('cfgModel')?.value || document.getElementById('cfg-ai-model')?.value || '').trim(),
                    api_key: (document.getElementById('cfgApiKey')?.value || document.getElementById('cfg-ai-key')?.value || '').trim()
                };
                const res = await fetch('/api/edge/settings/test-provider', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (res.ok) {
                    const data = await res.json();
                    if (data.reachable || data.status === 'ok') {
                        PixelSystem.toast(`Provedor alcancavel (${data.latency_ms || 0}ms) // Modelo: ${data.model || payload.model}`, 'success');
                    } else {
                        PixelSystem.toast(`Aviso do provedor: ${data.detail || 'Verifique URL/Chave'}`, 'warning');
                    }
                } else {
                    PixelSystem.toast(`Falha no teste: servidor retornou status ${res.status}`, 'danger');
                }
            } catch (err) {
                PixelSystem.toast(`Erro ao conectar ao servidor: ${err.message}`, 'danger');
            }
        }

        function saveAISettingsCustom() {
            if (window.PiDotsAPI && typeof PiDotsAPI.saveAISettings === 'function') {
                PiDotsAPI.saveAISettings();
            }
        }


        // Redirecionamento das funções globais da interface para o PiDotsAPI
        function createNewSpaceCustom() { PiDotsAPI.createNewSpace(); }
        function saveArtifactRevision() { PiDotsAPI.saveArtifact(); }
        function toggleDiffHighlight() { PiDotsAPI.toggleDiffView(); }
        function resolveHitlFull(decision) { PiDotsAPI.resolveHitl(decision === 'HOMOLOGADO'); }
        function resolveHitlQuick(decision) {
            if (decision === 'HOMOLOGADO') {
                PixelSystem.confirm(
                    'Homologar Acao Critica',
                    'Deseja autorizar o despacho do comando de seguranca para o sandbox Bubblewrap?',
                    () => {
                        openHitlCanvas();
                        PiDotsAPI.resolveHitl(true);
                    }
                );
            } else {
                PixelSystem.confirm(
                    'Vetar Acao Critica',
                    'Confirma o veto e cancelamento desta solicitacao na fila de governanca?',
                    () => {
                        openHitlCanvas();
                        PiDotsAPI.resolveHitl(false);
                    }
                );
            }
        }


        // =====================================================================
        // GERENCIADOR DE VISUALIZAÇÃO MOBILE-FIRST (BOTTOM-NAV)
        // =====================================================================
        let currentMobileView = 'chat'; // 'dots', 'chat', 'canvas'

        function setMobileView(viewName) {
            currentMobileView = viewName;
            
            const sidebar = document.getElementById('leftSidebar');
            const ticker = document.querySelector('.center-ticker-column');
            const canvas = document.getElementById('rightCanvas');

            if (!sidebar || !ticker || !canvas) return;

            const triptych = document.querySelector('.triptych-shell');
            if (triptych && viewName !== 'chat' && triptych.classList.contains('mode-focus-zen')) {
                triptych.classList.remove('mode-focus-zen');
            }

            if (typeof closeDrawer === 'function') {
                closeDrawer();
            }

            sidebar.classList.toggle('mobile-view-active', viewName === 'dots');
            ticker.classList.toggle('mobile-view-active', viewName === 'chat');
            canvas.classList.toggle('mobile-view-active', viewName === 'canvas');

            // Atualiza botões da barra inferior
            document.querySelectorAll('.mobile-nav-btn').forEach(btn => {
                const btnView = btn.getAttribute('data-view');
                btn.classList.toggle('active', btnView === viewName);
            });

            if (viewName === 'dots') {
                sidebar.classList.remove('collapsed');
            }

            // Se for para o canvas, garante que não fique colapsado e limpa badge mobile
            if (viewName === 'canvas') {
                canvas.classList.remove('collapsed');
                const badge = document.getElementById('mobileCanvasBadge');
                if (badge) badge.style.display = 'none';
            }

            // Rola chat para o final ao voltar para o chat
            if (viewName === 'chat') {
                const scrollArea = document.getElementById('tickerScroll');
                if (scrollArea) scrollArea.scrollTop = scrollArea.scrollHeight;
                if (window.PiDotsAPI && typeof PiDotsAPI.enforceDomCeiling === 'function') {
                    PiDotsAPI.enforceDomCeiling();
                }
            }
        }

        function notifyMobileCanvasUpdate(label) {
            const badge = document.getElementById('mobileCanvasBadge');
            if (!badge) return;
            if (window.innerWidth <= 768 && currentMobileView !== 'canvas') {
                badge.textContent = label || 'NOVO';
                badge.style.display = 'inline-block';
                if (navigator.vibrate) {
                    try { navigator.vibrate(12); } catch (_) {}
                }
            }
        }

        // Sincroniza estado de layout entre desktop (tríptico simultâneo) e mobile
        function syncResponsiveLayout() {
            const isMobile = window.innerWidth <= 768;
            const sidebar = document.getElementById('leftSidebar');
            const ticker = document.querySelector('.center-ticker-column');
            const canvas = document.getElementById('rightCanvas');

            if (!sidebar || !ticker || !canvas) return;

            if (isMobile) {
                setMobileView(currentMobileView);
            } else {
                sidebar.classList.remove('mobile-view-active');
                ticker.classList.remove('mobile-view-active');
                canvas.classList.remove('mobile-view-active');
            }
        }

        window.addEventListener('resize', syncResponsiveLayout);
        window.addEventListener('orientationchange', syncResponsiveLayout);

        // Engine de Viewport Dinamico e Teclado Virtual (iOS Safari & Android Chrome)
        if (window.visualViewport) {
            const handleViewportChange = () => {
                const vv = window.visualViewport;
                const isKeyboardOpen = vv.height < (window.innerHeight * 0.85);
                document.body.classList.toggle('keyboard-open', isKeyboardOpen);

                if (isKeyboardOpen) {
                    // Previne que o WebKit empurre o cabecalho para coordenadas negativas
                    window.scrollTo(0, 0);
                }

                if (currentMobileView === 'chat' && isKeyboardOpen) {
                    const scrollArea = document.getElementById('tickerScroll');
                    if (scrollArea) {
                        setTimeout(() => {
                            scrollArea.scrollTop = scrollArea.scrollHeight;
                        }, 60);
                    }
                }
            };

            window.visualViewport.addEventListener('resize', handleViewportChange);
            window.visualViewport.addEventListener('scroll', () => {
                if (document.body.classList.contains('keyboard-open')) {
                    window.scrollTo(0, 0);
                }
            });
        }

        // Alternância de Abas do Canvas Direito
        function switchCanvasTab(tabId, el) {
            document.querySelectorAll('.canvas-panel-view').forEach(panel => {
                panel.classList.remove('active');
            });
            document.querySelectorAll('.canvas-tab').forEach(tab => {
                tab.classList.remove('active');
            });

            const target = document.getElementById(tabId);
            if (target) target.classList.add('active');
            if (el) el.classList.add('active');
        }

        // Alternância de Tema: Dark Paper Noir vs Blueprint
        let isBlueprint = false;
        function toggleTheme() {
            isBlueprint = !isBlueprint;
            const btn = document.getElementById('btn-theme-toggle');
            const span = btn ? btn.querySelector('span') : null;
            if (isBlueprint) {
                document.documentElement.setAttribute('data-theme', 'blueprint');
                if (span) span.textContent = 'Blueprint';
                else if (btn) btn.textContent = 'Tema: Blueprint';
            } else {
                document.documentElement.removeAttribute('data-theme');
                if (span) span.textContent = 'Dark Noir';
                else if (btn) btn.textContent = 'Tema: Dark Noir';
            }
        }

        // Controle de Layout: Ocultar/Exibir Sidebar Esquerda
        function toggleSidebar() {
            const sidebar = document.getElementById('leftSidebar');
            sidebar.classList.toggle('collapsed');
        }

        // Comutação dos 4 Modos da Sidebar OpenDots (Activity Rail)
        let currentSidebarCtx = 'spaces';
        function switchSidebarContext(ctxName, btnEl) {
            currentSidebarCtx = ctxName || 'spaces';
            const sidebar = document.getElementById('leftSidebar');
            if (sidebar && sidebar.classList.contains('collapsed')) {
                sidebar.classList.remove('collapsed');
            }

            const paneMap = {
                spaces: 'sidebarCtxSpaces',
                dots: 'sidebarCtxDots',
                tasks: 'sidebarCtxTasks',
                memory: 'sidebarCtxMemory',
                configs: 'sidebarCtxConfigs'
            };

            document.querySelectorAll('.sidebar-ctx-pane').forEach(pane => {
                pane.classList.remove('active');
            });
            document.querySelectorAll('.activity-rail .rail-btn[data-ctx]').forEach(btn => {
                btn.classList.toggle('active', btn.getAttribute('data-ctx') === currentSidebarCtx);
            });

            const targetId = paneMap[currentSidebarCtx] || 'sidebarCtxSpaces';
            const targetPane = document.getElementById(targetId);
            if (targetPane) targetPane.classList.add('active');

            // Dispara carregamento sob demanda do contexto selecionado
            if (window.PiDotsAPI) {
                if (currentSidebarCtx === 'dots' && typeof PiDotsAPI.loadDotsStudioPane === 'function') {
                    PiDotsAPI.loadDotsStudioPane();
                } else if (currentSidebarCtx === 'tasks' && typeof PiDotsAPI.loadTasksSidebar === 'function') {
                    PiDotsAPI.loadTasksSidebar();
                    if (typeof PiDotsAPI.loadEdgeTriggersSidebar === 'function') PiDotsAPI.loadEdgeTriggersSidebar();
                } else if (currentSidebarCtx === 'memory' && typeof PiDotsAPI.loadMemorySidebar === 'function') {
                    PiDotsAPI.loadMemorySidebar();
                } else if (currentSidebarCtx === 'configs') {
                    if (typeof PiDotsAPI.fetchTelemetry === 'function') PiDotsAPI.fetchTelemetry();
                    if (typeof PiDotsAPI.loadSettings === 'function') PiDotsAPI.loadSettings();
                }
            }
        }

        // Controle do Modal Studio de Criação/Edição de Dots (@Coworkers)
        function openDotCreatorModal(dotId) {
            const modal = document.getElementById('pixelDotCreatorModal');
            if (!modal) return;
            modal.style.display = 'flex';
            modal.classList.add('active');
            if (window.PiDotsAPI && typeof PiDotsAPI.populateDotCreatorModal === 'function') {
                PiDotsAPI.populateDotCreatorModal(dotId || null);
            }
        }

        function closeDotCreatorModal() {
            const modal = document.getElementById('pixelDotCreatorModal');
            if (!modal) return;
            modal.style.display = 'none';
            modal.classList.remove('active');
        }

        // Alternância do Modo Takeover Interativo no Computador de Borda do Dot
        let isComputerTakeoverActive = false;
        function toggleComputerTakeoverMode() {
            isComputerTakeoverActive = !isComputerTakeoverActive;
            const banner = document.getElementById('computerConsoleBanner');
            const btn = document.getElementById('computerTakeoverBtn');
            const takeoverBar = document.getElementById('computerTakeoverBar');
            const tabTerminal = document.getElementById('canvasTabTerminal');

            if (banner) banner.classList.toggle('takeover-active', isComputerTakeoverActive);
            if (takeoverBar) {
                takeoverBar.style.display = 'flex';
                takeoverBar.classList.toggle('takeover-active', isComputerTakeoverActive);
            }

            if (isComputerTakeoverActive) {
                if (btn) {
                    const span = btn.querySelector('span');
                    if (span) span.textContent = 'Modo Controle Ativo';
                    btn.classList.add('btn-amber');
                }
                switchCanvasTab('canvas-terminal', tabTerminal);
                const cmdInput = document.getElementById('computerExecInput');
                if (cmdInput) setTimeout(() => cmdInput.focus(), 50);
                if (window.PiDotsAPI && typeof PiDotsAPI.refreshComputerWorkspaceFiles === 'function') {
                    PiDotsAPI.refreshComputerWorkspaceFiles();
                }
                if (window.PixelSystem && PixelSystem.toast) {
                    PixelSystem.toast('Modo Takeover ativado: controle interativo do Sandbox Bubblewrap assumido pelo operador.', 'warning');
                }
            } else {
                if (btn) {
                    const span = btn.querySelector('span');
                    if (span) span.textContent = 'Modo Observação';
                    btn.classList.remove('btn-amber');
                }
                if (window.PixelSystem && PixelSystem.toast) {
                    PixelSystem.toast('Modo Observação restaurado: execução devolvida ao Dot autônomo.', 'info');
                }
            }
        }

        // Controle de Layout: Ocultar/Exibir Canvas Direito (Split View)
        function toggleCanvasSplit() {
            const canvas = document.getElementById('rightCanvas');
            const btn = document.getElementById('btn-canvas-toggle');
            const btnHeaderOpen = document.getElementById('btnHeaderOpenCanvas');
            const triptych = document.querySelector('.triptych-shell');
            if (!canvas) return;
            canvas.classList.toggle('collapsed');
            if (canvas.classList.contains('collapsed')) {
                const span = btn ? btn.querySelector('span') : null;
                if (span) span.textContent = 'Abrir';
                if (btnHeaderOpen) btnHeaderOpen.style.display = 'inline-flex';
                canvas.classList.remove('expanded');
                if (triptych) triptych.classList.remove('canvas-maximized');
            } else {
                const span = btn ? btn.querySelector('span') : null;
                if (span) span.textContent = 'Fechar';
                if (btnHeaderOpen) btnHeaderOpen.style.display = 'none';
                canvas.classList.remove('expanded');
                if (triptych) triptych.classList.remove('canvas-maximized');
                const btnExp = document.getElementById('btnCanvasExpand');
                const spanExp = btnExp ? btnExp.querySelector('span') : null;
                if (spanExp) spanExp.textContent = 'Maximizar';
            }
        }

        // Controle de Layout: Expandir Canvas Direito para Tela Cheia
        function toggleCanvasExpand() {
            const canvas = document.getElementById('rightCanvas');
            const sidebar = document.getElementById('leftSidebar');
            const btn = document.getElementById('btnCanvasExpand');
            const triptych = document.querySelector('.triptych-shell');
            if (!canvas) return;

            const span = btn ? btn.querySelector('span') : null;
            if (canvas.classList.contains('expanded')) {
                canvas.classList.remove('expanded');
                if (triptych) triptych.classList.remove('canvas-maximized');
                if (sidebar) sidebar.classList.remove('collapsed');
                if (span) span.textContent = 'Maximizar';
            } else {
                canvas.classList.remove('collapsed');
                canvas.classList.add('expanded');
                if (triptych) triptych.classList.add('canvas-maximized');
                if (sidebar) sidebar.classList.add('collapsed');
                if (span) span.textContent = 'Restaurar';
            }
        }

        // Controle do Menu Retrátil Lateral Direito
        function toggleDrawer() {
            const drawer = document.getElementById('retractableDrawer');
            const backdrop = document.getElementById('drawerBackdrop');
            if (!drawer) return;

            const willOpen = !drawer.classList.contains('open');
            drawer.classList.toggle('open', willOpen);
            if (backdrop) backdrop.classList.toggle('open', willOpen);

            const docsBtn = document.getElementById('mobileNavDocs');
            if (docsBtn) {
                if (willOpen) {
                    document.querySelectorAll('.mobile-nav-btn').forEach(b => b.classList.remove('active'));
                    docsBtn.classList.add('active');
                } else {
                    docsBtn.classList.remove('active');
                    const activeBtn = document.querySelector(`.mobile-nav-btn[data-view="${currentMobileView}"]`);
                    if (activeBtn) activeBtn.classList.add('active');
                }
            }

            if (window.ScrollLockManager) {
                if (willOpen) {
                    window.ScrollLockManager.bloquear();
                } else {
                    window.ScrollLockManager.desbloquear();
                }
            }
        }

        function closeDrawer() {
            const drawer = document.getElementById('retractableDrawer');
            const backdrop = document.getElementById('drawerBackdrop');
            if (drawer) drawer.classList.remove('open');
            if (backdrop) backdrop.classList.remove('open');

            const docsBtn = document.getElementById('mobileNavDocs');
            if (docsBtn) {
                docsBtn.classList.remove('active');
                const activeBtn = document.querySelector(`.mobile-nav-btn[data-view="${currentMobileView}"]`);
                if (activeBtn) activeBtn.classList.add('active');
            }

            if (window.ScrollLockManager) {
                window.ScrollLockManager.desbloquear();
            }
        }

        // Abertura do Painel Técnico / Gaveta de Sistema
        function openSystemDrawer() {
            toggleDrawer();
        }

        // Controle de Layout: Alternar Modo de Trabalho (Modo Foco Zen vs Modo Criacao 50/50)
        function toggleWorkspaceMode() {
            const shell = document.querySelector('.triptych-shell');
            const label = document.getElementById('labelWorkspaceMode');
            if (!shell) return;
            const isZen = shell.classList.toggle('mode-focus-zen');
            if (isZen) {
                if (label) label.textContent = 'Modo Criação';
                if (window.PixelSystem && PixelSystem.toast) {
                    PixelSystem.toast('Modo Foco Zen ativado: barra lateral e canvas recolhidos.', 'info');
                }
            } else {
                if (label) label.textContent = 'Modo Foco';
                if (window.PixelSystem && PixelSystem.toast) {
                    PixelSystem.toast('Modo Criacao restaurado: visao ampla 50/50 com Canvas.', 'info');
                }
            }
        }

        // Ação Rápida: Aplicar Sugestão Inicial no Composer
        function applyStarterSuggestion(text) {
            const input = document.getElementById('instructionInput');
            if (!input) return;
            input.value = text;
            input.focus();
            if (typeof transmitInstruction === 'function') {
                transmitInstruction();
            }
        }
        window.applyStarterSuggestion = applyStarterSuggestion;

        // Ação Rápida: Iniciar Nova Conversa Limpa (Padrão OpenDots Empty State)
        function startNewConversation() {
            if (window.PiDotsAPI) {
                PiDotsAPI.activeThreadId = null;
            }
            const scrollArea = document.getElementById('tickerScroll');
            const agentName = document.getElementById('headerActiveAgentName')?.textContent || 'Dev Assistant';
            const activeDot = (window.PiDotsAPI && PiDotsAPI.dotsCache) ? PiDotsAPI.dotsCache.find(d => d.id === PiDotsAPI.activeDotId) : null;
            const monogram = agentName.split(/[\s-_]+/).map(w => w[0]).join('').slice(0, 2).toUpperCase() || 'DA';
            const roleText = activeDot?.role || 'Especialista de borda em código, refatoração e auditoria no Raspberry Pi ARM64. O que vamos construir ou revisar agora?';

            if (scrollArea) {
                scrollArea.innerHTML = `
                    <div class="empty-chat-persona" id="emptyChatPersona">
                        <div class="dot-monogram-avatar" id="emptyChatAvatar" style="width: 48px; height: 48px; font-size: 16px; margin: 0 auto 12px auto;">${escapeHtml(monogram)}</div>
                        <div style="font-family: var(--font-pixel); font-size: 14px; font-weight: 700; color: var(--blueprint-cyan); margin-bottom: 4px;" id="emptyChatName">${escapeHtml(agentName)}</div>
                        <div style="font-size: 11px; color: var(--ink-secondary); max-width: 440px; margin: 0 auto 16px auto; line-height: 1.5;" id="emptyChatRole">${escapeHtml(roleText)}</div>
                        <div class="starter-suggestions" id="starterSuggestions">
                            <button type="button" class="starter-pill" onclick="applyStarterSuggestion('Verificar saúde térmica do SOC e memória RSS do processo')">
                                <svg class="ui-icon ui-icon-sm" viewBox="0 0 24 24"><path d="M22 12h-4l-3 9L9 3l-3 9H2"></path></svg>
                                <span>Verificar saúde do hardware e RSS</span>
                            </button>
                            <button type="button" class="starter-pill" onclick="applyStarterSuggestion('Inspecionar integridade das tabelas do banco SQLite WAL')">
                                <svg class="ui-icon ui-icon-sm" viewBox="0 0 24 24"><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path></svg>
                                <span>Auditar integridade do SQLite WAL</span>
                            </button>
                            <button type="button" class="starter-pill" onclick="applyStarterSuggestion('Revisar especificação arquitetural architecture_spec.md')">
                                <svg class="ui-icon ui-icon-sm" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                                <span>Revisar arquitetura em Spaces</span>
                            </button>
                        </div>
                    </div>
                `;
            }
            const input = document.getElementById('instructionInput');
            if (input) {
                input.value = '';
                input.focus();
            }
            if (window.PixelSystem && PixelSystem.toast) {
                PixelSystem.toast(`Nova conversa iniciada com ${agentName}.`, 'info');
            }
        }

        // Filtro em Tempo Real do Manual Técnico
        function filterDrawerContent(query) {
            const term = query.toLowerCase();
            const items = document.querySelectorAll('#drawerContentList .guide-step');
            items.forEach(item => {
                const text = item.textContent.toLowerCase();
                item.style.display = text.includes(term) ? 'block' : 'none';
            });
        }

        // Seleção de Dot Ativo
        function selectDot(dotId, el) {
            if (window.PiDotsAPI && typeof PiDotsAPI.selectDot === 'function') {
                PiDotsAPI.selectDot(dotId, el);
            }
        }

        // Carregamento de Artefatos no Canvas
        const artifactDocs = {
            'architecture_spec.md': `# piDots Architecture Specification v3.0\n\n## 1. Edge Core Topology\n- Framework: FastAPI + uvloop (Single Worker)\n- Target: Hardware de Borda / SBCs ARM64 & x86_64 (Benchmark: Raspberry Pi 4B)\n- Memory RSS Ceiling: < 300MB\n- Storage Engine: SQLite WAL mode with synchronous=NORMAL`,
            'sqlite_guide.md': `# Calibracao de SQLite WAL em Memoria Flash\n\n1. PRAGMA journal_mode = WAL;\n2. PRAGMA synchronous = NORMAL;\n3. PRAGMA cache_size = -64000;\n4. PRAGMA wal_autocheckpoint = 1000;\n5. PRAGMA busy_timeout = 5000;\n\nElimina pausas de I/O e desgaste de blocos flash no MicroSD.`,
            'fibonacci.py': `import sys\n\ndef fib(n: int) -> int:\n    if n <= 1: return n\n    return fib(n - 1) + fib(n - 2)\n\nif __name__ == '__main__':\n    print(f'Fib(8) = {fib(8)}')`
        };

        function loadArtifact(target) {
            // Se for ID ou nome existente no cache do PiDotsAPI, delega para a API REST oficial
            const byId = (window.PiDotsAPI && PiDotsAPI.spacesCache || []).find(s => s.id === target);
            const byName = (window.PiDotsAPI && PiDotsAPI.spacesCache || []).find(s => s.filename === target);
            if (byId) {
                PiDotsAPI.loadArtifact(byId.id);
                return;
            }
            if (byName) {
                PiDotsAPI.loadArtifact(byName.id);
                return;
            }

            // Fallback para documentos locais em memoria
            document.querySelectorAll('.space-item').forEach(item => {
                item.classList.toggle('active', item.textContent.includes(target));
            });
            const titleEl = document.getElementById('currentArtifactTitle');
            if (titleEl) titleEl.textContent = target;
            const editorEl = document.getElementById('artifactContent');
            if (editorEl) editorEl.value = (typeof artifactDocs !== 'undefined' && artifactDocs[target]) ? artifactDocs[target] : '# Documento em branco';
            
            // Garante que o canvas da direita esteja visível e na aba de artefatos
            const canvas = document.getElementById('rightCanvas');
            if (canvas) canvas.classList.remove('collapsed');
            const btnToggle = document.getElementById('btn-canvas-toggle');
            const spanToggle = btnToggle ? btnToggle.querySelector('span') : null;
            if (spanToggle) spanToggle.textContent = 'Fechar';
            const btnHeaderOpen = document.getElementById('btnHeaderOpenCanvas');
            if (btnHeaderOpen) btnHeaderOpen.style.display = 'none';
            const tabs = document.querySelectorAll('.canvas-tab');
            if (tabs.length) switchCanvasTab('canvas-artifact', tabs[0]);
            
            // No mobile, comuta automaticamente para a visão de Canvas
            if (window.innerWidth <= 768) {
                setMobileView('canvas');
            }
        }

        // Alternância da Trava Mecânica Personalizada
        let isSafetyUnlocked = false;
        function toggleSafetySwitch(el) {
            const switchEl = document.getElementById('safetySwitchMechanical');
            const btnApprove = document.getElementById('btnApproveCanvas');
            isSafetyUnlocked = !isSafetyUnlocked;
            
            if (isSafetyUnlocked) {
                if (switchEl) switchEl.classList.add('active');
                if (btnApprove) btnApprove.disabled = false;
                PixelSystem.toast('TRAVA DESTRIVADA: Autorizacao de comandos criticos liberada.', 'warning');
            } else {
                if (switchEl) switchEl.classList.remove('active');
                if (btnApprove) btnApprove.disabled = true;
                PixelSystem.toast('TRAVA ENGATADA: Protecao de seguranca ativa.', 'info');
            }
        }


        // =====================================================================
        // CONTROLE MULTI-BOT: MENÇÃO DINÂMICA (@BOT) E CADERNO DE RACIOCÍNIO
        // =====================================================================
        let mentionActiveIndex = 0;
        let filteredMentionDots = [];

        function toggleReasoning(toggleEl) {
            const contentEl = toggleEl.nextElementSibling;
            const badgeEl = toggleEl.querySelector('.reasoning-state-badge');
            if (!contentEl) return;
            const isCollapsed = contentEl.classList.toggle('collapsed');
            if (badgeEl) {
                badgeEl.textContent = isCollapsed ? 'Expandir' : 'Colapsar';
            }
        }

        // =====================================================================

        let seqCounter = 3;
        function transmitInstruction() {
            const input = document.getElementById('instructionInput');
            const dropdown = document.getElementById('mentionDropdown');
            if (dropdown) dropdown.style.display = 'none';
            if (window.SlashCommandsEngine) SlashCommandsEngine.closePopover();

            const prompt = input.value.trim();
            if (!prompt) return;

            // Interceptacao: se for Slash Command, executa localmente e encerra fluxo de envio
            if (prompt.startsWith('/')) {
                executeSlashCommand(prompt);
                input.value = '';
                return;
            }

            const scrollArea = document.getElementById('tickerScroll');
            const emptyPersona = document.getElementById('emptyChatPersona');
            if (emptyPersona) {
                emptyPersona.remove();
            }

            // 1. Mensagem do Operador com Carimbo Tátil Limpo
            const userSlip = document.createElement('article');
            userSlip.className = 'ticker-slip';
            userSlip.innerHTML = `
                <header class="slip-header">
                    <span class="actor-stamp stamp-user">Operador · Instrução</span>
                    <span>${new Date().toISOString()}</span>
                    <span>SEQ# 000${window.getNextSeqCounter ? window.getNextSeqCounter() : ++seqCounter}</span>
                </header>
                <section class="slip-output">
                    <p class="slip-text">${escapeHtml(prompt)}</p>
                </section>
                <footer class="slip-perforation">
                    <span class="perforation-line"></span>
                </footer>
            `;
            scrollArea.appendChild(userSlip);
            input.value = '';
            scrollArea.scrollTop = scrollArea.scrollHeight;
            PiDotsAPI.enforceDomCeiling();

            // 2. Dispara o streaming real via SSE do protocolo AG-UI com orquestração Multi-Bot
            PiDotsAPI.transmitStream(prompt);
        }

        function clearTickerStream() {
            startNewConversation();
        }

        // Terminal Sandbox Simulação
        function simulateBwrapCommand() {
            const term = document.getElementById('terminalViewport');
            const timeStr = new Date().toTimeString().split(' ')[0];
            const div = document.createElement('div');
            div.innerHTML = `[${timeStr}] <span style="color: var(--blueprint-cyan);">piDots@rpi4-arm64:~$</span> bwrap --ro-bind / / --bind /workspace /workspace ls -la<br>
<span style="color: var(--ink-secondary);">bwrap: namespace temporario montado com isolamento de PID e IPC.</span><br>
<span style="color: var(--phosphor-green);">[OK] 4 arquivos ativos no espaco do Dot. Retorno: 0.</span>`;
            term.appendChild(div);
            term.scrollTop = term.scrollHeight;
        }

        function clearTerminalLogs() {
            document.getElementById('terminalViewport').innerHTML = '<div style="color: var(--ink-muted);">[BUFFER LIMPO // AGUARDANDO EVENTOS DO SANDBOX]</div>';
        }

        function escapeHtml(str) {
            return String(str ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
        }

        // Leitura de comando injetado via URL deep link (ex: /app?inject_cmd=...)
        window.addEventListener('DOMContentLoaded', () => {
            const urlParams = new URLSearchParams(window.location.search);
            const injectCmd = urlParams.get('inject_cmd');
            if (injectCmd) {
                const input = document.getElementById('instructionInput');
                if (input) {
                    input.value = decodeURIComponent(injectCmd);
                    input.focus();
                    if (window.PixelSystem && PixelSystem.toast) {
                        PixelSystem.toast('Instrucao tecnica injetada da documentacao pronta para despacho.', 'info');
                    }
                }
            }
        });

        // Navegacao Global por Teclado e Resolucao de Superficies delegada ao CrossSurfaceRouter (static/js/core/cross-surface-router.js)

        // Eventos Globais: Menu de Contexto, Tooltips e Tecla ESC
        window.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            PixelSystem.openContextMenu(e.clientX, e.clientY);
        });

        window.addEventListener('click', (e) => {
            if (!e.target.closest('#pixelContextMenu')) {
                PixelSystem.closeContextMenu();
            }
        });

        // Atalhos de Teclado Globais do Console Operacional (Correspondentes ao Menu de Contexto)
        window.addEventListener('keydown', (e) => {
            // Tecla ESC: Fecha menus, modais, autocomplete e gavetas
            if (e.key === 'Escape') {
                PixelSystem.closeContextMenu();
                PixelSystem.closeDialog(false);
                closeDrawer();
                closeDotCreatorModal();
                const patchModal = document.getElementById('pixelPatchNotesModal');
                if (patchModal && patchModal.style.display !== 'none' && window.PiDotsUX && PiDotsUX.PatchNotes) {
                    PiDotsUX.PatchNotes.acknowledge();
                }
                if (typeof SlashCommandsEngine !== 'undefined') SlashCommandsEngine.closePopover();
                const mentionDropdown = document.getElementById('mentionDropdown');
                if (mentionDropdown) mentionDropdown.style.display = 'none';
                return;
            }

            // Alt+1..5: Comutar Modos do Activity Rail da Sidebar OpenDots
            if (e.altKey && ['1', '2', '3', '4', '5'].includes(e.key)) {
                e.preventDefault();
                const ctxList = ['spaces', 'dots', 'tasks', 'memory', 'configs'];
                const targetCtx = ctxList[parseInt(e.key, 10) - 1];
                if (targetCtx) switchSidebarContext(targetCtx);
                return;
            }

            // Tecla Enter no dialogo de confirmacao
            if (e.key === 'Enter') {
                const backdrop = document.getElementById('pixelDialogBackdrop');
                if (backdrop && backdrop.classList.contains('active')) {
                    e.preventDefault();
                    PixelSystem.confirmDialog();
                    return;
                }
            }

            // F1: Manual Operacional (evita Ajuda padrao do navegador)
            if (e.key === 'F1') {
                e.preventDefault();
                PixelSystem.contextAction('docs');
                return;
            }

            // Alt+I: Inspecionar / Focar Artefato no Live Canvas
            if (e.altKey && (e.key === 'i' || e.key === 'I')) {
                e.preventDefault();
                PixelSystem.contextAction('inspect');
                return;
            }

            // Alt+H: Abrir Dossie de Governanca HITL
            if (e.altKey && (e.key === 'h' || e.key === 'H')) {
                e.preventDefault();
                PixelSystem.contextAction('hitl');
                return;
            }

            // Ctrl+S / Cmd+S: Gravar Revisao SQLite (evita Salvar Pagina do navegador)
            if ((e.ctrlKey || e.metaKey) && (e.key === 's' || e.key === 'S')) {
                e.preventDefault();
                PixelSystem.contextAction('save');
                return;
            }

            // Ctrl+L: Limpar Bobina de Chat / Teletipo
            if ((e.ctrlKey || e.metaKey) && (e.key === 'l' || e.key === 'L')) {
                const tag = (e.target && e.target.tagName) ? e.target.tagName.toLowerCase() : '';
                if (tag !== 'input') {
                    e.preventDefault();
                    PixelSystem.contextAction('clear');
                    return;
                }
            }

            // Ctrl+B / Cmd+B: Alternar Barra Lateral Esquerda
            if ((e.ctrlKey || e.metaKey) && (e.key === 'b' || e.key === 'B')) {
                e.preventDefault();
                toggleSidebar();
                return;
            }

            // Ctrl+N / Cmd+N: Iniciar Nova Conversa Limpa
            if ((e.ctrlKey || e.metaKey) && (e.key === 'n' || e.key === 'N')) {
                e.preventDefault();
                startNewConversation();
                return;
            }

            // F11: Alternar Split / Maximizacao do Canvas
            if (e.key === 'F11') {
                e.preventDefault();
                PixelSystem.contextAction('split');
                return;
            }
        });

    // Bootstrap unificado do Console SPA no carregamento do DOM
    document.addEventListener("DOMContentLoaded", () => {
        if (window.PixelSystem && typeof PixelSystem.initTooltips === "function") {
            PixelSystem.initTooltips();
        }
        if (typeof syncResponsiveLayout === "function") {
            syncResponsiveLayout();
        }
        if (window.PiDotsAPI && typeof PiDotsAPI.init === "function") {
            PiDotsAPI.init();
        }
        if (window.PiDotsUX && typeof PiDotsUX.init === "function") {
            PiDotsUX.init();
        }

        // Disparo automatico do Novo Spotlight Tour no primeiro acesso ao console
        setTimeout(() => {
            const tourDone = localStorage.getItem("pidots_tour_completed");
            if (tourDone !== "true" && window.PiDotsTourEngine) {
                console.log("[piDots] Primeiro acesso detectado. Acionando Spotlight Tour...");
                window.PiDotsTourEngine.start(0);
            }
        }, 600);
    });

    // Exportacao Global para compatibilidade total com manipuladores inline do HTML
    window.formatDiffHighlight = formatDiffHighlight;
    window.openHitlCanvas = openHitlCanvas;
    window.testProviderConnectionCustom = testProviderConnectionCustom;
    window.saveAISettingsCustom = saveAISettingsCustom;
    window.createNewSpaceCustom = createNewSpaceCustom;
    window.saveArtifactRevision = saveArtifactRevision;
    window.toggleDiffHighlight = toggleDiffHighlight;
    window.resolveHitlFull = resolveHitlFull;
    window.resolveHitlQuick = resolveHitlQuick;
    window.setMobileView = setMobileView;
    window.notifyMobileCanvasUpdate = notifyMobileCanvasUpdate;
    window.syncResponsiveLayout = syncResponsiveLayout;
    window.switchCanvasTab = switchCanvasTab;
    window.toggleTheme = toggleTheme;
    window.toggleSidebar = toggleSidebar;
    window.switchSidebarContext = switchSidebarContext;
    window.openDotCreatorModal = openDotCreatorModal;
    window.closeDotCreatorModal = closeDotCreatorModal;
    window.toggleComputerTakeoverMode = toggleComputerTakeoverMode;
    window.toggleCanvasSplit = toggleCanvasSplit;
    window.toggleCanvasExpand = toggleCanvasExpand;
    window.toggleDrawer = toggleDrawer;
    window.closeDrawer = closeDrawer;
    window.openSystemDrawer = openSystemDrawer;
    window.toggleWorkspaceMode = toggleWorkspaceMode;
    window.startNewConversation = startNewConversation;
    window.filterDrawerContent = filterDrawerContent;
    window.selectDot = selectDot;
    window.artifactDocs = artifactDocs;
    window.loadArtifact = loadArtifact;
    window.toggleSafetySwitch = toggleSafetySwitch;
    window.toggleReasoning = toggleReasoning;
    window.transmitInstruction = transmitInstruction;
    window.clearTickerStream = clearTickerStream;
    window.simulateBwrapCommand = simulateBwrapCommand;
    window.clearTerminalLogs = clearTerminalLogs;
})(typeof window !== "undefined" ? window : this);
