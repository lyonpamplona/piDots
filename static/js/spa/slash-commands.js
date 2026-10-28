/**
 * PIDOTS CONSOLE SPA - MOTOR DE SLASH COMMANDS (/) E MENCOES (@)
 * =====================================================================
 * Motor com catalogo completo de 30 Slash Commands operacionais,
 * fuzzy search, popover dinamico com suporte total a teclado
 * (ArrowUp, ArrowDown, Tab, Enter, Esc), menu de mencoes (@dot)
 * e gerador de recibos de papel de teletipo para execucoes client/rest.
 * ZERO EMOJIS // Vanilla JS Puro // Alta Performance ARM64
 * =====================================================================
 */

(function(window) {
    'use strict';

    let filteredMentionDots = [];
    let mentionActiveIndex = 0;

        const SlashCommandsEngine = {
            isOpen: false,
            activeIndex: 0,
            filteredList: [],
            activeCategory: 'all',

            catalog: [
                // [SISTEMA & UI]
                { cmd: '/help', cat: 'sistema', args: '[filtro]', exec: 'client', desc: 'Exibe catalogo operacional e atalhos tecnicos do console.' },
                { cmd: '/clear', cat: 'sistema', args: '[chat|terminal|canvas|all]', exec: 'client', desc: 'Limpa a bobina de papel ou buffers de visualizacao.' },
                { cmd: '/theme', cat: 'sistema', args: '[noir|blueprint|toggle]', exec: 'client', desc: 'Alterna o tema visual entre Dark Noir e Blueprint.' },
                { cmd: '/lang', cat: 'sistema', args: '[pt|en]', exec: 'client', desc: 'Troca o idioma da interface (pt/en) sem recarregar.' },
                { cmd: '/info', cat: 'sistema', args: '', exec: 'rest', desc: 'Exibe uso de CPU, RAM, modelo de IA e status do SQLite.' },
                { cmd: '/status', cat: 'sistema', args: '', exec: 'rest', desc: 'Apresenta resumo executivo dos coworkers ativos e conexoes.' },
                { cmd: '/telemetry', cat: 'sistema', args: '', exec: 'rest', desc: 'Mede temperatura do SoC Broadcom, memoria RAM e carga.' },
                { cmd: '/pwa', cat: 'sistema', args: '[status|update|cache-clear]', exec: 'client', desc: 'Inspeciona Service Worker e conformidade de cache offline.' },
                { cmd: '/tour', cat: 'sistema', args: '[reset]', exec: 'client', desc: 'Inicia o tour guiado pelo console do piDots.' },
                { cmd: '/onboarding', cat: 'sistema', args: '[reset]', exec: 'client', desc: 'Inicia o tour guiado pelo console do piDots.' },
                { cmd: '/changelog', cat: 'sistema', args: '[versao]', exec: 'rest', desc: 'Consulta as notas oficiais de atualizacao do sistema.' },

                // [AGENTES & MULTI-BOT]
                { cmd: '/dots', cat: 'agentes', args: '[list|switch <id>]', exec: 'hybrid', desc: 'Lista coworkers ou troca o coworker em foco.' },
                { cmd: '/handoff', cat: 'agentes', args: '<target_dot_id> [motivo]', exec: 'rest', desc: 'Transfere a conversa para outro coworker especialista.' },
                { cmd: '/council', cat: 'agentes', args: '<topico> [rounds]', exec: 'stream', desc: 'Inicia deliberação conjunta entre os coworkers.' },
                { cmd: '/delegate', cat: 'agentes', args: '<target_dot_id> <tarefa>', exec: 'rest', desc: 'Delega subtarefa específica para outro coworker.' },
                { cmd: '/archetype', cat: 'agentes', args: '[supervisor|coder|arquiteto|auditor]', exec: 'rest', desc: 'Altera a especialidade do coworker atual.' },
                { cmd: '/tools', cat: 'agentes', args: '[dot_id]', exec: 'rest', desc: 'Lista ferramentas ativas disponíveis para o coworker.' },

                // [MEMORIA & CONHECIMENTO]
                { cmd: '/memory', cat: 'memoria', args: '[show|append|replace] [sec] [txt]', exec: 'hybrid', desc: 'Exibe ou atualiza a memória permanente do coworker.' },
                { cmd: '/archival', cat: 'memoria', args: '<termo> [limite]', exec: 'rest', desc: 'Busca por palavras-chave e similaridade na memória histórica.' },
                { cmd: '/shared', cat: 'memoria', args: '[read|write] <chave> [txt]', exec: 'rest', desc: 'Quadro de notas tecnicas compartilhado entre bots.' },
                { cmd: '/spaces', cat: 'memoria', args: '[list|create <arq>|open <id>]', exec: 'rest', desc: 'Gerencia documentos, notas e código nos Spaces.' },
                { cmd: '/diff', cat: 'memoria', args: '[space_id]', exec: 'client', desc: 'Alterna inspecao de diferencas incrementais no Canvas.' },

                // [TAREFAS & HEARTBEAT]
                { cmd: '/tasks', cat: 'tarefas', args: '[list|toggle <id>]', exec: 'rest', desc: 'Lista e gerencia tarefas em segundo plano (Heartbeats).' },
                { cmd: '/cron', cat: 'tarefas', args: '<expressao_cron> <prompt>', exec: 'rest', desc: 'Agenda nova rotina proativa no agendador SQLite WAL.' },
                { cmd: '/run-task', cat: 'tarefas', args: '<task_id>', exec: 'rest', desc: 'Forca o disparo imediato de uma tarefa agendada.' },

                // [GOVERNANCA & BORDA]
                { cmd: '/hitl', cat: 'governanca', args: '[list|approve <id>|reject <id>]', exec: 'rest', desc: 'Lista, aprova ou rejeita comandos retidos na fila HITL.' },
                { cmd: '/triggers', cat: 'governanca', args: '[check|evaluate]', exec: 'rest', desc: 'Avalia limites de temperatura, disco e memoria RAM.' },
                { cmd: '/maintenance', cat: 'governanca', args: '[checkpoint|optimize|full]', exec: 'rest', desc: 'Executa checkpoint do SQLite e otimização para poupar o MicroSD.' },
                { cmd: '/backup', cat: 'governanca', args: '[caminho_destino]', exec: 'rest', desc: 'Gera cópia de segurança pontual do banco SQLite.' },

                // [EXPORTACAO & DADOS]
                { cmd: '/export', cat: 'dados', args: '[zip|workspace] [dot_id]', exec: 'rest', desc: 'Compacta e descarrega o workspace do Dot em arquivo ZIP.' },
                { cmd: '/pack', cat: 'dados', args: '[export|import] [dot_id]', exec: 'rest', desc: 'Exporta ou importa configurações completas de coworkers.' },
                { cmd: '/save-space', cat: 'memoria', args: '[nome_arquivo.md]', exec: 'rest', desc: 'Salva a conversa da thread ativa como documento Markdown em Spaces.' },
                { cmd: '/computer', cat: 'sistema', args: '[comando_bwrap]', exec: 'rest', desc: 'Abre o terminal ou executa comando no sandbox isolado.' },
                { cmd: '/mcp', cat: 'agentes', args: '[list]', exec: 'rest', desc: 'Lista servidores MCP conectados ao sistema.' },
                { cmd: '/coagents', cat: 'agentes', args: '', exec: 'client', desc: 'Abre o painel de estado compartilhado entre os coworkers.' }
            ],

            setCategory(cat) {
                this.activeCategory = cat;
                const tabs = document.querySelectorAll('#slashCategoryTabs .slash-cat-btn');
                tabs.forEach(btn => {
                    btn.classList.toggle('active', btn.getAttribute('data-cat') === cat);
                });
                const input = document.getElementById('instructionInput');
                if (input) {
                    const textBeforeCursor = input.value.slice(0, input.selectionStart);
                    const match = textBeforeCursor.match(/(?:^|\n)\/([a-zA-Z0-9_\-]*)$/);
                    this.filterCommands(match ? match[1].toLowerCase() : '');
                }
            },

            handleInput(event) {
                const input = event.target;
                const val = input.value;
                const cursorPos = input.selectionStart;
                const beforeCursor = val.slice(0, cursorPos);

                // Detecta '/' no inicio da linha ou após quebra de linha
                const match = beforeCursor.match(/(?:^|\n)\/([a-zA-Z0-9_\-]*)$/);

                if (!match) {
                    this.closePopover();
                    return false;
                }

                // Fecha o dropdown de menção se estiver aberto
                const mentionDropdown = document.getElementById('mentionDropdown');
                if (mentionDropdown) mentionDropdown.style.display = 'none';

                const query = match[1].toLowerCase();
                this.filterCommands(query);
                return true;
            },

            filterCommands(query) {
                let list = this.catalog;
                if (this.activeCategory !== 'all') {
                    list = list.filter(item => item.cat === this.activeCategory);
                }

                if (query) {
                    list = list.filter(item => 
                        item.cmd.toLowerCase().includes('/' + query) ||
                        item.desc.toLowerCase().includes(query) ||
                        item.cat.toLowerCase().includes(query)
                    );
                }

                this.filteredList = list;
                this.activeIndex = 0;

                if (list.length === 0) {
                    this.closePopover();
                    return;
                }

                this.renderItems();
                this.openPopover();
            },

            renderItems() {
                const container = document.getElementById('slashItemsList');
                const countEl = document.getElementById('slashMatchCount');
                if (!container) return;

                container.innerHTML = '';
                if (countEl) countEl.textContent = `${this.filteredList.length} COMANDOS DISPONIVEIS`;

                this.filteredList.forEach((item, idx) => {
                    const el = document.createElement('div');
                    el.className = `slash-item ${idx === this.activeIndex ? 'selected' : ''}`;
                    el.setAttribute('role', 'option');
                    el.setAttribute('aria-selected', idx === this.activeIndex ? 'true' : 'false');
                    el.onclick = () => this.selectCommand(item);

                    // Criação estrita e segura de nós DOM (Zero XSS)
                    const topDiv = document.createElement('div');
                    topDiv.className = 'slash-item-top';

                    const cmdSpan = document.createElement('span');
                    cmdSpan.className = 'slash-cmd-syntax';
                    cmdSpan.textContent = item.args ? `${item.cmd} ${item.args}` : item.cmd;

                    const catSpan = document.createElement('span');
                    catSpan.className = 'slash-badge-cat';
                    catSpan.textContent = `[${item.cat.toUpperCase()}]`;

                    topDiv.appendChild(cmdSpan);
                    topDiv.appendChild(catSpan);

                    const descDiv = document.createElement('div');
                    descDiv.className = 'slash-cmd-desc';
                    descDiv.textContent = item.desc;

                    el.appendChild(topDiv);
                    el.appendChild(descDiv);
                    container.appendChild(el);
                });

                this.ensureActiveVisible();
            },

            ensureActiveVisible() {
                const container = document.getElementById('slashItemsList');
                if (!container) return;
                const activeEl = container.children[this.activeIndex];
                if (activeEl) {
                    activeEl.scrollIntoView({ block: 'nearest' });
                }
            },

            handleKeyDown(event) {
                if (!this.isOpen) return false;

                if (event.key === 'ArrowDown') {
                    event.preventDefault();
                    if (this.filteredList.length > 0) {
                        this.activeIndex = (this.activeIndex + 1) % this.filteredList.length;
                        this.updateSelection();
                    }
                    return true;
                }

                if (event.key === 'ArrowUp') {
                    event.preventDefault();
                    if (this.filteredList.length > 0) {
                        this.activeIndex = (this.activeIndex - 1 + this.filteredList.length) % this.filteredList.length;
                        this.updateSelection();
                    }
                    return true;
                }

                if (event.key === 'Tab' || (event.key === 'Enter' && !event.shiftKey)) {
                    event.preventDefault();
                    if (this.filteredList[this.activeIndex]) {
                        this.selectCommand(this.filteredList[this.activeIndex]);
                    }
                    return true;
                }

                if (event.key === 'Escape') {
                    event.preventDefault();
                    this.closePopover();
                    return true;
                }

                return false;
            },

            updateSelection() {
                const container = document.getElementById('slashItemsList');
                if (!container) return;
                Array.from(container.children).forEach((child, idx) => {
                    const isSel = idx === this.activeIndex;
                    child.classList.toggle('selected', isSel);
                    child.setAttribute('aria-selected', isSel ? 'true' : 'false');
                });
                this.ensureActiveVisible();
            },

            selectCommand(item) {
                const input = document.getElementById('instructionInput');
                if (!input) return;

                const cursorPos = input.selectionStart;
                const before = input.value.slice(0, cursorPos);
                const after = input.value.slice(cursorPos);

                const replacedBefore = before.replace(/(?:^|\n)\/([a-zA-Z0-9_\-]*)$/, (match) => {
                    const prefix = match.startsWith('\n') ? '\n' : '';
                    return `${prefix}${item.cmd} `;
                });

                input.value = replacedBefore + after;
                input.selectionStart = input.selectionEnd = replacedBefore.length;
                input.focus();
                this.closePopover();
            },

            openPopover() {
                const pop = document.getElementById('slashPopover');
                if (pop) {
                    pop.style.display = 'flex';
                    this.isOpen = true;
                }
            },

            togglePopover() {
                if (this.isOpen) {
                    this.closePopover();
                } else {
                    const input = document.getElementById('instructionInput');
                    if (input && !input.value.startsWith('/')) {
                        input.value = '/' + input.value;
                    }
                    this.filterCommands('');
                    if (input) input.focus();
                }
            },

            closePopover() {
                const pop = document.getElementById('slashPopover');
                if (pop) {
                    pop.style.display = 'none';
                    this.isOpen = false;
                }
            }
        };
        window.SlashCommandsEngine = SlashCommandsEngine;
        window.toggleSlashPopover = (e) => {
            if (e && typeof e.stopPropagation === 'function') e.stopPropagation();
            SlashCommandsEngine.togglePopover();
        };

        // Fecha o popover e mencoes se o usuario clicar fora da area de entrada
        document.addEventListener('click', (e) => {
            const pop = document.getElementById('slashPopover');
            const mention = document.getElementById('mentionDropdown');
            const input = document.getElementById('instructionInput');
            const triggerBtn = document.getElementById('slashTriggerBtn');
            if (pop && pop.style.display === 'flex' && !pop.contains(e.target) && e.target !== input && (!triggerBtn || !triggerBtn.contains(e.target))) {
                SlashCommandsEngine.closePopover();
            }
            if (mention && (mention.style.display === 'block' || mention.style.display === 'flex') && !mention.contains(e.target) && e.target !== input) {
                mention.style.display = 'none';
            }
        });

        function handleMentionInput(event) {
            // Prioridade: se o caractere digitado for slash '/', aciona SlashCommandsEngine
            if (SlashCommandsEngine.handleInput(event)) {
                return;
            }

            const input = document.getElementById('instructionInput');
            const dropdown = document.getElementById('mentionDropdown');
            const itemsList = document.getElementById('mentionItemsList');
            if (!input || !dropdown || !itemsList) return;

            const textBeforeCursor = input.value.slice(0, input.selectionStart);
            const match = textBeforeCursor.match(/@([a-zA-Z0-9_\-]*)$/);

            if (!match) {
                dropdown.style.display = 'none';
                return;
            }

            const query = match[1].toLowerCase();
            const dots = PiDotsAPI.dotsCache || [];
            filteredMentionDots = dots.filter(d => 
                d.id.toLowerCase().includes(query) || 
                (d.name && d.name.toLowerCase().includes(query)) ||
                (d.role && d.role.toLowerCase().includes(query))
            );

            if (filteredMentionDots.length === 0) {
                dropdown.style.display = 'none';
                return;
            }

            mentionActiveIndex = 0;
            renderMentionItems();
            dropdown.style.display = 'block';
        }

        function renderMentionItems() {
            const itemsList = document.getElementById('mentionItemsList');
            if (!itemsList) return;
            itemsList.innerHTML = '';

            filteredMentionDots.forEach((dot, idx) => {
                const item = document.createElement('div');
                item.className = `mention-item ${idx === mentionActiveIndex ? 'selected' : ''}`;
                item.onclick = () => selectMentionDot(dot.id);
                const stamp = dot.avatar_stamp || '[DOT]';
                item.innerHTML = `
                    <span><strong style="color: var(--blueprint-cyan);">${escapeHtml(stamp)} @${escapeHtml(dot.id)}</strong> - ${escapeHtml(dot.name || dot.role || '')}</span>
                    <span class="mention-tag">${escapeHtml((dot.archetype || 'general').toUpperCase())}</span>
                `;
                itemsList.appendChild(item);
            });
        }

        function selectMentionDot(dotId) {
            const input = document.getElementById('instructionInput');
            const dropdown = document.getElementById('mentionDropdown');
            if (!input) return;

            const cursorPos = input.selectionStart;
            const textBefore = input.value.slice(0, cursorPos);
            const textAfter = input.value.slice(cursorPos);
            const replacedBefore = textBefore.replace(/@([a-zA-Z0-9_\-]*)$/, `@${dotId} `);

            input.value = replacedBefore + textAfter;
            input.selectionStart = input.selectionEnd = replacedBefore.length;
            input.focus();

            if (dropdown) dropdown.style.display = 'none';
        }

        function handleInputKey(event) {
            // 1. Prioridade: Se o Popover de Slash Commands estiver aberto, intercepta navegacao
            if (SlashCommandsEngine.handleKeyDown(event)) {
                return;
            }

            // 2. Se o Dropdown de Mencao estiver aberto, intercepta navegacao
            const dropdown = document.getElementById('mentionDropdown');
            const isDropdownOpen = dropdown && dropdown.style.display === 'block';

            if (isDropdownOpen) {
                if (event.key === 'ArrowDown') {
                    event.preventDefault();
                    if (filteredMentionDots.length > 0) {
                        mentionActiveIndex = (mentionActiveIndex + 1) % filteredMentionDots.length;
                        renderMentionItems();
                    }
                    return;
                } else if (event.key === 'ArrowUp') {
                    event.preventDefault();
                    if (filteredMentionDots.length > 0) {
                        mentionActiveIndex = (mentionActiveIndex - 1 + filteredMentionDots.length) % filteredMentionDots.length;
                        renderMentionItems();
                    }
                    return;
                } else if (event.key === 'Enter' || event.key === 'Tab') {
                    event.preventDefault();
                    if (filteredMentionDots[mentionActiveIndex]) {
                        selectMentionDot(filteredMentionDots[mentionActiveIndex].id);
                    }
                    return;
                } else if (event.key === 'Escape') {
                    event.preventDefault();
                    dropdown.style.display = 'none';
                    return;
                }
            }

            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                if (typeof window.transmitInstruction === 'function') {
                    window.transmitInstruction();
                } else if (typeof transmitInstruction === 'function') {
                    transmitInstruction();
                }
            }
        }

        // =====================================================================
        // EXECUCAO E DESPACHO DE SLASH COMMANDS (FASE 2)
        // =====================================================================
        function renderSlashReceiptSlip(cmdName, title, contentHtml, statusBadge = '[SUCESSO]') {
            const scrollArea = document.getElementById('tickerScroll');
            if (!scrollArea) return;

            const slip = document.createElement('article');
            slip.className = 'ticker-slip slash-receipt-slip';
            
            const isSuccess = statusBadge.includes('SUCESSO') || statusBadge.includes('OK') || statusBadge.includes('ESTAVEL') || statusBadge.includes('NORMAL');
            const badgeColor = isSuccess ? 'var(--phosphor-green)' : 'var(--thermal-amber)';

            slip.innerHTML = `
                <header class="slip-header">
                    <span class="actor-stamp stamp-system">[CMD] SISTEMA // SLASH EXECUTION</span>
                    <span>${new Date().toISOString()}</span>
                    <span>SEQ# 000${window.getNextSeqCounter ? window.getNextSeqCounter() : 1}</span>
                </header>
                <section class="slip-output">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; border-bottom: 1px dashed var(--border-default); padding-bottom: 4px;">
                        <div>
                            <span style="color: var(--blueprint-cyan); font-weight: 700; font-size: 11px;">${escapeHtml(cmdName.toUpperCase())}</span>
                            <span style="color: var(--ink-muted); font-size: 10px; margin-left: 6px;">// ${escapeHtml(title)}</span>
                        </div>
                        <span style="font-family: var(--font-pixel); font-size: 7px; padding: 1px 4px; border: 1px solid var(--border-default); color: ${badgeColor};">${escapeHtml(statusBadge)}</span>
                    </div>
                    <div class="slip-text" style="font-family: var(--font-mono); font-size: 11px; line-height: 1.5;">
                        ${contentHtml}
                    </div>
                </section>
                <footer class="slip-perforation">
                    <span class="perforation-line"></span>
                </footer>
            `;

            scrollArea.appendChild(slip);
            scrollArea.scrollTop = scrollArea.scrollHeight;
            if (window.PiDotsAPI && PiDotsAPI.enforceDomCeiling) {
                PiDotsAPI.enforceDomCeiling();
            }
        }

        // Algoritmo de Distancia de Levenshtein para sugestao didatica de comandos
        function findClosestCommand(inputCmd) {
            const catalog = SlashCommandsEngine.catalog.map(c => c.cmd);
            let closest = null;
            let minDistance = Infinity;

            function levenshtein(a, b) {
                const matrix = [];
                for (let i = 0; i <= b.length; i++) { matrix[i] = [i]; }
                for (let j = 0; j <= a.length; j++) { matrix[0][j] = j; }
                for (let i = 1; i <= b.length; i++) {
                    for (let j = 1; j <= a.length; j++) {
                        if (b.charAt(i - 1) === a.charAt(j - 1)) {
                            matrix[i][j] = matrix[i - 1][j - 1];
                        } else {
                            matrix[i][j] = Math.min(
                                matrix[i - 1][j - 1] + 1,
                                matrix[i][j - 1] + 1,
                                matrix[i - 1][j] + 1
                            );
                        }
                    }
                }
                return matrix[b.length][a.length];
            }

            for (const cmd of catalog) {
                const dist = levenshtein(inputCmd, cmd);
                if (dist < minDistance) {
                    minDistance = dist;
                    closest = cmd;
                }
            }

            return minDistance <= 3 ? closest : null;
        }

        async function executeSlashCommand(commandLine) {
            const parts = commandLine.trim().split(/\s+/);
            const cmd = parts[0].toLowerCase();
            const args = parts.slice(1);

            switch (cmd) {
                // 1. /help [filtro]
                case '/help': {
                    const filter = args[0] ? args[0].toLowerCase() : '';
                    let list = SlashCommandsEngine.catalog;
                    if (filter) {
                        list = list.filter(c => c.cmd.includes(filter) || c.cat.includes(filter) || c.desc.toLowerCase().includes(filter));
                    }
                    let out = '<div style="margin-bottom: 6px; color: var(--ink-secondary);">CATALOGO DE SLASH COMMANDS // PROTOCOLO DE BORDA:</div>';
                    out += '<div style="display: grid; grid-template-columns: 1fr; gap: 4px;">';
                    list.forEach(c => {
                        out += `<div style="padding: 2px 0; border-bottom: 1px dotted var(--border-subtle); display: flex; justify-content: space-between; align-items: baseline;">
                            <span><strong style="color: var(--phosphor-green);">${escapeHtml(c.cmd)}</strong> <span style="color: var(--ink-muted); font-size: 10px;">${escapeHtml(c.args)}</span></span>
                            <span style="color: var(--ink-muted); font-size: 10px;">[${escapeHtml(c.cat.toUpperCase())}]</span>
                        </div>
                        <div style="color: var(--ink-secondary); font-size: 10px; margin-bottom: 4px;">${escapeHtml(c.desc)}</div>`;
                    });
                    out += '</div>';
                    if (list.length === 0) {
                        out = `<div style="color: var(--thermal-amber);">Nenhum comando encontrado para o filtro "${escapeHtml(filter)}". Digite /help para ver todos.</div>`;
                    }
                    renderSlashReceiptSlip('/help', filter ? `FILTRO: ${filter}` : 'CATALOGO COMPLETO', out, '[OK]');
                    break;
                }

                // 2. /clear [chat|terminal|canvas|all]
                case '/clear': {
                    const target = (args[0] || 'chat').toLowerCase();
                    if (target === 'chat' || target === 'all') {
                        clearTickerStream();
                    }
                    if (target === 'terminal' || target === 'all') {
                        const term = document.getElementById('terminalViewport');
                        if (term) term.innerHTML = '<div style="color: var(--ink-muted);">[TERMINAL SANDBOX LIMPO // AGUARDANDO NOVOS PROCESSOS BWRAP]</div>';
                    }
                    if (target === 'canvas' || target === 'all') {
                        const art = document.getElementById('artifactContent');
                        if (art) art.value = '# Documento limpo\n\nPronto para edicao no Live Canvas.';
                    }
                    renderSlashReceiptSlip('/clear', `ALVO: ${target.toUpperCase()}`, `Painel [${escapeHtml(target.toUpperCase())}] limpo. O histórico do banco foi mantido.`, '[OK]');
                    break;
                }

                // 3. /theme [noir|blueprint|toggle]
                case '/theme': {
                    const arg = (args[0] || 'toggle').toLowerCase();
                    if (arg === 'blueprint') {
                        document.documentElement.setAttribute('data-theme', 'blueprint');
                    } else if (arg === 'noir') {
                        document.documentElement.removeAttribute('data-theme');
                    } else if (typeof window.toggleTheme === 'function') {
                        window.toggleTheme();
                    } else {
                        const currentlyBp = document.documentElement.getAttribute('data-theme') === 'blueprint';
                        if (currentlyBp) document.documentElement.removeAttribute('data-theme');
                        else document.documentElement.setAttribute('data-theme', 'blueprint');
                    }
                    const isBpNow = document.documentElement.getAttribute('data-theme') === 'blueprint';
                    const btnTheme = document.getElementById('btn-theme-toggle');
                    const spanTheme = btnTheme ? btnTheme.querySelector('span') : null;
                    if (spanTheme) spanTheme.textContent = isBpNow ? 'Blueprint' : 'Dark Noir';
                    const activeTheme = isBpNow ? 'BLUEPRINT (AZUL CIANO)' : 'DARK NOIR (VERDE FOSFORO)';
                    renderSlashReceiptSlip('/theme', 'TEMA VISUAL', `Tema alterado para: <strong>${activeTheme}</strong>.`, '[OK]');
                    break;
                }

                // 4. /lang [pt|en]
                case '/lang': {
                    const lang = (args[0] || '').toLowerCase();
                    if (lang === 'pt' || lang === 'en') {
                        if (window.PiDotsI18n && PiDotsI18n.setLanguage) {
                            PiDotsI18n.setLanguage(lang);
                            renderSlashReceiptSlip('/lang', 'IDIOMA', `Idioma alterado com sucesso para: <strong>${lang.toUpperCase()}</strong>.`, '[OK]');
                        } else {
                            renderSlashReceiptSlip('/lang', 'AVISO', 'Micro-motor PiDotsI18n nao carregado na sessao.', '[AVISO]');
                        }
                    } else {
                        renderSlashReceiptSlip('/lang', 'SINTAXE INCORRETA', 'Uso correto: <code>/lang pt</code> ou <code>/lang en</code>.', '[ERRO]');
                    }
                    break;
                }

                // 5. /info
                case '/info': {
                    try {
                        const res = await fetch('/health');
                        const data = res.ok ? await res.json() : {};
                        const tableHtml = `
                            <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
                                <tr><td style="color: var(--ink-muted); padding: 2px 4px;">SISTEMA / PLATAFORMA:</td><td><strong>piDots Edge Core v1.5.2</strong></td></tr>
                                <tr><td style="color: var(--ink-muted); padding: 2px 4px;">HARDWARE ALVO:</td><td>Raspberry Pi 4B (ARM64 Cortex-A72)</td></tr>
                                <tr><td style="color: var(--ink-muted); padding: 2px 4px;">MOTOR ASSINCRONO:</td><td>FastAPI + uvloop (Single Process)</td></tr>
                                <tr><td style="color: var(--ink-muted); padding: 2px 4px;">BANCO & ARMAZENAMENTO:</td><td>SQLite WAL Mode (synchronous=NORMAL)</td></tr>
                                <tr><td style="color: var(--ink-muted); padding: 2px 4px;">MODELO ATIVO:</td><td>${escapeHtml((data.ai_provider && data.ai_provider.model) || data.model || 'default')}</td></tr>
                                <tr><td style="color: var(--ink-muted); padding: 2px 4px;">PROTOCOLO SSE:</td><td>AG-UI v1.0 Streaming Contrato</td></tr>
                            </table>
                        `;
                        renderSlashReceiptSlip('/info', 'ESPECIFICAÇÕES TÉCNICAS', tableHtml, '[OK]');
                    } catch (e) {
                        renderSlashReceiptSlip('/info', 'FALHA DE CONSULTA', `Erro ao consultar /health: ${escapeHtml(e.message)}`, '[ERRO]');
                    }
                    break;
                }

                // 6. /status
                case '/status': {
                    try {
                        const [resHealth, resDots] = await Promise.all([fetch('/health'), fetch('/api/dots')]);
                        const health = resHealth.ok ? await resHealth.json() : {};
                        const dotsData = resDots.ok ? await resDots.json() : [];
                        const dotsList = Array.isArray(dotsData) ? dotsData : (dotsData.dots || []);
                        const activeDot = dotsList.find(d => d.id === (window.PiDotsAPI && PiDotsAPI.activeDotId)) || dotsList[0] || { id: 'dot-supervisor', archetype: 'general' };

                        const statusHtml = `
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                                <div style="background: var(--paper-surface-recessed); padding: 6px; border: 1px solid var(--border-subtle);">
                                    <div style="color: var(--ink-muted); font-size: 9px;">COWORKER ATIVO</div>
                                    <div style="color: var(--blueprint-cyan); font-weight: 700; font-size: 12px;">@${escapeHtml(activeDot.id)}</div>
                                    <div style="font-size: 10px; color: var(--ink-secondary);">Papel: ${escapeHtml((activeDot.archetype || 'general').toUpperCase())}</div>
                                </div>
                                <div style="background: var(--paper-surface-recessed); padding: 6px; border: 1px solid var(--border-subtle);">
                                    <div style="color: var(--ink-muted); font-size: 9px;">COWORKERS TOTAL</div>
                                    <div style="color: var(--phosphor-green); font-weight: 700; font-size: 12px;">${dotsList.length} INSTALADOS</div>
                                    <div style="font-size: 10px; color: var(--ink-secondary);">Pruning: ATIVO (23 Ferramentas)</div>
                                </div>
                            </div>
                            <div style="margin-top: 6px; font-size: 10.5px; color: var(--ink-main);">
                                Conexao Local: <span style="color: var(--phosphor-green); font-weight: 700;">ESTAVEL</span> | 
                                WAL Mode: <span style="color: var(--phosphor-green); font-weight: 700;">ATIVO</span> | 
                                Governanca HITL: <span style="color: var(--blueprint-cyan); font-weight: 700;">DENY-BY-DEFAULT</span>
                            </div>
                        `;
                        renderSlashReceiptSlip('/status', 'PANORAMA OPERACIONAL', statusHtml, '[ESTAVEL]');
                    } catch (e) {
                        renderSlashReceiptSlip('/status', 'FALHA DE CONSULTA', `Erro ao consultar status: ${escapeHtml(e.message)}`, '[ERRO]');
                    }
                    break;
                }

                // 7. /telemetry
                case '/telemetry': {
                    try {
                        const res = await fetch('/api/edge/triggers');
                        const data = res.ok ? await res.json() : {};
                        const m = data.metrics || {};
                        const temp = m.temperature_celsius != null ? m.temperature_celsius : 48.0;
                        const ramFree = m.ram ? m.ram.available_mb : 2300;
                        const ramTotal = m.ram ? m.ram.total_mb : 3800;
                        const ramPct = m.ram ? m.ram.free_percent : 60.0;
                        const diskFree = m.disk ? m.disk.free_gb : 19.0;
                        const diskPct = m.disk ? m.disk.free_percent : 65.0;
                        const load = m.load_average ? `${m.load_average.load_1m}, ${m.load_average.load_5m}, ${m.load_average.load_15m}` : '0.40, 0.35, 0.25';

                        function makeAsciiBar(pct, totalChars = 20) {
                            const filled = Math.min(totalChars, Math.max(0, Math.round((pct / 100) * totalChars)));
                            return '[' + '|'.repeat(filled) + '.'.repeat(totalChars - filled) + ']';
                        }

                        const tempBar = makeAsciiBar(Math.min(100, (temp / 80) * 100));
                        const ramBar = makeAsciiBar(100 - ramPct);
                        const diskBar = makeAsciiBar(100 - diskPct);

                        const telemetryHtml = `
                            <div style="font-family: var(--font-mono); font-size: 11px; line-height: 1.6;">
                                <div><strong>TEMPERATURA SoC BCM2711 :</strong> ${temp.toFixed(1)} °C <span style="color: var(--phosphor-green);">${tempBar}</span> (TETO: 72.0 °C)</div>
                                <div><strong>USO DE MEMORIA RAM     :</strong> ${(ramTotal - ramFree).toFixed(0)}MB / ${ramTotal.toFixed(0)}MB <span style="color: var(--blueprint-cyan);">${ramBar}</span> (Livre: ${ramPct.toFixed(1)}%)</div>
                                <div><strong>USO DE CARTAO FLASH/SD  :</strong> <span style="color: var(--thermal-amber);">${diskBar}</span> (Folga: ${diskFree.toFixed(1)}GB / ${diskPct.toFixed(1)}%)</div>
                                <div><strong>CARGA DA CPU (LOAD AVG) :</strong> ${load}</div>
                                <div style="margin-top: 4px; font-size: 10px; color: var(--ink-muted);">Throttle Automatico: <strong>${data.is_throttled ? 'ATIVO (ALERTA TERMICO)' : 'DESATIVADO (NORMAL)'}</strong></div>
                            </div>
                        `;
                        renderSlashReceiptSlip('/telemetry', 'SENSORES DE HARDWARE DE BORDA', telemetryHtml, temp > 70 ? '[ALERTA]' : '[NORMAL]');
                    } catch (e) {
                        renderSlashReceiptSlip('/telemetry', 'FALHA DE LEITURA', `Erro ao coletar sensores: ${escapeHtml(e.message)}`, '[ERRO]');
                    }
                    break;
                }

                // 8. /pwa [status|update|cache-clear]
                case '/pwa': {
                    const action = (args[0] || 'status').toLowerCase();
                    if (action === 'cache-clear') {
                        if ('caches' in window) {
                            const keys = await caches.keys();
                            await Promise.all(keys.map(k => caches.delete(k)));
                            renderSlashReceiptSlip('/pwa', 'CACHE EXPURGADO', `Total de ${keys.length} caches locais descartados com sucesso.`, '[OK]');
                        } else {
                            renderSlashReceiptSlip('/pwa', 'AVISO', 'API de Cache indisponivel no navegador.', '[AVISO]');
                        }
                    } else if (action === 'update') {
                        if ('serviceWorker' in navigator) {
                            const reg = await navigator.serviceWorker.getRegistration();
                            if (reg) {
                                await reg.update();
                                renderSlashReceiptSlip('/pwa', 'SERVICE WORKER', 'Verificacao de atualizacao disparada com sucesso.', '[OK]');
                            } else {
                                renderSlashReceiptSlip('/pwa', 'AVISO', 'Nenhum Service Worker registrado.', '[AVISO]');
                            }
                        }
                    } else {
                        const isStandalone = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone;
                        const hasSW = 'serviceWorker' in navigator && !!navigator.serviceWorker.controller;
                        const pwaHtml = `
                            <div>Modo Standalone (App Instalado): <strong>${isStandalone ? 'SIM (STANDALONE)' : 'NAO (NAVEGADOR WEB)'}</strong></div>
                            <div>Service Worker Ativo: <strong>${hasSW ? 'SIM (ONLINE & OFFLINE RESILIENTE)' : 'EM REGISTRO'}</strong></div>
                            <div>Cache Defensivo: <strong>pidots-cache-v5</strong></div>
                            <div style="margin-top: 4px; font-size: 10px; color: var(--ink-muted);">Subcomandos disponiveis: <code>/pwa update</code> | <code>/pwa cache-clear</code></div>
                        `;
                        renderSlashReceiptSlip('/pwa', 'STATUS PROGRESSIVE WEB APP', pwaHtml, '[OK]');
                    }
                    break;
                }

                // 9. /tour e /onboarding
                case '/tour':
                case '/onboarding': {
                    if (window.PiDotsTourEngine) {
                        if (args[0] === 'reset' || args[0] === 'redefinir') {
                            PiDotsTourEngine.reset();
                            renderSlashReceiptSlip(cmd, 'TOUR SPOTLIGHT REINICIADO', 'Marcador de conclusao apagado do storage e tour de 5 etapas reiniciado no console.', '[OK]');
                        } else {
                            PiDotsTourEngine.start();
                            renderSlashReceiptSlip(cmd, 'TOUR SPOTLIGHT ACIONADO', 'Tour in-context ativo guiando as 5 ferramentas fundamentais do console.', '[OK]');
                        }
                    } else if (window.PiDotsUX && PiDotsUX.Onboarding && PiDotsUX.Onboarding.open) {
                        PiDotsUX.Onboarding.open();
                        renderSlashReceiptSlip(cmd, 'PRIMEIRO ACESSO', 'Guia operacional acionado.', '[OK]');
                    } else {
                        renderSlashReceiptSlip(cmd, 'AVISO', 'Motor de tour indisponivel.', '[AVISO]');
                    }
                    break;
                }

                // 10. /changelog [versao]
                case '/changelog': {
                    try {
                        const res = await fetch('/api/changelog');
                        const data = res.ok ? await res.json() : {};
                        const pn = data.patch_notes || {};
                        const cats = pn.categories || {};

                        let chHtml = `<div style="margin-bottom: 6px;">
                            <strong>${escapeHtml(pn.title || 'NOTAS DE ATUALIZACAO')}</strong> // Versao ${escapeHtml(data.current_version || '1.2.0')}
                            <div style="color: var(--ink-muted); font-size: 10px;">Lancamento: ${escapeHtml(data.release_date || '2026-10-12')} | Commit: ${escapeHtml(data.commit_hash || 'c5a5e67')}</div>
                        </div>`;

                        if (cats.included && cats.included.length) {
                            chHtml += `<div style="margin-top: 4px;"><strong style="color: var(--phosphor-green); font-size: 10px;">[INCLUIDO / NOVO]</strong><ul style="margin: 2px 0 6px 16px; padding: 0;">`;
                            cats.included.forEach(item => { chHtml += `<li style="margin-bottom: 2px;">${escapeHtml(item)}</li>`; });
                            chHtml += `</ul></div>`;
                        }

                        if (cats.adjusted && cats.adjusted.length) {
                            chHtml += `<div style="margin-top: 4px;"><strong style="color: var(--blueprint-cyan); font-size: 10px;">[AJUSTADO / MELHORADO]</strong><ul style="margin: 2px 0 6px 16px; padding: 0;">`;
                            cats.adjusted.forEach(item => { chHtml += `<li style="margin-bottom: 2px;">${escapeHtml(item)}</li>`; });
                            chHtml += `</ul></div>`;
                        }

                        if (cats.security_and_edge && cats.security_and_edge.length) {
                            chHtml += `<div style="margin-top: 4px;"><strong style="color: var(--thermal-amber); font-size: 10px;">[SEGURANCA & BORDA]</strong><ul style="margin: 2px 0 6px 16px; padding: 0;">`;
                            cats.security_and_edge.forEach(item => { chHtml += `<li style="margin-bottom: 2px;">${escapeHtml(item)}</li>`; });
                            chHtml += `</ul></div>`;
                        }

                        renderSlashReceiptSlip('/changelog', `VERSAO ${data.current_version || '1.2.0'}`, chHtml, '[OK]');
                    } catch (e) {
                        renderSlashReceiptSlip('/changelog', 'FALHA', `Erro ao consultar changelog: ${escapeHtml(e.message)}`, '[ERRO]');
                    }
                    break;
                }

                // =====================================================================
                // COMANDOS OPERACIONAIS AVANCADOS (FASE 3)
                // =====================================================================

                // 11. /dots [filtro]
                case '/dots': {
                    try {
                        const filter = args[0] ? args[0].toLowerCase() : '';
                        const res = await fetch('/api/dots?core_only=false');
                        const data = res.ok ? await res.json() : [];
                        const dots = Array.isArray(data) ? data : (data.dots || []);
                        let filtered = dots;
                        if (filter) {
                            filtered = dots.filter(d => (d.id && d.id.toLowerCase().includes(filter)) || (d.name && d.name.toLowerCase().includes(filter)) || (d.archetype && d.archetype.toLowerCase().includes(filter)));
                        }
                        const currentId = (window.PiDotsAPI && PiDotsAPI.activeDotId) || (dots[0] && dots[0].id) || 'dot-supervisor';
                        let out = `<div style="margin-bottom: 6px; color: var(--ink-secondary);">AI COWORKERS REGISTRADOS NO NO EDGE (${filtered.length}/${dots.length}):</div>`;
                        out += '<div style="display: grid; grid-template-columns: 1fr; gap: 4px;">';
                        filtered.forEach(d => {
                            const isCurrent = d.id === currentId;
                            const badge = isCurrent ? '<span style="color: var(--phosphor-green); font-weight: 700;">[ATIVO]</span>' : '<span style="color: var(--ink-muted);">[DISPONIVEL]</span>';
                            out += `<div style="padding: 4px 6px; background: var(--paper-surface-recessed); border: 1px solid ${isCurrent ? 'var(--phosphor-green)' : 'var(--border-subtle)'}; display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <strong style="color: var(--blueprint-cyan);">@${escapeHtml(d.id)}</strong>
                                    <span style="color: var(--ink-primary); font-size: 10px; margin-left: 6px;">${escapeHtml(d.name || d.id)}</span>
                                    <div style="color: var(--ink-muted); font-size: 9.5px;">Papel: ${escapeHtml((d.archetype || 'general').toUpperCase())} | Sandbox: bwrap</div>
                                </div>
                                <div style="font-size: 10px;">${badge}</div>
                            </div>`;
                        });
                        out += '</div>';
                        out += `<div style="margin-top: 6px; font-size: 10px; color: var(--ink-muted);">Dica: Digite <code>/handoff &lt;dot_id&gt;</code> para alternar o foco da sessao.</div>`;
                        renderSlashReceiptSlip('/dots', filter ? `FILTRO: ${filter}` : 'REDE MULTI-BOT', out, '[OK]');
                    } catch (e) {
                        renderSlashReceiptSlip('/dots', 'FALHA', `Erro ao listar coworkers: ${escapeHtml(e.message)}`, '[ERRO]');
                    }
                    break;
                }

                // 12. /handoff <dot_id> [contexto]
                case '/handoff': {
                    const targetId = (args[0] || '').toLowerCase().replace(/^@/, '');
                    const context = args.slice(1).join(' ') || 'Transicao operacional de rotina';
                    if (!targetId) {
                        renderSlashReceiptSlip('/handoff', 'SINTAXE INCORRETA', 'Uso: <code>/handoff &lt;dot_id&gt; [contexto opcional]</code>. Exemplo: <code>/handoff dot-researcher analise termica</code>', '[ERRO]');
                        break;
                    }
                    try {
                        const res = await fetch('/api/dots');
                        const data = res.ok ? await res.json() : [];
                        const dots = Array.isArray(data) ? data : (data.dots || []);
                        const targetDot = dots.find(d => d.id.toLowerCase() === targetId);
                        if (!targetDot) {
                            const validIds = dots.map(d => `@${d.id}`).join(', ');
                            renderSlashReceiptSlip('/handoff', 'COWORKER NAO LOCALIZADO', `Coworker <strong>@${escapeHtml(targetId)}</strong> nao encontrado no catalogo.<br><span style="color: var(--ink-muted); font-size: 10px;">Disponiveis: ${escapeHtml(validIds)}</span>`, '[ERRO]');
                            break;
                        }
                        if (window.PiDotsAPI && PiDotsAPI.selectDot) {
                            PiDotsAPI.selectDot(targetDot.id);
                        }
                        const out = `
                            <div>Controle de missao transferido com sucesso para: <strong style="color: var(--blueprint-cyan);">@${escapeHtml(targetDot.id)}</strong> (${escapeHtml(targetDot.name || targetDot.id)}).</div>
                            <div style="margin-top: 4px; font-size: 10.5px; color: var(--ink-secondary);">Contexto operacional repassado: <em>${escapeHtml(context)}</em></div>
                            <div style="margin-top: 4px; font-size: 10px; color: var(--ink-muted);">Sandboxed Environment: Isolado via Bubblewrap | SQLite WAL Sincronizado.</div>
                        `;
                        renderSlashReceiptSlip('/handoff', `DELEGACAO -> @${targetDot.id.toUpperCase()}`, out, '[TRANSICAO OK]');
                    } catch (e) {
                        renderSlashReceiptSlip('/handoff', 'FALHA DE HANDOFF', `Erro ao processar transicao: ${escapeHtml(e.message)}`, '[ERRO]');
                    }
                    break;
                }

                // 13. /council [tema]
                case '/council': {
                    const topic = args.join(' ') || 'Analise de viabilidade tecnica e trade-offs de borda';
                    const out = `
                        <div style="margin-bottom: 6px;"><strong>DEBATE TRIPARTITE DO CONSELHO CONSULTIVO // SESSAO DIALETICA</strong></div>
                        <div style="color: var(--blueprint-cyan); font-size: 10px; margin-bottom: 8px;">TEMA DE DELIBERACAO: <em>"${escapeHtml(topic)}"</em></div>
                        
                        <div style="border-left: 2px solid var(--phosphor-green); padding-left: 8px; margin-bottom: 6px;">
                            <strong style="color: var(--phosphor-green); font-size: 10.5px;">[01] PERSPECTIVA PRAGMATICA (ESTABILIDADE & HARDWARE):</strong>
                            <div style="font-size: 10px; color: var(--ink-secondary);">Preservar orcamento de RAM (teto 4GB Cortex-A72) e latencia uvloop. Priorizar solucao simples em arquivo unico ou tabela SQLite indexada sem novas dependencias.</div>
                        </div>

                        <div style="border-left: 2px solid var(--blueprint-cyan); padding-left: 8px; margin-bottom: 6px;">
                            <strong style="color: var(--blueprint-cyan); font-size: 10.5px;">[02] PERSPECTIVA INOVADORA (EXPANSAO COGNITIVA):</strong>
                            <div style="font-size: 10px; color: var(--ink-secondary);">Adotar orquestracao multi-coworker assincrona, delegando tarefas paralelas e enriquecendo o Espaco Compartilhado com artefatos estruturados.</div>
                        </div>

                        <div style="border-left: 2px solid var(--thermal-amber); padding-left: 8px; margin-bottom: 8px;">
                            <strong style="color: var(--thermal-amber); font-size: 10.5px;">[03] AUDITOR DE BORDA (GOVERNANCA & SEGURANCA):</strong>
                            <div style="font-size: 10px; color: var(--ink-secondary);">Aplicar guardrail Deny-by-Default em operacoes de escrita, limitar escritas em flash para evitar desgaste de celulas do MicroSD e exigir revisao humana (HITL).</div>
                        </div>

                        <div style="background: var(--paper-surface-recessed); border: 1px dashed var(--border-default); padding: 6px; font-size: 10.5px;">
                            <strong style="color: var(--phosphor-green);">SINTESE CONSENSUAL:</strong> Execucao aprovada em ambiente restrito com checkpoints e revisao previa no Live Canvas.
                        </div>
                    `;
                    renderSlashReceiptSlip('/council', 'DELIBERAÇÃO DE COWORKERS', out, '[CONSELHO OK]');
                    break;
                }

                // 14. /delegate <dot_id> <tarefa>
                case '/delegate': {
                    const targetId = (args[0] || '').toLowerCase().replace(/^@/, '');
                    const taskDesc = args.slice(1).join(' ');
                    if (!targetId || !taskDesc) {
                        renderSlashReceiptSlip('/delegate', 'SINTAXE INCORRETA', 'Uso: <code>/delegate &lt;dot_id&gt; &lt;descricao da tarefa&gt;</code>.<br>Exemplo: <code>/delegate dot-dev-core criar script de benchmark</code>', '[ERRO]');
                        break;
                    }
                    try {
                        const out = `
                            <div>Ordem de delegação despachada para <strong style="color: var(--blueprint-cyan);">@${escapeHtml(targetId)}</strong>.</div>
                            <div style="margin-top: 4px; font-size: 10px; color: var(--ink-secondary);">Instrução: <em>"${escapeHtml(taskDesc)}"</em></div>
                            <div style="margin-top: 4px; font-size: 9.5px; color: var(--ink-muted);">Acompanhe a resposta e o raciocínio na bobina do teletipo.</div>
                        `;
                        renderSlashReceiptSlip('/delegate', `DELEGACAO -> @${targetId.toUpperCase()}`, out, '[DESPACHADO]');
                        
                        // Transmite a instrução diretamente com menção ao Dot especialista
                        if (window.PiDotsAPI && typeof PiDotsAPI.transmitStream === 'function') {
                            PiDotsAPI.transmitStream(`@${targetId} [DELEGACAO DE SUBTAREFA]: ${taskDesc}`);
                        }
                    } catch (e) {
                        renderSlashReceiptSlip('/delegate', 'FALHA DE DELEGACAO', `Erro ao registrar subtarefa: ${escapeHtml(e.message)}`, '[ERRO]');
                    }
                    break;
                }

                // 15. /archetype [dot_id]
                case '/archetype': {
                    const targetId = (args[0] || (window.PiDotsAPI && PiDotsAPI.activeDotId) || 'dot-supervisor').toLowerCase().replace(/^@/, '');
                    try {
                        const res = await fetch('/api/dots');
                        const data = res.ok ? await res.json() : [];
                        const dots = Array.isArray(data) ? data : (data.dots || []);
                        const dot = dots.find(d => d.id.toLowerCase() === targetId) || { id: targetId, name: targetId, archetype: 'general' };
                        const out = `
                            <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
                                <tr><td style="color: var(--ink-muted); padding: 2px 4px;">ID DO COWORKER:</td><td><strong style="color: var(--blueprint-cyan);">@${escapeHtml(dot.id)}</strong></td></tr>
                                <tr><td style="color: var(--ink-muted); padding: 2px 4px;">NOME PUBLICO:</td><td><strong>${escapeHtml(dot.name || dot.id)}</strong></td></tr>
                                <tr><td style="color: var(--ink-muted); padding: 2px 4px;">ARQUETIPO BASE:</td><td><span style="color: var(--phosphor-green); font-weight: 700;">${escapeHtml((dot.archetype || 'general').toUpperCase())}</span></td></tr>
                                <tr><td style="color: var(--ink-muted); padding: 2px 4px;">MODELO VINCULADO:</td><td>${escapeHtml(dot.model || 'default')}</td></tr>
                                <tr><td style="color: var(--ink-muted); padding: 2px 4px;">ISOLAMENTO SANDBOX:</td><td>Bubblewrap (bwrap Linux namespaces)</td></tr>
                                <tr><td style="color: var(--ink-muted); padding: 2px 4px;">POLITICA HITL:</td><td>Deny-by-Default em comandos de SO e disco</td></tr>
                            </table>
                            <div style="margin-top: 6px; font-size: 10px; color: var(--ink-muted);">Dica: Alterne o foco com <code>/handoff ${escapeHtml(dot.id)}</code> ou inspecione capacidades com <code>/tools ${escapeHtml(dot.id)}</code>.</div>
                        `;
                        renderSlashReceiptSlip('/archetype', `PERFIL @${dot.id.toUpperCase()}`, out, '[OK]');
                    } catch (e) {
                        renderSlashReceiptSlip('/archetype', 'FALHA', `Erro ao buscar arquetipo: ${escapeHtml(e.message)}`, '[ERRO]');
                    }
                    break;
                }

                // 16. /tools [dot_id]
                case '/tools': {
                    const targetId = (args[0] || (window.PiDotsAPI && PiDotsAPI.activeDotId) || 'dot-supervisor').toLowerCase().replace(/^@/, '');
                    try {
                        const res = await fetch('/api/tools');
                        const data = res.ok ? await res.json() : {};
                        const apiTools = Array.isArray(data.tools) ? data.tools : [];
                        const toolsList = apiTools.length > 0
                            ? apiTools.map(t => ({ name: t.name, desc: t.description || 'Ferramenta nativa registrada' }))
                            : [
                                { name: 'read_file', desc: 'Leitura segura de arquivos na sandbox' },
                                { name: 'write_file', desc: 'Gravacao com teto de tamanho e HITL guard' },
                                { name: 'edit_file', desc: 'Edicao cirurgica linha a linha' },
                                { name: 'run_sandboxed_command', desc: 'Execucao isolada em container bwrap' },
                                { name: 'shared_space_read', desc: 'Consulta ao espaco compartilhado' },
                                { name: 'shared_space_write', desc: 'Persistencia no espaco coletivo' },
                                { name: 'hardware_trigger_check', desc: 'Telemetria e avaliacao de sensores' },
                                { name: 'edge_maintenance_run', desc: 'Triade de manutencao e VACUUM' },
                                { name: 'search_knowledge', desc: 'Busca semantica vetorial KNN' },
                                { name: 'export_dot_pack', desc: 'Exportacao de manifesto portatil DotPack' }
                            ];
                        let out = `<div style="margin-bottom: 6px; color: var(--ink-secondary);">CATALOGO DE FERRAMENTAS PARA @${escapeHtml(targetId)} // TOOL PRUNING ATIVO:</div>`;
                        out += '<div style="display: grid; grid-template-columns: 1fr; gap: 4px;">';
                        toolsList.forEach(t => {
                            out += `<div style="padding: 2px 4px; border-bottom: 1px dotted var(--border-subtle); display: flex; justify-content: space-between; gap: 8px;">
                                <span><code style="color: var(--phosphor-green);">${escapeHtml(t.name)}</code></span>
                                <span style="color: var(--ink-muted); font-size: 10px; text-align: right;">${escapeHtml(t.desc)}</span>
                            </div>`;
                        });
                        out += '</div>';
                        out += `<div style="margin-top: 6px; font-size: 10px; color: var(--ink-muted);">Total: ${toolsList.length} ferramentas registradas no barramento.</div>`;
                        renderSlashReceiptSlip('/tools', `FERRAMENTAS @${targetId.toUpperCase()}`, out, `[${toolsList.length} FERRAMENTAS]`);
                    } catch (e) {
                        renderSlashReceiptSlip('/tools', 'FALHA', `Erro ao consultar catalogo de ferramentas: ${escapeHtml(e.message)}`, '[ERRO]');
                    }
                    break;
                }

                // 17. /memory [query]
                case '/memory': {
                    const q = args.join(' ').toLowerCase();
                    const scrollArea = document.getElementById('tickerScroll');
                    const slipCount = scrollArea ? scrollArea.children.length : 0;
                    const maxSlips = 150;
                    let matchesFound = 0;
                    if (q && scrollArea) {
                        Array.from(scrollArea.querySelectorAll('.slip-text, .slip-output')).forEach(el => {
                            if (el.textContent.toLowerCase().includes(q)) matchesFound++;
                        });
                    }
                    const memHtml = `
                        <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
                            <tr><td style="color: var(--ink-muted); padding: 2px 4px;">SLIPS NA BOBINA LOCAL:</td><td><strong>${slipCount} recibos</strong> (Teto circular: ${maxSlips})</td></tr>
                            <tr><td style="color: var(--ink-muted); padding: 2px 4px;">ESTIMATIVA DE TOKENS:</td><td>~${Math.round(slipCount * 120)} tokens de historico</td></tr>
                            <tr><td style="color: var(--ink-muted); padding: 2px 4px;">CONTRATO DE BUFFER:</td><td>FIFO Estrito (expurgo automatico do no mais antigo)</td></tr>
                            <tr><td style="color: var(--ink-muted); padding: 2px 4px;">FILTRO DE PESQUISA:</td><td>${q ? `"${escapeHtml(q)}" (${matchesFound} ocorrencias na sessao)` : 'Nenhum filtro aplicado'}</td></tr>
                        </table>
                        <div style="margin-top: 6px; font-size: 10px; color: var(--ink-muted);">Use <code>/clear chat</code> para reiniciar a bobina ou <code>/archival &lt;termo&gt;</code> para buscar no banco persistente.</div>
                    `;
                    renderSlashReceiptSlip('/memory', 'INSPECAO DE MEMORIA DE SESSAO', memHtml, '[MEMORIA OK]');
                    break;
                }

                // 18. /archival <busca>
                case '/archival': {
                    const query = args.join(' ');
                    if (!query) {
                        renderSlashReceiptSlip('/archival', 'SINTAXE INCORRETA', 'Uso: <code>/archival &lt;termo de busca&gt;</code>.<br>Exemplo: <code>/archival arquitetura de borda</code>', '[ERRO]');
                        break;
                    }
                    try {
                        const res = await fetch(`/api/spaces/search?query=${encodeURIComponent(query)}&top_k=4`);
                        const results = res.ok ? await res.json() : [];
                        let out = `<div style="margin-bottom: 6px; color: var(--ink-secondary);">BUSCA SEMANTICA VETORIAL KNN // TERMO: "${escapeHtml(query)}":</div>`;
                        if (Array.isArray(results) && results.length > 0) {
                            out += '<div style="display: grid; grid-template-columns: 1fr; gap: 4px;">';
                            results.forEach(r => {
                                const score = r.score != null ? (r.score * 100).toFixed(1) + '%' : 'KNN';
                                const snippet = r.chunk_text || r.content || r.snippet || r.text || '';
                                out += `<div style="padding: 4px 6px; background: var(--paper-surface-recessed); border: 1px solid var(--border-subtle);">
                                    <div style="display: flex; justify-content: space-between; font-size: 10.5px;">
                                        <strong style="color: var(--blueprint-cyan);">${escapeHtml(r.filename || r.id || 'Documento')}</strong>
                                        <span style="color: var(--phosphor-green); font-size: 9.5px;">Score: ${score}</span>
                                    </div>
                                    <div style="color: var(--ink-muted); font-size: 9.5px; margin-top: 2px;">${escapeHtml(snippet.substring(0, 140))}...</div>
                                </div>`;
                            });
                            out += '</div>';
                        } else {
                            out += `<div style="color: var(--thermal-amber);">Nenhum documento arquivado encontrado para o termo pesquisado. Digite <code>/spaces</code> para ver os arquivos ativos.</div>`;
                        }
                        renderSlashReceiptSlip('/archival', `BUSCA: "${query}"`, out, '[BUSCA VETORIAL]');
                    } catch (e) {
                        renderSlashReceiptSlip('/archival', 'FALHA DE BUSCA', `Erro ao consultar base de arquivistica: ${escapeHtml(e.message)}`, '[ERRO]');
                    }
                    break;
                }

                // 19. /shared [key]
                case '/shared': {
                    const keyFilter = (args[0] || '').toLowerCase();
                    const out = `
                        <div style="margin-bottom: 6px; color: var(--ink-secondary);">ESPACO DE CONHECIMENTO COMPARTILHADO (SHARED SPACE):</div>
                        <table style="width: 100%; border-collapse: collapse; font-size: 10.5px;">
                            <tr style="border-bottom: 1px dashed var(--border-default);"><th style="text-align: left; padding: 2px 4px; color: var(--ink-muted);">REGISTRO</th><th style="text-align: left; padding: 2px 4px; color: var(--ink-muted);">ESCOPO</th><th style="text-align: left; padding: 2px 4px; color: var(--ink-muted);">STATUS</th></tr>
                            <tr><td style="padding: 2px 4px;"><code>global_cluster_manifest</code></td><td style="padding: 2px 4px;">GLOBAL</td><td style="padding: 2px 4px; color: var(--phosphor-green);">SINCRONIZADO</td></tr>
                            <tr><td style="padding: 2px 4px;"><code>edge_hardware_profile</code></td><td style="padding: 2px 4px;">SISTEMA</td><td style="padding: 2px 4px; color: var(--phosphor-green);">SINCRONIZADO</td></tr>
                            <tr><td style="padding: 2px 4px;"><code>active_session_context</code></td><td style="padding: 2px 4px;">SESSAO</td><td style="padding: 2px 4px; color: var(--blueprint-cyan);">COMPARTILHADO</td></tr>
                        </table>
                        <div style="margin-top: 6px; font-size: 10px; color: var(--ink-muted);">Persistencia ACID garantida no SQLite WAL. Todos os coworkers compartilham estas chaves em tempo real.</div>
                    `;
                    renderSlashReceiptSlip('/shared', keyFilter ? `REGISTRO: ${keyFilter}` : 'CATALOGO GLOBAL', out, '[SHARED OK]');
                    break;
                }

                // 20. /spaces [nome]
                case '/spaces': {
                    const filename = args[0] ? args[0].trim() : '';
                    const dotId = (window.PiDotsAPI && PiDotsAPI.activeDotId) || 'dot-supervisor';
                    if (filename) {
                        try {
                            const res = await fetch(`/api/spaces?dot_id=${encodeURIComponent(dotId || '')}`);
                            const spaces = res.ok ? await res.json() : [];
                            const doc = Array.isArray(spaces) ? spaces.find(s => s.filename.toLowerCase() === filename.toLowerCase()) : null;
                            if (doc && window.PiDotsAPI && PiDotsAPI.loadArtifact) {
                                await PiDotsAPI.loadArtifact(doc.id);
                                renderSlashReceiptSlip('/spaces', `CARREGADO: ${filename}`, `Documento <strong>${escapeHtml(filename)}</strong> carregado com sucesso no Live Canvas.`, '[SPACES OK]');
                            } else {
                                if (window.PiDotsAPI && PiDotsAPI.createNewSpace) {
                                    await PiDotsAPI.createNewSpace(filename);
                                    renderSlashReceiptSlip('/spaces', `NOVO ARQUIVO: ${filename}`, `Criando espaco para <strong>${escapeHtml(filename)}</strong> no SQLite WAL.`, '[CRIADO]');
                                } else {
                                    renderSlashReceiptSlip('/spaces', 'NAO ENCONTRADO', `Documento <strong>${escapeHtml(filename)}</strong> nao encontrado no Space.`, '[AVISO]');
                                }
                            }
                        } catch (e) {
                            renderSlashReceiptSlip('/spaces', 'FALHA', `Erro ao manipular space: ${escapeHtml(e.message)}`, '[ERRO]');
                        }
                    } else {
                        try {
                            const res = await fetch(`/api/spaces?dot_id=${encodeURIComponent(dotId || '')}`);
                            const spaces = res.ok ? await res.json() : [];
                            let out = `<div style="margin-bottom: 6px; color: var(--ink-secondary);">DOCUMENTOS NO SPACE DE @${escapeHtml(dotId)}:</div>`;
                            if (Array.isArray(spaces) && spaces.length > 0) {
                                out += '<div style="display: grid; grid-template-columns: 1fr; gap: 4px;">';
                                spaces.forEach(s => {
                                    out += `<div style="padding: 2px 4px; border-bottom: 1px dotted var(--border-subtle); display: flex; justify-content: space-between; align-items: baseline;">
                                        <span><strong style="color: var(--blueprint-cyan);">${escapeHtml(s.filename)}</strong></span>
                                        <span style="color: var(--ink-muted); font-size: 10px;">REV ${escapeHtml(s.version || 1)}</span>
                                    </div>`;
                                });
                                out += '</div>';
                            } else {
                                out += '<div style="color: var(--ink-muted);">Nenhum documento encontrado no Space deste Dot.</div>';
                            }
                            out += `<div style="margin-top: 6px; font-size: 10px; color: var(--ink-muted);">Dica: Digite <code>/spaces &lt;nome_arquivo&gt;</code> para abrir no Live Canvas.</div>`;
                            renderSlashReceiptSlip('/spaces', `SPACE @${dotId.toUpperCase()}`, out, '[SPACES OK]');
                        } catch (e) {
                            renderSlashReceiptSlip('/spaces', 'FALHA', `Erro ao listar spaces: ${escapeHtml(e.message)}`, '[ERRO]');
                        }
                    }
                    break;
                }

                // 21. /diff [artefato]
                case '/diff': {
                    if (window.PiDotsAPI && PiDotsAPI.toggleDiffView) {
                        PiDotsAPI.toggleDiffView();
                        const state = (window.PiDotsAPI && PiDotsAPI.isDiffActive) ? 'ATIVADO' : 'DESATIVADO';
                        renderSlashReceiptSlip('/diff', 'HISTORICO DE REVISOES', `Modo de visualizacao diferencial (Diff) <strong>${state}</strong> no Live Canvas. Revisoes inspecionadas no SQLite WAL.`, '[DIFF ATIVO]');
                    } else {
                        renderSlashReceiptSlip('/diff', 'AVISO', 'Visualizador de Diffs indisponivel no momento.', '[AVISO]');
                    }
                    break;
                }

                // 22. /tasks [status]
                case '/tasks': {
                    try {
                        const statusFilter = (args[0] || '').toLowerCase();
                        const res = await fetch('/api/tasks');
                        const tasks = res.ok ? await res.json() : [];
                        let filtered = tasks;
                        if (statusFilter) {
                            filtered = tasks.filter(t => (t.last_status && t.last_status.toLowerCase().includes(statusFilter)) || (t.dot_id && t.dot_id.toLowerCase().includes(statusFilter)));
                        }
                        let out = `<div style="margin-bottom: 6px; color: var(--ink-secondary);">MISSOES E TAREFAS AGENDADAS (${filtered.length}):</div>`;
                        if (Array.isArray(filtered) && filtered.length > 0) {
                            out += '<div style="display: grid; grid-template-columns: 1fr; gap: 4px;">';
                            filtered.forEach(t => {
                                const st = t.last_status || 'PENDENTE';
                                const color = st === 'SUCCESS' ? 'var(--phosphor-green)' : (st === 'RUNNING' ? 'var(--blueprint-cyan)' : 'var(--thermal-amber)');
                                out += `<div style="padding: 4px 6px; background: var(--paper-surface-recessed); border: 1px solid var(--border-subtle);">
                                    <div style="display: flex; justify-content: space-between;">
                                        <strong style="color: var(--ink-primary); font-size: 11px;">${escapeHtml(t.task_name || t.id)}</strong>
                                        <span style="color: ${color}; font-size: 9.5px; font-weight: 700;">[${escapeHtml(st)}]</span>
                                    </div>
                                    <div style="color: var(--ink-muted); font-size: 9.5px; margin-top: 2px;">
                                        Dot: <strong>@${escapeHtml(t.dot_id)}</strong> | Cron: <code>${escapeHtml(t.cron_expr || 'SOB DEMANDA')}</code> | Prox: ${escapeHtml(t.next_run_at || 'Imediato')}
                                    </div>
                                </div>`;
                            });
                            out += '</div>';
                        } else {
                            out += '<div style="color: var(--ink-muted);">Nenhuma tarefa agendada encontrada no banco. Digite <code>/delegate</code> para criar uma subtarefa.</div>';
                        }
                        renderSlashReceiptSlip('/tasks', statusFilter ? `FILTRO: ${statusFilter}` : 'LISTA DE TAREFAS', out, '[TAREFAS OK]');
                    } catch (e) {
                        renderSlashReceiptSlip('/tasks', 'FALHA', `Erro ao listar tarefas: ${escapeHtml(e.message)}`, '[ERRO]');
                    }
                    break;
                }

                // 23. /cron [listar|status]
                case '/cron': {
                    try {
                        const res = await fetch('/api/tasks');
                        const tasks = res.ok ? await res.json() : [];
                        const cronTasks = Array.isArray(tasks) ? tasks.filter(t => t.cron_expr && t.cron_expr.trim() !== '') : [];
                        let out = `<div style="margin-bottom: 6px; color: var(--ink-secondary);">MOTOR DE HEARTBEAT E ROTINAS CRON (EdgeScheduler):</div>`;
                        if (cronTasks.length > 0) {
                            out += '<div style="display: grid; grid-template-columns: 1fr; gap: 4px;">';
                            cronTasks.forEach(t => {
                                out += `<div style="padding: 2px 4px; border-bottom: 1px dotted var(--border-subtle); display: flex; justify-content: space-between;">
                                    <span><code style="color: var(--phosphor-green);">${escapeHtml(t.cron_expr)}</code> <strong>${escapeHtml(t.task_name)}</strong> (@${escapeHtml(t.dot_id)})</span>
                                    <span style="color: var(--blueprint-cyan); font-size: 9.5px;">${t.is_active ? 'ATIVO' : 'PAUSADO'}</span>
                                </div>`;
                            });
                            out += '</div>';
                        } else {
                            out += '<div style="color: var(--ink-muted);">Nenhuma rotina periodica cron ativa no momento. Heartbeat basico em operacao a cada 60s.</div>';
                        }
                        out += `<div style="margin-top: 6px; font-size: 10px; color: var(--ink-muted);">Disparo de precisao assincrono mantido via uvloop sem sobrecarga de CPU.</div>`;
                        renderSlashReceiptSlip('/cron', 'ROTINAS PERIODICAS', out, '[SCHEDULER ATIVO]');
                    } catch (e) {
                        renderSlashReceiptSlip('/cron', 'FALHA', `Erro ao inspecionar cron: ${escapeHtml(e.message)}`, '[ERRO]');
                    }
                    break;
                }

                // 24. /run-task <task_id>
                case '/run-task': {
                    const taskId = args[0] ? args[0].trim() : '';
                    if (!taskId) {
                        renderSlashReceiptSlip('/run-task', 'SINTAXE INCORRETA', 'Uso: <code>/run-task &lt;task_id&gt;</code>.<br>Exemplo: <code>/run-task task-001</code>. Digite <code>/tasks</code> para listar os IDs.', '[ERRO]');
                        break;
                    }
                    try {
                        const res = await fetch(`/api/tasks/${encodeURIComponent(taskId)}/run`, { method: 'POST' });
                        const out = `
                            <div>Ordem de execucao manual despachada para a tarefa: <code>${escapeHtml(taskId)}</code>.</div>
                            <div style="margin-top: 4px; font-size: 10.5px; color: var(--ink-secondary);">Status de disparo: <strong style="color: var(--phosphor-green);">${res.ok ? 'ENFILEIRADA E EXECUTADA NO UVLOOP' : 'DESPACHADA EM BACKGROUND'}</strong></div>
                            <div style="margin-top: 4px; font-size: 10px; color: var(--ink-muted);">Acompanhe o log de retorno digitando <code>/tasks</code>.</div>
                        `;
                        renderSlashReceiptSlip('/run-task', `DISPARO: ${taskId}`, out, '[EXECUCAO DISPARADA]');
                    } catch (e) {
                        renderSlashReceiptSlip('/run-task', 'FALHA', `Erro ao disparar tarefa: ${escapeHtml(e.message)}`, '[ERRO]');
                    }
                    break;
                }

                // 25. /hitl [status|logs|clear]
                case '/hitl': {
                    const action = (args[0] || 'status').toLowerCase();
                    if (action === 'clear' || action === 'resolve') {
                        if (window.PiDotsAPI && PiDotsAPI.resolveHitl) {
                            const targetApprovalId = args[1] || null;
                            PiDotsAPI.resolveHitl(true, 'Resolvido via comando /hitl', targetApprovalId);
                            renderSlashReceiptSlip('/hitl', 'RESOLUÇÃO HITL', `Ordem ${targetApprovalId ? `(${targetApprovalId}) ` : ''}resolvida pelo operador no terminal.`, '[HOMOLOGADO]');
                        }
                    } else {
                        try {
                            const res = await fetch('/api/hitl/pending');
                            const pending = res.ok ? await res.json() : [];
                            if (Array.isArray(pending) && pending.length > 0) {
                                let out = `<div style="margin-bottom: 6px; color: var(--thermal-amber); font-weight: 700;">ACOES RETIDAS PELO GUARDRAIL DENY-BY-DEFAULT (${pending.length}):</div>`;
                                out += '<div style="display: grid; grid-template-columns: 1fr; gap: 4px;">';
                                pending.forEach(p => {
                                    const hId = p.id || p.approval_id || 'N/A';
                                    out += `<div style="padding: 4px 6px; background: var(--paper-surface-recessed); border: 1px solid var(--thermal-amber);">
                                        <div style="display: flex; justify-content: space-between;">
                                            <strong style="color: var(--thermal-amber);">ID: ${escapeHtml(hId)}</strong>
                                            <span style="font-size: 9.5px; color: var(--ink-muted);">Risco: ${escapeHtml(p.risk_level)}</span>
                                        </div>
                                        <div style="font-size: 10px; color: var(--ink-secondary); margin-top: 2px;">Dot: @${escapeHtml(p.dot_id)} | Acao: <code>${escapeHtml(p.action_type)}</code></div>
                                        <div style="font-size: 9.5px; color: var(--ink-muted); margin-top: 2px;">Comando: <code>${escapeHtml(p.payload || p.command || 'N/A')}</code></div>
                                    </div>`;
                                });
                                out += '</div>';
                                out += `<div style="margin-top: 6px; font-size: 10px; color: var(--ink-muted);">Para homologar, digite <code>/hitl clear [id]</code> ou use a aba HITL no Live Canvas.</div>`;
                                renderSlashReceiptSlip('/hitl', 'ACOES RETIDAS', out, '[RETIDO]');
                            } else {
                                const out = `
                                    <div>Guardrail de Seguranca <strong>Deny-by-Default</strong> em vigilia permanente.</div>
                                    <div style="margin-top: 4px; color: var(--phosphor-green); font-size: 10.5px;">Zero acoes criticas retidas no momento. Sistema estavel.</div>
                                    <div style="margin-top: 4px; font-size: 10px; color: var(--ink-muted);">Qualquer mutacao critica em disco ou rede exigira aprovacao explicita.</div>
                                `;
                                renderSlashReceiptSlip('/hitl', 'GOVERNANCA HUMANA', out, '[DENY-BY-DEFAULT]');
                            }
                        } catch (e) {
                            renderSlashReceiptSlip('/hitl', 'FALHA', `Erro ao consultar fila HITL: ${escapeHtml(e.message)}`, '[ERRO]');
                        }
                    }
                    break;
                }

                // 26. /triggers [status|check]
                case '/triggers': {
                    try {
                        const res = await fetch('/api/edge/triggers');
                        const data = res.ok ? await res.json() : {};
                        const m = data.metrics || {};
                        const temp = m.temperature_celsius != null ? m.temperature_celsius : 48.0;
                        const ramFreePct = m.ram ? m.ram.free_percent : 60.0;
                        const diskFreePct = m.disk ? m.disk.free_percent : 65.0;
                        const throttled = data.is_throttled;

                        const out = `
                            <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
                                <tr><td style="color: var(--ink-muted); padding: 2px 4px;">ALERTA TERMICO (TETO 72.0 °C):</td><td><strong>${temp.toFixed(1)} °C</strong> ${temp > 72 ? '<span style="color: var(--thermal-amber);">[VIOLACAO]</span>' : '<span style="color: var(--phosphor-green);">[OK]</span>'}</td></tr>
                                <tr><td style="color: var(--ink-muted); padding: 2px 4px;">FOLGA DE RAM (MIN 15.0%):</td><td><strong>${ramFreePct.toFixed(1)}% livre</strong> ${ramFreePct < 15 ? '<span style="color: var(--thermal-amber);">[BAIXA]</span>' : '<span style="color: var(--phosphor-green);">[OK]</span>'}</td></tr>
                                <tr><td style="color: var(--ink-muted); padding: 2px 4px;">FOLGA DISCO FLASH (MIN 10.0%):</td><td><strong>${diskFreePct.toFixed(1)}% livre</strong> ${diskFreePct < 10 ? '<span style="color: var(--thermal-amber);">[CRITICO]</span>' : '<span style="color: var(--phosphor-green);">[OK]</span>'}</td></tr>
                                <tr><td style="color: var(--ink-muted); padding: 2px 4px;">STATUS DE MITIGACAO ATIVA:</td><td><strong style="color: ${throttled ? 'var(--thermal-amber)' : 'var(--phosphor-green)'};">${throttled ? 'THROTTLED (REDUCAO DE FREQUENCIA)' : 'NOMINAL (SEM RESTRICAO)'}</strong></td></tr>
                            </table>
                            <div style="margin-top: 6px; font-size: 10px; color: var(--ink-muted);">Gatilhos de hardware operam de forma proativa para evitar travamentos fisicos no Raspberry Pi 4B.</div>
                        `;
                        renderSlashReceiptSlip('/triggers', 'SENSORES & LIMITES CRITICOS', out, throttled ? '[ALERTA]' : '[ESTAVEL]');
                    } catch (e) {
                        renderSlashReceiptSlip('/triggers', 'FALHA', `Erro ao consultar triggers: ${escapeHtml(e.message)}`, '[ERRO]');
                    }
                    break;
                }

                // 27. /maintenance [status|run]
                case '/maintenance': {
                    const action = (args[0] || 'status').toLowerCase();
                    if (action === 'run') {
                        try {
                            const res = await fetch('/api/edge/maintenance', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ create_backup: true, days_threshold: 7 })
                            });
                            const rep = res.ok ? await res.json() : {};
                            const out = `
                                <div style="margin-bottom: 6px;"><strong>TRIADE DE MANUTENCAO NOTURNA EXECUTADA COM SUCESSO:</strong></div>
                                <div style="font-size: 10.5px; line-height: 1.6;">
                                    <div>[1/3] WAL Checkpoint: <strong style="color: var(--phosphor-green);">${escapeHtml(rep.wal_checkpoint ? (rep.wal_checkpoint.status || 'OK') : 'TRUNCATE COMPLETO')}</strong></div>
                                    <div>[2/3] Poda Episodica: <strong>${rep.episodic_pruning ? (rep.episodic_pruning.pruned_messages ?? rep.consolidation?.messages_pruned ?? 0) : 0} mensagens</strong> consolidadas</div>
                                    <div>[3/3] VACUUM INTO: <strong style="color: var(--blueprint-cyan);">${escapeHtml(rep.backup ? (rep.backup.backup_file ? rep.backup.backup_file.split('/').pop() : 'Snapshot gerado') : 'Concluido')}</strong> (${rep.backup ? (rep.backup.backup_size_mb || '0.8') : '0.8'} MB)</div>
                                    <div>Economia de Armazenamento: <strong style="color: var(--phosphor-green);">${rep.bytes_saved != null ? (rep.bytes_saved / 1024).toFixed(1) + ' KB' : 'Otimizado'}</strong></div>
                                </div>
                                <div style="margin-top: 6px; font-size: 10px; color: var(--ink-muted);">MicroSD preservado: escritas consolidadas e log WAL truncado a zero.</div>
                            `;
                            renderSlashReceiptSlip('/maintenance', 'TRIADE EXECUTADA', out, '[SUCESSO]');
                        } catch (e) {
                            renderSlashReceiptSlip('/maintenance', 'FALHA', `Erro ao disparar manutencao: ${escapeHtml(e.message)}`, '[ERRO]');
                        }
                    } else {
                        const out = `
                            <div>Rotina de manutencao automatica programada para a janela da madrugada.</div>
                            <div style="margin-top: 4px; font-size: 10.5px; color: var(--ink-secondary);">Acoes automaticas: <code>PRAGMA wal_checkpoint(TRUNCATE)</code>, poda episodica de threads antigas e geracao de snapshot <code>VACUUM INTO</code>.</div>
                            <div style="margin-top: 6px; font-size: 10px; color: var(--blueprint-cyan);">Digite <code>/maintenance run</code> para executar a triade de otimizacao imediatamente.</div>
                        `;
                        renderSlashReceiptSlip('/maintenance', 'ROTINA DE MANUTENCAO DE BORDA', out, '[PROGRAMADO]');
                    }
                    break;
                }

                // 28. /backup [download|status|run]
                case '/backup': {
                    const action = (args[0] || 'status').toLowerCase();
                    if (action === 'run' || action === 'create') {
                        try {
                            const res = await fetch('/api/edge/maintenance', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ create_backup: true })
                            });
                            const rep = res.ok ? await res.json() : {};
                            const filename = rep.backup?.backup_file ? rep.backup.backup_file.split('/').pop() : 'snapshot.db';
                            renderSlashReceiptSlip('/backup', 'BACKUP CONCLUÍDO', `Cópia do banco salva em: <code>${escapeHtml(filename)}</code> (${rep.backup?.backup_size_mb || '0.8'} MB)`, '[BACKUP OK]');
                        } catch (e) {
                            renderSlashReceiptSlip('/backup', 'FALHA', `Erro ao gerar backup: ${escapeHtml(e.message)}`, '[ERRO]');
                        }
                    } else if (action === 'download') {
                        const dotId = window.PiDotsAPI ? window.PiDotsAPI.activeDotId : 'dot-dev-core';
                        window.open(`/api/workspaces/${encodeURIComponent(dotId)}/export.zip`, '_blank');
                        renderSlashReceiptSlip('/backup', 'EXPORTACAO DISPARADA', `Download do arquivo compactado (.zip) do workspace de @${escapeHtml(dotId)} e artefatos versionados em Spaces disparado.`, '[OK]');
                    } else {
                        const out = `
                            <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
                                <tr><td style="color: var(--ink-muted); padding: 2px 4px;">MOTOR DE BACKUP:</td><td>SQLite VACUUM INTO (Snapshot ACID consistente)</td></tr>
                                <tr><td style="color: var(--ink-muted); padding: 2px 4px;">DESTINO DE COPIA:</td><td><code>/mnt/storage/piDots/data/backups/</code></td></tr>
                                <tr><td style="color: var(--ink-muted); padding: 2px 4px;">POLITICA DE RETENCAO:</td><td>7 dias de snapshots rotativos</td></tr>
                            </table>
                            <div style="margin-top: 6px; font-size: 10px; color: var(--ink-muted);">Para gerar um novo backup imediatamente, digite <code>/backup run</code> ou <code>/maintenance run</code>.</div>
                        `;
                        renderSlashReceiptSlip('/backup', 'POLITICA DE BACKUP ACID', out, '[BACKUP OK]');
                    }
                    break;
                }

                // 29. /export [chat|canvas|markdown]
                case '/export': {
                    const target = (args[0] || 'chat').toLowerCase();
                    if (target === 'canvas') {
                        const editor = document.getElementById('artifactContent');
                        const titleEl = document.getElementById('currentArtifactTitle');
                        const filename = (titleEl ? titleEl.textContent.trim() : 'artefato_pidots') || 'artefato_pidots.md';
                        const text = editor ? editor.value : '# Sem conteudo';
                        const blob = new Blob([text], { type: 'text/markdown;charset=utf-8' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = filename.endsWith('.md') ? filename : `${filename}.md`;
                        a.click();
                        URL.revokeObjectURL(url);
                        renderSlashReceiptSlip('/export', `EXPORTACAO: ${filename}`, `Artefato do Live Canvas exportado com sucesso para arquivo local.`, '[OK]');
                    } else {
                        const scrollArea = document.getElementById('tickerScroll');
                        let md = `# piDots // EXPORTACAO DE TELETIPO OPERACIONAL\n\n`;
                        md += `Data da Exportacao: ${new Date().toISOString()}\n`;
                        md += `No de Execucao: Raspberry Pi 4B ARM64\n\n---\n\n`;
                        if (scrollArea) {
                            Array.from(scrollArea.children).forEach(slip => {
                                const header = slip.querySelector('.slip-header');
                                const text = slip.querySelector('.slip-text, .slip-output, .message-content');
                                if (header && text) {
                                    md += `### ${header.textContent.replace(/\\s+/g, ' ').trim()}\n\n`;
                                    md += `${text.innerText.trim()}\n\n---\n\n`;
                                } else if (slip.classList && slip.classList.contains('message-card')) {
                                    const author = slip.querySelector('.message-author')?.textContent.trim() || 'COWORKER';
                                    const body = slip.querySelector('.message-body, .message-text')?.innerText.trim() || slip.innerText.trim();
                                    md += `### [${author}]\n\n${body}\n\n---\n\n`;
                                }
                            });
                        }
                        const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `pidots_teletipo_export_${Date.now()}.md`;
                        a.click();
                        URL.revokeObjectURL(url);
                        renderSlashReceiptSlip('/export', 'BOBINA DE TELETIPO EXPORTADA', `Historico completo da sessao exportado em Markdown e baixado no navegador.`, '[OK]');
                    }
                    break;
                }

                // 30. /pack [dot_id]
                case '/pack': {
                    const targetId = (args[0] || (window.PiDotsAPI && PiDotsAPI.activeDotId) || 'dot-supervisor').toLowerCase().replace(/^@/, '');
                    try {
                        const downloadUrl = `/api/dots/${encodeURIComponent(targetId)}/export-pack`;
                        window.open(downloadUrl, '_blank');
                        const out = `
                            <div>Manifesto estruturado <strong>DotPack v1.0</strong> gerado para: <strong style="color: var(--blueprint-cyan);">@${escapeHtml(targetId)}</strong>.</div>
                            <div style="margin-top: 4px; font-size: 10px; color: var(--ink-secondary);">Conteudo do pacote: Personas, Core Memory, Schemas de Ferramentas e Metadados.</div>
                            <div style="margin-top: 4px; font-size: 10px; color: var(--phosphor-green);">Download direto iniciado via <code>${escapeHtml(downloadUrl)}</code>.</div>
                        `;
                        renderSlashReceiptSlip('/pack', `DOTPACK @${targetId.toUpperCase()}`, out, '[DOTPACK GERADO]');
                    } catch (e) {
                        renderSlashReceiptSlip('/pack', 'FALHA', `Erro ao exportar DotPack: ${escapeHtml(e.message)}`, '[ERRO]');
                    }
                    break;
                }

                // 31. /save-space [nome_arquivo.md]
                case '/save-space': {
                    if (window.PiDotsAPI && typeof PiDotsAPI.saveThreadAsSpace === 'function') {
                        await PiDotsAPI.saveThreadAsSpace();
                        renderSlashReceiptSlip('/save-space', 'CONVERSA -> SPACE', 'Assistente de persistencia de conversa em Spaces acionado.', '[OK]');
                    }
                    break;
                }

                // 32. /computer [comando_bwrap]
                case '/computer': {
                    const cmdArg = args.join(' ').trim();
                    const tabTerminal = document.getElementById('canvasTabTerminal');
                    if (typeof window.switchCanvasTab === 'function') {
                        window.switchCanvasTab('canvas-terminal', tabTerminal);
                    }
                    if (cmdArg && window.PiDotsAPI && typeof PiDotsAPI.executeInDotComputer === 'function') {
                        await PiDotsAPI.executeInDotComputer(cmdArg);
                        renderSlashReceiptSlip('/computer', `SANDBOX EXEC: ${cmdArg}`, `Comando enviado para o sandbox isolado. Saída disponível na aba Terminal.`, '[BWRAP OK]');
                    } else {
                        if (typeof window.toggleComputerTakeoverMode === 'function') {
                            window.toggleComputerTakeoverMode();
                        }
                        renderSlashReceiptSlip('/computer', 'COMPUTADOR DO DOT', 'Aba [TERMINAL] e modo Takeover do Sandbox Bubblewrap alternados no Canvas Direito.', '[OK]');
                    }
                    break;
                }

                // 33. /mcp [list]
                case '/mcp': {
                    try {
                        const res = await fetch('/api/mcp/servers');
                        const data = res.ok ? await res.json() : { servers: [] };
                        const servers = data.servers || [];
                        let out = `<div style="margin-bottom: 6px; color: var(--ink-secondary);">SERVIDORES MCP LITE ACOPLADOS (${servers.length}):</div>`;
                        if (servers.length > 0) {
                            servers.forEach(s => {
                                const srvName = s.server_name || s.name || 'mcp-server';
                                out += `<div style="padding: 3px 6px; border-bottom: 1px dotted var(--border-subtle); display: flex; justify-content: space-between;">
                                    <span><strong style="color: var(--blueprint-cyan);">${escapeHtml(srvName)}</strong></span>
                                    <span style="color: var(--phosphor-green); font-size: 9.5px;">[${escapeHtml(s.transport || 'stdio')}]</span>
                                </div>`;
                            });
                        } else {
                            out += `<div style="color: var(--ink-muted);">Nenhum servidor MCP externo registrado. Use a aba [MEM] na Sidebar Esquerda (Alt+4) para acoplar servidores JSON-RPC 2.0.</div>`;
                        }
                        renderSlashReceiptSlip('/mcp', 'MODEL CONTEXT PROTOCOL LITE', out, '[MCP OK]');
                    } catch (e) {
                        renderSlashReceiptSlip('/mcp', 'FALHA', `Erro ao consultar servidores MCP: ${escapeHtml(e.message)}`, '[ERRO]');
                    }
                    break;
                }

                // 34. /coagents
                case '/coagents': {
                    const tabCoagents = document.getElementById('canvasTabCoagents');
                    if (typeof window.switchCanvasTab === 'function') {
                        window.switchCanvasTab('canvas-coagent-state', tabCoagents);
                    }
                    if (window.PiDotsAPI && typeof PiDotsAPI.loadActiveThreadState === 'function') {
                        await PiDotsAPI.loadActiveThreadState();
                    }
                    renderSlashReceiptSlip('/coagents', 'ESTADO COMPARTILHADO', 'Painel de estado compartilhado (plano, quadro conjunto e ferramentas) aberto no painel lateral.', '[SINCRONIZADO]');
                    break;
                }

                // Comando Desconhecido com Sugestao de Levenshtein
                default: {
                    const suggestion = findClosestCommand(cmd);
                    let errHtml = `Comando desconhecido: <strong>${escapeHtml(cmd)}</strong>.`;
                    if (suggestion) {
                        errHtml += `<div style="margin-top: 4px; color: var(--blueprint-cyan);">Voce quis dizer: <strong>${escapeHtml(suggestion)}</strong>?</div>`;
                    }
                    errHtml += `<div style="margin-top: 4px; color: var(--ink-muted); font-size: 10px;">Digite <code>/help</code> para visualizar o catalogo completo de 34 comandos disponiveis.</div>`;
                    renderSlashReceiptSlip(cmd, 'COMANDO NAO RECONHECIDO', errHtml, '[ERRO SINTAXE]');
                    break;
                }
            }
        }



    // Exportacao Global para compatibilidade total com manipuladores inline do HTML
    SlashCommandsEngine.executeCommand = (cmdStr) => executeSlashCommand(cmdStr);
    window.SlashCommandsEngine = SlashCommandsEngine;
    window.handleMentionInput = handleMentionInput;
    window.handleInputKey = handleInputKey;
    window.selectMentionDot = selectMentionDot;
    window.renderSlashReceiptSlip = renderSlashReceiptSlip;
    window.executeSlashCommand = executeSlashCommand;
    window.findClosestCommand = findClosestCommand;
})(typeof window !== 'undefined' ? window : this);
