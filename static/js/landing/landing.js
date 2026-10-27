/**
 * PIDOTS LANDING PAGE - SCRIPTS INTERATIVOS E SIMULADORES AO VIVO
 * =====================================================================
 * Gerencia: Simulador ReAct ao vivo, Calculadora de ROI de Silicio
 * com Duty Cycle, Trava Mecanica de Seguranca HITL, Sanfona de Objecoes,
 * PWA e Teclas de Navegacao Chords.
 * ZERO EMOJIS // Vanilla JS Puro // Alta Performance ARM64
 * =====================================================================
 */

(function(window) {
    "use strict";

        let isBlueprint = false;
        let isMechanicalUnlocked = false;
        let dutyCycleHours = 24; // Padrao continuo 24/7
        let simActiveTimers = [];

        function clearSimTimers() {
            while (simActiveTimers.length > 0) {
                clearTimeout(simActiveTimers.pop());
            }
        }

        function registerSimTimer(fn, delay) {
            const id = setTimeout(fn, delay);
            simActiveTimers.push(id);
            return id;
        }

        // Sintetizador de Som Tatil Mecanico 8-Bit (Web Audio API sem dependencias)
        function playHapticMechanicalClick() {
            if (window.PixelSystem && typeof window.PixelSystem.playMechanicalClick === 'function') {
                window.PixelSystem.playMechanicalClick();
            }
        }

        // Alternancia de Tema: Dark Noir vs Blueprint
        function toggleTheme() {
            if (window.PixelSystem && window.PixelSystem.ThemeManager) {
                const next = window.PixelSystem.ThemeManager.toggleTheme(true);
                isBlueprint = next === 'blueprint';
                return;
            }
            isBlueprint = !isBlueprint;
            playHapticMechanicalClick();
            try {
                if (isBlueprint) {
                    document.documentElement.setAttribute('data-theme', 'blueprint');
                    localStorage.setItem('pidots-theme', 'blueprint');
                    showToast('Tema comutado para Blueprint Tecnico de Prancheta.', 'info');
                } else {
                    document.documentElement.removeAttribute('data-theme');
                    localStorage.setItem('pidots-theme', 'noir');
                    showToast('Tema comutado para Dark Paper Noir Oficial.', 'info');
                }
            } catch (e) {}
        }

        // Carregamento Imediato do Tema Salvo
        (function initSavedTheme() {
            try {
                const saved = localStorage.getItem('pidots-theme');
                if (saved === 'blueprint') {
                    isBlueprint = true;
                    document.documentElement.setAttribute('data-theme', 'blueprint');
                }
            } catch (e) {}
        })();

        // Controle do Menu Retratil Direito (Guia Tecnico)
        function toggleDrawer() {
            const drawer = document.getElementById('retractableDrawer');
            const backdrop = document.getElementById('drawerBackdrop');
            if (!drawer || !backdrop) return;

            const mobilePanel = document.getElementById('mobileNavPanel');
            if (mobilePanel && mobilePanel.classList.contains('open')) {
                mobilePanel.classList.remove('open');
                const btnMobile = document.querySelector('.nav-btn-mobile');
                if (btnMobile) btnMobile.setAttribute('aria-expanded', 'false');
            }

            const willOpen = !drawer.classList.contains('open');
            drawer.classList.toggle('open', willOpen);
            backdrop.classList.toggle('open', willOpen);

            const btnManual = document.querySelector('.nav-btn-manual');
            if (btnManual) btnManual.setAttribute('aria-expanded', willOpen ? 'true' : 'false');

            if (window.ScrollLockManager) {
                if (willOpen) {
                    window.ScrollLockManager.bloquear();
                } else {
                    window.ScrollLockManager.desbloquear();
                }
            }

            playHapticMechanicalClick();
        }

        // Filtro de Passos do Manual no Drawer
        function filterDrawerSteps(query) {
            const term = query.toLowerCase().trim();
            const steps = document.querySelectorAll('#drawerContentList .guide-step');
            steps.forEach(step => {
                const text = step.textContent.toLowerCase();
                step.style.display = text.includes(term) ? 'flex' : 'none';
            });
        }

        // Simulador de Governanca HITL
        function toggleMechanicalSafetyLock() {
            isMechanicalUnlocked = !isMechanicalUnlocked;
            const switchEl = document.getElementById('demoSafetySwitch');
            const labelEl = document.getElementById('demoSafetyLabel');
            const btnApprove = document.getElementById('btnDemoApprove');

            if (switchEl) switchEl.classList.toggle('active', isMechanicalUnlocked);
            if (btnApprove) btnApprove.disabled = !isMechanicalUnlocked;

            playHapticMechanicalClick();

            const isEn = window.PiDotsI18n && window.PiDotsI18n.getLanguage() === 'en';
            if (isMechanicalUnlocked) {
                if (labelEl) labelEl.textContent = isEn ? 'SAFETY LOCK UNLOCKED' : 'TRAVA DESTRAVADA';
                showToast(isEn ? 'WARNING: Mechanical safety lock unlocked by operator.' : 'ALERTA: Trava mecanica de seguranca destravada pelo operador.', 'warning');
            } else {
                if (labelEl) labelEl.textContent = isEn ? 'SAFETY LOCK ENGAGED' : 'TRAVA ENGATADA';
                showToast(isEn ? 'SECURITY: Mechanical lock engaged. Homologation blocked.' : 'SEGURANCA: Trava mecanica engatada. Homologacao bloqueada.', 'info');
            }
        }

        function triggerDemoApprove() {
            const approveStamp = document.getElementById('demoStampApprove');
            const rejectStamp = document.getElementById('demoStampReject');

            if (approveStamp) {
                approveStamp.style.opacity = '1';
                approveStamp.style.transform = 'rotate(2.5deg) scale(1.15)';
            }
            if (rejectStamp) rejectStamp.style.opacity = '0.25';

            playHapticMechanicalClick();

            const isEn = window.PiDotsI18n && window.PiDotsI18n.getLanguage() === 'en';
            const msg = isEn 
                ? 'HOMOLOGATED: Action authorized in SQLite WAL. Command dispatched to sandbox.'
                : 'HOMOLOGADO: Ação autorizada no SQLite WAL. Comando liberado para o sandbox.';

            setTimeout(() => {
                showToast(msg, 'success');
                if (approveStamp) approveStamp.style.transform = 'rotate(2deg) scale(1.0)';
            }, 180);
        }

        function triggerDemoVeto() {
            const approveStamp = document.getElementById('demoStampApprove');
            const rejectStamp = document.getElementById('demoStampReject');

            if (rejectStamp) {
                rejectStamp.style.opacity = '1';
                rejectStamp.style.transform = 'rotate(-3deg) scale(1.15)';
            }
            if (approveStamp) approveStamp.style.opacity = '0.25';

            playHapticMechanicalClick();

            const isEn = window.PiDotsI18n && window.PiDotsI18n.getLanguage() === 'en';
            const msg = isEn
                ? 'VETO RECORDED: Action cancelled and archived securely in governance queue.'
                : 'VETO REGISTRADO: Acao cancelada e arquivada com seguranca na fila de governanca.';

            setTimeout(() => {
                showToast(msg, 'danger');
                if (rejectStamp) rejectStamp.style.transform = 'rotate(-3deg) scale(1.0)';
            }, 180);
        }

        // Controle de Ciclo de Trabalho Diario da Calculadora
        function setDutyCycle(hours, btnElement) {
            dutyCycleHours = hours;
            const buttons = document.querySelectorAll('.btn-duty-chip, .calc-mode-btn');
            buttons.forEach(b => b.classList.remove('active'));
            if (btnElement) btnElement.classList.add('active');

            const labels = {
                8: '8 HORAS / DIA',
                16: '16 HORAS / DIA',
                24: '24/7 CONTINUO'
            };
            const labelEl = document.getElementById('displayHoursMode');
            if (labelEl) labelEl.textContent = labels[hours] || `${hours}H / DIA`;

            recalculateRoi();
            playHapticMechanicalClick();
        }

        // Recalculo Matematico Instantaneo do ROI Edge
        function recalculateRoi() {
            const sliderAgents = document.getElementById('sliderAgents');
            const sliderCloudCost = document.getElementById('sliderCloudCost');

            if (!sliderAgents || !sliderCloudCost) return;

            const agents = parseInt(sliderAgents.value, 10);
            const monthlyCloudCostPerAgent = parseFloat(sliderCloudCost.value);

            const dispAgents = document.getElementById('displayAgentsCount');
            if (dispAgents) dispAgents.textContent = `${agents} ${agents === 1 ? 'AGENTE' : 'AGENTES'}`;

            const dispCloud = document.getElementById('displayCloudCost');
            if (dispCloud) dispCloud.textContent = `R$ ${monthlyCloudCostPerAgent.toLocaleString('pt-BR')} / MES`;

            // Formulas Financeiras & Eletricas
            const annualCloudSavings = agents * monthlyCloudCostPerAgent * 12;

            const hoursPerYear = dutyCycleHours * 365;
            const kwhServer = 0.300 * hoursPerYear;
            const kwhRpi = 0.006 * hoursPerYear;
            const energyKwhSaved = Math.round(kwhServer - kwhRpi);
            const energyCostSavings = energyKwhSaved * 0.85;

            const totalAnnualSavingsBRL = Math.round(annualCloudSavings + energyCostSavings);
            const totalAnnualSavingsUSD = Math.round(totalAnnualSavingsBRL / 5.50);

            const hardwareCost = 650;
            const dailySavings = totalAnnualSavingsBRL / 365;
            const paybackDays = dailySavings > 0 ? Math.max(1, Math.round(hardwareCost / dailySavings)) : 30;
            const co2AvoidedKg = Math.round(energyKwhSaved * 0.08);

            const elBRL = document.getElementById('resAnnualSavingsBRL');
            if (elBRL) elBRL.textContent = `R$ ${totalAnnualSavingsBRL.toLocaleString('pt-BR')}`;

            const elUSD = document.getElementById('resAnnualSavingsUSD');
            if (elUSD) elUSD.textContent = `Aproximadamente US$ ${totalAnnualSavingsUSD.toLocaleString('en-US')} / ano (cambio 5.50)`;

            const elPayback = document.getElementById('resPaybackDays');
            if (elPayback) elPayback.textContent = `${paybackDays} ${paybackDays === 1 ? 'DIA' : 'DIAS'}`;

            const elEnergy = document.getElementById('resEnergySaved');
            if (elEnergy) elEnergy.textContent = `${energyKwhSaved.toLocaleString('pt-BR')} KWH`;

            const elCo2 = document.getElementById('resCo2Avoided');
            if (elCo2) elCo2.textContent = `${co2AvoidedKg.toLocaleString('pt-BR')} KG`;
        }

        // Emissao do Dossie de Economia Forense em Toast Termico
        function generateRoiSummaryToast() {
            const elBRL = document.getElementById('resAnnualSavingsBRL');
            const elPayback = document.getElementById('resPaybackDays');
            const savingsText = elBRL ? elBRL.textContent : 'R$ 11.309';
            const paybackText = elPayback ? elPayback.textContent : '21 DIAS';

            const isEn = window.PiDotsI18n && window.PiDotsI18n.getLanguage() === 'en';
            const msg = isEn
                ? `SAVINGS ESTIMATE: Projected annual savings of ${savingsText}. Hardware amortization in ${paybackText}.`
                : `PROJEÇÃO DE ECONOMIA: Economia anual estimada em ${savingsText}. Amortização do hardware em ${paybackText}.`;

            showToast(msg, 'success', 4500);
            playHapticMechanicalClick();
        }

        // Controle do FAQ Retratil (Accordion Mecanico)
        function toggleObjection(cardId) {
            const card = document.getElementById(cardId);
            if (!card) return;

            const isExpanded = card.classList.contains('expanded');
            
            const allCards = document.querySelectorAll('.objection-card');
            allCards.forEach(c => {
                c.classList.remove('expanded');
                const ind = c.querySelector('.objection-indicator');
                if (ind) ind.textContent = '[+]';
                const hdr = c.querySelector('.objection-header');
                if (hdr) hdr.setAttribute('aria-expanded', 'false');
            });

            if (!isExpanded) {
                card.classList.add('expanded');
                const indicator = card.querySelector('.objection-indicator');
                if (indicator) indicator.textContent = '[-]';
                const header = card.querySelector('.objection-header');
                if (header) header.setAttribute('aria-expanded', 'true');
            }

            playHapticMechanicalClick();
        }

        // Controle do Menu Movel de Secoes
        function toggleMobileNavMenu(isNavigating = false) {
            playHapticMechanicalClick();
            const panel = document.getElementById('mobileNavPanel');
            if (!panel) return;

            const drawer = document.getElementById('retractableDrawer');
            const backdrop = document.getElementById('drawerBackdrop');
            if (drawer && drawer.classList.contains('open')) {
                drawer.classList.remove('open');
                if (backdrop) backdrop.classList.remove('open');
                const btnManual = document.querySelector('.nav-btn-manual');
                if (btnManual) btnManual.setAttribute('aria-expanded', 'false');
            }

            const willOpen = !panel.classList.contains('open');
            panel.classList.toggle('open', willOpen);

            const btnMobile = document.querySelector('.nav-btn-mobile');
            if (btnMobile) btnMobile.setAttribute('aria-expanded', willOpen ? 'true' : 'false');

            if (window.ScrollLockManager) {
                if (willOpen) {
                    window.ScrollLockManager.bloquear();
                } else {
                    window.ScrollLockManager.desbloquear(false, !isNavigating);
                }
            }
        }

        // Alternancia de Abas no Simulador ReAct do Hero
        function switchSimulatorTab(tab) {
            playHapticMechanicalClick();
            const termVp = document.getElementById('heroSimViewport');
            const teleVp = document.getElementById('heroTelemetryViewport');
            const btnTerm = document.getElementById('tabBtnTerminal');
            const btnTele = document.getElementById('tabBtnTelemetry');

            if (tab === 'terminal') {
                if (termVp) termVp.style.display = 'flex';
                if (teleVp) teleVp.style.display = 'none';
                if (btnTerm) btnTerm.classList.add('active');
                if (btnTele) btnTele.classList.remove('active');
            } else {
                if (termVp) termVp.style.display = 'none';
                if (teleVp) teleVp.style.display = 'flex';
                if (btnTerm) btnTerm.classList.remove('active');
                if (btnTele) btnTele.classList.add('active');
            }
        }

        // Limpeza do Viewport do Simulador
        function clearSimViewport() {
            playHapticMechanicalClick();
            clearSimTimers();
            const vp = document.getElementById('heroSimViewport');
            if (vp) {
                vp.innerHTML = `
                    <div class="sim-line prefix">[BOOT] piDots Edge Core pronto para receber novas instrucoes.</div>
                    <div class="sim-line" style="color: var(--blueprint-cyan);">[INFO] Selecione um comando rapido ou envie seu comando customizado.</div>
                `;
            }
            showToast('Terminal limpo com sucesso.', 'info');
        }

        // Helper de Alta Performance: Anexo Atômico sem Reflow Destrutivo
        function appendSimLine(container, html) {
            if (container) {
                container.insertAdjacentHTML('beforeend', html);
            }
        }

        // Execucao de Instrucoes Simuladas no Protocolo AG-UI
        function executeSimulatedOrder(type) {
            playHapticMechanicalClick();
            clearSimTimers();
            switchSimulatorTab('terminal');
            const vp = document.getElementById('heroSimViewport');
            if (!vp) return;

            const input = document.getElementById('heroSimInput');
            if (input) input.value = '';

            const statusText = document.getElementById('heroSimStatusText');
            if (statusText) statusText.innerText = 'PROCESSANDO INSTRUCAO AG-UI...';

            if (type === 'audit_flash') {
                appendSimLine(vp, `<div class="sim-line prefix">[OPERADOR]&gt; @dot-coder auditar integridade Flash MicroSD e consumo RSS</div>`);
                vp.scrollTop = vp.scrollHeight;

                registerSimTimer(() => {
                    appendSimLine(vp, `<div class="sim-line thought">[CADERNO DE RACIOCINIO // DOT-CODER]<br>Inspecionando /proc/meminfo, journal_mode do SQLite e espaco de particao /workspace...</div>`);
                    vp.scrollTop = vp.scrollHeight;
                }, 350);

                registerSimTimer(() => {
                    appendSimLine(vp, `<div class="sim-line tool">[TOOL CALL // SUB-15MS BWRAP]<br>execute_bwrap_command("cat /proc/meminfo | grep MemFree &amp;&amp; df -h /workspace")</div>`);
                    vp.scrollTop = vp.scrollHeight;
                }, 750);

                registerSimTimer(() => {
                    appendSimLine(vp, `<div class="sim-line success">[TOOL RESULT] Codigo: 0 | Saida: MemFree: 3120 MB | Particao Flash: 68% livre. Desgaste 0.</div>`);
                    appendSimLine(vp, `<div class="sim-line" style="color: var(--phosphor-green); font-weight: bold;">[DOT-CODER // RESPOSTA] O nó de borda opera com 64.2MB de RAM física. Nenhuma escrita síncrona nociva foi detectada no MicroSD.</div>`);
                    vp.scrollTop = vp.scrollHeight;
                    if (statusText) statusText.innerText = 'NO ATIVO // 3 AGENTES EM ESPERA // RSS: 64.2MB';
                }, 1200);

            } else if (type === 'council_debate') {
                appendSimLine(vp, `<div class="sim-line prefix">[OPERADOR]&gt; @conselho deliberar sobre politica de sincronizacao WAL para modo headless</div>`);
                vp.scrollTop = vp.scrollHeight;

                registerSimTimer(() => {
                    appendSimLine(vp, `<div class="sim-line thought">[CONSELHO // RODADA 1 - PROPOSTA]<br>@dot-coder: "Proponho manter PRAGMA synchronous=NORMAL e flush a cada 15 segundos."</div>`);
                    vp.scrollTop = vp.scrollHeight;
                }, 400);

                registerSimTimer(() => {
                    appendSimLine(vp, `<div class="sim-line thought" style="border-color: var(--stamp-danger); color: var(--ink-main);">[CONSELHO // RODADA 2 - AUDITORIA]<br>@dot-auditor: "Validado: sob kernel Linux com journaling, o risco de corrupcao e zero e poupa 94% de I/O."</div>`);
                    vp.scrollTop = vp.scrollHeight;
                }, 850);

                registerSimTimer(() => {
                    appendSimLine(vp, `<div class="sim-line success">[CONSELHO // RESOLUCAO DO SUPERVISOR]<br>@dot-supervisor: "Deliberacao encerrada com consenso. Gravando diretriz no SQLite WAL."</div>`);
                    vp.scrollTop = vp.scrollHeight;
                    if (statusText) statusText.innerText = 'DELIBERACAO HOMOLOGADA // WAL PERSISTIDO';
                }, 1300);

            } else if (type === 'self_healing') {
                appendSimLine(vp, `<div class="sim-line prefix">[OPERADOR]&gt; @self-healing executar pipeline de validacao do script data/loader.py</div>`);
                vp.scrollTop = vp.scrollHeight;

                registerSimTimer(() => {
                    appendSimLine(vp, `<div class="sim-line danger">[FALHA DETECTADA // TRACEBACK]<br>ZeroDivisionError: division by zero na linha 28 de data/loader.py (divisor = 0)</div>`);
                    vp.scrollTop = vp.scrollHeight;
                }, 400);

                registerSimTimer(() => {
                    appendSimLine(vp, `<div class="sim-line thought">[SELF-HEALING HARNESS // DIAGNOSTICO CIRURGICO]<br>Detectada divisao por zero. Aplicando guarda condicional "if divisor == 0: return 0.0"...</div>`);
                    vp.scrollTop = vp.scrollHeight;
                }, 850);

                registerSimTimer(() => {
                    appendSimLine(vp, `<div class="sim-line success">[AUTO-CURA CONCLUÍDA // EXIT 0]<br>Script reexecutado em sandbox Bubblewrap. Testes validados sem intervenção do operador.</div>`);
                    vp.scrollTop = vp.scrollHeight;
                    if (statusText) statusText.innerText = 'AUTO-CURA CONCLUÍDA // VALIDAÇÃO NOMINAL';
                }, 1350);

            } else if (type === 'proactive_heartbeat') {
                appendSimLine(vp, `<div class="sim-line prefix">[SISTEMA // CRONITER]&gt; Disparo de tarefa proativa agendada: rotina de checagem a cada 15s</div>`);
                vp.scrollTop = vp.scrollHeight;

                registerSimTimer(() => {
                    appendSimLine(vp, `<div class="sim-line tool">[EDGE SCHEDULER // CHECAGEM PROATIVA]<br>Lendo temperatura SoC (/sys/class/thermal), pool SQLite e portas de rede...</div>`);
                    vp.scrollTop = vp.scrollHeight;
                }, 350);

                registerSimTimer(() => {
                    appendSimLine(vp, `<div class="sim-line success">[SILENCIO INTELIGENTE // HEARTBEAT_OK]<br>Todos os parametros nominais. Nenhuma notificacao desnecessaria enviada ao operador (0 tokens desperdicados).</div>`);
                    vp.scrollTop = vp.scrollHeight;
                    if (statusText) statusText.innerText = 'PULSO OPERACIONAL NOMINAL // 0 TOKENS';
                }, 800);

            } else if (type === 'slash_telemetry') {
                appendSimLine(vp, `<div class="sim-line prefix">[OPERADOR]&gt; /telemetry</div>`);
                vp.scrollTop = vp.scrollHeight;

                registerSimTimer(() => {
                    appendSimLine(vp, `<div class="sim-line" style="font-family: var(--font-pixel); font-size: 8px; color: var(--blueprint-cyan); margin-top: 4px;">=== [RECIBO DE SLASH COMMAND // LOCAL CLIENT-SIDE &lt; 16MS] ===</div>`);
                    appendSimLine(vp, `<div class="sim-line" style="background: rgba(56, 189, 248, 0.08); border-left: 3px solid var(--blueprint-cyan); padding: 6px; font-family: var(--font-mono); font-size: 11px;">
[COMANDO] /telemetry | STATUS: SUCESSO | LATENCIA: 4ms | CONSUMO TOKENS: 0<br>
[CPU SOC]  Broadcom BCM2711 ARM64: [========..] 44.8 C (Nominal &lt; 72 C)<br>
[RAM RSS]  64.2 MB / 3840 MB:      [=.........] 1.6% em uso fisico<br>
[FLASH]    Particao MicroSD:       [===.......] 32% ocupado (14GB livres)<br>
[STORAGE]  SQLite WAL Checkpoint:  Sincronizado | Conexoes ativas: 3
</div>`);
                    vp.scrollTop = vp.scrollHeight;
                    if (statusText) statusText.innerText = 'SLASH COMMAND EXECUTADO LOCALMENTE // 0 TOKENS';
                    showToast('Comando /telemetry executado localmente sem consumo de tokens.', 'info');
                }, 150);

            } else if (type === 'mcp_tools') {
                appendSimLine(vp, `<div class="sim-line prefix">[OPERADOR]&gt; /mcp list</div>`);
                vp.scrollTop = vp.scrollHeight;

                registerSimTimer(() => {
                    appendSimLine(vp, `<div class="sim-line tool">[CLIENTE MCP LITE // PROTOCOLO JSON-RPC 2.0]<br>Servidores conectados: 2 (git-bridge, mqtt-telemetry) | Consumo RAM: 3.8 MB</div>`);
                    vp.scrollTop = vp.scrollHeight;
                }, 300);

                registerSimTimer(() => {
                    appendSimLine(vp, `<div class="sim-line success">[TOOL PRUNING ATIVO]<br>Ferramentas descobertas: 4 | Injetadas no prompt: 2 (apenas allowed_tools_json do @dot-coder). Zero inflação de contexto.</div>`);
                    vp.scrollTop = vp.scrollHeight;
                    if (statusText) statusText.innerText = 'MCP LITE CONECTADO // DYNAMIC TOOL PRUNING';
                    showToast('Servidores MCP Lite listados com Dynamic Tool Pruning.', 'info');
                }, 750);

            } else if (type === 'coagents_state') {
                appendSimLine(vp, `<div class="sim-line prefix">[OPERADOR]&gt; /coagents</div>`);
                vp.scrollTop = vp.scrollHeight;

                registerSimTimer(() => {
                    appendSimLine(vp, `<div class="sim-line tool">[AG-UI // COAGENTS SHARED STATE // STATE_SNAPSHOT]<br>GET /api/threads/thr_active/state -> dot_id: "dot-coder" | phase: "executing_tool" | hop_count: 1</div>`);
                    vp.scrollTop = vp.scrollHeight;
                }, 250);

                registerSimTimer(() => {
                    appendSimLine(vp, `<div class="sim-line success">[SSE // STATE_DELTA SINCRONIZADO AO VIVO]<br>Delta aplicado em sub-4ms: {"active_tool": "execute_shell_command", "plan_progress": 100, "process_rss_mb": 64.2}</div>`);
                    vp.scrollTop = vp.scrollHeight;
                    if (statusText) statusText.innerText = 'COAGENTS STATE SINCRONIZADO // STATE_DELTA OK';
                    showToast('Estado compartilhado CoAgents sincronizado.', 'info');
                }, 650);

            } else if (type === 'dots_computer') {
                appendSimLine(vp, `<div class="sim-line prefix">[OPERADOR]&gt; /computer takeover</div>`);
                vp.scrollTop = vp.scrollHeight;

                registerSimTimer(() => {
                    appendSimLine(vp, `<div class="sim-line tool">[DOT'S COMPUTER // COMPUTADOR DE BORDA]<br>Montando workspace isolado (/workspace/dot-coder) + Explorador de Arquivos + Terminal Bubblewrap...</div>`);
                    vp.scrollTop = vp.scrollHeight;
                }, 300);

                registerSimTimer(() => {
                    appendSimLine(vp, `<div class="sim-line success">[MODO TAKEOVER ATIVO // CONTROLE HUMANO DIRETO]<br>Operador assumiu o terminal bwrap em sub-12ms. Acoes sincronizadas no feed AG-UI da thread!</div>`);
                    vp.scrollTop = vp.scrollHeight;
                    if (statusText) statusText.innerText = 'DOT COMPUTER // MODO TAKEOVER HUMANO ATIVO';
                    showToast('Terminal do Computador de Borda ativo.', 'success');
                }, 750);

            } else if (type === 'save_space') {
                appendSimLine(vp, `<div class="sim-line prefix">[OPERADOR]&gt; /save-space Arquitetura_CoAgents_Edge</div>`);
                vp.scrollTop = vp.scrollHeight;

                registerSimTimer(() => {
                    appendSimLine(vp, `<div class="sim-line tool">[SAVE THREAD AS SPACE // POST /api/threads/thr_active/save-as-space]<br>Consolidando mensagens da thread e indexando no motor de embedding 64D unificado...</div>`);
                    vp.scrollTop = vp.scrollHeight;
                }, 300);

                registerSimTimer(() => {
                    appendSimLine(vp, `<div class="sim-line success">[SPACE CRIADO // REVISAO #1 GRAVADA NO SQLITE WAL]<br>Artefato "Arquitetura_CoAgents_Edge.md" disponivel no painel Spaces &amp; Canais e no Live Canvas!</div>`);
                    vp.scrollTop = vp.scrollHeight;
                    if (statusText) statusText.innerText = 'THREAD SALVA COMO SPACE // MOTOR 64D INDEXADO';
                    showToast('Conversa versionada em Spaces no SQLite WAL.', 'success');
                }, 750);

            } else if (type === 'hitl_danger') {
                appendSimLine(vp, `<div class="sim-line prefix">[OPERADOR]&gt; @dot-coder limpar logs antigos em /var/log</div>`);
                vp.scrollTop = vp.scrollHeight;

                registerSimTimer(() => {
                    appendSimLine(vp, `<div class="sim-line danger" style="background: rgba(239, 68, 68, 0.15); border-left: 3px solid var(--stamp-danger); padding: 8px;">[GENERATIVE UI CARD // HITL RETENCAO DE SEGURANCA]<br>Tool: execute_shell_command | Args originais: {"command": "rm -rf /var/log/*"}<br>Operador editou modified_args para: {"command": "rm -f /workspace/logs/*.tmp"} e homologou!</div>`);
                    vp.scrollTop = vp.scrollHeight;
                }, 400);

                registerSimTimer(() => {
                    appendSimLine(vp, `<div class="sim-line success">[HITL RESOLVE // RETOMADA AUTOMATICA DO AGENTE]<br>POST /api/hitl/apr_01/resolve (modified_args aplicado) -> Agente retomou turno automaticamente com seguranca!</div>`);
                    vp.scrollTop = vp.scrollHeight;
                    if (statusText) statusText.innerText = 'HITL HOMOLOGADO COM MODIFIED_ARGS // RETOMADO';
                    showToast('Ordem HITL autorizada pelo operador e retomada.', 'success');
                }, 950);
            }
        }

        // Comando Customizado Digitado pelo Usuario no Prompt
        function handleCustomSimOrder() {
            const input = document.getElementById('heroSimInput');
            if (!input || !input.value.trim()) return;

            const text = input.value.trim();
            playHapticMechanicalClick();
            clearSimTimers();
            switchSimulatorTab('terminal');

            const vp = document.getElementById('heroSimViewport');
            if (!vp) return;

            const safeText = String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
            appendSimLine(vp, `<div class="sim-line prefix">[OPERADOR]&gt; ${safeText}</div>`);
            input.value = '';
            vp.scrollTop = vp.scrollHeight;

            if (text.startsWith('/')) {
                const cmd = text.split(' ')[0].toLowerCase();
                const safeCmd = cmd.replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
                registerSimTimer(() => {
                    appendSimLine(vp, `<div class="sim-line" style="font-family: var(--font-pixel); font-size: 8px; color: var(--blueprint-cyan); margin-top: 4px;">=== [RECIBO DE SLASH COMMAND // CATALOGO DE 34 COMANDOS] ===</div>`);
                    if (cmd === '/clear') {
                        vp.innerHTML = `<div class="sim-line prefix">[BOOT] piDots Edge Core v1.5.3 inicializado sob SQLite WAL e Python 3.13 uvloop.</div>
                        <div class="sim-line" style="color: var(--phosphor-green);">[RECIBO] Bobina de teletipo limpa cirurgicamente via comando /clear (0 tokens consumidos).</div>`;
                        showToast('Teletipo limpo via /clear', 'info');
                    } else if (cmd === '/telemetry') {
                        executeSimulatedOrder('slash_telemetry');
                    } else if (cmd === '/coagents') {
                        executeSimulatedOrder('coagents_state');
                    } else if (cmd === '/computer') {
                        executeSimulatedOrder('dots_computer');
                    } else if (cmd === '/save-space') {
                        executeSimulatedOrder('save_space');
                    } else if (cmd === '/mcp') {
                        executeSimulatedOrder('mcp_tools');
                    } else {
                        appendSimLine(vp, `<div class="sim-line success">[RECIBO] Comando ${safeCmd} executado no cliente em sub-16ms | 0 tokens gastos | Sessao intacta.</div>`);
                        showToast(`Comando ${safeCmd} processado localmente.`, 'info');
                    }
                    vp.scrollTop = vp.scrollHeight;
                }, 120);
                return;
            }

            registerSimTimer(() => {
                appendSimLine(vp, `<div class="sim-line thought">[CADERNO DE RACIOCINIO // AG-UI]<br>Analisando intencao semantica... Roteando comando atraves da poda dinamica de ferramentas...</div>`);
                vp.scrollTop = vp.scrollHeight;
            }, 300);

            registerSimTimer(() => {
                appendSimLine(vp, `<div class="sim-line tool">[TOOL CALL // LOCAL FIRST]<br>execute_bwrap_command("echo '[PROCESSO EM EXECUCAO NA BORDA]'")</div>`);
                vp.scrollTop = vp.scrollHeight;
            }, 700);

            registerSimTimer(() => {
                appendSimLine(vp, `<div class="sim-line success">[RESPOSTA DO AGENTE]<br>Comando processado pelo nó local piDots em menos de 14ms.</div>`);
                vp.scrollTop = vp.scrollHeight;
            }, 1100);
        }

        // Helper de Alta Performance: Anexo Atômico sem Reflow Destrutivo
        function appendSimLine(container, html) {
            if (container) {
                container.insertAdjacentHTML('beforeend', html);
            }
        }

        // Simulacao da Arena: Conselho Tripartite com Pool de Timers
        function runCouncilDemoSimulation() {
            playHapticMechanicalClick();
            clearSimTimers();
            const feed = document.getElementById('councilDemoFeed');
            const status = document.getElementById('councilRoundStatus');
            if (!feed) return;

            if (status) status.innerText = 'STATUS: SESSAO EM ANDAMENTO (RODADA 1/3)';
            feed.innerHTML = `<div class="council-bubble coder"><strong>[@dot-coder // PROPOSTA]:</strong> Proponho unificar o historico de mensagens com visibilidade 'internal' para manter o feed do operador 100% limpo.</div>`;

            registerSimTimer(() => {
                if (status) status.innerText = 'STATUS: DEBATE CRITICO (RODADA 2/3)';
                appendSimLine(feed, `<div class="council-bubble auditor"><strong>[@dot-auditor // AUDITORIA]:</strong> Ponto critico: mensagens internas devem ter chave estrangeira estrita no SQLite WAL para evitar orfaos.</div>`);
                feed.scrollTop = feed.scrollHeight;
            }, 600);

            registerSimTimer(() => {
                if (status) status.innerText = 'STATUS: CONCLUIDO (RODADA 3/3)';
                appendSimLine(feed, `<div class="council-bubble supervisor"><strong>[@dot-supervisor // VEREDITO]:</strong> Aprovado com a restricao do auditor. Registrando resolucao na tabela agent_handoffs como COMPLETED.</div>`);
                feed.scrollTop = feed.scrollHeight;
                showToast('Conselho Consultivo: Deliberação tripartite concluída.', 'success');
            }, 1200);
        }

        // Simulacao da Arena: Self-Healing com Pool de Timers
        function runHealingDemoSimulation() {
            playHapticMechanicalClick();
            clearSimTimers();
            const feed = document.getElementById('healingDemoFeed');
            const status = document.getElementById('healingStatus');
            if (!feed) return;

            if (status) status.innerText = 'HARNESS: INTERCEPTANDO FALHA';
            feed.innerHTML = `<div style="color: var(--stamp-danger);">[EXECUCAO FALHOU] File "pipeline.py", line 42: ZeroDivisionError: float division by zero</div>`;

            registerSimTimer(() => {
                appendSimLine(feed, `<div style="color: var(--thermal-amber); margin: 4px 0;">[HARNESS] AST Parser isolou a falha: variavel 'taxa_amostragem' recebendo 0.</div>`);
                feed.scrollTop = feed.scrollHeight;
            }, 500);

            registerSimTimer(() => {
                appendSimLine(feed, `<div style="color: var(--phosphor-green); font-weight: bold;">[AUTO-CURA] Correcao aplicada: adicionada guarda 'max(taxa, 1e-6)'. Reexecutando... SUCESSO (Exit: 0).</div>`);
                if (status) status.innerText = 'HARNESS: REPARADO COM EXITO';
                feed.scrollTop = feed.scrollHeight;
                showToast('Self-Healing: Script corrigido em sandbox.', 'success');
            }, 1100);
        }

        // Simulacao da Arena: Telemetria & Triggers com Pool de Timers
        function injectTelemetryPulse() {
            playHapticMechanicalClick();
            clearSimTimers();
            const ramPolyline = document.getElementById('arenaRamPolyline');
            const ramPolygon = document.getElementById('arenaRamPolygon');
            const ramDisplay = document.getElementById('arenaRamDisplay');

            if (ramDisplay) ramDisplay.innerText = '178.6 MB (59.5% // PULSO DE TESTE)';
            if (ramPolyline) ramPolyline.setAttribute('points', '0,60 40,60 40,35 90,35 90,38 140,38 140,25 190,25 190,30 240,30 240,40 290,40 290,42 310,42');
            if (ramPolygon) ramPolygon.setAttribute('points', '0,80 0,60 40,60 40,35 90,35 90,38 140,38 140,25 190,25 190,30 240,30 240,40 290,40 290,42 310,42 310,80');

            showToast('TELEMETRIA: Pulso de estresse injetado. RAM contida em limite seguro.', 'warning');

            registerSimTimer(() => {
                if (ramDisplay) ramDisplay.innerText = '118.4 MB (39.4% // RECUPERADO)';
                if (ramPolyline) ramPolyline.setAttribute('points', '0,60 40,60 40,55 90,55 90,62 140,62 140,50 190,50 190,52 240,52 240,46 290,46 290,44 310,44');
                if (ramPolygon) ramPolygon.setAttribute('points', '0,80 0,60 40,60 40,55 90,55 90,62 140,62 140,50 190,50 190,52 240,52 240,46 290,46 290,44 310,44 310,80');
            }, 3000);
        }

        function simulateThermalTriggerAlert() {
            playHapticMechanicalClick();
            clearSimTimers();
            const tempDisplay = document.getElementById('arenaTempDisplay');
            const tempPolyline = document.getElementById('arenaTempPolyline');
            const tempPolygon = document.getElementById('arenaTempPolygon');

            if (tempDisplay) tempDisplay.innerHTML = '<span style="color: var(--stamp-danger);">76.4 C (TRIGGER ATIVADO // MITIGACAO)</span>';
            if (tempPolyline) tempPolyline.setAttribute('stroke', '#ef4444');
            if (tempPolyline) tempPolyline.setAttribute('points', '0,52 50,52 50,30 110,30 110,22 170,22 170,18 230,18 230,15 290,15 290,14 310,14');
            if (tempPolygon) tempPolygon.setAttribute('points', '0,80 0,52 50,52 50,30 110,30 110,22 170,22 170,18 230,18 230,15 290,15 290,14 310,14 310,80');

            showToast('ALERTA TÉRMICO: Temperatura acima de 72 °C. EdgeHardwareTriggers ativou desaceleração de polling.', 'danger', 4500);

            registerSimTimer(() => {
                if (tempDisplay) tempDisplay.innerHTML = '<span>48.2 C (NOMINAL)</span>';
                if (tempPolyline) tempPolyline.setAttribute('stroke', '#33ff66');
                if (tempPolyline) tempPolyline.setAttribute('points', '0,52 50,52 50,50 110,50 110,54 170,54 170,49 230,49 230,48 290,48 290,47 310,47');
                if (tempPolygon) tempPolygon.setAttribute('points', '0,80 0,52 50,52 50,50 110,50 110,54 170,54 170,49 230,49 230,48 290,48 290,47 310,47 310,80');
            }, 3500);
        }

        // Copiar Snippet com Feedback Tatil e Fallback HTTP LAN
        function copySnippet(text) {
            playHapticMechanicalClick();
            const isEn = window.PiDotsI18n && window.PiDotsI18n.getLanguage() === 'en';
            const successMsg = isEn ? 'Command copied to clipboard.' : 'Comando copiado para a área de transferência.';

            if (window.PixelSystem && window.PixelSystem.copyToClipboard) {
                window.PixelSystem.copyToClipboard(text).then(() => {
                    showToast(successMsg, 'success');
                }).catch(() => {
                    showToast(`Comando: ${text}`, 'info');
                });
                return;
            }

            // Fallback direto se PixelSystem nao estiver presente
            try {
                const ta = document.createElement('textarea');
                ta.value = text;
                ta.setAttribute('readonly', '');
                ta.style.position = 'fixed';
                ta.style.top = '-9999px';
                document.body.appendChild(ta);
                ta.select();
                const ok = document.execCommand('copy');
                document.body.removeChild(ta);
                showToast(ok ? successMsg : `Comando: ${text}`, ok ? 'success' : 'info');
            } catch (e) {
                showToast(`Comando: ${text}`, 'info');
            }
        }

        // Sistema de Notificacoes em Papel Termico (Pixel Toast)
        function showToast(message, type = 'info', duration = 3200) {
            if (window.PixelSystem && typeof window.PixelSystem.toast === 'function') {
                window.PixelSystem.toast(message, type, duration);
                return;
            }
            const container = document.getElementById('pixelToastContainer');
            if (!container) return;
            const toast = document.createElement('div');
            toast.className = 'pixel-toast';
            toast.textContent = message;
            container.appendChild(toast);
            setTimeout(() => toast.remove(), duration);
        }

        // Executa calculo inicial ao carregar a pagina
        window.addEventListener('DOMContentLoaded', () => {
            recalculateRoi();
        });

        // Tecla ESC fecha Drawer e Menu Movel
        window.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const drawer = document.getElementById('retractableDrawer');
                if (drawer && drawer.classList.contains('open')) {
                    toggleDrawer();
                }
                const mobilePanel = document.getElementById('mobileNavPanel');
                if (mobilePanel && mobilePanel.classList.contains('open')) {
                    toggleMobileNavMenu();
                }
            }
        });

        window.addEventListener('pidots:langchange', () => {
            recalculateRoi();
        });

        // Navegacao Global por Teclado e Resolucao de Superficies delegada ao CrossSurfaceRouter (static/js/core/cross-surface-router.js)

        // Integracao PWA & Service Worker na Landing Page Oficial
        const PiDotsLandingPWA = (function() {
            let deferredPrompt = null;

            function init() {
                if ('serviceWorker' in navigator) {
                    window.addEventListener('load', () => {
                        navigator.serviceWorker.register('/sw.js').catch((err) => {
                            console.warn('[piDots Landing] Falha ao registrar Service Worker:', err);
                        });
                    });
                }

                window.addEventListener('beforeinstallprompt', (e) => {
                    e.preventDefault();
                    deferredPrompt = e;
                    const btn = document.getElementById('btnLandingPwaInstall');
                    if (btn) btn.style.display = 'inline-flex';
                });

                window.addEventListener('appinstalled', () => {
                    deferredPrompt = null;
                    const btn = document.getElementById('btnLandingPwaInstall');
                    if (btn) btn.style.display = 'none';
                });

                // Detecção do iOS Safari
                const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
                const isStandalone = window.navigator.standalone === true;
                if (isIOS && !isStandalone) {
                    const btn = document.getElementById('btnLandingPwaInstall');
                    if (btn) {
                        btn.style.display = 'inline-flex';
                        btn.onclick = () => {
                            alert('Instalacao no iOS Safari:\n1. Toque no botao Compartilhar (icone de quadrado com seta para cima)\n2. Selecione "Adicionar a Tela de Inicio"');
                        };
                    }
                }
            }

            async function install() {
                if (!deferredPrompt) return;
                deferredPrompt.prompt();
                const { outcome } = await deferredPrompt.userChoice;
                if (outcome === 'accepted') {
                    console.log('[piDots Landing] Instalacao PWA aceita.');
                }
                deferredPrompt = null;
                const btn = document.getElementById('btnLandingPwaInstall');
                if (btn) btn.style.display = 'none';
            }

            return {
                init: init,
                install: install
            };
        })();

        // Demonstrador Interativo de Aprovacao HITL no Hero Split-Screen
        function handleHeroDemoHitl(action) {
            playHapticMechanicalClick();
            const hitlBox = document.getElementById('heroDemoHitlBox');
            const actionsContainer = document.getElementById('heroDemoHitlActions');
            if (!hitlBox || !actionsContainer) return;

            if (action === 'approve') {
                hitlBox.style.borderColor = 'var(--phosphor-green)';
                actionsContainer.innerHTML = '<span class="silicon-badge badge-green" style="font-size: 10px; padding: 4px 8px; border-radius: 2px;">HOMOLOGADO // EXECUCAO LIBERADA VIA HMAC-SHA256</span>';
                showToast('Aprovacao HITL concedida para bwrap. Retomando agente autonomo.', 'success');
            } else if (action === 'reject') {
                hitlBox.style.borderColor = 'var(--stamp-danger)';
                actionsContainer.innerHTML = '<span class="silicon-badge badge-red" style="font-size: 10px; padding: 4px 8px; border-radius: 2px;">VETADO // EXECUCAO RECUSADA POR GOVERNANCA</span>';
                showToast('Comando de sandbox vetado por governanca Deny-by-Default.', 'warning');
            } else if (action === 'inspect') {
                const arena = document.getElementById('arena-hitl');
                if (arena) {
                    arena.scrollIntoView({ behavior: 'smooth' });
                }
                showToast('Abrindo auditoria de governança e arena interativa de segurança.', 'info');
            }
        }

        document.addEventListener('DOMContentLoaded', () => {
            PiDotsLandingPWA.init();
        });

    // Exportacao Global para manipuladores de evento inline
    window.playHapticMechanicalClick = playHapticMechanicalClick;
    window.handleHeroDemoHitl = handleHeroDemoHitl;
    window.toggleTheme = toggleTheme;
    window.toggleDrawer = toggleDrawer;
    window.filterDrawerSteps = filterDrawerSteps;
    window.toggleMechanicalSafetyLock = toggleMechanicalSafetyLock;
    window.triggerDemoApprove = triggerDemoApprove;
    window.triggerDemoVeto = triggerDemoVeto;
    window.setDutyCycle = setDutyCycle;
    window.recalculateRoi = recalculateRoi;
    window.generateRoiSummaryToast = generateRoiSummaryToast;
    window.toggleObjection = toggleObjection;
    window.toggleMobileNavMenu = toggleMobileNavMenu;
    window.switchSimulatorTab = switchSimulatorTab;
    window.clearSimViewport = clearSimViewport;
    window.executeSimulatedOrder = executeSimulatedOrder;
    window.handleCustomSimOrder = handleCustomSimOrder;
    window.runCouncilDemoSimulation = runCouncilDemoSimulation;
    window.runHealingDemoSimulation = runHealingDemoSimulation;
    window.injectTelemetryPulse = injectTelemetryPulse;
    window.simulateThermalTriggerAlert = simulateThermalTriggerAlert;
    window.copySnippet = copySnippet;
    window.showToast = showToast;
    window.PiDotsLandingPWA = PiDotsLandingPWA;
})(typeof window !== "undefined" ? window : this);
