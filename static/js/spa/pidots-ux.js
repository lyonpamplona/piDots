/**
 * PIDOTS CONSOLE SPA - CONTROLADOR DE EXPERIENCIA DO USUARIO (PIDOTSUX)
 * =====================================================================
 * Modulos de Onboarding (Ponte com PiDotsTourEngine), Patch Notes
 * (/api/changelog) e PWA (instalacao progressiva e prompt de tela cheia).
 * ZERO EMOJIS // Vanilla JS Puro // Alta Performance ARM64
 * =====================================================================
 */

(function(window) {
    'use strict';

    const PiDotsUX = (function() {
        // ---------------------------------------------------------------------
        // MODULO 1: ONBOARDING / GUIA DE PRIMEIRO ACESSO (SPOTLIGHT TOUR)
        // ---------------------------------------------------------------------
        const Onboarding = {
            STORAGE_KEY: 'pidots_tour_completed',

            init() {
                // Disparo automatico gerenciado via PiDotsTourEngine no DOMContentLoaded
            },

            open(step = 0) {
                if (window.PiDotsTourEngine) {
                    window.PiDotsTourEngine.start(step);
                }
            },

            close(skipped = false) {
                if (window.PiDotsTourEngine) {
                    window.PiDotsTourEngine.exit(skipped);
                }
            },

            finish() {
                if (window.PiDotsTourEngine) {
                    window.PiDotsTourEngine.exit(true);
                } else {
                    localStorage.setItem(this.STORAGE_KEY, 'true');
                }
            },

            goToStep(step) {
                if (window.PiDotsTourEngine) {
                    window.PiDotsTourEngine.goToStep(step);
                }
            },

            nextStep() {
                if (window.PiDotsTourEngine) {
                    window.PiDotsTourEngine.next();
                }
            },

            prevStep() {
                if (window.PiDotsTourEngine) {
                    window.PiDotsTourEngine.prev();
                }
            }
        };

        // ---------------------------------------------------------------------
        // MODULO 2: CHANGELOG E NOTAS DE ATUALIZACAO AUTOMATICA
        // ---------------------------------------------------------------------
        const PatchNotes = {
            STORAGE_KEY: 'pidots_last_seen_version',
            activeVersion: '1.5.3',
            dataCache: null,

            async init() {
                try {
                    const res = await fetch('/api/changelog');
                    if (!res.ok) return;
                    const data = await res.json();
                    this.dataCache = data;
                    this.activeVersion = data.current_version || '1.5.3';

                    const footerBtn = document.getElementById('btnFooterPatchNotes');
                    if (footerBtn) {
                        const span = footerBtn.querySelector('span');
                        if (span) span.textContent = `Notas da Versão (v${this.activeVersion})`;
                    }

                    const lastSeen = localStorage.getItem(this.STORAGE_KEY);
                    if (lastSeen !== this.activeVersion) {
                        const tourDone = localStorage.getItem('pidots_tour_completed') === 'true';
                        if (!tourDone) {
                            // Se o tour de iniciacao ainda nao foi concluido, nao sobrepoe a interface
                            return;
                        }
                        setTimeout(() => {
                            this.open();
                        }, 1200);
                    }
                } catch (err) {
                    console.warn('[piDots UX] Falha ao consultar endpoint de changelog:', err);
                }
            },

            open() {
                const modal = document.getElementById('pixelPatchNotesModal');
                if (!modal) return;

                if (this.dataCache && this.dataCache.patch_notes) {
                    const pn = this.dataCache.patch_notes;
                    const titleElem = document.getElementById('patchNotesTitle');
                    if (titleElem) {
                        if (window.PiDotsI18n && window.PiDotsI18n.getLanguage() === 'en' && window.t) {
                            titleElem.textContent = window.t('patch.title');
                        } else {
                            titleElem.textContent = pn.title || `NOTAS DE ATUALIZACAO - VERSAO ${this.activeVersion}`;
                        }
                    }

                    const buildElem = document.getElementById('patchNotesBuildTag');
                    if (buildElem && this.dataCache.build) buildElem.textContent = `BUILD: ${this.dataCache.build}`;

                    const commitElem = document.getElementById('patchNotesCommitTag');
                    if (commitElem && this.dataCache.commit_hash) commitElem.textContent = `COMMIT: ${this.dataCache.commit_hash}`;

                    const stampDate = document.getElementById('patchNotesStampDate');
                    if (stampDate && this.dataCache.release_date) stampDate.textContent = `${this.dataCache.release_date} // 04:00 UTC`;

                    const stampHash = document.getElementById('patchNotesStampHash');
                    if (stampHash && this.dataCache.commit_hash) stampHash.textContent = `SHA256: ${this.dataCache.commit_hash}`;

                    // Preenche listas categorizadas se fornecidas
                    const cats = pn.categories || {};
                    this._fillList('patchListIncluded', cats.included);
                    this._fillList('patchListAdjusted', cats.adjusted);
                    this._fillList('patchListRemoved', cats.removed);
                    this._fillList('patchListSecurity', cats.security_and_edge);
                }

                modal.style.display = 'flex';
            },

            _fillList(elementId, items) {
                const ul = document.getElementById(elementId);
                if (!ul || !items || !Array.isArray(items) || items.length === 0) return;
                ul.textContent = '';
                items.forEach((item) => {
                    const li = document.createElement('li');
                    const colonIdx = item.indexOf(':');
                    if (colonIdx > 0 && colonIdx < 60) {
                        const strong = document.createElement('strong');
                        strong.textContent = item.substring(0, colonIdx + 1);
                        li.appendChild(strong);
                        const textNode = document.createTextNode(item.substring(colonIdx + 1));
                        li.appendChild(textNode);
                    } else {
                        li.textContent = item;
                    }
                    ul.appendChild(li);
                });
            },

            dismiss() {
                this.acknowledge();
            },

            acknowledge() {
                localStorage.setItem(this.STORAGE_KEY, this.activeVersion);
                const modal = document.getElementById('pixelPatchNotesModal');
                if (modal) modal.style.display = 'none';
                if (window.PixelSystem && PixelSystem.toast) {
                    PixelSystem.toast(`Atualizacao v${this.activeVersion} reconhecida.`, 'info');
                }
            }
        };

        // ---------------------------------------------------------------------
        // MODULO 3: PWA & SERVICE WORKER CONTROLLER
        // ---------------------------------------------------------------------
        const PWA = {
            deferredInstallPrompt: null,
            newWorkerWaiting: null,

            init() {
                this.setupOfflineWatcher();
                this.registerServiceWorker();
                this.setupInstallPromptCapture();
                this.setupIOSInstallHint();
            },

            registerServiceWorker() {
                if (!('serviceWorker' in navigator)) return;

                window.addEventListener('load', () => {
                    navigator.serviceWorker.register('/sw.js')
                        .then((registration) => {
                            if (registration.waiting) {
                                this.newWorkerWaiting = registration.waiting;
                                this.showUpdateBanner();
                            }

                            registration.addEventListener('updatefound', () => {
                                const installingWorker = registration.installing;
                                if (!installingWorker) return;

                                installingWorker.addEventListener('statechange', () => {
                                    if (installingWorker.state === 'installed' && navigator.serviceWorker.controller) {
                                        this.newWorkerWaiting = installingWorker;
                                        this.showUpdateBanner();
                                    }
                                });
                            });
                        })
                        .catch((err) => {
                            console.warn('[piDots PWA] Falha no registro do Service Worker:', err);
                        });

                    let refreshing = false;
                    navigator.serviceWorker.addEventListener('controllerchange', () => {
                        if (!refreshing) {
                            refreshing = true;
                            window.location.reload();
                        }
                    });
                });
            },

            showUpdateBanner() {
                if (document.getElementById('pwaUpdateBanner')) return;

                const banner = document.createElement('div');
                banner.id = 'pwaUpdateBanner';
                banner.setAttribute('role', 'alert');
                banner.style.cssText = `
                    position: fixed;
                    bottom: calc(16px + env(safe-area-inset-bottom, 0px));
                    right: 16px;
                    z-index: 100015;
                    background: #11161d;
                    border: 2px solid #38bdf8;
                    box-shadow: 4px 4px 0px #000000;
                    padding: 10px 14px;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    font-family: 'JetBrains Mono', monospace;
                    font-size: 11px;
                    color: #f1f5f9;
                `;

                banner.innerHTML = `
                    <span style="display: inline-block; width: 8px; height: 8px; background: #38bdf8;"></span>
                    <span>NOVA VERSAO DO PIDOTS PRONTA</span>
                    <button id="pwaReloadBtn" class="pixel-btn btn-cyan" style="padding: 4px 8px; font-size: 9px;">[REINICIAR]</button>
                    <button id="pwaDismissBtn" class="pixel-btn" style="padding: 4px 6px; font-size: 9px;">[X]</button>
                `;

                document.body.appendChild(banner);

                document.getElementById('pwaReloadBtn').addEventListener('click', () => {
                    if (this.newWorkerWaiting) {
                        this.newWorkerWaiting.postMessage({ type: 'SKIP_WAITING' });
                    }
                });

                document.getElementById('pwaDismissBtn').addEventListener('click', () => {
                    banner.remove();
                });
            },

            setupInstallPromptCapture() {
                window.addEventListener('beforeinstallprompt', (e) => {
                    e.preventDefault();
                    this.deferredInstallPrompt = e;
                    this.showInstallUI();
                });

                window.addEventListener('appinstalled', () => {
                    this.deferredInstallPrompt = null;
                    this.hideInstallUI();
                    if (window.PixelSystem && PixelSystem.toast) {
                        PixelSystem.toast('piDots Edge Console instalado com sucesso!', 'success');
                    }
                });
            },

            showInstallUI() {
                const btn = document.getElementById('pixelPwaInstallBtn');
                if (btn) btn.style.display = 'inline-flex';

                const bannerDismissed = sessionStorage.getItem('pidots_pwa_banner_dismissed');
                const isStandalone = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;

                if (!bannerDismissed && !isStandalone) {
                    const banner = document.getElementById('pixelPwaInstallBanner');
                    if (banner) banner.style.display = 'flex';
                }
            },

            hideInstallUI() {
                const btn = document.getElementById('pixelPwaInstallBtn');
                if (btn) btn.style.display = 'none';

                const banner = document.getElementById('pixelPwaInstallBanner');
                if (banner) banner.style.display = 'none';
            },

            async install() {
                if (!this.deferredInstallPrompt) {
                    if (window.PixelSystem && PixelSystem.toast) {
                        PixelSystem.toast('Instalacao disponivel no menu do navegador ou ja instalada.', 'info');
                    }
                    return;
                }
                this.deferredInstallPrompt.prompt();
                const { outcome } = await this.deferredInstallPrompt.userChoice;
                if (outcome === 'accepted') {
                    console.log('[piDots PWA] Instalacao aceita pelo operador.');
                }
                this.deferredInstallPrompt = null;
                this.hideInstallUI();
            },

            dismissBanner() {
                const banner = document.getElementById('pixelPwaInstallBanner');
                if (banner) banner.style.display = 'none';
                sessionStorage.setItem('pidots_pwa_banner_dismissed', 'true');
            },

            setupIOSInstallHint() {
                const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
                const isStandalone = window.navigator.standalone === true;

                if (isIOS && !isStandalone) {
                    const btn = document.getElementById('pixelPwaInstallBtn');
                    if (btn) {
                        btn.style.display = 'inline-flex';
                        btn.onclick = () => {
                            alert('Instalacao no iOS Safari:\n1. Toque no botao Compartilhar (icone de quadrado com seta para cima)\n2. Selecione "Adicionar a Tela de Inicio"');
                        };
                    }
                }
            },

            setupOfflineWatcher() {
                function updateNetworkStatus() {
                    const isOnline = navigator.onLine;
                    let badge = document.getElementById('networkStatusBadge');
                    if (!badge) {
                        badge = document.createElement('div');
                        badge.id = 'networkStatusBadge';
                        badge.style.cssText = `
                            position: fixed;
                            top: calc(8px + env(safe-area-inset-top, 0px));
                            right: 16px;
                            z-index: 9999;
                            font-family: 'JetBrains Mono', monospace;
                            font-size: 10px;
                            padding: 3px 8px;
                            border: 1px solid #ffb830;
                            display: none;
                            background: #07090c;
                            color: #ffb830;
                        `;
                        document.body.appendChild(badge);
                    }

                    if (!isOnline) {
                        badge.style.display = 'block';
                        badge.textContent = '[MODO OFFLINE // CACHE LOCAL ATIVO]';
                    } else {
                        badge.style.display = 'none';
                    }
                }

                window.addEventListener('online', updateNetworkStatus);
                window.addEventListener('offline', updateNetworkStatus);
                updateNetworkStatus();
            }
        };

        return {
            Onboarding: Onboarding,
            PatchNotes: PatchNotes,
            PWA: PWA,
            init() {
                this.Onboarding.init();
                this.PatchNotes.init();
                this.PWA.init();
            }
        };
    })();

    window.PiDotsUX = PiDotsUX;
})(typeof window !== 'undefined' ? window : this);
