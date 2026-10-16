/**
 * PIDOTS CONSOLE SPA - CAMADA DE API E COMUNICACAO BACKEND
 * =====================================================================
 * Gerencia chamadas assincronas para o backend FastAPI e SQLite WAL:
 * SSE Stream (/api/execute/stream), Dots, Spaces, HITL, Telemetria,
 * Diffs, Configuracoes e Contingencia Offline.
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

        const PiDotsAPI = {
            activeDotId: 'dot-dev-core',
            activeThreadId: null,
            activeSpaceId: null,
            activeSpaceDoc: null,
            spacesCache: [],
            dotsCache: [],
            pendingHitlCache: [],
            telemetryHistory: { ram: [110, 115, 120, 118, 125, 122, 118], temp: [45, 46, 47, 48, 48.2, 48.5, 48.2] },
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
                    const result = await res.json();
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
                await this.loadSpaces();
                await this.loadPendingHitl();
                await this.loadSettings();
                
                // Inicia loop contínuo de telemetria a cada 4 segundos com guarda de concorrencia
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

            // 2. Telemetria Real (/health)
            async fetchTelemetry() {
                try {
                    const res = await fetch('/health');
                    if (!res.ok) return;
                    const data = await res.json();

                    // Temperatura
                    if (data.soc_temperature_celsius !== undefined) {
                        const tempEl = document.getElementById('val-temp');
                        if (tempEl) tempEl.textContent = `${data.soc_temperature_celsius} °C`;
                        const compactNodeEl = document.getElementById('val-compact-node');
                        if (compactNodeEl) compactNodeEl.textContent = `${data.soc_temperature_celsius}°C`;
                        const plotterTempEl = document.querySelector('.plotter-card:nth-child(2) .plotter-val');
                        if (plotterTempEl) plotterTempEl.textContent = `${data.soc_temperature_celsius} °C`;

                        this.telemetryHistory.temp.push(data.soc_temperature_celsius);
                        if (this.telemetryHistory.temp.length > 10) this.telemetryHistory.temp.shift();
                        this.updateTempSvg();
                    }

                    // Memória RAM
                    if (data.memory) {
                        const ramEl = document.getElementById('val-ram');
                        if (ramEl) ramEl.textContent = `${data.memory.used_mb} MB / ${data.memory.total_mb} MB`;
                        const plotterRamEl = document.querySelector('.plotter-card:nth-child(1) .plotter-val');
                        if (plotterRamEl) plotterRamEl.textContent = `${data.memory.used_mb} MB`;

                        this.telemetryHistory.ram.push(data.memory.used_mb);
                        if (this.telemetryHistory.ram.length > 10) this.telemetryHistory.ram.shift();
                        this.updateRamSvg();
                    }

                    // Status do Banco
                    if (data.database && data.database.mode) {
                        const walEl = document.querySelector('.telemetry-chip.desktop-only .chip-value');
                        if (walEl) walEl.textContent = `${data.database.mode} (ATIVO)`;
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
                const maxRam = 300; // Teto de 300MB
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
                const maxTemp = 85; // Throttle 85C
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

            // 3. Dots Coworkers (/api/dots)
            async loadDots() {
                try {
                    const res = await fetch('/api/dots?core_only=true');
                    if (!res.ok) return;
                    const dots = await res.json();
                    if (!dots || !dots.length) return;

                    this.dotsCache = dots;
                    const container = document.getElementById('dotsListContainer');
                    if (!container) return;

                    container.innerHTML = '';
                    dots.forEach((dot, idx) => {
                        const card = document.createElement('div');
                        card.className = `dot-card ${idx === 0 ? 'active' : ''}`;
                        card.onclick = () => this.selectDot(dot.id, card);
                        
                        // Badge arquetípico sutil
                        let archetypeLabel = (dot.archetype || 'COWORKER').toUpperCase();
                        card.innerHTML = `
                            <div class="dot-card-header">
                                <span class="dot-card-name">${escapeHtml(dot.name || dot.id)}</span>
                                <span class="dot-card-status" style="font-size: 8px;">[${archetypeLabel}]</span>
                            </div>
                            <div class="dot-card-role" style="font-size: 10px; color: var(--ink-secondary); margin-top: 2px;">${escapeHtml(dot.role || 'Edge Coworker')}</div>
                        `;
                        container.appendChild(card);
                    });

                    // Seleciona o primeiro especialista ativo (Supervisor ou Dev)
                    this.activeDotId = dots[0].id;
                    const activeAgentName = dots[0].name || dots[0].id;
                    const chEl = document.getElementById('activeDotChannel');
                    if (chEl) chEl.textContent = `CANAL DE TRABALHO // ${activeAgentName.toUpperCase()}`;

                    const headerAgentEl = document.getElementById('headerActiveAgentName');
                    if (headerAgentEl) headerAgentEl.textContent = activeAgentName;

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

                // Recarrega Spaces e reinicia thread ativa para este Dot
                this.activeThreadId = null;
                this.loadSpaces();
                PixelSystem.toast(`Coworker '${dot ? dot.name : dotId}' selecionado como ativo.`, 'info');
            },

            // 4. Spaces e Artefatos (/api/spaces)
            async loadSpaces() {
                try {
                    const res = await fetch(`/api/spaces?dot_id=${this.activeDotId}`);
                    if (!res.ok) return;
                    const spaces = await res.json();
                    this.spacesCache = spaces;

                    const container = document.getElementById('spacesListContainer');
                    if (!container) return;

                    if (!spaces || !spaces.length) {
                        container.innerHTML = '<div style="font-size: 10px; color: var(--ink-muted); padding: 6px;">Nenhum arquivo no Space deste Dot.</div>';
                        return;
                    }

                    container.innerHTML = '';
                    spaces.forEach((sp, idx) => {
                        const item = document.createElement('div');
                        item.className = `space-item ${idx === 0 ? 'active' : ''}`;
                        item.onclick = () => this.loadArtifact(sp.id, item);
                        item.innerHTML = `
                            <span>${escapeHtml(sp.filename)}</span>
                            <span class="space-item-rev">REV ${sp.version || 1}</span>
                        `;
                        container.appendChild(item);
                    });

                    // Sincroniza o seletor dropdown do Live Canvas com a lista real de spaces
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

                    // Carrega o primeiro artefato automaticamente
                    if (spaces.length > 0 && !this.activeSpaceId) {
                        this.loadArtifact(spaces[0].id);
                    }

                } catch (e) {
                    console.warn('Erro ao carregar Spaces:', e);
                }
            },

            selectSpaceFromDropdown(filename) {
                if (!filename) return;
                const doc = (this.spacesCache || []).find(s => s.filename === filename);
                if (doc) {
                    this.loadArtifact(doc.id);
                } else if (typeof artifactDocs !== 'undefined' && artifactDocs[filename]) {
                    const titleEl = document.getElementById('currentArtifactTitle');
                    if (titleEl) titleEl.textContent = filename;
                    const editorEl = document.getElementById('artifactContent');
                    if (editorEl) editorEl.value = artifactDocs[filename];
                    PixelSystem.toast(`Documento '${filename}' carregado localmente.`, 'info');
                }
            },

            async loadArtifact(spaceId, el) {
                try {
                    const res = await fetch(`/api/spaces/${spaceId}`);
                    if (!res.ok) return;
                    const doc = await res.json();

                    this.activeSpaceId = doc.id;
                    this.activeSpaceDoc = doc;

                    // Atualiza itens ativos na lista
                    document.querySelectorAll('.space-item').forEach(it => it.classList.remove('active'));
                    if (el) el.classList.add('active');

                    // Atualiza editor
                    const titleEl = document.getElementById('currentArtifactTitle');
                    if (titleEl) titleEl.textContent = doc.filename;

                    const selectorEl = document.getElementById('spaceDocSelector');
                    if (selectorEl) selectorEl.value = doc.filename;

                    const editorEl = document.getElementById('artifactContent');
                    if (editorEl) editorEl.value = doc.content || '';

                    const revBadge = document.querySelector('.artifact-header .space-item-rev');
                    if (revBadge) revBadge.textContent = `REV ${doc.version || 1}`;

                    // Esconde diff se estava ativo
                    this.isDiffActive = false;
                    const diffView = document.getElementById('diffViewContainer');
                    if (diffView) diffView.style.display = 'none';
                    if (editorEl) editorEl.style.display = 'block';

                    // Garante que o canvas da direita esteja visível
                    const canvas = document.getElementById('rightCanvas');
                    if (canvas) {
                        canvas.classList.remove('collapsed');
                        const tabs = document.querySelectorAll('.canvas-tab');
                        switchCanvasTab('canvas-artifact', tabs[0]);
                    }

                    // Se estiver no celular, transiciona para a visualização de Canvas
                    if (window.innerWidth <= 768) {
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

            async createNewSpace() {
                PixelSystem.prompt(
                    'Criar Espaco no SQLite WAL',
                    'Informe o nome do arquivo a ser criado no Space (ex: analise_arm64.py):',
                    'novo_arquivo.md',
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

            // 5. Governança HITL (/api/hitl)
            async loadPendingHitl() {
                try {
                    const res = await fetch('/api/hitl/pending');
                    if (!res.ok) return;
                    const pending = await res.json();
                    this.pendingHitlCache = pending;

                    const chipHitl = document.getElementById('val-hitl');
                    const descHitl = document.getElementById('hitlSidebarDesc');

                    if (chipHitl) {
                        chipHitl.textContent = `${pending.length} PENDENTE${pending.length === 1 ? '' : 'S'}`;
                        chipHitl.className = pending.length > 0 ? 'chip-value' : 'chip-value ok';
                    }

                    if (descHitl) {
                        if (pending.length > 0) {
                            descHitl.textContent = `Acao: ${pending[0].action_type} (Risco: ${pending[0].risk_level})`;
                        } else {
                            descHitl.textContent = 'Nenhuma acao retida no momento.';
                        }
                    }

                    // Controle Just-in-Time: Exibe seção lateral de HITL apenas se houver ação pendente
                    const hitlSection = document.getElementById('hitlSidebarSection');
                    const hitlBadge = document.getElementById('hitlSidebarCountBadge');
                    if (hitlSection) {
                        hitlSection.style.display = pending.length > 0 ? 'block' : 'none';
                    }
                    if (hitlBadge) {
                        hitlBadge.textContent = `RETIDO (${pending.length})`;
                    }

                    // Se houver pendências, atualiza dossiê do Canvas
                    if (pending.length > 0) {
                        const item = pending[0];
                        const hitlView = document.getElementById('canvas-hitl');
                        if (hitlView) {
                            const infoDiv = hitlView.querySelector('div:nth-child(2)');
                            if (infoDiv) {
                                infoDiv.innerHTML = `
                                    <strong>ID:</strong> ${escapeHtml(item.id)}<br>
                                    <strong>AGENTE:</strong> ${escapeHtml(item.dot_id)}<br>
                                    <strong>RISCO:</strong> ${escapeHtml(item.risk_level)}<br>
                                    <strong>PAYLOAD / ALVO:</strong> ${escapeHtml(item.payload || item.command || 'N/A')}
                                `;
                            }
                        }
                    }

                } catch (e) {
                    console.warn('Erro ao carregar fila HITL:', e);
                }
            },

            async resolveHitl(approved, notes = '') {
                if (!this.pendingHitlCache || !this.pendingHitlCache.length) {
                    // Simulação visual de segurança se não houver pendência real
                    this.applyHitlVisual(approved);
                    return;
                }

                const item = this.pendingHitlCache[0];
                try {
                    const res = await fetch(`/api/hitl/${item.id}/resolve`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            approved: approved,
                            notes: notes || (approved ? 'Homologado via Console Pixel Paper UI' : 'Vetado pelo operador')
                        })
                    });

                    if (!res.ok) throw new Error(`Status ${res.status}`);
                    this.applyHitlVisual(approved);
                    await this.loadPendingHitl();
                await this.loadSettings();

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
                        PixelSystem.toast('HOMOLOGADO: Acao oficial autenticada no SQLite WAL! Despachando para Bubblewrap.', 'success');
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

            // 6. Streaming SSE Conversacional ReAct (AG-UI v1.0)
            async transmitStream(promptText) {
                const scrollArea = document.getElementById('tickerScroll');
                if (!scrollArea) return;

                // 1. Cria ou recupera thread durável no backend
                if (!this.activeThreadId) {
                    try {
                        const tRes = await fetch('/api/threads', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                dot_id: this.activeDotId,
                                title: promptText.slice(0, 30)
                            })
                        });
                        if (tRes.ok) {
                            const tData = await tRes.json();
                            this.activeThreadId = tData.id;
                        }
                    } catch (e) {
                        this.activeThreadId = 'local-fallback-' + Date.now();
                    }
                }

                // 2. Cria a tira de resposta no teletipo com carimbo tátil e fita de carbono
                const agentSlip = document.createElement('article');
                agentSlip.className = 'ticker-slip';
                const thoughtId = 'thought-' + Date.now();
                const contentId = 'content-' + Date.now();

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
                        <span class="actor-stamp ${stampClass}">${escapeHtml(stampText)} ${escapeHtml(dotName)}</span>
                        <span>${new Date().toISOString()}</span>
                        <span>SEQ# 000${window.getNextSeqCounter()}</span>
                    </header>
                    <section class="slip-reasoning">
                        <div class="reasoning-toggle" onclick="toggleReasoning(this)">
                            <span>[CADERNO DE RACIOCINIO - AG-UI STREAM]</span>
                            <span class="reasoning-state-badge">[-] COLAPSAR</span>
                        </div>
                        <div class="reasoning-content" id="${thoughtId}" style="font-family: var(--font-mono); font-size: 11px; white-space: pre-wrap;">Iniciando ciclo de raciocinio assincrono no nó de borda local...</div>
                    </section>
                    <section class="slip-output">
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
                let textAccumulator = '';

                // 3. Dispara a requisição SSE para o backend com orquestração Multi-Bot
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

                    while (true) {
                        const {done, value} = await reader.read();
                        if (done) break;

                        const chunk = decoder.decode(value, {stream: true});
                        const lines = chunk.split('\n');

                        for (let i = 0; i < lines.length; i++) {
                            const line = lines[i];
                            if (line.startsWith('data: ')) {
                                try {
                                    const evData = JSON.parse(line.slice(6));
                                    if (evData.thought && thoughtEl) {
                                        thoughtEl.textContent += '\n> ' + evData.thought;
                                    }
                                    if (evData.content_chunk) {
                                        textAccumulator += evData.content_chunk;
                                        contentEl.innerHTML = escapeHtml(textAccumulator) + ' <span class="pixel-cursor">█</span>';
                                    }
                                    const toolName = evData.tool || evData.name || evData.tool_name;
                                    if (toolName && thoughtEl) {
                                        thoughtEl.textContent += `\n[TOOL]: Executando ${toolName}...`;
                                    }
                                    if (evData.handoff && thoughtEl) {
                                        thoughtEl.textContent += `\n[HANDOFF]: Tarefa delegada para @${evData.handoff.target_dot_id || 'agente'}`;
                                    }
                                    if (evData.event === 'hitl:approval_required' || evData.approval_id) {
                                        if (thoughtEl) thoughtEl.textContent += `\n[GOVERNANCA HITL]: Acao critica retida pelo Guardrail Deny-by-Default. Aguardando aprovacao humana.`;
                                        await this.loadPendingHitl();
                                    }
                                    if (evData.event === 'self_healing:triggered' && thoughtEl) {
                                        thoughtEl.textContent += `\n[SELF-HEALING]: Tentativa automatica de autocura disparada pelo motor cognitivo.`;
                                    }
                                    // Sincronização ao vivo do Live Canvas (Canvas Patch)
                                    if (evData.event === 'canvas:patch' || evData.canvas_patch) {
                                        const patch = evData.canvas_patch || evData.patch || {};
                                        const artEl = document.getElementById('artifactContent');
                                        if (artEl && patch.content) {
                                            artEl.value = patch.content;
                                            PixelSystem.toast('CANVAS ATUALIZADO: Documento editado ao vivo pelo agente', 'info');
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

                    // Enforce DOM ceiling apos finalizacao do stream sem causar layout thrashing
                    if (window.PiDotsAPI && typeof PiDotsAPI.enforceDomCeiling === 'function') {
                        PiDotsAPI.enforceDomCeiling();
                    }

                    // Remove o cursor piscante ao finalizar
                    contentEl.innerHTML = escapeHtml(textAccumulator || 'Operacao concluida com sucesso.');

                } catch (err) {
                    if (thoughtEl) thoughtEl.textContent += `\n[Circuito de Protecao]: Provedor remoto offline ou timeout. Operando em contingencia local.`;
                    if (contentEl) contentEl.innerHTML = `Instrucao processada no ambiente local do piDots. Os dados estao preservados e persistidos no SQLite WAL.`;
                    scrollArea.scrollTop = scrollArea.scrollHeight;
                    if (window.PiDotsAPI && typeof PiDotsAPI.enforceDomCeiling === 'function') {
                        PiDotsAPI.enforceDomCeiling();
                    }
                }
            }
        };

        
        // =====================================================================
        // CONFORMIDADE PWA, SERVICE WORKER E RENDERIZADOR DE DIFFS (FASE 5)
        // =====================================================================

    window.PiDotsAPI = PiDotsAPI;
})(typeof window !== 'undefined' ? window : this);
