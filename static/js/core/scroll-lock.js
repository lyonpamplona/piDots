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
        estaBloqueado: false,

        /**
         * Trava o corpo do documento na coordenada atual de rolagem.
         */
        bloquear() {
            if (this.estaBloqueado) return;
            this.scrollYAnterior = window.scrollY || window.pageYOffset || document.documentElement.scrollTop || 0;
            document.body.style.position = 'fixed';
            document.body.style.top = `-${this.scrollYAnterior}px`;
            document.body.style.left = '0';
            document.body.style.right = '0';
            document.body.style.width = '100%';
            document.body.style.overflow = 'hidden';
            this.estaBloqueado = true;
        },

        /**
         * Destrava o corpo do documento e restaura a coordenada original de rolagem.
         */
        desbloquear() {
            if (!this.estaBloqueado) return;
            document.body.style.position = '';
            document.body.style.top = '';
            document.body.style.left = '';
            document.body.style.right = '';
            document.body.style.width = '';
            document.body.style.overflow = '';
            window.scrollTo(0, this.scrollYAnterior);
            this.estaBloqueado = false;
        },

        // Aliases para conformidade com APIs padrao
        lock() { this.bloquear(); },
        unlock() { this.desbloquear(); }
    };

    window.ScrollLockManager = ScrollLockManager;
})(typeof window !== 'undefined' ? window : this);
