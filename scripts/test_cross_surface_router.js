/**
 * Teste Unitario e de Integracao em Node.js para cross-surface-router.js
 * Valida a logica de resolucao de superficies em todos os modos:
 * - decoupled-ports (:8081, :8082, :8083)
 * - subdomains (app.dominio.com, docs.dominio.com, pidots.dominio.com)
 * - path-based (:8088, :8000, proxies genericos)
 */

const fs = require('fs');
const vm = require('vm');
const path = require('path');
const assert = require('assert');

const scriptPath = path.resolve(__dirname, '../static/js/core/cross-surface-router.js');
const scriptCode = fs.readFileSync(scriptPath, 'utf8');

function createMockEnv(locationConfig) {
    const mockDocument = {
        readyState: 'complete',
        getElementById: (id) => null,
        querySelector: (sel) => null,
        querySelectorAll: (sel) => [],
        addEventListener: (event, cb) => {}
    };

    const mockWindow = {
        location: {
            port: locationConfig.port || '',
            hostname: locationConfig.hostname || 'localhost',
            protocol: locationConfig.protocol || 'http:',
            pathname: locationConfig.pathname || '/'
        },
        document: mockDocument,
        addEventListener: (event, cb) => {},
        Date: Date
    };

    const context = vm.createContext({
        window: mockWindow,
        document: mockDocument,
        Date: Date,
        console: console
    });

    vm.runInContext(scriptCode, context);
    return context.window.CrossSurfaceRouter;
}

console.log('========================================================================');
console.log('VALIDACAO EM RUNTIME JS: CROSS-SURFACE-ROUTER.JS');
console.log('========================================================================');

// Teste 1: Modo Portas Desacopladas no Localhost (:8081 - Landing Page)
console.log('[TESTE 1/4] Validando modo portas desacopladas a partir de :8081 (Landing)...');
const router8081 = createMockEnv({ port: '8081', hostname: 'localhost', pathname: '/' });
const topo8081 = router8081.detectTopology();
assert.strictEqual(topo8081.mode, 'decoupled-ports', 'Modo deve ser decoupled-ports');
assert.strictEqual(router8081.resolveSurfaceUrl('overview'), 'http://localhost:8081/');
assert.strictEqual(router8081.resolveSurfaceUrl('workspace'), 'http://localhost:8082/');
assert.strictEqual(router8081.resolveSurfaceUrl('docs'), 'http://localhost:8083/');
assert.strictEqual(router8081.resolveSurfaceUrl('report'), 'http://localhost:8083/relatorio');
console.log('  -> [OK] Modo :8081 resolveu perfeitamente :8082 para Workspace e :8083 para Docs.');

// Teste 2: Modo Portas Desacopladas em IP da LAN (:8082 - Workspace App)
console.log('[TESTE 2/4] Validando modo portas desacopladas em IP de LAN :8082 (Workspace)...');
const routerLan = createMockEnv({ port: '8082', hostname: '192.168.1.100', pathname: '/' });
assert.strictEqual(routerLan.resolveSurfaceUrl('overview'), 'http://192.168.1.100:8081/');
assert.strictEqual(routerLan.resolveSurfaceUrl('workspace'), 'http://192.168.1.100:8082/');
assert.strictEqual(routerLan.resolveSurfaceUrl('docs'), 'http://192.168.1.100:8083/');
console.log('  -> [OK] Modo LAN :8082 preservou o IP 192.168.1.100 nas rotas cruzadas.');

// Teste 3: Modo Cloudflare Tunnel Subdominios (app.meupisite.com)
console.log('[TESTE 3/4] Validando modo subdominios Cloudflare (app.meupisite.com)...');
const routerSub = createMockEnv({ port: '', hostname: 'app.meupisite.com', protocol: 'https:', pathname: '/' });
const topoSub = routerSub.detectTopology();
assert.strictEqual(topoSub.mode, 'subdomains', 'Modo deve ser subdomains');
assert.strictEqual(routerSub.resolveSurfaceUrl('overview'), 'https://pidots.meupisite.com/');
assert.strictEqual(routerSub.resolveSurfaceUrl('workspace'), 'https://app.meupisite.com/');
assert.strictEqual(routerSub.resolveSurfaceUrl('docs'), 'https://docs.meupisite.com/');
assert.strictEqual(routerSub.resolveSurfaceUrl('report'), 'https://docs.meupisite.com/relatorio');
console.log('  -> [OK] Modo Cloudflare subdominios resolveu perfeitamente pidots.*, app.* e docs.*.');

// Teste 4: Modo Gateway Unificado Path-Based (:8088 / :8000)
console.log('[TESTE 4/4] Validando modo Gateway Unificado Path-Based (:8088)...');
const routerPath = createMockEnv({ port: '8088', hostname: 'localhost', pathname: '/' });
const topoPath = routerPath.detectTopology();
assert.strictEqual(topoPath.mode, 'path-based', 'Modo deve ser path-based');
assert.strictEqual(routerPath.resolveSurfaceUrl('overview'), '/');
assert.strictEqual(routerPath.resolveSurfaceUrl('workspace'), '/app');
assert.strictEqual(routerPath.resolveSurfaceUrl('docs'), '/docs');
assert.strictEqual(routerPath.resolveSurfaceUrl('report'), '/relatorio');
console.log('  -> [OK] Modo Path-based manteve rotas relativas limpas sem quebrar rotas legadas.');

console.log('========================================================================');
console.log('RESULTADO FINAL: 100% DAS ASSERCOES DO ROTEADOR APROVADAS NO NODE.JS.');
console.log('========================================================================');
