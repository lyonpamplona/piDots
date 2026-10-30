# Diretrizes de Contribuição (CONTRIBUTING)

O **piDots** é uma plataforma de AI Coworkers persistentes projetada para rodar em hardware com recursos restritos, tendo o Raspberry Pi 4B ARM64 como bancada de referência.

Siga estas diretrizes para manter a estabilidade do sistema, o isolamento de segurança e a disciplina de recursos.

---

## 1. Princípios de Engenharia do Projeto

Ao propor alterações no piDots, mantenha em mente os seguintes requisitos:

1. **Eficiência de Memória:**
   - O consumo de RAM em repouso (idle) deve permanecer abaixo de **60 MB**.
   - O consumo sob carga com agentes ativos não ultrapassa **150 MB**.
   - Não introduza bibliotecas pesadas de aprendizado profundo (PyTorch, TensorFlow, Transformers locais) ou navegadores headless (Puppeteer, Playwright, Chromium) no runtime principal.

2. **Preservação de Hardware e I/O de Disco:**
   - Evite chamadas excessivas ou síncronas de gravação em disco (`fsync`).
   - Todas as operações de persistência utilizam a camada gerenciada de SQLite em modo WAL (`journal_mode=WAL`, `synchronous=NORMAL`).

3. **Assincronismo Estrito:**
   - Todo código deve ser compatível com AsyncIO e uvloop.
   - Nunca execute chamadas bloqueantes de I/O de rede ou disco diretamente na thread principal do event loop. Use `asyncio.to_thread` ou APIs nativamente assíncronas (`httpx`, `aiofiles`).

4. **Regra de Estilo: Zero Emojis:**
   - É proibido o uso de emojis no código-fonte, nomes de variáveis, logs, documentação técnica, mensagens de commit e interfaces.

5. **Padrão Visual: Design System Pixel Paper UI:**
   - Toda alteração em interfaces web (HTML/CSS) deve obedecer estritamente ao **Pixel Paper UI** (Dark Paper Noir).
   - É proibido introduzir frameworks de estilização pesados (Tailwind, Bootstrap) ou bibliotecas de componentes externas.
   - Rigor geométrico ortogonal absoluto (`border-radius: 0px`).
   - Sombras puramente cartesianas sem desfoque gaussiano (`box-shadow: 2px 2px 0px #000000;`, etc.).
   - Dupla tipografia técnica: `Silkscreen` para displays, títulos e carimbos; `JetBrains Mono` (com `font-variant-numeric: tabular-nums`) para dados, telemetria e teletipo.
   - Todos os ícones vetoriais SVG devem conter a diretiva `shape-rendering="crispEdges"`.

---

## 2. Padrão de Commits Semânticos (Conventional Commits)

Adotamos a convenção de [Conventional Commits](https://www.conventionalcommits.org/) para manter o histórico de versões legível e auditável. As mensagens de commit seguem o formato:

```
<tipo>(<escopo>): <descrição em texto claro e direto>
```

### Tipos Permitidos:
- `feat`: Adição de nova funcionalidade ou ferramenta.
- `fix`: Correção de defeito ou falha de execução.
- `docs`: Alterações em documentação, manuais ou diagramas.
- `perf`: Melhorias de desempenho ou redução de consumo de memória RAM/CPU.
- `refactor`: Refatoração de código sem alteração de comportamento externo.
- `test`: Criação ou atualização de suítes de testes automatizados.
- `chore`: Atualização de dependências, empacotamento ou tarefas de manutenção.
- `ci`: Alterações nos workflows de integração contínua.

### Exemplos:
- `feat(tools): adicionar timeout configuravel para o extrator web`
- `fix(storage): ajustar busy_timeout na inicializacao do sqlite wal`
- `perf(memory): otimizar representacao vetorial crc32 para reduzir alocacao de bytes`
- `docs(readme): atualizar tabela de endpoints da api rest`

---

## 3. Fluxo de Trabalho e Submissão de Pull Requests

1. **Fork do Repositório:**
   Crie um fork do repositório oficial na sua conta do GitHub.

2. **Criação de Branch Temática:**
   Crie uma branch descritiva a partir da branch principal (`main`):
   ```bash
   git checkout -b feat/nova-ferramenta-telemetria
   ```

3. **Ambiente de Desenvolvimento Local:**
   Configure o ambiente virtual e instale as dependências do projeto em modo editável:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

4. **Validação e Testes:**
   Antes de submeter o Pull Request, execute toda a suíte de testes de regressão, testes de homologação do Pixel Paper UI e o teste de estresse de concorrência:
   ```bash
   python3 scripts/test_pixel_paper_phase4_global_homologation.py
   python3 scripts/test_phase20_port_decoupling_nginx.py
   python3 scripts/test_phase1.py
   python3 scripts/test_phase2.py
   python3 scripts/test_phase3.py
   python3 scripts/test_phase4.py
   python3 scripts/test_phase5.py
   python3 scripts/stress_test.py
   ```
   Todos os testes precisam passar integralmente antes da submissão.

5. **Abertura do Pull Request:**
   - Preencha o template padrão de PR detalhando as motivações técnicas da alteração.
   - Forneça evidências de que a alteração não elevou o consumo de memória RAM nem inseriu vulnerabilidades de execução de comandos.
   - Certifique-se de que a regra de zero emojis foi rigorosamente respeitada.

---

## 4. Governança e Revisão de Código

Todos os Pull Requests passam por revisão técnica pelo mantenedor do projeto (**lyon christopher**). Aprovações exigem:
- Aprovação no pipeline de CI/CD.
- Cobertura de testes automatizados para novas capacidades.
- Conformidade estrita com o padrão assíncrono e o sandbox de segurança.
