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

        // Sintetizador de Som Tatil Mecanico 8-Bit (Web Audio API sem dependencias)
        function playHapticMechanicalClick() {
            if (window.PixelSystem && typeof window.PixelSystem.playMechanicalClick === 'function') {
                window.PixelSystem.playMechanicalClick();
            }
        }

        // Alternancia de Tema: Dark Noir vs Blueprint
        function toggleTheme() {
            isBlueprint = !isBlueprint;
            playHapticMechanicalClick();
            if (isBlueprint) {
                document.documentElement.setAttribute('data-theme', 'blueprint');
                showToast('Tema comutado para Blueprint Tecnico de Prancheta.', 'info');
            } else {
                document.documentElement.removeAttribute('data-theme');
                showToast('Tema comutado para Dark Paper Noir Oficial.', 'info');
            }
        }

        // Controle do Menu Retratil Direito (Guia Tecnico)
        function toggleDrawer() {
            const drawer = document.getElementById('retractableDrawer');
            const backdrop = document.getElementById('drawerBackdrop');
            if (!drawer || !backdrop) return;

            const willOpen = !drawer.classList.contains('open');
            drawer.classList.toggle('open', willOpen);
            backdrop.classList.toggle('open', willOpen);

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
                step.style.display = text.includes(term) ? 'block' : 'none';
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

            if (isMechanicalUnlocked) {
                if (labelEl) labelEl.textContent = 'TRAVA DESTRAVADA';
                showToast('ALERTA: Trava mecanica de seguranca destravada pelo operador.', 'warning');
            } else {
                if (labelEl) labelEl.textContent = 'TRAVA ENGATADA';
                showToast('SEGURANCA: Trava mecanica engatada. Homologacao bloqueada.', 'info');
            }
        }

        function triggerDemoApprove() {
            const approveStamp = document.getElementById('demoStampApprove');
            const rejectStamp = document.getElementById('demoStampReject');

            if (approveStamp) approveStamp.style.transform = 'rotate(2.5deg) scale(1.15)';
            if (rejectStamp) rejectStamp.style.opacity = '0.25';

            playHapticMechanicalClick();

            setTimeout(() => {
                showToast('HOMOLOGADO: Acao oficial autenticada no SQLite WAL! Comando liberado para o sandbox.', 'success');
                if (approveStamp) approveStamp.style.transform = 'rotate(2deg) scale(1.0)';
            }, 180);
        }

        function triggerDemoVeto() {
            const approveStamp = document.getElementById('demoStampApprove');
            const rejectStamp = document.getElementById('demoStampReject');

            if (rejectStamp) rejectStamp.style.transform = 'rotate(-3deg) scale(1.15)';
            if (approveStamp) approveStamp.style.opacity = '0.25';

            playHapticMechanicalClick();

            setTimeout(() => {
                showToast('VETO REGISTRADO: Acao cancelada e arquivada com seguranca na fila de governanca.', 'danger');
                if (rejectStamp) rejectStamp.style.transform = 'rotate(-3deg) scale(1.0)';
            }, 180);
        }

        // Controle de Ciclo de Trabalho Diario da Calculadora
        function setDutyCycle(hours, btnElement) {
            dutyCycleHours = hours;
            const buttons = document.querySelectorAll('.calc-mode-btn');
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

            showToast(`DOSSIE FORENSE: Economia anual projetada de ${savingsText}. Amortizacao do hardware em apenas ${paybackText}!`, 'success', 4500);
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
            });

            if (!isExpanded) {
                card.classList.add('expanded');
                const indicator = card.querySelector('.objection-indicator');
                if (indicator) indicator.textContent = '[-]';
            }

            playHapticMechanicalClick();
        }

        // Controle do Menu Movel de Secoes
        function toggleMobileNavMenu(isNavigating = false) {
            playHapticMechanicalClick();
            const panel = document.getElementById('mobileNavPanel');
            if (!panel) return;

            const willOpen = !panel.classList.contains('open');
            panel.classList.toggle('open', willOpen);

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
                if (termVp) termVp.style.display = 'block';
                if (teleVp) teleVp.style.display = 'none';
                if (btnTerm) btnTerm.classList.add('active');
                if (btnTele) btnTele.classList.remove('active');
            } else {
                if (termVp) termVp.style.display = 'none';
                if (teleVp) teleVp.style.display = 'block';
                if (btnTerm) btnTerm.classList.remove('active');
                if (btnTele) btnTele.classList.add('active');
            }
        }

        // Limpeza do Viewport do Simulador
        function clearSimViewport() {
            playHapticMechanicalClick();
            const vp = document.getElementById('heroSimViewport');
            if (vp) {
                vp.innerHTML = `
                    <div class="sim-line prefix">[BOOT] piDots Edge Core pronto para receber novas instrucoes.</div>
                    <div class="sim-line" style="color: var(--blueprint-cyan);">[INFO] Selecione um comando rapido ou envie seu comando customizado.</div>
                `;
            }
            showToast('Terminal limpo com sucesso.', 'info');
        }

        // Execucao de Instrucoes Simuladas no Protocolo AG-UI
        function executeSimulatedOrder(type) {
            playHapticMechanicalClick();
            switchSimulatorTab('terminal');
            const vp = document.getElementById('heroSimViewport');
            if (!vp) return;

            const input = document.getElementById('heroSimInput');
            if (input) input.value = '';

            const statusText = document.getElementById('heroSimStatusText');
            if (statusText) statusText.innerText = 'PROCESSANDO INSTRUCAO AG-UI...';

            if (type === 'audit_flash') {
                vp.innerHTML += `<div class="sim-line prefix">[OPERADOR]&gt; @dot-coder auditar integridade Flash MicroSD e consumo RSS</div>`;
                vp.scrollTop = vp.scrollHeight;

                setTimeout(() => {
                    vp.innerHTML += `<div class="sim-line thought">[CADERNO DE RACIOCINIO // DOT-CODER]<br>Inspecionando /proc/meminfo, journal_mode do SQLite e espaco de particao /workspace...</div>`;
                    vp.scrollTop = vp.scrollHeight;
                }, 350);

                setTimeout(() => {
                    vp.innerHTML += `<div class="sim-line tool">[TOOL CALL // SUB-15MS BWRAP]<br>execute_bwrap_command("cat /proc/meminfo | grep MemFree &amp;&amp; df -h /workspace")</div>`;
                    vp.scrollTop = vp.scrollHeight;
                }, 750);

                setTimeout(() => {
                    vp.innerHTML += `<div class="sim-line success">[TOOL RESULT] Codigo: 0 | Saida: MemFree: 3120 MB | Particao Flash: 68% livre. Desgaste 0.</div>`;
                    vp.innerHTML += `<div class="sim-line" style="color: var(--phosphor-green); font-weight: bold;">[DOT-CODER // RESPOSTA] O ecossistema esta operando com 64.2MB de RAM real. Nenhuma escrita sincrona danosa foi detectada no MicroSD.</div>`;
                    vp.scrollTop = vp.scrollHeight;
                    if (statusText) statusText.innerText = 'NO ATIVO // 3 AGENTES EM ESPERA // RSS: 64.2MB';
                }, 1200);

            } else if (type === 'council_debate') {
                vp.innerHTML += `<div class="sim-line prefix">[OPERADOR]&gt; @conselho deliberar sobre politica de sincronizacao WAL para modo headless</div>`;
                vp.scrollTop = vp.scrollHeight;

                setTimeout(() => {
                    vp.innerHTML += `<div class="sim-line thought">[CONSELHO // RODADA 1 - PROPOSTA]<br>@dot-coder: "Proponho manter PRAGMA synchronous=NORMAL e flush a cada 15 segundos."</div>`;
                    vp.scrollTop = vp.scrollHeight;
                }, 400);

                setTimeout(() => {
                    vp.innerHTML += `<div class="sim-line thought" style="border-color: var(--stamp-danger); color: #fecaca;">[CONSELHO // RODADA 2 - AUDITORIA]<br>@dot-auditor: "Validado: sob kernel Linux com journaling, o risco de corrupcao e zero e poupa 94% de I/O."</div>`;
                    vp.scrollTop = vp.scrollHeight;
                }, 850);

                setTimeout(() => {
                    vp.innerHTML += `<div class="sim-line success">[CONSELHO // RESOLUCAO DO SUPERVISOR]<br>@dot-supervisor: "Deliberacao encerrada com consenso. Gravando diretriz no SQLite WAL."</div>`;
                    vp.scrollTop = vp.scrollHeight;
                    if (statusText) statusText.innerText = 'DELIBERACAO HOMOLOGADA // WAL PERSISTIDO';
                }, 1300);

            } else if (type === 'self_healing') {
                vp.innerHTML += `<div class="sim-line prefix">[OPERADOR]&gt; @self-healing executar pipeline de validacao do script data/loader.py</div>`;
                vp.scrollTop = vp.scrollHeight;

                setTimeout(() => {
                    vp.innerHTML += `<div class="sim-line danger">[FALHA DETECTADA // TRACEBACK]<br>ZeroDivisionError: division by zero na linha 28 de data/loader.py (divisor = 0)</div>`;
                    vp.scrollTop = vp.scrollHeight;
                }, 400);

                setTimeout(() => {
                    vp.innerHTML += `<div class="sim-line thought">[SELF-HEALING HARNESS // DIAGNOSTICO CIRURGICO]<br>Detectada divisao por zero. Aplicando guarda condicional "if divisor == 0: return 0.0"...</div>`;
                    vp.scrollTop = vp.scrollHeight;
                }, 850);

                setTimeout(() => {
                    vp.innerHTML += `<div class="sim-line success">[AUTO-CURA CONCLUIDA // EXIT 0]<br>Script reexecutado com sucesso em sandbox Bubblewrap. 100% dos testes aprovados sem intervencao humana!</div>`;
                    vp.scrollTop = vp.scrollHeight;
                    if (statusText) statusText.innerText = 'AUTO-CURA FINALIZADA COM SUCESSO';
                }, 1350);

            } else if (type === 'proactive_heartbeat') {
                vp.innerHTML += `<div class="sim-line prefix">[SISTEMA // CRONITER]&gt; Disparo de tarefa proativa agendada: rotina de checagem a cada 15s</div>`;
                vp.scrollTop = vp.scrollHeight;

                setTimeout(() => {
                    vp.innerHTML += `<div class="sim-line tool">[EDGE SCHEDULER // CHECAGEM PROATIVA]<br>Lendo temperatura SoC (/sys/class/thermal), pool SQLite e portas de rede...</div>`;
                    vp.scrollTop = vp.scrollHeight;
                }, 350);

                setTimeout(() => {
                    vp.innerHTML += `<div class="sim-line success">[SILENCIO INTELIGENTE // HEARTBEAT_OK]<br>Todos os parametros nominais. Nenhuma notificacao desnecessaria enviada ao operador (0 tokens desperdicados).</div>`;
                    vp.scrollTop = vp.scrollHeight;
                    if (statusText) statusText.innerText = 'PULSO OPERACIONAL NOMINAL // 0 TOKENS';
                }, 800);

            } else if (type === 'slash_telemetry') {
                vp.innerHTML += `<div class="sim-line prefix">[OPERADOR]&gt; /telemetry</div>`;
                vp.scrollTop = vp.scrollHeight;

                setTimeout(() => {
                    vp.innerHTML += `<div class="sim-line" style="font-family: var(--font-pixel); font-size: 8px; color: var(--blueprint-cyan); margin-top: 4px;">=== [RECIBO DE SLASH COMMAND // LOCAL CLIENT-SIDE &lt; 16MS] ===</div>`;
                    vp.innerHTML += `<div class="sim-line" style="background: rgba(56, 189, 248, 0.08); border-left: 3px solid var(--blueprint-cyan); padding: 6px; font-family: var(--font-mono); font-size: 11px;">
[COMANDO] /telemetry | STATUS: SUCESSO | LATENCIA: 4ms | CONSUMO TOKENS: 0<br>
[CPU SOC]  Broadcom BCM2711 ARM64: [========..] 44.8 C (Nominal &lt; 72 C)<br>
[RAM RSS]  64.2 MB / 3840 MB:      [=.........] 1.6% em uso fisico<br>
[FLASH]    Particao MicroSD:       [===.......] 32% ocupado (14GB livres)<br>
[STORAGE]  SQLite WAL Checkpoint:  Sincronizado | Conexoes ativas: 3
</div>`;
                    vp.scrollTop = vp.scrollHeight;
                    if (statusText) statusText.innerText = 'SLASH COMMAND EXECUTADO LOCALMENTE // 0 TOKENS';
                    showToast('Comando /telemetry executado em 4ms sem consumo de tokens!', 'info');
                }, 150);

            } else if (type === 'mcp_tools') {
                vp.innerHTML += `<div class="sim-line prefix">[OPERADOR]&gt; /mcp list</div>`;
                vp.scrollTop = vp.scrollHeight;

                setTimeout(() => {
                    vp.innerHTML += `<div class="sim-line tool">[CLIENTE MCP LITE // PROTOCOLO JSON-RPC 2.0]<br>Servidores conectados: 2 (git-bridge, mqtt-telemetry) | Consumo RAM: 3.8 MB</div>`;
                    vp.scrollTop = vp.scrollHeight;
                }, 300);

                setTimeout(() => {
                    vp.innerHTML += `<div class="sim-line success">[TOOL PRUNING ATIVO]<br>Ferramentas descobertas: 4 | Injetadas no prompt: 2 (apenas allowed_tools_json do @dot-coder). Zero inflacao de contexto!</div>`;
                    vp.scrollTop = vp.scrollHeight;
                    if (statusText) statusText.innerText = 'MCP LITE CONECTADO // DYNAMIC TOOL PRUNING';
                    showToast('Servidores MCP Lite listados com Dynamic Tool Pruning!', 'info');
                }, 750);

            } else if (type === 'coagents_state') {
                vp.innerHTML += `<div class="sim-line prefix">[OPERADOR]&gt; /coagents</div>`;
                vp.scrollTop = vp.scrollHeight;

                setTimeout(() => {
                    vp.innerHTML += `<div class="sim-line tool">[AG-UI // COAGENTS SHARED STATE // STATE_SNAPSHOT]<br>GET /api/threads/thr_active/state -> dot_id: "dot-coder" | phase: "executing_tool" | hop_count: 1</div>`;
                    vp.scrollTop = vp.scrollHeight;
                }, 250);

                setTimeout(() => {
                    vp.innerHTML += `<div class="sim-line success">[SSE // STATE_DELTA SINCRONIZADO AO VIVO]<br>Delta aplicado em sub-4ms: {"active_tool": "execute_shell_command", "plan_progress": 100, "process_rss_mb": 64.2}</div>`;
                    vp.scrollTop = vp.scrollHeight;
                    if (statusText) statusText.innerText = 'COAGENTS STATE SINCRONIZADO // STATE_DELTA OK';
                    showToast('Estado compartilhado CoAgents sincronizado ao vivo!', 'info');
                }, 650);

            } else if (type === 'dots_computer') {
                vp.innerHTML += `<div class="sim-line prefix">[OPERADOR]&gt; /computer takeover</div>`;
                vp.scrollTop = vp.scrollHeight;

                setTimeout(() => {
                    vp.innerHTML += `<div class="sim-line tool">[DOT'S COMPUTER // COMPUTADOR DE BORDA]<br>Montando workspace isolado (/workspace/dot-coder) + Explorador de Arquivos + Terminal Bubblewrap...</div>`;
                    vp.scrollTop = vp.scrollHeight;
                }, 300);

                setTimeout(() => {
                    vp.innerHTML += `<div class="sim-line success">[MODO TAKEOVER ATIVO // CONTROLE HUMANO DIRETO]<br>Operador assumiu o terminal bwrap em sub-12ms. Acoes sincronizadas no feed AG-UI da thread!</div>`;
                    vp.scrollTop = vp.scrollHeight;
                    if (statusText) statusText.innerText = 'DOT COMPUTER // MODO TAKEOVER HUMANO ATIVO';
                    showToast('Computador de Borda aberto em Modo Takeover!', 'success');
                }, 750);

            } else if (type === 'save_space') {
                vp.innerHTML += `<div class="sim-line prefix">[OPERADOR]&gt; /save-space Arquitetura_CoAgents_Edge</div>`;
                vp.scrollTop = vp.scrollHeight;

                setTimeout(() => {
                    vp.innerHTML += `<div class="sim-line tool">[SAVE THREAD AS SPACE // POST /api/threads/thr_active/save-as-space]<br>Consolidando mensagens da thread e indexando no motor de embedding 64D unificado...</div>`;
                    vp.scrollTop = vp.scrollHeight;
                }, 300);

                setTimeout(() => {
                    vp.innerHTML += `<div class="sim-line success">[SPACE CRIADO // REVISAO #1 GRAVADA NO SQLITE WAL]<br>Artefato "Arquitetura_CoAgents_Edge.md" disponivel no painel Spaces &amp; Canais e no Live Canvas!</div>`;
                    vp.scrollTop = vp.scrollHeight;
                    if (statusText) statusText.innerText = 'THREAD SALVA COMO SPACE // MOTOR 64D INDEXADO';
                    showToast('Conversa convertida em Space versionado com sucesso!', 'success');
                }, 750);

            } else if (type === 'hitl_danger') {
                vp.innerHTML += `<div class="sim-line prefix">[OPERADOR]&gt; @dot-coder limpar logs antigos em /var/log</div>`;
                vp.scrollTop = vp.scrollHeight;

                setTimeout(() => {
                    vp.innerHTML += `<div class="sim-line danger" style="background: rgba(239, 68, 68, 0.15); border-left: 3px solid var(--stamp-danger); padding: 8px;">[GENERATIVE UI CARD // HITL RETENCAO DE SEGURANCA]<br>Tool: execute_shell_command | Args originais: {"command": "rm -rf /var/log/*"}<br>Operador editou modified_args para: {"command": "rm -f /workspace/logs/*.tmp"} e homologou!</div>`;
                    vp.scrollTop = vp.scrollHeight;
                }, 400);

                setTimeout(() => {
                    vp.innerHTML += `<div class="sim-line success">[HITL RESOLVE // RETOMADA AUTOMATICA DO AGENTE]<br>POST /api/hitl/apr_01/resolve (modified_args aplicado) -> Agente retomou turno automaticamente com seguranca!</div>`;
                    vp.scrollTop = vp.scrollHeight;
                    if (statusText) statusText.innerText = 'HITL HOMOLOGADO COM MODIFIED_ARGS // RETOMADO';
                    showToast('HITL homologado com edicao de argumentos e retomada automatica!', 'success');
                }, 950);
            }
        }

        // Comando Customizado Digitado pelo Usuario no Prompt
        function handleCustomSimOrder() {
            const input = document.getElementById('heroSimInput');
            if (!input || !input.value.trim()) return;

            const text = input.value.trim();
            playHapticMechanicalClick();
            switchSimulatorTab('terminal');

            const vp = document.getElementById('heroSimViewport');
            if (!vp) return;

            const safeText = String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
            vp.innerHTML += `<div class="sim-line prefix">[OPERADOR]&gt; ${safeText}</div>`;
            input.value = '';
            vp.scrollTop = vp.scrollHeight;

            if (text.startsWith('/')) {
                const cmd = text.split(' ')[0].toLowerCase();
                const safeCmd = cmd.replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
                setTimeout(() => {
                    vp.innerHTML += `<div class="sim-line" style="font-family: var(--font-pixel); font-size: 8px; color: var(--blueprint-cyan); margin-top: 4px;">=== [RECIBO DE SLASH COMMAND // CATALOGO DE 34 COMANDOS] ===</div>`;
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
                        vp.innerHTML += `<div class="sim-line success">[RECIBO] Comando ${safeCmd} executado no cliente em sub-16ms | 0 tokens gastos | Sessao intacta.</div>`;
                        showToast(`Slash command ${safeCmd} executado localmente!`, 'info');
                    }
                    vp.scrollTop = vp.scrollHeight;
                }, 120);
                return;
            }

            setTimeout(() => {
                vp.innerHTML += `<div class="sim-line thought">[CADERNO DE RACIOCINIO // AG-UI]<br>Analisando intencao semantica... Roteando comando atraves da poda dinamica de ferramentas...</div>`;
                vp.scrollTop = vp.scrollHeight;
            }, 300);

            setTimeout(() => {
                vp.innerHTML += `<div class="sim-line tool">[TOOL CALL // LOCAL FIRST]<br>execute_bwrap_command("echo '[PROCESSO EM EXECUCAO NA BORDA]'")</div>`;
                vp.scrollTop = vp.scrollHeight;
            }, 700);

            setTimeout(() => {
                vp.innerHTML += `<div class="sim-line success">[RESPOSTA DO AGENTE]<br>Comando processado com sucesso pelo ecossistema soberano piDots em menos de 14ms.</div>`;
                vp.scrollTop = vp.scrollHeight;
            }, 1100);
        }

        // Simulacao da Arena: Conselho Tripartite
        function runCouncilDemoSimulation() {
            playHapticMechanicalClick();
            const feed = document.getElementById('councilDemoFeed');
            const status = document.getElementById('councilRoundStatus');
            if (!feed) return;

            if (status) status.innerText = 'STATUS: SESSAO EM ANDAMENTO (RODADA 1/3)';
            feed.innerHTML = `<div class="council-bubble coder"><strong>[@dot-coder // PROPOSTA]:</strong> Proponho unificar o historico de mensagens com visibilidade 'internal' para manter o feed do operador 100% limpo.</div>`;

            setTimeout(() => {
                if (status) status.innerText = 'STATUS: DEBATE CRITICO (RODADA 2/3)';
                feed.innerHTML += `<div class="council-bubble auditor"><strong>[@dot-auditor // AUDITORIA]:</strong> Ponto critico: mensagens internas devem ter chave estrangeira estrita no SQLite WAL para evitar orfaos.</div>`;
                feed.scrollTop = feed.scrollHeight;
            }, 600);

            setTimeout(() => {
                if (status) status.innerText = 'STATUS: CONCLUIDO (RODADA 3/3)';
                feed.innerHTML += `<div class="council-bubble supervisor"><strong>[@dot-supervisor // VEREDITO]:</strong> Aprovado com a restricao do auditor. Registrando resolucao na tabela agent_handoffs como COMPLETED.</div>`;
                feed.scrollTop = feed.scrollHeight;
                showToast('Conselho Consultivo: Deliberacao tripartite homologada!', 'success');
            }, 1200);
        }

        // Simulacao da Arena: Self-Healing
        function runHealingDemoSimulation() {
            playHapticMechanicalClick();
            const feed = document.getElementById('healingDemoFeed');
            const status = document.getElementById('healingStatus');
            if (!feed) return;

            if (status) status.innerText = 'HARNESS: INTERCEPTANDO FALHA';
            feed.innerHTML = `<div style="color: var(--stamp-danger);">[EXECUCAO FALHOU] File "pipeline.py", line 42: ZeroDivisionError: float division by zero</div>`;

            setTimeout(() => {
                feed.innerHTML += `<div style="color: var(--thermal-amber); margin: 4px 0;">[HARNESS] AST Parser isolou a falha: variavel 'taxa_amostragem' recebendo 0.</div>`;
                feed.scrollTop = feed.scrollHeight;
            }, 500);

            setTimeout(() => {
                feed.innerHTML += `<div style="color: var(--phosphor-green); font-weight: bold;">[AUTO-CURA] Correcao aplicada: adicionada guarda 'max(taxa, 1e-6)'. Reexecutando... SUCESSO (Exit: 0).</div>`;
                if (status) status.innerText = 'HARNESS: REPARADO COM EXITO';
                feed.scrollTop = feed.scrollHeight;
                showToast('Self-Healing: Script reparado automaticamente sem parada de servico!', 'success');
            }, 1100);
        }

        // Simulacao da Arena: Telemetria & Triggers
        function injectTelemetryPulse() {
            playHapticMechanicalClick();
            const ramPolyline = document.getElementById('arenaRamPolyline');
            const ramPolygon = document.getElementById('arenaRamPolygon');
            const ramDisplay = document.getElementById('arenaRamDisplay');

            if (ramDisplay) ramDisplay.innerText = '178.6 MB (59.5% // PULSO DE TESTE)';
            if (ramPolyline) ramPolyline.setAttribute('points', '0,60 40,60 40,35 90,35 90,38 140,38 140,25 190,25 190,30 240,30 240,40 290,40 290,42 310,42');
            if (ramPolygon) ramPolygon.setAttribute('points', '0,80 0,60 40,60 40,35 90,35 90,38 140,38 140,25 190,25 190,30 240,30 240,40 290,40 290,42 310,42 310,80');

            showToast('TELEMETRIA: Pulso de estresse injetado. RAM estabilizada abaixo de 200MB!', 'warning');

            setTimeout(() => {
                if (ramDisplay) ramDisplay.innerText = '118.4 MB (39.4% // RECUPERADO)';
                if (ramPolyline) ramPolyline.setAttribute('points', '0,60 40,60 40,55 90,55 90,62 140,62 140,50 190,50 190,52 240,52 240,46 290,46 290,44 310,44');
                if (ramPolygon) ramPolygon.setAttribute('points', '0,80 0,60 40,60 40,55 90,55 90,62 140,62 140,50 190,50 190,52 240,52 240,46 290,46 290,44 310,44 310,80');
            }, 3000);
        }

        function simulateThermalTriggerAlert() {
            playHapticMechanicalClick();
            const tempDisplay = document.getElementById('arenaTempDisplay');
            const tempPolyline = document.getElementById('arenaTempPolyline');
            const tempPolygon = document.getElementById('arenaTempPolygon');

            if (tempDisplay) tempDisplay.innerHTML = '<span style="color: var(--stamp-danger);">76.4 C (TRIGGER ATIVADO // MITIGACAO)</span>';
            if (tempPolyline) tempPolyline.setAttribute('stroke', '#ef4444');
            if (tempPolyline) tempPolyline.setAttribute('points', '0,52 50,52 50,30 110,30 110,22 170,22 170,18 230,18 230,15 290,15 290,14 310,14');
            if (tempPolygon) tempPolygon.setAttribute('points', '0,80 0,52 50,52 50,30 110,30 110,22 170,22 170,18 230,18 230,15 290,15 290,14 310,14 310,80');

            showToast('ALERTA TERMICO: Temperatura acima de 72 C! EdgeHardwareTriggers ativou desaceleracao de polling preventivo.', 'danger', 4500);

            setTimeout(() => {
                if (tempDisplay) tempDisplay.innerHTML = '<span>48.2 C (NOMINAL)</span>';
                if (tempPolyline) tempPolyline.setAttribute('stroke', '#33ff66');
                if (tempPolyline) tempPolyline.setAttribute('points', '0,52 50,52 50,50 110,50 110,54 170,54 170,49 230,49 230,48 290,48 290,47 310,47');
                if (tempPolygon) tempPolygon.setAttribute('points', '0,80 0,52 50,52 50,50 110,50 110,54 170,54 170,49 230,49 230,48 290,48 290,47 310,47 310,80');
            }, 3500);
        }

        // Copiar Snippet com Feedback Tatil
        function copySnippet(text) {
            playHapticMechanicalClick();
            navigator.clipboard.writeText(text).then(() => {
                showToast('Comando copiado para a area de transferencia!', 'success');
            }).catch(() => {
                showToast(`Comando: ${text}`, 'info');
            });
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

        // Tecla ESC fecha Drawer
        window.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const drawer = document.getElementById('retractableDrawer');
                if (drawer && drawer.classList.contains('open')) {
                    toggleDrawer();
                }
            }
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
                actionsContainer.innerHTML = '<span class="silicon-badge badge-green" style="font-size: 9px; padding: 4px 8px;">[HOMOLOGADO // EXECUCAO LIBERADA VIA HMAC-SHA256]</span>';
                showToast('Aprovacao HITL concedida para bwrap. Retomando agente autonomo.', 'success');
            } else if (action === 'reject') {
                hitlBox.style.borderColor = 'var(--stamp-danger)';
                actionsContainer.innerHTML = '<span class="silicon-badge badge-red" style="font-size: 9px; padding: 4px 8px;">[VETADO // EXECUCAO RECUSADA POR GOVERNANCA]</span>';
                showToast('Comando de sandbox vetado por governanca Deny-by-Default.', 'warning');
            } else if (action === 'inspect') {
                const arena = document.getElementById('arena-hitl');
                if (arena) {
                    arena.scrollIntoView({ behavior: 'smooth' });
                }
                showToast('Abrindo analise forense e arena interativa de seguranca.', 'info');
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
