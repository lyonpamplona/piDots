/**
 * Script de Homologação da Fase 3:
 * Card Interativo de Diagnóstico do Provedor de IA (Eliminação do Falso Positivo).
 */

const fs = require('fs');
const path = require('path');
const vm = require('vm');

console.log("=== [piDots] Teste e Validação da Fase 3: Card de Diagnóstico do Provedor ===");

// 1. Simula ambiente de janela DOM para carregar pidots-api.js
const mockWindow = {
    escapeHtml: function(s) {
        return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    },
    getNextSeqCounter: () => 1,
    document: {
        getElementById: () => null,
        querySelectorAll: () => []
    },
    PixelSystem: { toast: () => {} }
};
mockWindow.window = mockWindow;

const apiCode = fs.readFileSync(path.join(__dirname, '../static/js/spa/pidots-api.js'), 'utf-8');
const context = vm.createContext(mockWindow);
vm.runInContext(apiCode, context);

const PiDotsAPI = context.PiDotsAPI;
if (!PiDotsAPI) {
    console.error("Falha fatal: PiDotsAPI não instanciado no contexto global.");
    process.exit(1);
}

// 2. Teste do Card de Diagnóstico
console.log("[1/3] Validando renderização do Card de Diagnóstico Pixel Paper...");
const sampleError = "Provedor primário retornou HTTP 503: Service Temporarily Unavailable";
const samplePrompt = "Olá @dot-supervisor, execute a validação técnica";
const cardHtml = PiDotsAPI.renderProviderErrorCard(sampleError, samplePrompt);

if (!cardHtml.includes("pixel-error-diagnostic-card")) {
    console.error("Falha: Classe pixel-error-diagnostic-card não encontrada no HTML gerado.");
    process.exit(1);
}
if (!cardHtml.includes("[DIAGNÓSTICO: FALHA DE INFERÊNCIA]")) {
    console.error("Falha: Tag de cabeçalho do diagnóstico ausente.");
    process.exit(1);
}
if (!cardHtml.includes("HTTP 503")) {
    console.error("Falha: Causa raiz do erro (HTTP 503) não foi incluída no card.");
    process.exit(1);
}
if (!cardHtml.includes("Tentar Novamente")) {
    console.error("Falha: Botão Tentar Novamente ausente.");
    process.exit(1);
}
if (!cardHtml.includes("Configurar Provedor")) {
    console.error("Falha: Botão Configurar Provedor ausente.");
    process.exit(1);
}
if (!cardHtml.includes("Testar Conexão")) {
    console.error("Falha: Botão Testar Conexão ausente.");
    process.exit(1);
}
console.log("      Sucesso: Card de diagnóstico renderizado com todos os botões e texto técnico.");

// 3. Verificação de Ausência de Falsos Positivos no Código
console.log("[2/3] Verificando eliminação de mensagens ilusórias ('Operacao concluida com sucesso')...");
if (apiCode.includes("Operacao concluida com sucesso.")) {
    console.error("Falha: String 'Operacao concluida com sucesso.' ainda encontrada no pidots-api.js.");
    process.exit(1);
}
console.log("      Sucesso: Nenhuma mensagem ilusória presente em pidots-api.js.");

// 4. Verificação de Funções Globais de Suporte
console.log("[3/3] Validando funções globais window.openAIConfigDrawer e window.retryLastPrompt...");
if (typeof context.openAIConfigDrawer !== 'function') {
    console.error("Falha: window.openAIConfigDrawer não é uma função.");
    process.exit(1);
}
if (typeof context.retryLastPrompt !== 'function') {
    console.error("Falha: window.retryLastPrompt não é uma função.");
    process.exit(1);
}
console.log("      Sucesso: Funções globais de retry e abertura de configurações prontas para acionamento.");

console.log("\n=== [SUCESSO] Fase 3 validada com 100% de êxito! Diagnósticos Reais Ativos! ===");
