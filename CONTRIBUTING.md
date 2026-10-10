# Diretrizes de Contribuicao (CONTRIBUTING)

Agradecemos o seu interesse em contribuir com o **piDots**. Este projeto e voltado para a criacao de AI Coworkers persistentes, eficientes e estaveis em ambientes de borda com recursos restritos (como o Raspberry Pi 4B ARM64).

Para manter a integridade arquitetural, a seguranca e a eficiencia computacional, solicitamos que leia e siga as diretrizes abaixo.

---

## 1. Principios de Engenharia do Projeto

Ao propor alteracoes no piDots, mantenha em mente os seguintes principios fundamentais:

1. **Eficiencia Extrema de Memoria:**
   - O consumo de RAM em repouso (idle) deve permanecer rigorosamente abaixo de **60 MB**.
   - O consumo maximo sob carga com agentes ativos nao deve ultrapassar **150 MB**.
   - Nunca introduza bibliotecas pesadas de aprendizado profundo (PyTorch, TensorFlow, Transformers locais) ou navegadores headless (Puppeteer, Playwright, Chromium) no runtime principal.

2. **Preservacao de Hardware e I/O de Disco:**
   - Evite chamadas excessivas ou sincronas de gravacao em disco (`fsync`).
   - Todas as operacoes de persistencia devem utilizar a camada gerenciada de SQLite em modo WAL (`journal_mode=WAL`, `synchronous=NORMAL`).

3. **Assincronismo Estrito:**
   - Todo codigo deve ser compativel com AsyncIO e uvloop.
   - Nunca execute chamadas bloqueantes de I/O de rede ou disco diretamente na thread principal do event loop. Use `asyncio.to_thread` ou APIs nativamente assincronas (`httpx`, `aiofiles`).

4. **Regra de Estilo e Padronizacao: Zero Emojis:**
   - E expressamente proibido o uso de emojis no codigo-fonte, nomes de variaveis, logs, documentacao tecnica, mensagens de commit e interfaces.

---

## 2. Padrao de Commits Semanticos (Conventional Commits)

Adotamos a convencao de [Conventional Commits](https://www.conventionalcommits.org/) para manter o historico de versoes legivel e auditavel. As mensagens de commit devem seguir o formato:

```
<tipo>(<escopo>): <descricao em texto claro e direto>
```

### Tipos Permitidos:
- `feat`: Adicao de nova funcionalidade ou ferramenta.
- `fix`: Correcao de defeito ou falha de execucao.
- `docs`: Alteracoes em documentacao, manuais ou diagramas.
- `perf`: Melhorias de desempenho ou reducao de consumo de memoria RAM/CPU.
- `refactor`: Refatoracao de codigo sem alteracao de comportamento externo.
- `test`: Criacao ou atualizacao de suites de testes automatizados.
- `chore`: Atualizacao de dependencias, empacotamento ou tarefas de manutencao.
- `ci`: Alteracoes nos workflows de integracao continua.

### Exemplos:
- `feat(tools): adicionar timeout configuravel para o extrator web`
- `fix(storage): ajustar busy_timeout na inicializacao do sqlite wal`
- `perf(memory): otimizar representacao vetorial crc32 para reduzir alocacao de bytes`
- `docs(readme): atualizar tabela de endpoints da api rest`

---

## 3. Fluxo de Trabalho e Submissao de Pull Requests

1. **Fork do Repositorio:**
   Crie um fork do repositorio oficial para a sua conta no GitHub.

2. **Criacao de Branch Tematica:**
   Crie uma branch descritiva a partir da branch principal (`main`):
   ```bash
   git checkout -b feat/nova-ferramenta-telemetria
   ```

3. **Ambiente de Desenvolvimento Local:**
   Instale o ambiente virtual e as dependencias do projeto em modo editavel:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

4. **Validacao e Testes:**
   Antes de submeter o Pull Request, execute obrigatoriamente toda a suite de testes de regressao e o teste de estresse de concorrencia:
   ```bash
   python3 scripts/test_phase1.py
   python3 scripts/test_phase2.py
   python3 scripts/test_phase3.py
   python3 scripts/test_phase4.py
   python3 scripts/test_phase5.py
   python3 scripts/stress_test.py
   ```
   Todos os testes devem passar com 100% de sucesso.

5. **Abertura do Pull Request:**
   - Preencha o template padrao de PR detalhando as motivacoes da alteracao.
   - Forneca evidencias de que a alteracao nao elevou a pegada de memoria RAM nem inseriu vulnerabilidades de execucao de comandos.
   - Certifique-se de que a regra de zero emojis foi estritamente respeitada.

---

## 4. Governanca e Revisao de Codigo

Todos os Pull Requests passam por revisao tecnica pelo mantenedor do projeto (**lyon christopher**). Aprovacoes exigem:
- Aprovacao no pipeline de CI/CD.
- Cobertura de testes automatizados para novas capacidades.
- Conformidade estrita com o padrao assincrono e o sandbox de seguranca.
