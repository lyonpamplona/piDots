/**
 * PIDOTS CONSOLE SPA - MOTOR DE SPOTLIGHT TOUR INTERATIVO
 * =====================================================================
 * Motor leve de guiamento visual (< 12KB) com mascara SVG dinamica,
 * caixa de recorte com pulsacao e popover tatico com posicionamento
 * trigonometrico automatico para prevencao de corte de tela.
 * ZERO EMOJIS // Vanilla JS Puro // Alta Performance ARM64
 * =====================================================================
 */

(function(window) {
    'use strict';

    const PiDotsTourEngine = (function() {
        'use strict';

        const STORAGE_KEY = 'pidots_tour_completed';
        const PADDING = 6; // Margem de respiro ao redor do elemento em foco (px)

        return {
            currentIndex: -1,
            isRunning: false,
            rafId: null,
            overlayEl: null,
            targetBoxEl: null,
            popoverEl: null,
            elementsBound: false,

            // -----------------------------------------------------------------
            // 1. DEFINIÇÃO DAS 5 ETAPAS CANÔNICAS DO CONSOLE PIDOTS
            // -----------------------------------------------------------------
            steps: [
                {
                    elementSelector: '.opendots-sidebar-layout, #leftSidebar',
                    title: 'ACTIVITY RAIL E COORDENACAO SPACES',
                    badge: '// NAVEGACAO & SPACES',
                    placement: 'right',
                    what: 'Trilho de atividades vertical de 48px com 5 contextos operacionais (Spaces, Dots, Tasks, Memoria e Configs) e diretorio de artefatos persistidos no SQLite WAL.',
                    how: 'Clique nos icones do trilho para chavear contextos ou selecione um Space para abrir arquivos, documentos e especificacoes na prancheta.',
                    tip: 'Use <kbd>Alt+1</kbd> a <kbd>Alt+5</kbd> para alternar os paineis contextuais ou <kbd>Ctrl+B</kbd> para recolher a barra lateral.',
                    beforeStep: function() {
                        const isMobile = window.innerWidth <= 768;
                        if (isMobile && typeof setMobileView === 'function') {
                            setMobileView('dots');
                        }
                        const shell = document.querySelector('.triptych-shell');
                        if (shell && shell.classList.contains('mode-focus-zen')) {
                            if (typeof toggleWorkspaceMode === 'function') toggleWorkspaceMode();
                        }
                        const sidebar = document.getElementById('leftSidebar');
                        if (sidebar && sidebar.classList.contains('collapsed')) {
                            if (typeof toggleSidebar === 'function') toggleSidebar();
                        }
                        if (typeof switchSidebarContext === 'function') {
                            switchSidebarContext('spaces');
                        }
                    }
                },
                {
                    elementSelector: '.ticker-input-bar, #instructionInput',
                    title: 'TELETIPO REACT E TERMINAL DE COMANDO',
                    badge: '// TELETIPO & COMANDOS',
                    placement: 'top',
                    what: 'Console conversacional de emissao de missoes com bobina continua matricial, Source Input Bar com indicador de canal e agente ativo, e caderno ReAct.',
                    how: 'Digite <kbd>/</kbd> ou clique no botao <kbd>/</kbd> para abrir o catalogo de comandos rapidos; digite <kbd>@</kbd> para convocar especialistas autonomos.',
                    tip: 'Pressione <kbd>Enter</kbd> para transmitir a instrucao, <kbd>Shift+Enter</kbd> para quebrar linha ou <kbd>Ctrl+L</kbd> para limpar a bobina de papel.',
                    beforeStep: function() {
                        const isMobile = window.innerWidth <= 768;
                        if (isMobile && typeof setMobileView === 'function') {
                            setMobileView('chat');
                        }
                        const input = document.getElementById('instructionInput');
                        if (input && !isMobile) {
                            try { input.focus(); } catch (e) {}
                        }
                    }
                },
                {
                    elementSelector: '#computerConsoleBanner, #rightCanvas',
                    title: 'COMPUTADOR DO DOT E SANDBOX BWRAP',
                    badge: '// ISOLAMENTO & SILICIO',
                    placement: 'bottom',
                    what: 'Ambiente de execucao local isolado por Linux Bubblewrap (bwrap) em /workspace, garantindo que o agente manipule arquivos sem risco ao no host.',
                    how: 'Inspecione o diretorio do Dot pelo banner superior e clique em <kbd>[Modo Observacao]</kbd> para assumir o controle interativo via terminal (Takeover).',
                    tip: 'O Sandbox roda em processo nativo ARM64 com restricao estrita de leitura/escrita e isolamento total de rede para operacoes nao autorizadas.',
                    beforeStep: function() {
                        const isMobile = window.innerWidth <= 768;
                        if (isMobile && typeof setMobileView === 'function') {
                            setMobileView('canvas');
                        }
                        const shell = document.querySelector('.triptych-shell');
                        if (shell && shell.classList.contains('mode-focus-zen')) {
                            if (typeof toggleWorkspaceMode === 'function') toggleWorkspaceMode();
                        }
                        const canvas = document.getElementById('rightCanvas');
                        if (canvas && canvas.classList.contains('collapsed')) {
                            if (typeof toggleCanvasSplit === 'function') toggleCanvasSplit();
                            else canvas.classList.remove('collapsed');
                        }
                        const tabTerminal = document.getElementById('canvasTabTerminal');
                        if (tabTerminal && typeof switchCanvasTab === 'function') {
                            switchCanvasTab('canvas-terminal', tabTerminal);
                        }
                    }
                },
                {
                    elementSelector: '.canvas-tab-bar, #rightCanvas',
                    title: 'LIVE CANVAS E AS 4 ABAS OPERACIONAIS',
                    badge: '// ARTEFATOS, COAGENTS & HITL',
                    placement: 'left',
                    what: 'Prancheta tecnica de alto rendimento organizada em 4 abas estritas: Artefato (Spaces e Diffs), CoAgents (Shared State), Terminal e Governanca HITL.',
                    how: 'Alterne entre as abas para verificar o estado compartilhado dos agentes, inspecionar logs de ferramentas ou aprovar acoes criticas na trava HITL.',
                    tip: 'Use <kbd>Alt+I</kbd> para focar no artefato ativo, <kbd>Alt+H</kbd> para abrir o dossie HITL ou <kbd>Ctrl+S</kbd> para gravar revisoes no banco WAL.',
                    beforeStep: function() {
                        const isMobile = window.innerWidth <= 768;
                        if (isMobile && typeof setMobileView === 'function') {
                            setMobileView('canvas');
                        }
                        const shell = document.querySelector('.triptych-shell');
                        if (shell && shell.classList.contains('mode-focus-zen')) {
                            if (typeof toggleWorkspaceMode === 'function') toggleWorkspaceMode();
                        }
                        const canvas = document.getElementById('rightCanvas');
                        if (canvas && canvas.classList.contains('collapsed')) {
                            if (typeof toggleCanvasSplit === 'function') toggleCanvasSplit();
                            else canvas.classList.remove('collapsed');
                        }
                        const tabArtifact = document.getElementById('canvasTabArtifact');
                        if (tabArtifact && typeof switchCanvasTab === 'function') {
                            switchCanvasTab('canvas-artifact', tabArtifact);
                        }
                    }
                },
                {
                    elementSelector: '#sidebarCtxConfigs, #sidebarHardwareFooter, #edgePulseSummaryBtn',
                    title: 'TELEMETRIA ARM64 E HOT-RELOAD DE IA',
                    badge: '// SILICIO & PROVEDORES',
                    placement: 'right',
                    what: 'Central de controle operacional de hardware e modelos. Permite atualizar chaves e endpoints de IA a quente sem reiniciar o no de borda.',
                    how: 'Monitore os graficos vetoriais em tempo real de RAM RSS (teto de 300MB) e temperatura do SoC, ajuste o provedor de IA e teste a conexao imediatamente.',
                    tip: 'Pressione <kbd>Alt+5</kbd> ou clique no rodape de telemetria ASCII para acessar o painel de configuracoes; pressione <kbd>F1</kbd> para o Manual Tecnico.',
                    beforeStep: function() {
                        const isMobile = window.innerWidth <= 768;
                        if (isMobile && typeof setMobileView === 'function') {
                            setMobileView('dots');
                        }
                        const shell = document.querySelector('.triptych-shell');
                        if (shell && shell.classList.contains('mode-focus-zen')) {
                            if (typeof toggleWorkspaceMode === 'function') toggleWorkspaceMode();
                        }
                        const sidebar = document.getElementById('leftSidebar');
                        if (sidebar && sidebar.classList.contains('collapsed')) {
                            if (typeof toggleSidebar === 'function') toggleSidebar();
                        }
                        if (typeof switchSidebarContext === 'function') {
                            switchSidebarContext('configs');
                        }
                    }
                }
            ],

            // -----------------------------------------------------------------
            // 2. INICIALIZAÇÃO DE ESTRUTURA E DOM
            // -----------------------------------------------------------------
            initDOM: function() {
                this.overlayEl = document.getElementById('pixelTourOverlay');
                this.targetBoxEl = document.getElementById('pixelTourTargetBox');
                this.popoverEl = document.getElementById('pixelTourPopover');
                this.stepIndicator = document.getElementById('pixelTourStepIndicator');
                this.stepBadge = document.getElementById('pixelTourStepBadge');
                this.titleEl = document.getElementById('pixelTourTitle');
                this.whatEl = document.getElementById('pixelTourWhatText');
                this.howEl = document.getElementById('pixelTourHowText');
                this.tipEl = document.getElementById('pixelTourTipText');
                this.btnNext = document.getElementById('pixelTourBtnNext');
                this.btnPrev = document.getElementById('pixelTourBtnPrev');
                this.btnSkip = document.getElementById('pixelTourBtnSkip');
                this.btnClose = document.getElementById('pixelTourBtnClose');
                this.btnFinish = document.getElementById('pixelTourBtnFinish');
                this.bindEvents();
            },

            bindEvents: function() {
                if (this.elementsBound) return;

                const self = this;
                if (this.btnNext) this.btnNext.addEventListener('click', function() { self.next(); });
                if (this.btnPrev) this.btnPrev.addEventListener('click', function() { self.prev(); });
                if (this.btnSkip) this.btnSkip.addEventListener('click', function() { self.exit(false); });
                if (this.btnClose) this.btnClose.addEventListener('click', function() { self.exit(false); });
                if (this.btnFinish) this.btnFinish.addEventListener('click', function() { self.exit(true); });

                // Atalhos de Teclado Operacionais
                window.addEventListener('keydown', function(e) {
                    if (!self.isRunning) return;

                    if (e.key === 'ArrowRight') {
                        e.preventDefault();
                        self.next();
                    } else if (e.key === 'ArrowLeft') {
                        e.preventDefault();
                        self.prev();
                    } else if (e.key === 'Escape') {
                        e.preventDefault();
                        self.exit(false);
                    } else if (e.key === 'Enter') {
                        e.preventDefault();
                        if (self.currentIndex === self.steps.length - 1) {
                            self.exit(true);
                        } else {
                            self.next();
                        }
                    }
                });

                // Suporte a Redimensionamento e Scroll com Debounce via requestAnimationFrame
                const handleReposition = function() {
                    if (!self.isRunning) return;
                    if (self.rafId) cancelAnimationFrame(self.rafId);
                    self.rafId = requestAnimationFrame(function() {
                        self.repositionActiveStep();
                    });
                };

                window.addEventListener('resize', handleReposition, { passive: true });
                window.addEventListener('scroll', handleReposition, { passive: true });

                this.elementsBound = true;
            },

            // -----------------------------------------------------------------
            // 3. API PÚBLICA DE EXECUÇÃO
            // -----------------------------------------------------------------
            start: function(stepIndex) {
                this.initDOM();
                if (!this.overlayEl || !this.popoverEl) return;

                // Fecha gaveta se estiver aberta para desobstruir tela
                if (typeof closeDrawer === 'function') closeDrawer();

                this.isRunning = true;
                this.overlayEl.classList.add('active');
                this.popoverEl.classList.add('active');
                this.goToStep(typeof stepIndex === 'number' ? stepIndex : 0);
            },

            next: function() {
                if (this.currentIndex < this.steps.length - 1) {
                    this.goToStep(this.currentIndex + 1);
                }
            },

            prev: function() {
                if (this.currentIndex > 0) {
                    this.goToStep(this.currentIndex - 1);
                }
            },

            goToStep: function(index) {
                if (index < 0 || index >= this.steps.length) return;
                this.currentIndex = index;

                const step = this.steps[index];

                // Executa rotina de preparação de layout prévia
                if (typeof step.beforeStep === 'function') {
                    try {
                        step.beforeStep();
                    } catch (err) {
                        console.warn('[PiDotsTourEngine] Erro no beforeStep:', err);
                    }
                }

                // Atualiza textos e rótulos com i18n dinâmico e fallback seguro
                const currentNum = String(index + 1).padStart(2, '0');
                const totalNum = String(this.steps.length).padStart(2, '0');
                const stepKey = `step${index + 1}`;

                const t = (k, fallback) => (window.PiDotsI18n && typeof window.PiDotsI18n.t === 'function' ? window.PiDotsI18n.t(k) : fallback);

                const stepPrefix = t('onboarding.step_counter_prefix', 'ETAPA');
                const title = t(`onboarding.${stepKey}.title`, step.title);
                const badge = t(`onboarding.${stepKey}.badge`, step.badge);
                const what = t(`onboarding.${stepKey}.what`, step.what);
                const how = t(`onboarding.${stepKey}.how`, step.how);
                const tip = t(`onboarding.${stepKey}.tip`, step.tip);

                if (this.stepIndicator) this.stepIndicator.textContent = `[${stepPrefix} ${currentNum}/${totalNum}]`;
                if (this.stepBadge) this.stepBadge.textContent = badge;
                if (this.titleEl) this.titleEl.textContent = title;
                if (this.whatEl) this.whatEl.innerHTML = what;
                if (this.howEl) this.howEl.innerHTML = how;
                if (this.tipEl) this.tipEl.innerHTML = tip;

                // Estado dos botões de controle com suporte a i18n
                if (this.btnSkip) this.btnSkip.textContent = t('onboarding.btn_skip', '[PULAR TOUR]');
                if (this.btnPrev) {
                    this.btnPrev.disabled = (index === 0);
                    this.btnPrev.textContent = t('onboarding.btn_prev', '[ANTERIOR]');
                }

                if (index === this.steps.length - 1) {
                    if (this.btnNext) this.btnNext.style.display = 'none';
                    if (this.btnFinish) {
                        this.btnFinish.style.display = 'inline-block';
                        this.btnFinish.textContent = t('onboarding.btn_finish', '[CONCLUIR TOUR]');
                    }
                } else {
                    if (this.btnNext) {
                        this.btnNext.style.display = 'inline-block';
                        this.btnNext.textContent = t('onboarding.btn_next', '[PROXIMO PASSO]');
                    }
                    if (this.btnFinish) this.btnFinish.style.display = 'none';
                }

                // Calcula coordenadas com micro-delay para acomodar mudanças no layout
                const self = this;
                setTimeout(function() {
                    self.repositionActiveStep();
                }, 60);
            },

            exit: function(completed) {
                this.isRunning = false;
                if (this.overlayEl) this.overlayEl.classList.remove('active');
                if (this.popoverEl) this.popoverEl.classList.remove('active');

                if (completed) {
                    localStorage.setItem(STORAGE_KEY, 'true');
                    const t = (k, fallback) => (window.PiDotsI18n && typeof window.PiDotsI18n.t === 'function' ? window.PiDotsI18n.t(k) : fallback);
                    const msg = t('onboarding.toast_completed', 'Tour operacional concluido com exito. Bom trabalho!');
                    if (window.PixelSystem && typeof window.PixelSystem.toast === 'function') {
                        window.PixelSystem.toast(msg, 'success');
                    }
                }
            },

            reset: function() {
                localStorage.removeItem(STORAGE_KEY);
                this.start(0);
            },

            // -----------------------------------------------------------------
            // 4. MOTOR MATEMÁTICO DE POSICIONAMENTO E DETECÇÃO DE BORDAS
            // -----------------------------------------------------------------
            repositionActiveStep: function() {
                if (!this.isRunning || this.currentIndex < 0) return;

                const step = this.steps[this.currentIndex];
                let targetEl = null;

                // Suporte a seletores múltiplos separados por vírgula (fallback resiliente)
                const selectors = step.elementSelector.split(',');
                for (let i = 0; i < selectors.length; i++) {
                    const found = document.querySelector(selectors[i].trim());
                    if (found && found.offsetParent !== null) {
                        targetEl = found;
                        break;
                    }
                }

                if (!targetEl) {
                    this.positionFallbackCenter();
                    return;
                }

                const vw = window.innerWidth;
                const vh = window.innerHeight;

                // Scroll preventivo para assegurar visibilidade do elemento alvo no desktop
                if (vw > 768 && typeof targetEl.scrollIntoView === 'function') {
                    try {
                        const targetRect = targetEl.getBoundingClientRect();
                        if (targetRect.top < 0 || targetRect.bottom > vh) {
                            targetEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                        }
                    } catch (e) {}
                }

                const rect = targetEl.getBoundingClientRect();

                // 4.1 Posiciona o Spotlight Target Box (orifício translúcido crisp)
                const boxTop = Math.max(0, rect.top - PADDING);
                const boxLeft = Math.max(0, rect.left - PADDING);
                const boxWidth = Math.min(vw - boxLeft, rect.width + (PADDING * 2));
                const boxHeight = Math.min(vh - boxTop, rect.height + (PADDING * 2));

                if (this.targetBoxEl) {
                    this.targetBoxEl.style.top = `${Math.round(boxTop)}px`;
                    this.targetBoxEl.style.left = `${Math.round(boxLeft)}px`;
                    this.targetBoxEl.style.width = `${Math.round(boxWidth)}px`;
                    this.targetBoxEl.style.height = `${Math.round(boxHeight)}px`;
                }

                // 4.2 Em telas móveis (< 768px), o popover fica ancorado como bottom-sheet via CSS
                if (vw <= 768) {
                    if (this.popoverEl) {
                        this.popoverEl.removeAttribute('data-placement');
                        this.popoverEl.style.top = '';
                        this.popoverEl.style.left = '';
                        if (rect.top > vh * 0.65) {
                            this.popoverEl.classList.add('popover-bottom-avoid');
                        } else {
                            this.popoverEl.classList.remove('popover-bottom-avoid');
                        }
                    }
                    return;
                }

                // 4.3 Posiciona o Balão Flutuante (Popover) com Flip Dinâmico
                let placement = step.placement || 'bottom';
                const popWidth = this.popoverEl ? (this.popoverEl.offsetWidth || 360) : 360;
                const popHeight = this.popoverEl ? (this.popoverEl.offsetHeight || 300) : 300;
                const GAP = 12; // Distância entre a caixa de foco e o popover (px)

                let top = 0;
                let left = 0;

                // Algoritmo de inversão (flip) em caso de colisão de borda
                if (placement === 'bottom' && (rect.bottom + GAP + popHeight > vh)) {
                    if (rect.top - GAP - popHeight > 0) placement = 'top';
                } else if (placement === 'top' && (rect.top - GAP - popHeight < 0)) {
                    if (rect.bottom + GAP + popHeight < vh) placement = 'bottom';
                } else if (placement === 'right' && (rect.right + GAP + popWidth > vw)) {
                    if (rect.left - GAP - popWidth > 0) placement = 'left';
                    else placement = 'bottom';
                } else if (placement === 'left' && (rect.left - GAP - popWidth < 0)) {
                    if (rect.right + GAP + popWidth < vw) placement = 'right';
                    else placement = 'bottom';
                }

                // Cálculo de coordenadas com base na orientação final
                switch (placement) {
                    case 'bottom':
                        top = rect.bottom + GAP;
                        left = rect.left + (rect.width / 2) - (popWidth / 2);
                        break;
                    case 'top':
                        top = rect.top - popHeight - GAP;
                        left = rect.left + (rect.width / 2) - (popWidth / 2);
                        break;
                    case 'right':
                        top = rect.top + (rect.height / 2) - (popHeight / 2);
                        left = rect.right + GAP;
                        break;
                    case 'left':
                        top = rect.top + (rect.height / 2) - (popHeight / 2);
                        left = rect.left - popWidth - GAP;
                        break;
                }

                // Restrição e Clamping Ortogonal Estrito aos limites da janela (Safe Zone)
                const MARGIN = 12;
                left = Math.max(MARGIN, Math.min(vw - popWidth - MARGIN, left));
                top = Math.max(MARGIN, Math.min(vh - popHeight - MARGIN, top));

                this.popoverEl.setAttribute('data-placement', placement);
                this.popoverEl.style.top = `${Math.round(top)}px`;
                this.popoverEl.style.left = `${Math.round(left)}px`;
            },

            positionFallbackCenter: function() {
                const vw = window.innerWidth;
                const vh = window.innerHeight;
                const popWidth = this.popoverEl ? (this.popoverEl.offsetWidth || 360) : 360;
                const popHeight = this.popoverEl ? (this.popoverEl.offsetHeight || 300) : 300;

                if (this.targetBoxEl) {
                    this.targetBoxEl.style.top = '0px';
                    this.targetBoxEl.style.left = '0px';
                    this.targetBoxEl.style.width = '0px';
                    this.targetBoxEl.style.height = '0px';
                }

                if (this.popoverEl) {
                    this.popoverEl.removeAttribute('data-placement');
                    this.popoverEl.style.top = `${Math.round((vh - popHeight) / 2)}px`;
                    this.popoverEl.style.left = `${Math.round((vw - popWidth) / 2)}px`;
                }
            }
        };
    })();

    // Exposição global para o console operacional
    window.PiDotsTourEngine = PiDotsTourEngine;
})(typeof window !== 'undefined' ? window : this);
