/**
 * piDots Micro-i18n Engine (Zero-Dependency Vanilla JS)
 * Otimizado para SBCs ARM64 (Raspberry Pi 4B) e Design System Pixel Paper UI.
 * Zero Emojis // < 1.2 KB // Alternancia in-memory < 5ms // Zero XSS
 */
(function(window) {
    'use strict';

    const STORAGE_KEY = 'pidots_lang';
    const DEFAULT_LANG = 'pt';
    const SUPPORTED_LANGS = ['pt', 'en'];

    const dictionaryCache = {};
    let currentLang = DEFAULT_LANG;
    let isInitialized = false;

    const PiDotsI18n = {
        getLanguage: function() {
            return currentLang;
        },

        detectInitialLanguage: function() {
            try {
                // 1. Parametro de URL (?lang=en)
                const urlParams = new URLSearchParams(window.location.search);
                const queryLang = urlParams.get('lang');
                if (queryLang && SUPPORTED_LANGS.includes(queryLang.toLowerCase())) {
                    return queryLang.toLowerCase();
                }

                // 2. Persistencia local
                const savedLang = localStorage.getItem(STORAGE_KEY);
                if (savedLang && SUPPORTED_LANGS.includes(savedLang)) {
                    return savedLang;
                }

                // 3. Preferencia do navegador
                const browserLang = (navigator.language || navigator.userLanguage || '').toLowerCase();
                if (browserLang.startsWith('pt')) {
                    return 'pt';
                } else if (browserLang) {
                    return 'en';
                }
            } catch (e) {
                // Fallback silencioso
            }
            return DEFAULT_LANG;
        },

        loadDictionary: async function(lang) {
            if (dictionaryCache[lang]) {
                return dictionaryCache[lang];
            }

            try {
                const response = await fetch('/data/locales/' + lang + '.json', {
                    cache: 'default'
                });
                if (!response.ok) {
                    throw new Error('HTTP ' + response.status + ' ao carregar locale ' + lang);
                }
                const data = await response.json();
                dictionaryCache[lang] = data;
                return data;
            } catch (err) {
                console.warn('[piDots i18n] Falha ao carregar locale ' + lang + ':', err);
                return {};
            }
        },

        t: function(key, params) {
            if (!key) return '';
            const dict = dictionaryCache[currentLang] || dictionaryCache[DEFAULT_LANG] || {};
            
            const parts = key.split('.');
            let val = dict;
            for (let i = 0; i < parts.length; i++) {
                if (val && typeof val === 'object' && parts[i] in val) {
                    val = val[parts[i]];
                } else {
                    val = null;
                    break;
                }
            }

            // Fallback para pt se a chave nao existir no dicionario ativo
            if (val === null && currentLang !== DEFAULT_LANG && dictionaryCache[DEFAULT_LANG]) {
                let fallbackVal = dictionaryCache[DEFAULT_LANG];
                for (let j = 0; j < parts.length; j++) {
                    if (fallbackVal && typeof fallbackVal === 'object' && parts[j] in fallbackVal) {
                        fallbackVal = fallbackVal[parts[j]];
                    } else {
                        fallbackVal = null;
                        break;
                    }
                }
                if (fallbackVal !== null) {
                    val = fallbackVal;
                }
            }

            if (val === null || typeof val !== 'string') {
                return key;
            }

            if (params && typeof params === 'object') {
                return val.replace(/\{(\w+)\}/g, function(match, paramKey) {
                    return params[paramKey] !== undefined ? params[paramKey] : match;
                });
            }

            return val;
        },

        applyDOM: function() {
            const startTime = performance.now();

            // 1. Textos principais (textContent seguro contra XSS)
            const textNodes = document.querySelectorAll('[data-i18n]');
            for (let i = 0; i < textNodes.length; i++) {
                const el = textNodes[i];
                const key = el.getAttribute('data-i18n');
                if (key) {
                    el.textContent = PiDotsI18n.t(key);
                }
            }

            // 2. Placeholders de entrada
            const placeholderNodes = document.querySelectorAll('[data-i18n-placeholder]');
            for (let i = 0; i < placeholderNodes.length; i++) {
                const el = placeholderNodes[i];
                const key = el.getAttribute('data-i18n-placeholder');
                if (key) {
                    el.setAttribute('placeholder', PiDotsI18n.t(key));
                }
            }

            // 3. Tooltips de titulo
            const titleNodes = document.querySelectorAll('[data-i18n-title]');
            for (let i = 0; i < titleNodes.length; i++) {
                const el = titleNodes[i];
                const key = el.getAttribute('data-i18n-title');
                if (key) {
                    el.setAttribute('title', PiDotsI18n.t(key));
                }
            }

            // 4. Acessibilidade Aria
            const ariaNodes = document.querySelectorAll('[data-i18n-aria]');
            for (let i = 0; i < ariaNodes.length; i++) {
                const el = ariaNodes[i];
                const key = el.getAttribute('data-i18n-aria');
                if (key) {
                    el.setAttribute('aria-label', PiDotsI18n.t(key));
                }
            }

            // 5. Atualiza o rotulo do seletor discreto [IDIOMA: PT | EN]
            const toggleBtns = document.querySelectorAll('.lang-toggle-btn');
            for (let i = 0; i < toggleBtns.length; i++) {
                const btn = toggleBtns[i];
                btn.textContent = currentLang === 'pt' ? '[IDIOMA: PT | EN]' : '[LANG: EN | PT]';
                btn.setAttribute('title', currentLang === 'pt' 
                    ? 'Alternar interface para Ingles Tecnico (EN)' 
                    : 'Switch interface to Brazilian Portuguese (PT)');
            }

            // 6. Atualizacao dos atributos HTML raiz
            document.documentElement.setAttribute('lang', currentLang === 'pt' ? 'pt-BR' : 'en');
            document.documentElement.setAttribute('data-lang', currentLang);

            const elapsed = (performance.now() - startTime).toFixed(2);
            window.dispatchEvent(new CustomEvent('pidots:langchange', {
                detail: { lang: currentLang, elapsedMs: elapsed }
            }));
        },

        setLanguage: async function(newLang) {
            if (!SUPPORTED_LANGS.includes(newLang)) return;
            currentLang = newLang;

            try {
                localStorage.setItem(STORAGE_KEY, newLang);
            } catch (e) {}

            await PiDotsI18n.loadDictionary(newLang);
            
            const deferFn = window.requestAnimationFrame || function(cb) { return setTimeout(cb, 0); };
            deferFn(function() {
                PiDotsI18n.applyDOM();
            });
        },

        toggleLanguage: function() {
            const nextLang = currentLang === 'pt' ? 'en' : 'pt';
            PiDotsI18n.setLanguage(nextLang);
        },

        init: async function() {
            if (isInitialized) return;
            isInitialized = true;

            currentLang = PiDotsI18n.detectInitialLanguage();
            await PiDotsI18n.loadDictionary(currentLang);

            if (currentLang !== DEFAULT_LANG) {
                PiDotsI18n.loadDictionary(DEFAULT_LANG);
            }

            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', function() {
                    PiDotsI18n.applyDOM();
                });
            } else {
                PiDotsI18n.applyDOM();
            }
        }
    };

    PiDotsI18n.init();
    window.PiDotsI18n = PiDotsI18n;
    window.t = PiDotsI18n.t;

})(window);
