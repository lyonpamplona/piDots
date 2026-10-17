/**
 * PIXEL PAPER UI - MOTOR DE TRAVA DE ROLAGEM (SCROLL LOCK)
 * =====================================================================
 * Previne rolagem fantasma em segundo plano no iOS Safari, Android e
 * navegadores desktop durante a exibicao de modais, drawers e popovers.
 * Restaura fidedignamente o scroll original sem saltos de tela.
 * =====================================================================
 */

(function(window) {
    'use strict';

    const ScrollLockManager = {
        scrollYAnterior: 0,
        lockCount: 0,

        get estaBloqueado() {
            return this.lockCount > 0;
        },

        /**
         * Trava o corpo do documento na coordenada atual de rolagem.
         * Suporta chamadas aninhadas incrementando lockCount.
         */
        bloquear() {
            this.lockCount++;
            if (this.lockCount > 1) return;

            this.scrollYAnterior = window.scrollY || window.pageYOffset || document.documentElement.scrollTop || 0;
            document.body.style.position = 'fixed';
            document.body.style.top = `-${this.scrollYAnterior}px`;
            document.body.style.left = '0';
            document.body.style.right = '0';
            document.body.style.width = '100%';
            document.body.style.overflow = 'hidden';
            document.body.style.touchAction = 'none';
        },

        /**
         * Destrava o corpo do documento e opcionalmente restaura a coordenada original de rolagem.
         * Apenas remove os estilos quando lockCount atingir 0 (ou force=true).
         */
        desbloquear(force = false, restoreScroll = true) {
            if (this.lockCount === 0) return;

            if (force) {
                this.lockCount = 0;
            } else {
                this.lockCount = Math.max(0, this.lockCount - 1);
            }

            if (this.lockCount > 0) return;

            document.body.style.position = '';
            document.body.style.top = '';
            document.body.style.left = '';
            document.body.style.right = '';
            document.body.style.width = '';
            document.body.style.overflow = '';
            document.body.style.touchAction = '';

            if (restoreScroll) {
                window.scrollTo(0, this.scrollYAnterior);
            }
        },

        // Aliases para conformidade com APIs padrao
        lock() { this.bloquear(); },
        unlock(force = false, restoreScroll = true) { this.desbloquear(force, restoreScroll); }
    };

    window.ScrollLockManager = ScrollLockManager;
})(typeof window !== 'undefined' ? window : this);
