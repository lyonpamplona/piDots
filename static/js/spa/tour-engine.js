/**
 * PIDOTS CONSOLE SPA - MOTOR DE SPOTLIGHT TOUR INTERATIVO
 * =====================================================================
 * Motor leve de guiamento visual (< 12KB) com mascara SVG dinamica,
 * caixa de recorte com pulsacao e popover pixel paper com posicionamento
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
                    elementSelector: '#dotsListContainer, #leftSidebar',
                    title: 'SQUAD DE AGENTES COWORKERS',
                    badge: '// SQUAD DE COWORKERS',
                    placement: 'right',
                    what: 'Barra lateral de agentes autônomos persistentes (Supervisores, Especialistas e Workers) gerenciados via SQLite WAL.',
                    how: 'Clique no card de um Dot para alternar o especialista ativo e direcionar sua missão.',
                    tip: 'Pressione <kbd>Ctrl+B</kbd> para alternar a barra lateral ou use o comando slash <kbd>/dots</kbd>.',
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
                    }
                },
                {
                    elementSelector: '.ticker-input-bar, #instructionInput',
                    title: 'TERMINAL DE COMANDO E TELETIPO',
                    badge: '// TELETIPO & COMANDO',
                    placement: 'top',
                    what: 'Terminal de emissão de missões com bobina matricial contínua e caderno de raciocínio interno dos Dots.',
                    how: 'Digite <kbd>/</kbd> para abrir o catálogo de comandos rápidos ou <kbd>@</kbd> para chamar especialistas.',
                    tip: 'Pressione <kbd>Enter</kbd> para transmitir a instrução ou <kbd>Shift+Enter</kbd> para quebrar linha.',
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
                    elementSelector: '#btnToggleMode, .header-center-controls',
                    title: 'MODOS DE CONCENTRAÇÃO E SESSÃO',
                    badge: '// MODOS DE FOCO',
                    placement: 'bottom',
                    what: 'Comutador ergonômico para alternar entre visão dividida e concentração de fluxo contínuo.',
                    how: 'Alterne entre o Modo Criação 50/50 (com Live Canvas aberto) e o Modo Foco Zen centrado.',
                    tip: 'Clique em <kbd>[+ NOVA CONVERSA]</kbd> ou pressione <kbd>Ctrl+N</kbd> para abrir uma sessão limpa.',
                    beforeStep: function() {
                        window.scrollTo({ top: 0, behavior: 'instant' });
                    }
                },
                {
                    elementSelector: '#rightCanvas, #canvas-artifact',
                    title: 'LIVE CANVAS E FICHAS SPACES',
                    badge: '// LIVE CANVAS & DIFFS',
                    placement: 'left',
                    what: 'Prancheta técnica de visualização e edição em tempo real de código, documentos e especificações.',
                    how: 'Inspecione entregas, visualize alterações no botão <kbd>[DIFFS]</kbd> e grave versões no SQLite WAL.',
                    tip: 'Pressione <kbd>Alt+I</kbd> para inspecionar artefato ou <kbd>Ctrl+S</kbd> para gravar revisão no banco.',
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
                        const tabs = document.querySelectorAll('.canvas-tab');
                        if (tabs && tabs.length > 0 && typeof switchCanvasTab === 'function') {
                            switchCanvasTab('canvas-artifact', tabs[0]);
                        }
                    }
                },
                {
                    elementSelector: '#btn-system-drawer, #edgePulseSummaryBtn',
                    title: 'TELEMETRIA DE SILÍCIO E AJUDA',
                    badge: '// HARDWARE & MANUAL',
                    placement: 'bottom',
                    what: 'Central técnica com telemetria do nó ARM64 (temperatura, RAM, CPU), governança e manual operacional.',
                    how: 'Monitore o consumo físico do Raspberry Pi 4B e configure chaves de provedor de IA com segurança.',
                    tip: 'Pressione a tecla física <kbd>F1</kbd> a qualquer momento para abrir ou fechar a Gaveta Técnica.',
                    beforeStep: function() {
                        window.scrollTo({ top: 0, behavior: 'instant' });
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
                this.bindEvents();
            },

            bindEvents: function() {
                if (this.elementsBound) return;

                const self = this;
                const btnNext = document.getElementById('pixelTourBtnNext');
                const btnPrev = document.getElementById('pixelTourBtnPrev');
                const btnSkip = document.getElementById('pixelTourBtnSkip');
                const btnClose = document.getElementById('pixelTourBtnClose');
                const btnFinish = document.getElementById('pixelTourBtnFinish');

                if (btnNext) btnNext.addEventListener('click', function() { self.next(); });
                if (btnPrev) btnPrev.addEventListener('click', function() { self.prev(); });
                if (btnSkip) btnSkip.addEventListener('click', function() { self.exit(false); });
                if (btnClose) btnClose.addEventListener('click', function() { self.exit(false); });
                if (btnFinish) btnFinish.addEventListener('click', function() { self.exit(true); });

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

                // Atualiza textos e rótulos
                const currentNum = String(index + 1).padStart(2, '0');
                const totalNum = String(this.steps.length).padStart(2, '0');
                
                const stepIndicator = document.getElementById('pixelTourStepIndicator');
                const stepBadge = document.getElementById('pixelTourStepBadge');
                const titleEl = document.getElementById('pixelTourTitle');
                const whatEl = document.getElementById('pixelTourWhatText');
                const howEl = document.getElementById('pixelTourHowText');
                const tipEl = document.getElementById('pixelTourTipText');

                const t = (k, fallback) => (window.PiDotsI18n && typeof window.PiDotsI18n.t === 'function' ? window.PiDotsI18n.t(k) : fallback);

                if (stepIndicator) stepIndicator.textContent = `[ETAPA ${currentNum}/${totalNum}]`;
                if (stepBadge) stepBadge.textContent = step.badge;
                if (titleEl) titleEl.textContent = step.title;
                if (whatEl) whatEl.innerHTML = step.what;
                if (howEl) howEl.innerHTML = step.how;
                if (tipEl) tipEl.innerHTML = step.tip;

                // Estado dos botões de controle com suporte a i18n
                const btnPrev = document.getElementById('pixelTourBtnPrev');
                const btnNext = document.getElementById('pixelTourBtnNext');
                const btnFinish = document.getElementById('pixelTourBtnFinish');
                const btnSkip = document.getElementById('pixelTourBtnSkip');

                if (btnSkip) btnSkip.textContent = t('onboarding.btn_skip', '[PULAR TOUR]');
                if (btnPrev) {
                    btnPrev.disabled = (index === 0);
                    btnPrev.textContent = t('onboarding.btn_prev', '[ANTERIOR]');
                }

                if (index === this.steps.length - 1) {
                    if (btnNext) btnNext.style.display = 'none';
                    if (btnFinish) {
                        btnFinish.style.display = 'inline-block';
                        btnFinish.textContent = t('onboarding.btn_finish', '[CONCLUIR]');
                    }
                } else {
                    if (btnNext) {
                        btnNext.style.display = 'inline-block';
                        btnNext.textContent = t('onboarding.btn_next', '[PROXIMO PASSO]');
                    }
                    if (btnFinish) btnFinish.style.display = 'none';
                }

                // Calcula coordenadas com micro-delay para acomodar mudanças no layout
                const self = this;
                setTimeout(function() {
                    self.repositionActiveStep();
                }, 50);
            },

            exit: function(completed) {
                this.isRunning = false;
                if (this.overlayEl) this.overlayEl.classList.remove('active');
                if (this.popoverEl) this.popoverEl.classList.remove('active');

                if (completed) {
                    localStorage.setItem(STORAGE_KEY, 'true');
                    if (window.PixelSystem && typeof window.PixelSystem.toast === 'function') {
                        window.PixelSystem.toast('Tour operacional concluido com exito. Bom trabalho!', 'success');
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

                const rect = targetEl.getBoundingClientRect();
                const vw = window.innerWidth;
                const vh = window.innerHeight;

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
                    }
                    return;
                }

                // 4.3 Posiciona o Balão Flutuante (Popover) com Flip Dinâmico
                let placement = step.placement || 'bottom';
                const popWidth = this.popoverEl.offsetWidth || 360;
                const popHeight = this.popoverEl.offsetHeight || 300;
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

    window.PiDotsTourEngine = PiDotsTourEngine;
})(typeof window !== 'undefined' ? window : this);
