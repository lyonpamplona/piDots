/**
 * PIXEL PAPER UI - MOTOR CENTRAL DO SISTEMA VISUAL E ANALOGICO
 * =====================================================================
 * Fornece componentes 100% customizados para substituir alert(),
 * confirm(), prompt(), tooltips e context menu nativos do navegador.
 * Suporta Web Audio API para feedback haptico auditivo sutil.
 * ZERO EMOJIS // Vanilla JS Puro // Alta Performance ARM64
 * =====================================================================
 */

(function(window) {
    'use strict';

    /**
     * Sanitizador estrito de HTML para prevencao de XSS em templates literais.
     */
    function escapeHtml(str) {
        return String(str ?? '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    const PixelSystem = {
        dialogCallback: null,

        /**
         * Emite som de clique mecânico analógico usando Web Audio API.
         */
        playMechanicalClick(freq = 850, duration = 0.02) {
            try {
                const AudioCtx = window.AudioContext || window.webkitAudioContext;
                if (!AudioCtx) return;
                const ctx = new AudioCtx();
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();

                osc.type = 'square';
                osc.frequency.setValueAtTime(freq, ctx.currentTime);
                osc.frequency.exponentialRampToValueAtTime(120, ctx.currentTime + duration);

                gain.gain.setValueAtTime(0.04, ctx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);

                osc.connect(gain);
                gain.connect(ctx.destination);

                osc.start();
                osc.stop(ctx.currentTime + duration);
            } catch (err) {
                // Navegadores com politica estrita de autoplay silenciam sem erro critico
            }
        },

        /**
         * Emite uma tira de papel termico (Toast) com estilo de recibo teletipo.
         */
        toast(message, type = 'info', duration = 3800) {
            const container = document.getElementById('pixelToastContainer');
            if (!container) return;

            this.playMechanicalClick(950, 0.015);

            const toast = document.createElement('div');
            toast.className = `pixel-toast toast-${type}`;

            const tagTitles = {
                'info': 'SISTEMA // NOTIFICACAO',
                'success': 'SUCESSO // PERSISTENCIA',
                'warning': 'ALERTA // ATENCAO',
                'danger': 'GOVERNANCA // QUARENTENA'
            };

            const tagTitle = tagTitles[type] || 'MENSAGEM';
            const timeStr = new Date().toTimeString().split(' ')[0];

            toast.innerHTML = `
                <div class="toast-header">
                    <span class="toast-tag">${tagTitle}</span>
                    <span style="color: var(--ink-muted); font-size: 7px;">${timeStr}</span>
                    <button class="toast-close-btn" onclick="this.closest('.pixel-toast').remove()">[X]</button>
                </div>
                <div class="toast-body">${escapeHtml(message)}</div>
            `;

            container.appendChild(toast);

            if (duration > 0) {
                setTimeout(() => {
                    if (toast.parentNode) {
                        toast.style.opacity = '0';
                        toast.style.transform = 'translateX(20px)';
                        setTimeout(() => toast.remove(), 100);
                    }
                }, duration);
            }
        },

        /**
         * Caixa de Alerta Personalizada (Substitui alert nativo).
         */
        alert(title, message, onOk) {
            this.showDialog({
                title: `[ALERTA // ${title.toUpperCase()}]`,
                message: message,
                isPrompt: false,
                showCancel: false,
                confirmLabel: '[ENTENDIDO]',
                onConfirm: () => {
                    if (onOk) onOk();
                }
            });
        },

        /**
         * Caixa de Confirmacao Personalizada (Substitui confirm nativo).
         */
        confirm(title, message, onConfirm, onCancel) {
            this.showDialog({
                title: `[CONFIRMACAO // ${title.toUpperCase()}]`,
                message: message,
                isPrompt: false,
                showCancel: true,
                confirmLabel: '[CONFIRMAR COMANDO]',
                cancelLabel: '[CANCELAR]',
                onConfirm: () => {
                    if (onConfirm) onConfirm();
                },
                onCancel: () => {
                    if (onCancel) onCancel();
                }
            });
        },

        /**
         * Caixa de Insercao de Texto Personalizada (Substitui prompt nativo).
         */
        prompt(title, message, defaultValue = '', onConfirm, onCancel) {
            this.showDialog({
                title: `[ENTRADA // ${title.toUpperCase()}]`,
                message: message,
                isPrompt: true,
                defaultValue: defaultValue,
                showCancel: true,
                confirmLabel: '[CONCLUIR]',
                cancelLabel: '[CANCELAR]',
                onConfirm: (val) => {
                    if (onConfirm) onConfirm(val);
                },
                onCancel: () => {
                    if (onCancel) onCancel();
                }
            });
        },

        /**
         * Renderiza o dialogo mecanico centrado na tela.
         */
        showDialog(opts) {
            const backdrop = document.getElementById('pixelDialogBackdrop');
            const titleEl = document.getElementById('pixelDialogTitle');
            const msgEl = document.getElementById('pixelDialogMessage');
            const inputContainer = document.getElementById('pixelDialogInputContainer');
            const inputEl = document.getElementById('pixelDialogInput');
            const cancelBtn = document.getElementById('pixelDialogCancelBtn');
            const confirmBtn = document.getElementById('pixelDialogConfirmBtn');

            if (!backdrop || !titleEl || !msgEl || !confirmBtn) return;

            titleEl.textContent = opts.title || '[SISTEMA // PROTOCOLO]';
            msgEl.textContent = opts.message || '';
            confirmBtn.textContent = opts.confirmLabel || '[CONFIRMAR]';
            if (cancelBtn) {
                cancelBtn.textContent = opts.cancelLabel || '[CANCELAR]';
                cancelBtn.style.display = opts.showCancel ? 'inline-flex' : 'none';
            }

            if (opts.isPrompt && inputContainer && inputEl) {
                inputContainer.style.display = 'block';
                inputEl.value = opts.defaultValue || '';
                setTimeout(() => {
                    inputEl.focus();
                    inputEl.select();
                }, 50);
            } else if (inputContainer) {
                inputContainer.style.display = 'none';
                setTimeout(() => confirmBtn.focus(), 50);
            }

            this.dialogCallback = {
                onConfirm: opts.onConfirm,
                onCancel: opts.onCancel,
                isPrompt: opts.isPrompt
            };

            backdrop.classList.add('active');
            if (window.ScrollLockManager && typeof window.ScrollLockManager.bloquear === 'function') {
                window.ScrollLockManager.bloquear();
            }
        },

        confirmDialog() {
            const backdrop = document.getElementById('pixelDialogBackdrop');
            const inputEl = document.getElementById('pixelDialogInput');
            const cb = this.dialogCallback;

            if (backdrop) backdrop.classList.remove('active');
            if (window.ScrollLockManager && typeof window.ScrollLockManager.desbloquear === 'function') {
                window.ScrollLockManager.desbloquear();
            }

            if (cb && cb.onConfirm) {
                if (cb.isPrompt && inputEl) {
                    cb.onConfirm(inputEl.value.trim());
                } else {
                    cb.onConfirm();
                }
            }
            this.dialogCallback = null;
        },

        closeDialog(isConfirmed = false) {
            const backdrop = document.getElementById('pixelDialogBackdrop');
            const cb = this.dialogCallback;

            if (backdrop) backdrop.classList.remove('active');
            if (window.ScrollLockManager && typeof window.ScrollLockManager.desbloquear === 'function') {
                window.ScrollLockManager.desbloquear();
            }

            if (!isConfirmed && cb && cb.onCancel) {
                cb.onCancel();
            }
            this.dialogCallback = null;
        },

        /**
         * Menu de Contexto Customizado (Botao Direito).
         */
        openContextMenu(x, y) {
            const menu = document.getElementById('pixelContextMenu');
            if (!menu) return;

            const menuWidth = 250;
            const menuHeight = 220;
            const posX = (x + menuWidth > window.innerWidth) ? (window.innerWidth - menuWidth - 10) : x;
            const posY = (y + menuHeight > window.innerHeight) ? (window.innerHeight - menuHeight - 10) : y;

            menu.style.left = `${posX}px`;
            menu.style.top = `${posY}px`;
            menu.style.display = 'flex';
        },

        closeContextMenu() {
            const menu = document.getElementById('pixelContextMenu');
            if (menu) menu.style.display = 'none';
        },

        contextAction(act) {
            this.closeContextMenu();
            switch(act) {
                case 'inspect':
                    const canvas = document.getElementById('rightCanvas');
                    if (canvas) canvas.classList.remove('collapsed');
                    const tabs = document.querySelectorAll('.canvas-tab');
                    if (typeof window.switchCanvasTab === 'function' && tabs.length > 0) {
                        window.switchCanvasTab('canvas-artifact', tabs[0]);
                    }
                    this.toast('Live Canvas focado no artefato em edicao.', 'info');
                    break;
                case 'save':
                    if (typeof window.saveArtifactRevision === 'function') {
                        window.saveArtifactRevision();
                    }
                    break;
                case 'hitl':
                    if (typeof window.openHitlCanvas === 'function') {
                        window.openHitlCanvas();
                    }
                    this.toast('Dossie de governanca HITL carregado.', 'warning');
                    break;
                case 'split':
                    if (typeof window.toggleCanvasExpand === 'function') {
                        window.toggleCanvasExpand();
                    }
                    break;
                case 'clear':
                    if (typeof window.clearTickerStream === 'function') {
                        window.clearTickerStream();
                    }
                    this.toast('Bobina de teletipo reiniciada.', 'info');
                    break;
                case 'docs':
                    if (typeof window.toggleDrawer === 'function') {
                        window.toggleDrawer();
                    }
                    break;
                case 'tour':
                    if (window.PiDotsTourEngine) {
                        window.PiDotsTourEngine.start();
                    } else if (window.PiDotsUX && window.PiDotsUX.Onboarding) {
                        window.PiDotsUX.Onboarding.open();
                    }
                    break;
                case 'changelog':
                    if (window.PiDotsUX && window.PiDotsUX.PatchNotes) {
                        window.PiDotsUX.PatchNotes.open();
                    }
                    break;
            }
        },

        /**
         * Inicializador de Tooltips Flutuantes.
         */
        initTooltips() {
            const tooltipEl = document.getElementById('pixelTooltip');
            if (!tooltipEl) return;

            document.body.addEventListener('mouseover', (e) => {
                const target = e.target.closest('[data-tooltip]');
                if (target) {
                    const text = target.getAttribute('data-tooltip');
                    if (!text) return;
                    tooltipEl.textContent = text;
                    tooltipEl.style.display = 'block';

                    const rect = target.getBoundingClientRect();
                    const top = rect.bottom + 6;
                    let left = rect.left + (rect.width / 2) - 30;

                    if (left + 220 > window.innerWidth) left = window.innerWidth - 230;
                    if (left < 10) left = 10;

                    tooltipEl.style.top = `${top}px`;
                    tooltipEl.style.left = `${left}px`;
                }
            });

            document.body.addEventListener('mouseout', (e) => {
                const target = e.target.closest('[data-tooltip]');
                if (target) {
                    tooltipEl.style.display = 'none';
                }
            });
        }
    };

    window.escapeHtml = escapeHtml;
    window.PixelSystem = PixelSystem;
})(typeof window !== 'undefined' ? window : this);
