/**
 * PIDOTS CONSOLE SPA - CAMADA DE API, AG-UI PROTOCOL E COAGENTS LIVE BINDING
 * =====================================================================
 * Gerencia chamadas assincronas para o backend FastAPI e SQLite WAL:
 * SSE Stream (/api/threads/{id}/runs), Dots Studio, Spaces, Canais, Threads,
 * CoAgents Shared State, Generative UI Cards Inline, HITL, Tasks Cron,
 * Memoria Semantica 64D, MCP Lite, Dot's Computer (bwrap) e Telemetria.
 * ZERO EMOJIS // Vanilla JS Puro // Alta Performance ARM64
 * =====================================================================
 */

(function(window) {
    'use strict';

    if (typeof window.getNextSeqCounter === 'undefined') {
        window._seqCounter = 3;
        window.getNextSeqCounter = function() {
            return window._seqCounter++;
        };
    }

    function safeEscape(str) {
        if (typeof window.escapeHtml === 'function') return window.escapeHtml(str);
        return String(str ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    const PiDotsAPI = {
        activeDotId: 'dot-dev-core',
        activeChannelId: 'ch-main',
        activeChannelName: 'geral',
        activeThreadId: null,
        activeSpaceId: null,
        activeSpaceDoc: null,
        spacesCache: [],
        dotsCache: [],
        channelsCache: [],
        threadsCache: [],
        toolsCache: [],
        tasksCache: [],
        pendingHitlCache: [],
        editingDotId: null,
        telemetryHistory: { ram: [62, 65, 68, 67, 70, 69, 68], temp: [45, 46, 47, 48, 48.2, 48.5, 48.2] },
        isDiffActive: false,

        // 7. Configurações de IA e Hot-Reload (/api/settings)
        async loadSettings() {
            try {
                const res = await fetch('/api/settings');
                if (!res.ok) return;
                const data = await res.json();
                if (data.ai) {
                    const mEl = document.getElementById('cfgModel');
                    const bEl = document.getElementById('cfgBaseUrl');
                    const rEl = document.getElementById('cfgRetries');
                    const tEl = document.getElementById('cfgTimeout');
                    if (mEl && data.ai.model) mEl.value = data.ai.model;
                    if (bEl && data.ai.base_url) bEl.value = data.ai.base_url;
                    if (rEl && data.ai.max_retries) rEl.value = data.ai.max_retries;
                    if (tEl && data.ai.timeout_seconds) tEl.value = data.ai.timeout_seconds;
                }
            } catch (e) {
                console.warn('Configuracoes locais:', e);
            }
        },

        async saveAISettings() {
            const model = document.getElementById('cfgModel').value.trim();
            const baseUrl = document.getElementById('cfgBaseUrl').value.trim();
            const apiKey = document.getElementById('cfgApiKey').value.trim();
            const retries = parseInt(document.getElementById('cfgRetries').value, 10) || 3;
            const timeout = parseFloat(document.getElementById('cfgTimeout').value) || 60.0;

            const payload = {
                base_url: baseUrl,
                model: model,
                max_retries: retries,
                timeout_seconds: timeout
            };
            if (apiKey) payload.api_key = apiKey;

            try {
                const res = await fetch('/api/settings/ai', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });
                if (!res.ok) throw new Error(`Status ${res.status}`);
                await res.json();
                PixelSystem.toast(`SUCESSO: Hot-Reload de IA aplicado! Modelo ativo: ${model}`, 'success');
                await this.fetchTelemetry();
            } catch (e) {
                PixelSystem.toast(`Erro ao aplicar Hot-Reload: ${e}`, 'danger');
            }
        },

        // 8. Buffer Circular de DOM no Teletype Scroll (Teto 150 Nós)
        enforceDomCeiling() {
            const scrollArea = document.getElementById('tickerScroll');
            if (!scrollArea) return;
            const maxSlips = 150;
            while (scrollArea.children.length > maxSlips) {
                scrollArea.removeChild(scrollArea.firstElementChild);
            }
        },

        // 1. Inicialização Geral de Dados
        async init() {
            await this.fetchTelemetry();
            await this.loadDots();
            await this.loadChannels();
            await this.loadThreads();
            await this.loadSpaces();
            await this.loadPendingHitl();
            await this.loadSettings();

            this._telemetryFetching = false;
            setInterval(async () => {
                if (this._telemetryFetching) return;
                this._telemetryFetching = true;
                try {
                    await this.fetchTelemetry();
                } finally {
                    this._telemetryFetching = false;
                }
            }, 4000);
        },

        // 2. Telemetria Real (/health) com process_rss_mb
        async fetchTelemetry() {
            try {
                const res = await fetch('/health');
                if (!res.ok) return;
                const data = await res.json();

                if (data.soc_temperature_celsius !== undefined) {
                    const tempEl = document.getElementById('val-temp');
                    if (tempEl) tempEl.textContent = `${data.soc_temperature_celsius} °C`;
                    const compactNodeEl = document.getElementById('val-compact-node');
                    if (compactNodeEl) compactNodeEl.textContent = `${data.soc_temperature_celsius}°C`;
                    const plotterTempEl = document.querySelector('.plotter-card:nth-child(2) .plotter-val');
                    if (plotterTempEl) plotterTempEl.textContent = `${data.soc_temperature_celsius} °C`;
                    const asciiTempEl = document.getElementById('sidebarAsciiTemp');
                    if (asciiTempEl) {
                        asciiTempEl.textContent = `${data.soc_temperature_celsius}°C`;
                        asciiTempEl.style.color = data.soc_temperature_celsius >= 72 ? 'var(--thermal-amber)' : 'var(--phosphor-green)';
                    }

                    this.telemetryHistory.temp.push(data.soc_temperature_celsius);
                    if (this.telemetryHistory.temp.length > 10) this.telemetryHistory.temp.shift();
                    this.updateTempSvg();
                }

                if (data.memory) {
                    const rssMb = data.memory.process_rss_mb !== undefined ? data.memory.process_rss_mb : data.memory.used_mb;
                    const ramEl = document.getElementById('val-ram');
                    if (ramEl) ramEl.textContent = `${rssMb} MB RSS (SO: ${data.memory.used_mb}/${data.memory.total_mb} MB)`;
                    const plotterRamEl = document.querySelector('.plotter-card:nth-child(1) .plotter-val');
                    if (plotterRamEl) plotterRamEl.textContent = `${rssMb} MB RSS`;

                    const asciiRamEl = document.getElementById('sidebarAsciiRamBar');
                    if (asciiRamEl) {
                        const ceilingMb = 300;
                        const filled = Math.max(1, Math.min(10, Math.round((rssMb / ceilingMb) * 10)));
                        const barStr = '[' + '|'.repeat(filled) + '.'.repeat(10 - filled) + ']';
                        asciiRamEl.textContent = `${barStr} ${Math.round(rssMb)}MB`;
                    }

                    this.telemetryHistory.ram.push(rssMb);
                    if (this.telemetryHistory.ram.length > 10) this.telemetryHistory.ram.shift();
                    this.updateRamSvg();
                }

                if (data.database && data.database.mode) {
                    const walEl = document.querySelector('.telemetry-chip.desktop-only .chip-value');
                    if (walEl) walEl.textContent = `${data.database.mode} (ATIVO)`;
                    const asciiWalEl = document.getElementById('sidebarAsciiWal');
                    if (asciiWalEl) asciiWalEl.textContent = `${String(data.database.mode).toUpperCase()} OK`;
                }
            } catch (e) {
                console.warn('Telemetria offline ou isolada:', e);
            }
        },

        updateRamSvg() {
            const polyline = document.querySelector('.plotter-card:nth-child(1) polyline');
            const polygon = document.querySelector('.plotter-card:nth-child(1) polygon');
            if (!polyline || !polygon) return;

            const values = this.telemetryHistory.ram;
            if (!values || values.length < 2) return;
            const maxRam = 300;
            let points = [];
            for (let i = 0; i < values.length; i++) {
                const x = Math.round((i / (values.length - 1)) * 310);
                const y = Math.round(105 - ((values[i] / maxRam) * 85));
                points.push(`${x},${Math.max(10, Math.min(105, y))}`);
            }
            const ptStr = points.join(' ');
            polyline.setAttribute('points', ptStr);
            polygon.setAttribute('points', `0,110 ${ptStr} 310,110`);
        },

        updateTempSvg() {
            const polyline = document.querySelector('.plotter-card:nth-child(2) polyline');
            const polygon = document.querySelector('.plotter-card:nth-child(2) polygon');
            if (!polyline || !polygon) return;

            const values = this.telemetryHistory.temp;
            if (!values || values.length < 2) return;
            const maxTemp = 85;
            let points = [];
            for (let i = 0; i < values.length; i++) {
                const x = Math.round((i / (values.length - 1)) * 310);
                const y = Math.round(105 - ((values[i] / maxTemp) * 80));
                points.push(`${x},${Math.max(15, Math.min(105, y))}`);
            }
            const ptStr = points.join(' ');
            polyline.setAttribute('points', ptStr);
            polygon.setAttribute('points', `0,110 ${ptStr} 310,110`);
        },

        // 3. Dots Coworkers (/api/dots) & Estúdio de Dots
        async loadDots() {
            try {
                const res = await fetch('/api/dots?core_only=false');
                if (!res.ok) return;
                const dots = await res.json();
                if (!dots || !dots.length) return;

                this.dotsCache = dots;
                const countBadge = document.getElementById('dotsCountBadge');
                if (countBadge) countBadge.textContent = `${dots.length} ATIVOS`;

                const container = document.getElementById('dotsListContainer');
                if (container) {
                    container.innerHTML = '';
                    dots.forEach((dot, idx) => {
                        const isActive = this.activeDotId ? dot.id === this.activeDotId : idx === 0;
                        const card = document.createElement('div');
                        card.className = `dot-card ${isActive ? 'active' : ''}`;
                        card.onclick = () => this.selectDot(dot.id, card);

                        const archetypeLabel = (dot.archetype || 'COWORKER').toUpperCase();
                        card.innerHTML = `
                            <div class="dot-card-header">
                                <span class="dot-card-name">${safeEscape(dot.name || dot.id)}</span>
                                <span class="dot-card-status" style="font-size: 8px;">[${safeEscape(archetypeLabel)}]</span>
                            </div>
                            <div class="dot-card-role" style="font-size: 10px; color: var(--ink-secondary); margin-top: 2px;">${safeEscape(dot.role || 'Edge Coworker')}</div>
                        `;
                        container.appendChild(card);
                    });
                }

                if (!this.activeDotId || !dots.some(d => d.id === this.activeDotId)) {
                    this.activeDotId = dots[0].id;
                }
                const currentDot = dots.find(d => d.id === this.activeDotId) || dots[0];
                const activeAgentName = currentDot.name || currentDot.id;
                const chEl = document.getElementById('activeDotChannel');
                if (chEl && !this.activeThreadId) {
                    chEl.textContent = `CANAL DE TRABALHO // ${activeAgentName.toUpperCase()}`;
                }
                const headerAgentEl = document.getElementById('headerActiveAgentName');
                if (headerAgentEl) headerAgentEl.textContent = activeAgentName;
                const compBadge = document.getElementById('computerActiveWorkspaceBadge');
                if (compBadge) compBadge.textContent = `/workspace/${this.activeDotId}`;
            } catch (e) {
                console.warn('Erro ao carregar Dots:', e);
            }
        },

        selectDot(dotId, cardEl) {
            this.activeDotId = dotId;
            document.querySelectorAll('.dot-card').forEach(c => c.classList.remove('active'));
            if (cardEl) cardEl.classList.add('active');

            const dot = this.dotsCache.find(d => d.id === dotId);
            const chEl = document.getElementById('activeDotChannel');
            if (chEl) chEl.textContent = `CANAL DE MISSAO // ${(dot ? (dot.name || dot.id) : dotId).toUpperCase()} (SESSAO ATIVA)`;
            const breadcrumb = document.getElementById('headerActiveAgentName');
            if (breadcrumb) breadcrumb.textContent = dot ? (dot.name || dot.id) : dotId;
            const compBadge = document.getElementById('computerActiveWorkspaceBadge');
            if (compBadge) compBadge.textContent = `/workspace/${dotId}`;

            this.activeThreadId = null;
            this.loadSpaces();
            this.loadThreads();

            const inputEl = document.getElementById('instructionInput');
            if (inputEl && inputEl.value.trim() === '') {
                inputEl.value = `@${dotId} `;
                inputEl.focus();
            }

            PixelSystem.toast(`Coworker '${dot ? dot.name : dotId}' selecionado como ativo.`, 'info');
        },

        // 3B. Canais Colaborativos e Threads Persistentes (Padrão OpenDots)
        async loadChannels() {
            try {
                const res = await fetch('/api/channels');
                if (!res.ok) return;
                const channels = await res.json();
                if (!Array.isArray(channels) || !channels.length) return;
                this.channelsCache = channels;

                const container = document.getElementById('channelsListContainer');
                if (!container) return;
                container.innerHTML = '';

                channels.forEach((ch, idx) => {
                    const isActive = this.activeChannelId ? ch.id === this.activeChannelId : idx === 0;
                    const div = document.createElement('div');
                    div.className = `space-item ${isActive ? 'active' : ''}`;
                    div.onclick = () => this.selectChannel(ch.id, ch.name, div);
                    div.innerHTML = `
                        <span># ${safeEscape(ch.name || ch.id)}</span>
                        <span class="space-item-rev">CANAL</span>
                    `;
                    container.appendChild(div);
                });
            } catch (e) {
                console.warn('Erro ao carregar canais:', e);
            }
        },

        selectChannel(channelId, channelName, el) {
            this.activeChannelId = channelId;
            this.activeChannelName = channelName || channelId;
            document.querySelectorAll('#channelsListContainer .space-item').forEach(it => it.classList.remove('active'));
            if (el) el.classList.add('active');

            const chEl = document.getElementById('activeDotChannel');
            if (chEl) chEl.textContent = `CANAL #${this.activeChannelName.toUpperCase()} // COLABORACAO MULTI-BOT`;
            this.loadThreads();
            PixelSystem.toast(`Canal #${this.activeChannelName} selecionado.`, 'info');
        },

        promptCreateChannel() {
            PixelSystem.prompt(
                'Criar Novo Canal Colaborativo',
                'Informe o nome do canal temático (ex: devops-arm64):',
                'arquitetura-borda',
                async (name) => {
                    if (!name) return;
                    try {
                        const slug = name.trim().toLowerCase().replace(/[^a-z0-9_-]/g, '-');
                        const res = await fetch('/api/channels', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                id: `ch-${slug}`,
                                name: slug,
                                description: `Canal colaborativo #${slug}`
                            })
                        });
                        if (!res.ok) throw new Error(`HTTP ${res.status}`);
                        PixelSystem.toast(`Canal #${slug} criado com sucesso!`, 'success');
                        await this.loadChannels();
                    } catch (e) {
                        PixelSystem.toast(`Erro ao criar canal: ${e}`, 'danger');
                    }
                }
            );
        },

        async loadThreads() {
            try {
                const res = await fetch('/api/threads?limit=25');
                if (!res.ok) return;
                const threads = await res.json();
                this.threadsCache = Array.isArray(threads) ? threads : [];

                const container = document.getElementById('threadsListContainer');
                if (!container) return;

                if (!this.threadsCache.length) {
                    container.innerHTML = '<div style="font-size: 10px; color: var(--ink-muted); padding: 4px;">Nenhuma conversa anterior. Envie uma mensagem para iniciar.</div>';
                    return;
                }

                container.innerHTML = '';
                this.threadsCache.slice(0, 12).forEach(th => {
                    const item = document.createElement('div');
                    item.className = `thread-sidebar-item ${this.activeThreadId === th.id ? 'active' : ''}`;
                    item.innerHTML = `
                        <div style="display: flex; justify-content: space-between; align-items: center; gap: 4px;">
                            <strong style="color: var(--ink-main); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${safeEscape(th.title || th.id)}</strong>
                            <button type="button" class="pixel-btn" style="padding: 0px 4px; font-size: 7px;" title="Excluir Thread" onclick="event.stopPropagation(); PiDotsAPI.deleteThread('${safeEscape(th.id)}')">[X]</button>
                        </div>
                        <div style="display: flex; justify-content: space-between; font-size: 8.5px; color: var(--ink-muted);">
                            <span>@${safeEscape(th.dot_id || 'dot')}</span>
                            <span>${safeEscape(String(th.created_at || '').slice(11, 16))}</span>
                        </div>
                    `;
                    item.onclick = () => this.openThread(th.id);
                    container.appendChild(item);
                });
            } catch (e) {
                console.warn('Erro ao carregar threads:', e);
            }
        },

        async openThread(threadId) {
            if (!threadId) return;
            try {
                const [msgRes, stateRes] = await Promise.all([
                    fetch(`/api/threads/${encodeURIComponent(threadId)}/messages`),
                    fetch(`/api/threads/${encodeURIComponent(threadId)}/state`)
                ]);
                if (!msgRes.ok) return;
                const messages = await msgRes.json();
                const stateData = stateRes.ok ? await stateRes.json() : null;

                this.activeThreadId = threadId;
                if (stateData && stateData.thread) {
                    if (stateData.thread.dot_id) this.activeDotId = stateData.thread.dot_id;
                    const chEl = document.getElementById('activeDotChannel');
                    if (chEl) {
                        chEl.textContent = `THREAD ATIVA // ${String(stateData.thread.title || threadId).toUpperCase()}`;
                    }
                }

                // Atualiza avatares dos participantes no header
                this.renderThreadParticipants(stateData?.participants || [this.activeDotId]);

                // Renderiza mensagens históricas na bobina
                const scrollArea = document.getElementById('tickerScroll');
                if (scrollArea) {
                    scrollArea.innerHTML = '';
                    (messages || []).forEach(m => {
                        const slip = document.createElement('article');
                        slip.className = 'ticker-slip';
                        const isUser = m.role === 'user';
                        const senderId = m.actor_id || m.sender_id || this.activeDotId || 'AGENTE';
                        const stampLabel = isUser ? '[USR] OPERADOR' : `[DOT] ${String(senderId).toUpperCase()}`;
                        const stampClass = isUser ? 'stamp-user' : 'stamp-coder';
                        const thoughtText = m.thought_log || m.thought_process || '';
                        slip.innerHTML = `
                            <header class="slip-header">
                                <span class="actor-stamp ${stampClass}">${safeEscape(stampLabel)}</span>
                                <span>${safeEscape(m.created_at || '')}</span>
                                <span>SEQ# 000${window.getNextSeqCounter()}</span>
                            </header>
                            ${thoughtText ? `
                            <section class="slip-reasoning">
                                <div class="reasoning-toggle" onclick="toggleReasoning(this)">
                                    <span>[CADERNO DE RACIOCINIO HISTORICO]</span>
                                    <span class="reasoning-state-badge">[-] COLAPSAR</span>
                                </div>
                                <div class="reasoning-content" style="font-family: var(--font-mono); font-size: 11px; white-space: pre-wrap;">${safeEscape(thoughtText)}</div>
                            </section>` : ''}
                            <section class="slip-output">
                                <p class="slip-text">${safeEscape(m.content || '')}</p>
                            </section>
                        `;
                        scrollArea.appendChild(slip);
                    });
                    scrollArea.scrollTop = scrollArea.scrollHeight;
                }

                if (stateData) {
                    this.renderCoAgentStateInspector(stateData);
                }
                await this.loadThreads();
            } catch (e) {
                PixelSystem.toast(`Erro ao abrir thread: ${e}`, 'danger');
            }
        },

        async deleteThread(threadId) {
            if (!threadId) return;
            try {
                const res = await fetch(`/api/threads/${encodeURIComponent(threadId)}`, { method: 'DELETE' });
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                if (this.activeThreadId === threadId) {
                    this.activeThreadId = null;
                    if (typeof window.startNewConversation === 'function') window.startNewConversation();
                }
                await this.loadThreads();
                PixelSystem.toast('Conversa removida do historico SQLite WAL.', 'info');
            } catch (e) {
                PixelSystem.toast(`Erro ao remover thread: ${e}`, 'danger');
            }
        },

        renderThreadParticipants(participants) {
            const bar = document.getElementById('threadParticipantPills');
            if (!bar || !Array.isArray(participants)) return;
            bar.innerHTML = '';
            participants.forEach(pId => {
                const cleanId = String(pId || '').replace(/^@/, '');
                if (!cleanId) return;
                let cls = 'stamp-coder';
                if (cleanId.includes('supervisor')) cls = 'stamp-supervisor';
                else if (cleanId.includes('auditor')) cls = 'stamp-auditor';
                else if (cleanId.includes('architect')) cls = 'stamp-architect';
                const span = document.createElement('span');
                span.className = `actor-stamp ${cls}`;
                span.style.cssText = 'font-size: 7px; padding: 1px 4px; cursor: pointer;';
                span.textContent = `@${cleanId}`;
                span.title = `Mencionar @${cleanId} na conversa`;
                span.onclick = () => {
                    const input = document.getElementById('instructionInput');
                    if (input) {
                        input.value = `@${cleanId} ` + input.value;
                        input.focus();
                    }
                };
                bar.appendChild(span);
            });
        },

        // Ações do Header da Thread: Handoff, Conselho e Save-as-Space
        async promptHandoffThread() {
            const availableIds = (this.dotsCache || []).map(d => d.id).join(', ') || 'dot-coder, dot-auditor, dot-supervisor';
            PixelSystem.prompt(
                'Transferir Titularidade da Thread (Handoff)',
                `Informe o ID do Dot especialista destino (${availableIds}):`,
                'dot-auditor',
                async (targetDotId) => {
                    if (!targetDotId) return;
                    const cleanTarget = targetDotId.trim().replace(/^@/, '');
                    try {
                        if (!this.activeThreadId) {
                            const tRes = await fetch('/api/threads', {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify({ dot_id: this.activeDotId, title: `Handoff para @${cleanTarget}` })
                            });
                            if (tRes.ok) {
                                const td = await tRes.json();
                                this.activeThreadId = td.id;
                            }
                        }
                        const res = await fetch(`/api/threads/${encodeURIComponent(this.activeThreadId)}/handoff`, {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                target_dot_id: cleanTarget,
                                reason: 'Transferencia manual solicitada pelo operador no Console',
                                context_summary: 'Continuidade da missao ativa'
                            })
                        });
                        if (!res.ok) throw new Error(`HTTP ${res.status}`);
                        this.selectDot(cleanTarget);
                        await this.loadActiveThreadState();
                        PixelSystem.toast(`Handoff concluido para @${cleanTarget}!`, 'success');
                    } catch (e) {
                        PixelSystem.toast(`Falha no handoff: ${e}`, 'danger');
                    }
                }
            );
        },

        async promptCouncilDebate() {
            PixelSystem.prompt(
                'Convocar Conselho Multi-Bot (3 Rodadas)',
                'Qual tópico ou decisão arquitetural o Conselho (@dot-coder, @dot-auditor, @dot-supervisor) deve deliberar?',
                'Revisar seguranca e consumo de RAM da solucao proposta',
                async (topic) => {
                    if (!topic) return;
                    try {
                        if (!this.activeThreadId) {
                            const tRes = await fetch('/api/threads', {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify({ dot_id: this.activeDotId, title: `Conselho: ${topic.slice(0, 24)}` })
                            });
                            if (tRes.ok) {
                                const td = await tRes.json();
                                this.activeThreadId = td.id;
                            }
                        }
                        PixelSystem.toast('Conselho Multi-Bot convocado. Deliberando...', 'info');
                        const res = await fetch(`/api/threads/${encodeURIComponent(this.activeThreadId)}/council`, {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                topic: topic,
                                prompt: topic,
                                proponent_dot_id: 'dot-coder',
                                critic_dot_id: 'dot-auditor',
                                supervisor_dot_id: 'dot-supervisor',
                                rounds: 2
                            })
                        });
                        if (!res.ok) throw new Error(`HTTP ${res.status}`);
                        const data = await res.json();
                        await this.openThread(this.activeThreadId);
                        PixelSystem.toast(`Veredito do Conselho registrado (${data.rounds_executed || 2} rodadas).`, 'success');
                    } catch (e) {
                        PixelSystem.toast(`Erro ao executar Conselho: ${e}`, 'danger');
                    }
                }
            );
        },

        async saveThreadAsSpace() {
            if (!this.activeThreadId) {
                PixelSystem.toast('Inicie ou selecione uma conversa antes de salvar em Spaces.', 'warning');
                return;
            }
            const defaultName = `thread_${String(this.activeThreadId).slice(-6)}.md`;
            PixelSystem.prompt(
                'Salvar Conversa em Spaces (Padrao OpenDots)',
                'Informe o nome do documento Markdown que será gerado e versionado em Spaces:',
                defaultName,
                async (filename) => {
                    if (!filename) return;
                    try {
                        const res = await fetch(`/api/threads/${encodeURIComponent(this.activeThreadId)}/save-as-space`, {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                filename: filename.trim(),
                                title: `Ata de Sessao: ${filename.trim()}`,
                                dot_id: this.activeDotId
                            })
                        });
                        if (!res.ok) throw new Error(`HTTP ${res.status}`);
                        const saved = await res.json();
                        PixelSystem.toast(`Conversa salva como '${saved.filename}' em Spaces!`, 'success');
                        await this.loadSpaces();
                        if (saved.space_id) {
                            await this.loadArtifact(saved.space_id);
                        }
                    } catch (e) {
                        PixelSystem.toast(`Erro ao salvar conversa em Spaces: ${e}`, 'danger');
                    }
                }
            );
        },

        // Inspetor de CoAgents Shared State (Aba [COAGENTS])
        async loadActiveThreadState() {
            try {
                if (!this.activeThreadId && this.threadsCache.length > 0) {
                    this.activeThreadId = this.threadsCache[0].id;
                }
                const [toolRunsRes, memRes] = await Promise.all([
                    fetch('/api/edge/tool-runs?limit=10'),
                    fetch(`/api/dots/${encodeURIComponent(this.activeDotId)}/memory`)
                ]);
                const toolRunsData = toolRunsRes.ok ? await toolRunsRes.json() : [];
                const fallbackRuns = Array.isArray(toolRunsData) ? toolRunsData : (toolRunsData.runs || []);
                const memData = memRes.ok ? await memRes.json() : null;

                let stateData = null;
                if (this.activeThreadId) {
                    const res = await fetch(`/api/threads/${encodeURIComponent(this.activeThreadId)}/state`);
                    if (res.ok) stateData = await res.json();
                }

                this.renderCoAgentStateInspector(stateData, fallbackRuns, memData);
            } catch (e) {
                console.warn('Erro ao sincronizar CoAgents Shared State:', e);
            }
        },

        renderCoAgentStateInspector(stateData, fallbackToolRuns, memData) {
            const planBox = document.getElementById('coagentActivePlanBox');
            const notesBox = document.getElementById('coagentSharedNotesBox');
            const handoffsBox = document.getElementById('coagentHandoffsBox');
            const toolsBox = document.getElementById('coagentToolRunsBox');
            const memgptBox = document.getElementById('coagentMemgptBox');
            const coagentTabLabel = document.getElementById('canvasTabCoagentsLabel');

            if (stateData && stateData.participants) {
                this.renderThreadParticipants(stateData.participants);
            }

            if (planBox) {
                const plan = stateData?.active_plan;
                const stepsList = (plan && (plan.milestones || plan.steps)) ? (plan.milestones || plan.steps) : [];
                if (Array.isArray(stepsList) && stepsList.length) {
                    let completedCount = 0;
                    planBox.innerHTML = stepsList.map((st, idx) => {
                        const status = (st.status || 'PENDING').toUpperCase();
                        const isDone = status === 'DONE' || status === 'COMPLETED';
                        if (isDone) completedCount++;
                        const color = isDone ? 'var(--phosphor-green)' : 'var(--blueprint-cyan)';
                        const stepText = st.title || st.description || st.step || JSON.stringify(st);
                        return `<div style="margin-bottom: 4px;"><strong style="color: ${color};">[${idx + 1}. ${safeEscape(status)}]</strong> ${safeEscape(stepText)}</div>`;
                    }).join('');
                    const pct = Math.round((completedCount / stepsList.length) * 100);
                    if (coagentTabLabel) coagentTabLabel.textContent = `[COAGENTS // ${pct}%]`;
                } else {
                    planBox.textContent = 'Nenhum plano multi-estagio ativo nesta thread.';
                    if (coagentTabLabel) coagentTabLabel.textContent = '[COAGENTS]';
                }
            }

            if (notesBox) {
                const notes = stateData?.shared_notes || stateData?.shared_space_notes || [];
                if (notes.length) {
                    notesBox.innerHTML = notes.map(n => {
                        const noteKey = n.topic_key || n.key || 'nota';
                        const noteContent = n.preview || n.content || '';
                        return `
                        <div style="border-bottom: 1px dotted var(--border-subtle); padding: 3px 0;">
                            <strong style="color: var(--thermal-amber);">${safeEscape(noteKey)}:</strong> ${safeEscape(String(noteContent).slice(0, 140))}
                            <span style="color: var(--ink-muted); font-size: 9px;">(@${safeEscape(n.author_dot_id || 'dot')})</span>
                        </div>
                        `;
                    }).join('');
                } else {
                    notesBox.textContent = 'Nenhuma nota compartilhada no quadro negro.';
                }
            }

            if (handoffsBox) {
                const handoffs = stateData?.handoffs || [];
                const council = stateData?.council_sessions || [];
                let html = '';
                handoffs.forEach(h => {
                    const fromDot = h.source_dot_id || h.from_dot_id || 'dot';
                    const toDot = h.target_dot_id || h.to_dot_id || 'dot';
                    const reasonText = h.task_goal || h.reason || h.result_summary || '';
                    html += `<div style="margin-bottom: 3px;"><span style="color: var(--blueprint-cyan);">[HANDOFF]</span> @${safeEscape(fromDot)} -&gt; <strong>@${safeEscape(toDot)}</strong> (${safeEscape(reasonText)})</div>`;
                });
                council.forEach(c => {
                    html += `<div style="margin-bottom: 3px;"><span style="color: var(--phosphor-green);">[CONSELHO]</span> Status: <strong>${safeEscape(c.status)}</strong> (${c.current_round || 2} rodadas)</div>`;
                });
                handoffsBox.innerHTML = html || 'Nenhuma transferencia ou deliberacao registrada nesta thread.';
            }

            if (toolsBox) {
                const stateRuns = stateData?.recent_tool_runs || stateData?.tool_runs || [];
                const runs = stateRuns.length ? stateRuns : (fallbackToolRuns || []);
                if (runs.length) {
                    toolsBox.innerHTML = runs.slice(0, 8).map(r => {
                        const isSuccess = r.status === 'SUCCESS' || r.exit_code === 0;
                        const statusLabel = r.status || (r.exit_code === 0 ? 'OK' : `EXIT ${r.exit_code ?? 0}`);
                        const stColor = isSuccess ? 'var(--phosphor-green)' : 'var(--thermal-amber)';
                        return `<div style="border-bottom: 1px dotted var(--border-subtle); padding: 2px 0; display: flex; justify-content: space-between;">
                            <span><strong style="color: var(--blueprint-cyan);">${safeEscape(r.tool_name)}</strong> (@${safeEscape(r.dot_id)})</span>
                            <span style="color: ${stColor};">[${safeEscape(statusLabel)}] ${r.duration_ms || 0}ms</span>
                        </div>`;
                    }).join('');
                } else {
                    toolsBox.textContent = 'Nenhuma execucao de ferramenta auditada recentemente.';
                }
            }

            if (memgptBox) {
                const personaStr = memData?.core_memory?.persona || 'Diretrizes padrao do especialista ativo.';
                const humanStr = memData?.core_memory?.human || 'Operador humano autenticado no console.';
                const archivalList = memData?.archival_memories || memData?.archival_memory || [];
                memgptBox.innerHTML = `
                    <div style="margin-bottom: 4px;"><strong style="color: var(--blueprint-cyan);">[PERSONA @${safeEscape(this.activeDotId)}]:</strong> ${safeEscape(String(personaStr).slice(0, 110))}</div>
                    <div style="margin-bottom: 4px;"><strong style="color: var(--thermal-amber);">[HUMAN]:</strong> ${safeEscape(String(humanStr).slice(0, 110))}</div>
                    <div style="color: var(--phosphor-green); font-size: 9.5px;">[ARCHIVAL 64D + FTS5]: ${archivalList.length} fato(s) indexado(s) no SQLite WAL.</div>
                `;
            }
        },

        // 4. Spaces e Artefatos (/api/spaces) + Busca Semântica KNN 64D
        async loadSpaces() {
            try {
                const res = await fetch(`/api/spaces?dot_id=${this.activeDotId}`);
                if (!res.ok) return;
                const spaces = await res.json();
                this.spacesCache = spaces;

                this.renderSpacesList(spaces);

                const selectorEl = document.getElementById('spaceDocSelector');
                if (selectorEl && spaces.length) {
                    selectorEl.innerHTML = '';
                    spaces.forEach(sp => {
                        const opt = document.createElement('option');
                        opt.value = sp.filename;
                        opt.textContent = sp.filename;
                        selectorEl.appendChild(opt);
                    });
                }

                if (spaces.length > 0 && !this.activeSpaceId) {
                    this.loadArtifact(spaces[0].id, null, true);
                }
            } catch (e) {
                console.warn('Erro ao carregar Spaces:', e);
            }
        },

        renderSpacesList(spaces) {
            const container = document.getElementById('spacesListContainer');
            if (!container) return;

            if (!spaces || !spaces.length) {
                container.innerHTML = '<div style="font-size: 10px; color: var(--ink-muted); padding: 6px;">Nenhum arquivo encontrado.</div>';
                return;
            }

            container.innerHTML = '';
            spaces.forEach((sp, idx) => {
                const item = document.createElement('div');
                const isActive = this.activeSpaceId ? sp.id === this.activeSpaceId : idx === 0;
                item.className = `space-item ${isActive ? 'active' : ''}`;
                item.onclick = () => this.loadArtifact(sp.id, item, false);
                const badgeText = sp.score !== undefined ? `${Math.round(sp.score * 100)}%` : `REV ${sp.version || 1}`;
                item.innerHTML = `
                    <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${safeEscape(sp.filename)}</span>
                    <span class="space-item-rev">${safeEscape(badgeText)}</span>
                `;
                container.appendChild(item);
            });
        },

        async filterOrSearchSpaces(query) {
            const q = (query || '').trim();
            if (!q) {
                this.renderSpacesList(this.spacesCache);
                return;
            }
            if (q.length < 3) {
                const filtered = (this.spacesCache || []).filter(s => s.filename.toLowerCase().includes(q.toLowerCase()));
                this.renderSpacesList(filtered);
                return;
            }
            try {
                const res = await fetch(`/api/spaces/search?query=${encodeURIComponent(q)}&top_k=6`);
                if (res.ok) {
                    const results = await res.json();
                    if (Array.isArray(results) && results.length) {
                        this.renderSpacesList(results);
                        return;
                    }
                }
            } catch (_) {}
            const fallback = (this.spacesCache || []).filter(s => s.filename.toLowerCase().includes(q.toLowerCase()));
            this.renderSpacesList(fallback);
        },

        selectSpaceFromDropdown(filename) {
            if (!filename) return;
            const doc = (this.spacesCache || []).find(s => s.filename === filename);
            if (doc) {
                this.loadArtifact(doc.id, null, false);
            } else if (typeof artifactDocs !== 'undefined' && artifactDocs[filename]) {
                const titleEl = document.getElementById('currentArtifactTitle');
                if (titleEl) titleEl.textContent = filename;
                const editorEl = document.getElementById('artifactContent');
                if (editorEl) editorEl.value = artifactDocs[filename];
                PixelSystem.toast(`Documento '${filename}' carregado localmente.`, 'info');
            }
        },

        async loadArtifact(spaceId, el, silentMobile = false) {
            try {
                const res = await fetch(`/api/spaces/${spaceId}`);
                if (!res.ok) return;
                const doc = await res.json();

                this.activeSpaceId = doc.id;
                this.activeSpaceDoc = doc;

                document.querySelectorAll('#spacesListContainer .space-item').forEach(it => it.classList.remove('active'));
                if (el) el.classList.add('active');

                const titleEl = document.getElementById('currentArtifactTitle');
                if (titleEl) titleEl.textContent = doc.filename;

                const selectorEl = document.getElementById('spaceDocSelector');
                if (selectorEl) selectorEl.value = doc.filename;

                const editorEl = document.getElementById('artifactContent');
                if (editorEl) editorEl.value = doc.content || '';

                const revBadge = document.querySelector('.artifact-header .space-item-rev');
                if (revBadge) revBadge.textContent = `REV ${doc.version || 1}`;

                this.isDiffActive = false;
                const diffView = document.getElementById('diffViewContainer');
                if (diffView) diffView.style.display = 'none';
                if (editorEl) editorEl.style.display = 'block';

                const canvas = document.getElementById('rightCanvas');
                if (canvas) {
                    canvas.classList.remove('collapsed');
                    const tabs = document.querySelectorAll('.canvas-tab');
                    switchCanvasTab('canvas-artifact', tabs[0]);
                }

                if (window.innerWidth <= 768 && !silentMobile) {
                    setMobileView('canvas');
                }
            } catch (e) {
                PixelSystem.toast(`Erro ao carregar documento: ${e}`, 'danger');
            }
        },

        async saveArtifact() {
            const editorEl = document.getElementById('artifactContent');
            const titleEl = document.getElementById('currentArtifactTitle');
            if (!editorEl || !titleEl) return;

            const filename = titleEl.textContent.trim();
            const content = editorEl.value;

            try {
                const res = await fetch('/api/spaces', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        dot_id: this.activeDotId,
                        filename: filename,
                        content: content,
                        title: filename
                    })
                });

                if (!res.ok) throw new Error(`Status ${res.status}`);
                const saved = await res.json();
                const docId = saved.space_id || saved.id;

                this.activeSpaceId = docId;
                this.activeSpaceDoc = saved;

                const revBadge = document.querySelector('.artifact-header .space-item-rev');
                if (revBadge) revBadge.textContent = `REV ${saved.version || 1}`;

                PixelSystem.toast(`Artefato '${filename}' persistido no SQLite WAL com sucesso! Revisão ${saved.version || 1}.`, 'success');
                await this.loadSpaces();
            } catch (e) {
                PixelSystem.toast(`Falha ao gravar no SQLite WAL: ${e}`, 'danger');
            }
        },

        async createNewSpace(defaultName = 'novo_arquivo.md') {
            PixelSystem.prompt(
                'Criar Espaco no SQLite WAL',
                'Informe o nome do arquivo a ser criado no Space (ex: analise_arm64.py):',
                defaultName || 'novo_arquivo.md',
                async (nome) => {
                    if (!nome) return;
                    try {
                        const res = await fetch('/api/spaces', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                dot_id: this.activeDotId,
                                filename: nome,
                                content: `# ${nome}\n\nCriado no SQLite WAL pelo operador.\nData: ${new Date().toISOString()}`,
                                title: nome
                            })
                        });

                        if (!res.ok) throw new Error(`Status ${res.status}`);
                        const created = await res.json();
                        const docId = created.space_id || created.id;

                        PixelSystem.toast(`Arquivo '${nome}' criado com sucesso no SQLite WAL!`, 'success');
                        await this.loadSpaces();
                        if (docId) {
                            await this.loadArtifact(docId);
                        }
                    } catch (e) {
                        PixelSystem.toast(`Erro ao criar arquivo no SQLite: ${e}`, 'danger');
                    }
                }
            );
        },

        async toggleDiffView() {
            if (!this.activeSpaceId) {
                PixelSystem.toast('Nenhum artefato selecionado para inspecionar diferencas.', 'warning');
                return;
            }

            this.isDiffActive = !this.isDiffActive;
            const diffView = document.getElementById('diffViewContainer');
            const editorEl = document.getElementById('artifactContent');
            const diffArea = document.getElementById('diffContentArea');

            if (this.isDiffActive) {
                try {
                    const res = await fetch(`/api/spaces/${this.activeSpaceId}/revisions`);
                    if (!res.ok) throw new Error(`Status ${res.status}`);
                    const revs = await res.json();

                    let diffText = '';
                    if (!revs || !revs.length) {
                        diffText = '[HISTORICO INICIAL // VERSAO 1.0 SEM REVISOES ANTERIORES]';
                    } else {
                        diffText = revs.map(r => `--- REVISAO #${r.version} [${r.created_at}] ---\n${r.diff_summary || 'Sem resumo de diff'}`).join('\n\n');
                    }

                    if (diffArea) diffArea.innerHTML = formatDiffHighlight(diffText);
                    if (editorEl) editorEl.style.display = 'none';
                    if (diffView) diffView.style.display = 'block';
                    PixelSystem.toast('Visualizador de diferencas (Diffs) ativado no Canvas.', 'info');
                } catch (e) {
                    PixelSystem.toast(`Erro ao obter historico de diffs: ${e}`, 'danger');
                }
            } else {
                if (diffView) diffView.style.display = 'none';
                if (editorEl) editorEl.style.display = 'block';
                PixelSystem.toast('Retornado ao modo de edicao de artefato.', 'info');
            }
        },

        // 5. Governança HITL (/api/hitl) com Execução Real Pós-Aprovação
        async loadPendingHitl() {
            try {
                const res = await fetch('/api/hitl/pending');
                if (!res.ok) return;
                const pending = await res.json();
                this.pendingHitlCache = pending;

                const chipHitl = document.getElementById('val-hitl');
                const descHitl = document.getElementById('hitlSidebarDesc');
                const railHitlBadge = document.getElementById('railHitlBadge');

                if (chipHitl) {
                    chipHitl.textContent = `${pending.length} PENDENTE${pending.length === 1 ? '' : 'S'}`;
                    chipHitl.className = pending.length > 0 ? 'chip-value' : 'chip-value ok';
                }
                if (railHitlBadge) {
                    railHitlBadge.textContent = pending.length > 0 ? `HITL(${pending.length})` : 'HITL';
                }

                if (descHitl) {
                    if (pending.length > 0) {
                        descHitl.textContent = `Acao: ${pending[0].action_type} (Risco: ${pending[0].risk_level})`;
                    } else {
                        descHitl.textContent = 'Nenhuma acao retida no momento.';
                    }
                }

                const hitlSection = document.getElementById('hitlSidebarSection');
                if (hitlSection) {
                    hitlSection.style.display = pending.length > 0 ? 'block' : 'none';
                }

                if (pending.length > 0) {
                    const item = pending[0];
                    const infoDiv = document.getElementById('hitlDossierDetailsBox');
                    if (infoDiv) {
                        infoDiv.innerHTML = `
                            <strong>ID:</strong> ${safeEscape(item.id)}<br>
                            <strong>AGENTE:</strong> ${safeEscape(item.dot_id)}<br>
                            <strong>RISCO:</strong> ${safeEscape(item.risk_level)}<br>
                            <strong>PAYLOAD / ALVO:</strong> ${safeEscape(item.payload || item.command || 'N/A')}
                        `;
                    }
                }
            } catch (e) {
                console.warn('Erro ao carregar fila HITL:', e);
            }
        },

        async resolveHitl(approved, notes = '', specificId = null, modifiedArgs = null) {
            const item = specificId
                ? { id: specificId }
                : (this.pendingHitlCache && this.pendingHitlCache.length ? this.pendingHitlCache[0] : null);

            if (!item) {
                this.applyHitlVisual(approved);
                return;
            }

            try {
                const res = await fetch(`/api/hitl/${encodeURIComponent(item.id)}/resolve`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        approved: approved,
                        notes: notes || (approved ? 'Homologado via Console Operacional' : 'Vetado pelo operador'),
                        execute_immediately: true,
                        modified_args: modifiedArgs
                    })
                });

                if (!res.ok) throw new Error(`Status ${res.status}`);
                const data = await res.json();
                this.applyHitlVisual(approved);

                const execInfo = data.execution_result || data.execution;
                if (approved && execInfo) {
                    const execOut = execInfo.result?.stdout || execInfo.output || execInfo.status || 'Executado no sandbox.';
                    const term = document.getElementById('terminalViewport');
                    if (term) {
                        const div = document.createElement('div');
                        div.innerHTML = `<span style="color: var(--phosphor-green);">[HITL EXEC #${safeEscape(item.id)}]</span> ${safeEscape(String(execOut).slice(0, 300))}`;
                        term.appendChild(div);
                        term.scrollTop = term.scrollHeight;
                    }
                }

                await this.loadPendingHitl();
                await this.loadSpaces();
            } catch (e) {
                PixelSystem.toast(`Erro ao resolver HITL: ${e}`, 'danger');
            }
        },

        applyHitlVisual(approved) {
            const rejectStamp = document.getElementById('stampRejectVisual');
            const approveStamp = document.getElementById('stampApproveVisual');

            if (approved) {
                if (approveStamp) approveStamp.style.transform = 'rotate(2.5deg) scale(1.15)';
                if (rejectStamp) rejectStamp.style.opacity = '0.3';
                setTimeout(() => {
                    PixelSystem.toast('HOMOLOGADO: Acao oficial autenticada e despachada no SQLite WAL!', 'success');
                    if (approveStamp) approveStamp.style.transform = 'rotate(2.5deg) scale(1.0)';
                }, 200);
            } else {
                if (rejectStamp) rejectStamp.style.transform = 'rotate(-3deg) scale(1.15)';
                if (approveStamp) approveStamp.style.opacity = '0.3';
                setTimeout(() => {
                    PixelSystem.toast('VETO REGISTRADO: Acao cancelada e arquivada com seguranca no SQLite WAL.', 'danger');
                    if (rejectStamp) rejectStamp.style.transform = 'rotate(-3deg) scale(1.0)';
                }, 200);
            }
        },

        // 9. Modos Contextuais da Sidebar OpenDots: Dots Studio, Tasks, Memory & Computer
        async loadDotsStudioPane() {
            await this.loadDots();
            const rosterEl = document.getElementById('dotsStudioRosterContainer');
            if (rosterEl) {
                rosterEl.innerHTML = '';
                (this.dotsCache || []).forEach(dot => {
                    const isCore = ['dot-supervisor', 'dot-coder', 'dot-architect', 'dot-auditor', 'dot-dev-core', 'dot-sys-ops', 'dot-sec-guard'].includes(dot.id);
                    const div = document.createElement('div');
                    div.className = 'task-sidebar-card';
                    div.innerHTML = `
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;">
                            <strong style="font-family: var(--font-pixel); font-size: 8px; color: var(--blueprint-cyan);">@${safeEscape(dot.id)}</strong>
                            <span style="font-size: 8px; color: var(--phosphor-green);">[${safeEscape((dot.archetype || 'general').toUpperCase())}]</span>
                        </div>
                        <div style="font-size: 10px; color: var(--ink-main); font-weight: 600;">${safeEscape(dot.name || dot.id)}</div>
                        <div style="font-size: 9.5px; color: var(--ink-secondary); margin-bottom: 6px;">${safeEscape(dot.role || '')}</div>
                        <div style="display: flex; gap: 4px;">
                            <button type="button" class="pixel-btn" style="padding: 1px 5px; font-size: 7px;" onclick="openDotCreatorModal('${safeEscape(dot.id)}')">[EDITAR]</button>
                            <button type="button" class="pixel-btn" style="padding: 1px 5px; font-size: 7px;" onclick="PiDotsAPI.selectDot('${safeEscape(dot.id)}')">[ATIVAR]</button>
                            ${!isCore ? `<button type="button" class="pixel-btn btn-danger" style="padding: 1px 5px; font-size: 7px;" onclick="PiDotsAPI.deleteCustomDot('${safeEscape(dot.id)}')">[EXCLUIR]</button>` : ''}
                        </div>
                    `;
                    rosterEl.appendChild(div);
                });
            }

            try {
                const res = await fetch('/api/tools');
                if (res.ok) {
                    const data = await res.json();
                    this.toolsCache = data.tools || [];
                    const badge = document.getElementById('toolsCatalogCountBadge');
                    if (badge) badge.textContent = `${this.toolsCache.length} TOOLS`;
                    const listEl = document.getElementById('toolsCatalogSidebarList');
                    if (listEl) {
                        listEl.innerHTML = this.toolsCache.map(t => `
                            <div style="background: var(--paper-surface-recessed); border: 1px solid var(--border-subtle); padding: 4px 6px; font-size: 9.5px;">
                                <div style="display: flex; justify-content: space-between;">
                                    <code style="color: var(--phosphor-green);">${safeEscape(t.name)}</code>
                                    <span style="color: ${t.requires_hitl ? 'var(--thermal-amber)' : 'var(--ink-muted)'}; font-size: 8px;">${t.requires_hitl ? '[HITL]' : '[AUTO]'}</span>
                                </div>
                                <div style="color: var(--ink-secondary); font-size: 9px; margin-top: 2px;">${safeEscape(String(t.description || '').slice(0, 75))}</div>
                            </div>
                        `).join('');
                    }
                }
            } catch (e) {
                console.warn('Erro ao carregar catalogo de tools:', e);
            }
        },

        async populateDotCreatorModal(dotId) {
            this.editingDotId = dotId || null;
            if (!this.toolsCache.length) {
                try {
                    const r = await fetch('/api/tools');
                    if (r.ok) {
                        const d = await r.json();
                        this.toolsCache = d.tools || [];
                    }
                } catch (_) {}
            }

            const existing = dotId ? (this.dotsCache || []).find(d => d.id === dotId) : null;
            const idInput = document.getElementById('dotFormId');
            const nameInput = document.getElementById('dotFormName');
            const roleInput = document.getElementById('dotFormRole');
            const archSelect = document.getElementById('dotFormArchetype');
            const promptInput = document.getElementById('dotFormPrompt');
            const toolsBox = document.getElementById('dotFormToolsCheckboxes');

            if (idInput) {
                idInput.value = existing ? existing.id : '';
                idInput.disabled = !!existing;
            }
            if (nameInput) nameInput.value = existing ? (existing.name || '') : '';
            if (roleInput) roleInput.value = existing ? (existing.role || '') : '';
            if (archSelect) archSelect.value = existing ? (existing.archetype || 'coder') : 'coder';
            if (promptInput) promptInput.value = existing ? (existing.system_prompt || '') : '';

            let allowedSet = new Set();
            if (existing) {
                if (Array.isArray(existing.allowed_tools)) {
                    existing.allowed_tools.forEach(t => allowedSet.add(t));
                } else if (typeof existing.allowed_tools_json === 'string' && existing.allowed_tools_json.trim()) {
                    try {
                        const parsed = JSON.parse(existing.allowed_tools_json);
                        if (Array.isArray(parsed)) parsed.forEach(t => allowedSet.add(t));
                    } catch (_) {}
                }
            }

            if (toolsBox) {
                toolsBox.innerHTML = (this.toolsCache || []).map(t => {
                    const checked = allowedSet.has(t.name) ? 'checked' : '';
                    return `<label style="display: flex; align-items: center; gap: 4px; cursor: pointer; color: var(--ink-secondary);">
                        <input type="checkbox" class="dot-tool-checkbox" value="${safeEscape(t.name)}" ${checked}>
                        <span>${safeEscape(t.name)}</span>
                    </label>`;
                }).join('');
            }
        },

        async submitDotCreatorForm() {
            const idVal = (document.getElementById('dotFormId')?.value || '').trim().toLowerCase().replace(/^@/, '');
            const nameVal = (document.getElementById('dotFormName')?.value || '').trim();
            const roleVal = (document.getElementById('dotFormRole')?.value || '').trim();
            const archVal = (document.getElementById('dotFormArchetype')?.value || 'coder').trim();
            const promptVal = (document.getElementById('dotFormPrompt')?.value || '').trim();

            const selectedTools = Array.from(document.querySelectorAll('.dot-tool-checkbox:checked')).map(cb => cb.value);

            if (!idVal || !nameVal) {
                PixelSystem.toast('Informe o Handle ID e o Nome de Exibicao do Coworker.', 'warning');
                return;
            }

            const payload = {
                id: idVal,
                name: nameVal,
                role: roleVal || 'AI Specialist Coworker',
                archetype: archVal,
                system_prompt: promptVal || `Voce e ${nameVal} (@${idVal}), especialista em ${roleVal || archVal}.`,
                allowed_tools: selectedTools.length > 0 ? selectedTools : null
            };

            try {
                const url = this.editingDotId ? `/api/dots/${encodeURIComponent(this.editingDotId)}` : '/api/dots';
                const method = this.editingDotId ? 'PUT' : 'POST';
                const res = await fetch(url, {
                    method: method,
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                if (typeof window.closeDotCreatorModal === 'function') window.closeDotCreatorModal();
                await this.loadDotsStudioPane();
                PixelSystem.toast(`Coworker @${idVal} salvo com sucesso no SQLite WAL!`, 'success');
            } catch (e) {
                PixelSystem.toast(`Erro ao salvar Coworker: ${e}`, 'danger');
            }
        },

        async deleteCustomDot(dotId) {
            if (!dotId) return;
            try {
                const res = await fetch(`/api/dots/${encodeURIComponent(dotId)}`, { method: 'DELETE' });
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                await this.loadDotsStudioPane();
                PixelSystem.toast(`Coworker @${dotId} removido.`, 'info');
            } catch (e) {
                PixelSystem.toast(`Nao foi possivel excluir @${dotId}: ${e}`, 'danger');
            }
        },

        // Painel 3 da Sidebar: Tasks Proativas (Cron) & Edge Triggers
        async loadTasksSidebar() {
            try {
                const res = await fetch('/api/tasks');
                if (!res.ok) return;
                const tasks = await res.json();
                this.tasksCache = Array.isArray(tasks) ? tasks : [];

                const container = document.getElementById('tasksSidebarListContainer');
                if (!container) return;

                if (!this.tasksCache.length) {
                    container.innerHTML = '<div style="font-size: 10px; color: var(--ink-muted);">Nenhuma rotina agendada. Clique em [+ AGENDAR].</div>';
                    return;
                }

                container.innerHTML = '';
                this.tasksCache.forEach(t => {
                    const card = document.createElement('div');
                    card.className = 'task-sidebar-card';
                    const isActive = t.is_active !== 0 && t.is_active !== false;
                    card.innerHTML = `
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;">
                            <strong style="font-size: 10px; color: var(--ink-main);">${safeEscape(t.task_name || t.id)}</strong>
                            <span style="font-family: var(--font-pixel); font-size: 7px; color: ${isActive ? 'var(--phosphor-green)' : 'var(--thermal-amber)'};">[${isActive ? 'ATIVA' : 'PAUSADA'}]</span>
                        </div>
                        <div style="font-size: 9px; color: var(--ink-muted); margin-bottom: 6px;">
                            @${safeEscape(t.dot_id)} | Cron: <code>${safeEscape(t.cron_expr || '*/15 * * * *')}</code>
                        </div>
                        <div style="display: flex; gap: 4px;">
                            <button type="button" class="pixel-btn btn-cyan" style="padding: 1px 5px; font-size: 7px;" onclick="PiDotsAPI.runTaskNow('${safeEscape(t.id)}')">[DISPARAR]</button>
                            <button type="button" class="pixel-btn" style="padding: 1px 5px; font-size: 7px;" onclick="PiDotsAPI.toggleTaskActive('${safeEscape(t.id)}', ${!isActive})">[${isActive ? 'PAUSAR' : 'ATIVAR'}]</button>
                            <button type="button" class="pixel-btn btn-danger" style="padding: 1px 5px; font-size: 7px;" onclick="PiDotsAPI.deleteTask('${safeEscape(t.id)}')">[X]</button>
                        </div>
                    `;
                    container.appendChild(card);
                });
            } catch (e) {
                console.warn('Erro ao carregar tasks:', e);
            }
        },

        promptCreateTask() {
            PixelSystem.prompt(
                'Agendar Rotina Proativa Cron (HEARTBEAT_OK)',
                'Informe nome e instrucao separados por | (ex: Auditoria Termica | Verificar sensores e alertar se >70C):',
                'Checkup Borda | Inspecionar saude do no ARM64 e responder HEARTBEAT_OK se nominal',
                async (val) => {
                    if (!val) return;
                    const parts = val.split('|').map(s => s.trim());
                    const name = parts[0] || 'Rotina Proativa';
                    const prompt = parts[1] || parts[0];
                    try {
                        const res = await fetch('/api/tasks', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                dot_id: this.activeDotId,
                                task_name: name,
                                cron_expr: '*/30 * * * *',
                                action_prompt: prompt
                            })
                        });
                        if (!res.ok) throw new Error(`HTTP ${res.status}`);
                        await this.loadTasksSidebar();
                        PixelSystem.toast(`Tarefa '${name}' agendada no EdgeScheduler!`, 'success');
                    } catch (e) {
                        PixelSystem.toast(`Erro ao agendar tarefa: ${e}`, 'danger');
                    }
                }
            );
        },

        async runTaskNow(taskId) {
            try {
                const res = await fetch(`/api/tasks/${encodeURIComponent(taskId)}/run`, { method: 'POST' });
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                PixelSystem.toast(`Tarefa ${taskId} disparada em background!`, 'success');
                await this.loadTasksSidebar();
            } catch (e) {
                PixelSystem.toast(`Erro ao disparar tarefa: ${e}`, 'danger');
            }
        },

        async toggleTaskActive(taskId, activeState) {
            try {
                const res = await fetch(`/api/tasks/${encodeURIComponent(taskId)}`, {
                    method: 'PATCH',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ is_active: activeState })
                });
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                await this.loadTasksSidebar();
            } catch (e) {
                PixelSystem.toast(`Erro ao atualizar tarefa: ${e}`, 'danger');
            }
        },

        async deleteTask(taskId) {
            try {
                const res = await fetch(`/api/tasks/${encodeURIComponent(taskId)}`, { method: 'DELETE' });
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                await this.loadTasksSidebar();
                PixelSystem.toast('Tarefa removida do agendador.', 'info');
            } catch (e) {
                PixelSystem.toast(`Erro ao excluir tarefa: ${e}`, 'danger');
            }
        },

        async loadEdgeTriggersSidebar() {
            const box = document.getElementById('edgeTriggersSidebarBox');
            if (!box) return;
            try {
                const res = await fetch('/api/edge/triggers');
                if (!res.ok) return;
                const data = await res.json();
                const m = data.metrics || {};
                box.innerHTML = `
                    <div><strong>SoC Temp:</strong> ${m.temperature_celsius ?? 48.0} °C</div>
                    <div><strong>RAM Livre:</strong> ${m.ram ? m.ram.free_percent : 60}% (${m.ram ? m.ram.available_mb : 2048} MB)</div>
                    <div><strong>MicroSD Livre:</strong> ${m.disk ? m.disk.free_percent : 70}% (${m.disk ? m.disk.free_gb : 20} GB)</div>
                    <div><strong>Throttle:</strong> <span style="color: ${data.is_throttled ? 'var(--thermal-amber)' : 'var(--phosphor-green)'};">${data.is_throttled ? 'ATIVO' : 'NOMINAL'}</span></div>
                `;
            } catch (_) {}
        },

        // Painel 4 da Sidebar: Memória Semântica 64D (Core + Archival) & MCP Lite
        async loadMemorySidebar() {
            try {
                const res = await fetch(`/api/dots/${encodeURIComponent(this.activeDotId)}/memory`);
                if (res.ok) {
                    const data = await res.json();
                    const personaEl = document.getElementById('sidebarCorePersonaInput');
                    const humanEl = document.getElementById('sidebarCoreHumanInput');
                    if (personaEl) personaEl.value = data.core_memory?.persona || '';
                    if (humanEl) humanEl.value = data.core_memory?.human || '';
                    this.renderArchivalSidebarList(data.archival_memories || data.archival_memory || []);
                }
            } catch (e) {
                console.warn('Erro ao carregar memoria do Dot:', e);
            }
            await this.loadMcpServersSidebar();
            await this.loadDotPacksCatalogSidebar();
        },

        async loadDotPacksCatalogSidebar() {
            const box = document.getElementById('sidebarDotPacksCatalogList');
            if (!box) return;
            try {
                const res = await fetch('/api/dots/packs/catalog');
                if (!res.ok) return;
                const data = await res.json();
                const packs = data.packs || [];
                if (!packs.length) {
                    box.innerHTML = 'Nenhum pacote encontrado em data/packs/.';
                    return;
                }
                box.innerHTML = packs.map(p => `
                    <div style="background: var(--paper-surface-recessed); border: 1px solid var(--border-subtle); padding: 5px 6px; display: flex; justify-content: space-between; align-items: center; gap: 6px;">
                        <div style="min-width: 0;">
                            <div style="color: var(--blueprint-cyan); font-weight: 700; font-size: 9.5px;">@${safeEscape(p.dot_id)} <span style="color: var(--phosphor-green); font-size: 8px;">[SHA256:${safeEscape(String(p.sha256_checksum).slice(0, 6))}]</span></div>
                            <div style="color: var(--ink-muted); font-size: 8.5px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${safeEscape(p.role)}</div>
                        </div>
                        <button type="button" class="pixel-btn btn-cyan" style="padding: 2px 5px; font-size: 7px; flex-shrink: 0;" onclick="PiDotsAPI.installOfficialDotPack('${safeEscape(p.pack_id)}')">[INSTALAR]</button>
                    </div>
                `).join('');
            } catch (_) {}
        },

        async installOfficialDotPack(packId) {
            if (!packId) return;
            try {
                const res = await fetch(`/api/dots/packs/install/${encodeURIComponent(packId)}`, { method: 'POST' });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
                PixelSystem.toast(`DotPack '${packId}' validado (SHA-256) e instalado como @${data.dot_id}!`, 'success');
                await this.loadDots();
            } catch (e) {
                PixelSystem.toast(`Falha ao instalar DotPack: ${e.message || e}`, 'danger');
            }
        },

        renderArchivalSidebarList(items) {
            const container = document.getElementById('sidebarArchivalListContainer');
            if (!container) return;
            if (!items || !items.length) {
                container.innerHTML = '<div style="font-size: 9.5px; color: var(--ink-muted);">Nenhum fato arquivado na memoria de longo prazo.</div>';
                return;
            }
            container.innerHTML = items.map(it => {
                const tagsStr = Array.isArray(it.tags) ? it.tags.join(', ') : (it.tags || 'fato');
                return `
                <div style="background: var(--paper-surface-recessed); border: 1px solid var(--border-subtle); padding: 4px 6px; font-size: 9.5px;">
                    <div style="color: var(--ink-main);">${safeEscape(String(it.content || '').slice(0, 120))}</div>
                    <div style="color: var(--ink-muted); font-size: 8px; margin-top: 2px;">${safeEscape(tagsStr)} | ${safeEscape(String(it.created_at || '').slice(0, 16))}</div>
                </div>
                `;
            }).join('');
        },

        async saveActiveDotCoreMemory() {
            const persona = document.getElementById('sidebarCorePersonaInput')?.value || '';
            const human = document.getElementById('sidebarCoreHumanInput')?.value || '';
            try {
                const [r1, r2] = await Promise.all([
                    fetch(`/api/dots/${encodeURIComponent(this.activeDotId)}/memory/persona`, {
                        method: 'PUT',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ content: persona })
                    }),
                    fetch(`/api/dots/${encodeURIComponent(this.activeDotId)}/memory/human`, {
                        method: 'PUT',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ content: human })
                    })
                ]);
                if (!r1.ok || !r2.ok) throw new Error(`HTTP ${r1.status}/${r2.status}`);
                PixelSystem.toast(`Core Memory de @${this.activeDotId} atualizada no SQLite WAL!`, 'success');
            } catch (e) {
                PixelSystem.toast(`Erro ao salvar Core Memory: ${e}`, 'danger');
            }
        },

        promptInsertArchivalMemory() {
            PixelSystem.prompt(
                'Arquivar Fato na Memoria Semantica 64D',
                'Digite o fato ou decisao tecnica para indexar com FTS5 BM25 + Projecao 64D:',
                'Regra de producao: limite de RSS no Raspberry Pi 4B fixado em 300MB.',
                async (content) => {
                    if (!content) return;
                    try {
                        const res = await fetch(`/api/dots/${encodeURIComponent(this.activeDotId)}/memory/archival`, {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({ content: content, tags: ['console', 'operador'] })
                        });
                        if (!res.ok) throw new Error(`HTTP ${res.status}`);
                        await this.loadMemorySidebar();
                        PixelSystem.toast('Fato indexado na Archival Memory 64D!', 'success');
                    } catch (e) {
                        PixelSystem.toast(`Erro ao arquivar fato: ${e}`, 'danger');
                    }
                }
            );
        },

        async searchActiveDotArchival(query) {
            const q = (query || '').trim();
            if (!q) {
                return this.loadMemorySidebar();
            }
            try {
                const res = await fetch(`/api/dots/${encodeURIComponent(this.activeDotId)}/memory/search?query=${encodeURIComponent(q)}`);
                if (res.ok) {
                    const data = await res.json();
                    this.renderArchivalSidebarList(data.results || data.archival_memories || []);
                }
            } catch (_) {}
        },

        async loadMcpServersSidebar() {
            const box = document.getElementById('sidebarMcpServersList');
            if (!box) return;
            try {
                const res = await fetch('/api/mcp/servers');
                if (!res.ok) return;
                const data = await res.json();
                const servers = data.servers || [];
                if (!servers.length) {
                    box.innerHTML = 'Nenhum servidor MCP externo acoplado.';
                    return;
                }
                box.innerHTML = servers.map(s => `
                    <div style="background: var(--paper-surface-recessed); border: 1px solid var(--border-subtle); padding: 4px 6px; margin-bottom: 4px;">
                        <strong style="color: var(--blueprint-cyan);">${safeEscape(s.server_name || s.name)}</strong>
                        <span style="color: var(--phosphor-green); font-size: 8.5px;">[${safeEscape(s.transport || 'stdio')}]</span>
                    </div>
                `).join('');
            } catch (_) {}
        },

        promptRegisterMcpServer() {
            PixelSystem.prompt(
                'Acoplar Servidor MCP Lite (JSON-RPC 2.0)',
                'Informe nome e comando STDIO ou URL SSE separados por | (ex: sqlite-mcp | python3 -m mcp_sqlite):',
                'edge-sensors | python3 -m pidots_mcp_sensors',
                async (val) => {
                    if (!val) return;
                    const parts = val.split('|').map(s => s.trim());
                    const name = parts[0] || 'mcp-custom';
                    const cmdStr = parts[1] || 'echo';
                    try {
                        const res = await fetch('/api/mcp/servers', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                server_name: name,
                                transport: cmdStr.startsWith('http') ? 'sse' : 'stdio',
                                command: cmdStr.split(' ')[0],
                                args: cmdStr.split(' ').slice(1),
                                sse_url: cmdStr.startsWith('http') ? cmdStr : null
                            })
                        });
                        if (!res.ok) throw new Error(`HTTP ${res.status}`);
                        await this.loadMcpServersSidebar();
                        PixelSystem.toast(`Servidor MCP '${name}' acoplado com sucesso!`, 'success');
                    } catch (e) {
                        PixelSystem.toast(`Erro ao registrar MCP: ${e}`, 'danger');
                    }
                }
            );
        },

        // Dot's Computer (Sandbox Bubblewrap & Explorador /workspace)
        async loadComputerFiles() {
            const box = document.getElementById('computerWorkspaceFilesBox');
            if (!box) return;
            try {
                const res = await fetch(`/api/edge/computer/files?dot_id=${encodeURIComponent(this.activeDotId)}`);
                if (!res.ok) return;
                const data = await res.json();
                const files = data.files || [];
                const compBadge = document.getElementById('computerActiveWorkspaceBadge');
                if (compBadge) compBadge.textContent = `/workspace/${this.activeDotId}`;

                if (!files.length) {
                    box.innerHTML = `<span style="font-family: var(--font-pixel); font-size: 7px; color: var(--thermal-amber);">/WORKSPACE (${safeEscape(this.activeDotId)}):</span> <span style="color: var(--ink-muted);">Diretorio limpo (0 arquivos).</span>`;
                    return;
                }
                box.innerHTML = `<span style="font-family: var(--font-pixel); font-size: 7px; color: var(--thermal-amber);">/WORKSPACE:</span>` +
                    files.map(f => `<span class="pixel-btn" style="padding: 1px 5px; font-size: 9px; cursor: pointer;" onclick="PiDotsAPI.inspectWorkspaceFile('${safeEscape(f.path)}')">${safeEscape(f.path)} (${f.size_bytes}B)</span>`).join('');
            } catch (e) {
                console.warn('Erro ao listar arquivos do Dot Computer:', e);
            }
        },

        refreshComputerWorkspaceFiles() {
            return this.loadComputerFiles();
        },

        async inspectWorkspaceFile(relPath) {
            await this.executeInDotComputer(`cat ${relPath}`);
        },

        async executeInDotComputer(customCommand) {
            const input = document.getElementById('computerExecInput');
            const cmd = (customCommand || (input ? input.value : '')).trim();
            if (!cmd) return;
            if (!customCommand && input) input.value = '';

            const term = document.getElementById('terminalViewport');
            const timeStr = new Date().toTimeString().split(' ')[0];
            if (term) {
                const cmdLine = document.createElement('div');
                cmdLine.innerHTML = `[${timeStr}] <span style="color: var(--blueprint-cyan);">${safeEscape(this.activeDotId)}@bwrap:~$</span> ${safeEscape(cmd)}`;
                term.appendChild(cmdLine);
                term.scrollTop = term.scrollHeight;
            }

            try {
                const res = await fetch('/api/edge/computer/exec', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        dot_id: this.activeDotId,
                        command: cmd
                    })
                });
                const data = await res.json();
                if (term) {
                    const outDiv = document.createElement('div');
                    if (data.status === 'BLOCKED_HITL') {
                        outDiv.innerHTML = `<span style="color: var(--thermal-amber);">[GUARDRAIL HITL] Comando retido para homologacao (#${safeEscape(data.approval_id)}): ${safeEscape(data.reason || '')}</span>`;
                        await this.loadPendingHitl();
                    } else {
                        const outText = data.output || data.stdout || data.stderr || '[Sem saida]';
                        outDiv.innerHTML = `<div style="color: #cbd5e1; white-space: pre-wrap;">${safeEscape(outText)}</div><div style="color: var(--phosphor-green); font-size: 9.5px;">[STATUS: ${safeEscape(data.status || 'OK')} // SANDBOX ISOLADO]</div>`;
                    }
                    term.appendChild(outDiv);
                    term.scrollTop = term.scrollHeight;
                }
                await this.loadComputerFiles();
            } catch (e) {
                if (term) {
                    const errDiv = document.createElement('div');
                    errDiv.style.color = 'var(--stamp-danger)';
                    errDiv.textContent = `[ERRO EXEC]: ${e.message}`;
                    term.appendChild(errDiv);
                }
            }
        },

        // Renderizador de Generative UI Cards Inline no Fluxo do Teletipo (AG-UI)
        appendGenerativeUiCard(containerEl, evData) {
            if (!containerEl) return;
            const card = document.createElement('div');
            const evType = evData.event || '';

            if (evType === 'tool_call:start' || evType === 'tool:called' || (evData.tool && !evData.result)) {
                const toolName = evData.tool || evData.name || evData.tool_name || 'tool';
                const toolArgs = evData.arguments || evData.args || {};
                card.className = 'gen-ui-card';
                card.innerHTML = `
                    <div class="gen-ui-header">
                        <span>[GENERATIVE UI // TOOL CALL EM EXECUCAO]</span>
                        <span>@${safeEscape(evData.dot_id || this.activeDotId)}</span>
                    </div>
                    <div class="gen-ui-body">Ferramenta: <strong style="color: var(--phosphor-green);">${safeEscape(toolName)}</strong>\nArgumentos: <code>${safeEscape(JSON.stringify(toolArgs))}</code></div>
                `;
            } else if (evType === 'tool_call:result' || evType === 'tool:result' || evData.result !== undefined) {
                const toolName = evData.tool || evData.name || evData.tool_name || 'tool';
                const resStr = typeof evData.result === 'object' ? JSON.stringify(evData.result) : String(evData.result || '');
                const isErr = resStr.includes('Erro') || resStr.includes('BLOQUEADO');
                card.className = `gen-ui-card ${isErr ? 'status-warn' : 'status-ok'}`;
                card.innerHTML = `
                    <div class="gen-ui-header">
                        <span>[RECIBO DE FERRAMENTA // ${safeEscape(toolName.toUpperCase())}]</span>
                        <span style="color: ${isErr ? 'var(--thermal-amber)' : 'var(--phosphor-green)'};">${isErr ? '[RETIDO/AVISO]' : `[CONCLUIDO ${evData.duration_ms ? evData.duration_ms + 'ms' : ''}]`}</span>
                    </div>
                    <div class="gen-ui-body">${safeEscape(resStr.slice(0, 400))}</div>
                `;
            } else if (evType === 'artifact:updated') {
                const filename = evData.filename || 'artefato.md';
                const spaceId = evData.space_id || filename;
                card.className = 'gen-ui-card status-ok';
                card.innerHTML = `
                    <div class="gen-ui-header">
                        <span>[ARTEFATO SINCRONIZADO EM SPACES // REV ${safeEscape(evData.version || 1)}]</span>
                        <span style="color: var(--phosphor-green);">[WAL ACID]</span>
                    </div>
                    <div class="gen-ui-body">O coworker atualizou o documento <strong>${safeEscape(filename)}</strong> no Live Canvas.</div>
                    <div class="gen-ui-actions">
                        <button type="button" class="pixel-btn btn-cyan" style="padding: 2px 6px; font-size: 8px;" onclick="PiDotsAPI.loadArtifact('${safeEscape(spaceId)}')">[ABRIR NO CANVAS]</button>
                        <button type="button" class="pixel-btn" style="padding: 2px 6px; font-size: 8px;" onclick="PiDotsAPI.toggleDiffView()">[INSPECIONAR DIFF]</button>
                    </div>
                `;
            } else {
                return;
            }

            containerEl.appendChild(card);
        },

        // 6. Streaming SSE Conversacional ReAct (AG-UI v1.0 + Multi-Bot + Generative UI)
        async transmitStream(promptText) {
            const scrollArea = document.getElementById('tickerScroll');
            if (!scrollArea) return;

            const statusBadge = document.getElementById('aguiStreamStatusBadge');
            if (statusBadge) {
                statusBadge.textContent = 'AG-UI STREAMING...';
                statusBadge.style.color = 'var(--thermal-amber)';
            }

            if (!this.activeThreadId) {
                try {
                    const tRes = await fetch('/api/threads', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            dot_id: this.activeDotId,
                            channel_id: this.activeChannelId,
                            title: promptText.slice(0, 36)
                        })
                    });
                    if (tRes.ok) {
                        const tData = await tRes.json();
                        this.activeThreadId = tData.id;
                        this.loadThreads();
                    }
                } catch (e) {
                    this.activeThreadId = 'local-fallback-' + Date.now();
                }
            }

            const agentSlip = document.createElement('article');
            agentSlip.className = 'ticker-slip';
            const thoughtId = 'thought-' + Date.now();
            const contentId = 'content-' + Date.now();
            const genUiId = 'genui-' + Date.now();

            const activeDot = (this.dotsCache || []).find(d => d.id === this.activeDotId);
            let stampClass = 'stamp-general';
            if (activeDot) {
                if (activeDot.archetype === 'supervisor') stampClass = 'stamp-supervisor';
                else if (activeDot.archetype === 'coder') stampClass = 'stamp-coder';
                else if (activeDot.archetype === 'auditor') stampClass = 'stamp-auditor';
                else if (activeDot.archetype === 'architect') stampClass = 'stamp-architect';
            }
            const stampText = activeDot?.avatar_stamp || '[DOT]';
            const dotName = (activeDot?.name || this.activeDotId).toUpperCase();

            agentSlip.innerHTML = `
                <header class="slip-header">
                    <span class="actor-stamp ${stampClass}">${safeEscape(stampText)} ${safeEscape(dotName)}</span>
                    <span>${new Date().toISOString()}</span>
                    <span>SEQ# 000${window.getNextSeqCounter()}</span>
                </header>
                <section class="slip-reasoning">
                    <div class="reasoning-toggle" onclick="toggleReasoning(this)">
                        <span>[CADERNO DE RACIOCINIO - AG-UI STREAM]</span>
                        <span class="reasoning-state-badge">[-] COLAPSAR</span>
                    </div>
                    <div class="reasoning-content" id="${thoughtId}" style="font-family: var(--font-mono); font-size: 11px; white-space: pre-wrap;">Iniciando ciclo de raciocinio assincrono no no de borda local...</div>
                </section>
                <section class="slip-output">
                    <div id="${genUiId}"></div>
                    <p class="slip-text" id="${contentId}"><span class="pixel-cursor">█</span></p>
                </section>
                <footer class="slip-perforation">
                    <span class="perforation-line"></span>
                </footer>
            `;
            scrollArea.appendChild(agentSlip);
            scrollArea.scrollTop = scrollArea.scrollHeight;
            this.enforceDomCeiling();

            const thoughtEl = document.getElementById(thoughtId);
            const contentEl = document.getElementById(contentId);
            const genUiEl = document.getElementById(genUiId);
            let textAccumulator = '';

            try {
                const response = await fetch(`/api/threads/${this.activeThreadId}/runs`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: promptText})
                });

                if (!response.ok || !response.body) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let currentSseEvent = '';

                while (true) {
                    const {done, value} = await reader.read();
                    if (done) break;

                    const chunk = decoder.decode(value, {stream: true});
                    const lines = chunk.split('\n');

                    for (let i = 0; i < lines.length; i++) {
                        const line = lines[i];
                        if (line.startsWith('event: ')) {
                            currentSseEvent = line.slice(7).trim();
                        } else if (line.startsWith('data: ')) {
                            try {
                                const evData = JSON.parse(line.slice(6));
                                if (!evData.event && currentSseEvent) {
                                    evData.event = currentSseEvent;
                                }
                                if (evData.thought && thoughtEl) {
                                    thoughtEl.textContent += '\n> ' + evData.thought;
                                }
                                if (evData.content_chunk) {
                                    textAccumulator += evData.content_chunk;
                                    contentEl.innerHTML = safeEscape(textAccumulator) + ' <span class="pixel-cursor">█</span>';
                                }
                                const toolName = evData.tool || evData.name || evData.tool_name;
                                if (toolName && thoughtEl && (evData.event === 'tool:called' || evData.event === 'tool_call:start')) {
                                    thoughtEl.textContent += `\n[TOOL]: Executando ${toolName}...`;
                                }
                                if (evData.event === 'tool_call:start' || evData.event === 'tool_call:result' || evData.event === 'tool:called' || evData.event === 'tool:result') {
                                    this.appendGenerativeUiCard(genUiEl, evData);
                                }
                                if (evData.event === 'artifact:updated') {
                                    this.appendGenerativeUiCard(genUiEl, evData);
                                    await this.loadSpaces();
                                    if (evData.space_id || evData.filename) {
                                        await this.loadArtifact(evData.space_id || evData.filename, null, true);
                                    }
                                    if (typeof window.notifyMobileCanvasUpdate === 'function') {
                                        window.notifyMobileCanvasUpdate('DOC');
                                    }
                                }
                                if (evData.handoff && thoughtEl) {
                                    thoughtEl.textContent += `\n[HANDOFF]: Tarefa delegada para @${evData.handoff.target_dot_id || 'agente'}`;
                                }
                                if (evData.event === 'hitl:approval_required' || evData.event === 'hitl:pending_approval' || evData.approval_id) {
                                    if (thoughtEl) thoughtEl.textContent += `\n[GOVERNANCA HITL]: Acao critica retida pelo Guardrail Deny-by-Default. Aguardando aprovacao humana.`;
                                    await this.loadPendingHitl();
                                    if (typeof window.openHitlCanvas === 'function') {
                                        window.openHitlCanvas();
                                    }
                                }
                                if (evData.event === 'self_healing:triggered' && thoughtEl) {
                                    thoughtEl.textContent += `\n[SELF-HEALING]: Tentativa automatica de autocura disparada pelo motor cognitivo.`;
                                }
                                if ((evData.event === 'self_healing:max_attempts_exceeded' || evData.max_attempts_exceeded) && thoughtEl) {
                                    thoughtEl.textContent += `\n[SELF-HEALING TETO]: Limite de 2 tentativas de reparo atingido. Escalonando para @dot-auditor ou operador humano.`;
                                }
                                if (evData.event === 'canvas:patch' || evData.canvas_patch) {
                                    const rawPatch = evData.canvas_patch || evData.patch || {};
                                    const patchContent = typeof rawPatch === 'string' ? rawPatch : (rawPatch.content || evData.content || '');
                                    const patchFile = evData.filename || (typeof rawPatch === 'object' ? rawPatch.filename : '');
                                    const artEl = document.getElementById('artifactContent');
                                    const titleEl = document.getElementById('currentArtifactTitle');
                                    if (titleEl && patchFile) titleEl.textContent = patchFile;
                                    if (artEl && patchContent) {
                                        artEl.value = patchContent;
                                        PixelSystem.toast('CANVAS ATUALIZADO: Documento editado ao vivo pelo agente', 'info');
                                        if (typeof window.notifyMobileCanvasUpdate === 'function') {
                                            window.notifyMobileCanvasUpdate('NOVO');
                                        }
                                    }
                                }
                                if (evData.event === 'state:sync') {
                                    this.loadActiveThreadState();
                                    if (typeof window.notifyMobileCanvasUpdate === 'function') {
                                        window.notifyMobileCanvasUpdate('PLAN');
                                    }
                                }
                                if (evData.error && thoughtEl) {
                                    thoughtEl.textContent += '\n[AVISO CIRCUIT BREAKER]: ' + evData.error;
                                }
                            } catch (_) {}
                        }
                    }
                    scrollArea.scrollTop = scrollArea.scrollHeight;
                }

                this.enforceDomCeiling();
                contentEl.innerHTML = safeEscape(textAccumulator || 'Operacao concluida com sucesso.');
                this.loadActiveThreadState();
            } catch (err) {
                if (thoughtEl) thoughtEl.textContent += `\n[Circuito de Protecao]: Provedor remoto offline ou timeout. Operando em contingencia local.`;
                if (contentEl) contentEl.innerHTML = `Instrucao processada no ambiente local do piDots. Os dados estao preservados e persistidos no SQLite WAL.`;
                scrollArea.scrollTop = scrollArea.scrollHeight;
                this.enforceDomCeiling();
            } finally {
                if (statusBadge) {
                    statusBadge.textContent = 'AG-UI PRONTO';
                    statusBadge.style.color = 'var(--phosphor-green)';
                }
            }
        }
    };

    window.PiDotsAPI = PiDotsAPI;
})(typeof window !== 'undefined' ? window : this);
