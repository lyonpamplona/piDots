# Política de Segurança (SECURITY)

A segurança da infraestrutura e o controle determinístico sobre a execução de ferramentas são requisitos centrais no **piDots**. Como a plataforma opera agentes autônomos com capacidade de execução de comandos em sistemas de borda persistentes, adotamos medidas rigorosas de isolamento em camadas.

---

## 1. Versões com Suporte Ativo

Correções de segurança aplicam-se exclusivamente às seguintes versões:

| Versão | Status de Suporte |
| :--- | :--- |
| `1.5.x` | Suporte ativo com correções prioritárias de borda |
| `< 1.5.0` | Descontinuada / Sem suporte |

---

## 2. Modelo de Ameaças e Fronteiras de Segurança

O piDots implementa o princípio de defesa em profundidade estruturado em nove barreiras:

### 1. Isolamento via Sandbox Bubblewrap (`bwrap`)
- Comandos de terminal disparados pelos agentes rodam dentro de namespaces isolados do kernel Linux (`CLONE_NEWNS`, `CLONE_NEWPID`, `CLONE_NEWIPC`, `CLONE_NEWUTS`).
- O sistema operacional hospedeiro é montado em modo somente leitura (`ro-bind`).
- Apenas o subdiretório atribuído ao workspace específico do agente (`workspaces/<dot_id>`) tem permissão de escrita.
- O parâmetro `--die-with-parent` encerra processos órfãos ou daemons não autorizados em segundo plano se o processo pai finalizar.

### 2. Governança Human-in-the-Loop (HITL)
- O motor de avaliação de risco analisa sintaticamente todas as chamadas de ferramentas.
- Comandos que envolvam remoção recursiva (`rm -rf`), elevação de privilégios (`sudo`, `su`), alteração de permissões (`chmod`, `chown`), operações de rede de baixo nível ou reinicialização do sistema entram imediatamente na fila de governança.
- O sistema não executa nenhuma ação de risco crítico sem a confirmação explícita do operador humano autenticado via interface web, CLI ou canal assinado.

### 3. Proteção Rigorosa Anti-SSRF (Server-Side Request Forgery)
- A ferramenta `read_web_page` valida os endereços IP resolvidos por DNS contra faixas de rede privada (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), loopback (`127.0.0.0/8`), link-local (`169.254.0.0/16`) e multicast.
- Redirecionamentos HTTP (301, 302, 303, 307, 308) são inspecionados salto a salto (hop-by-hop), o que bloqueia a evasão por redirecionamentos externos abertos.

### 4. Proteção Anti-Path-Traversal e Symlink Traversal
- Todas as operações de arquivo em `file_ops.py` e rotinas de empacotamento em `spaces_manager.py` aplicam verificação com `os.path.realpath` e `os.path.commonpath`.
- O sistema bloqueia qualquer tentativa de acesso fora da árvore autorizada do workspace ou a inclusão de symlinks que apontem para arquivos sensíveis do hospedeiro.

### 5. Proteção de Segredos e Variáveis de Ambiente
- Chaves de API de provedores de inferência são injetadas exclusivamente via variáveis de ambiente ou arquivo `.env`.
- Arquivos `.env`, bancos de dados SQLite com dados transacionais e workspaces de usuários são bloqueados no `.gitignore` e no `.dockerignore`, o que previne commits acidentais em repositórios públicos.

### 6. Integridade de Assets Estáticos Desacoplados e Cache ETag
- Todos os arquivos estáticos desacoplados (`pages/*.html`, `static/css/*.css`, `static/js/**/*.js`) são servidos com cabeçalhos de defesa `X-Content-Type-Options: nosniff` e validados via ETag SHA-256 no `EdgeAssetManager` em memória RAM, o que neutraliza adulterações de scripts client-side e contaminação de cache por intermediários.

### 7. Governança HITL Remota Assinada com HMAC-SHA256
- Autorizações remotas via Telegram ou WhatsApp utilizam tokens unívocos assinados com HMAC-SHA256, validados em tempo constante (`hmac.compare_digest`) no endpoint `/api/hitl/signed-resolve`.
- As requisições retidas possuem janela de validade temporal (TTL de 30 minutos em `expires_at`). Transcorrido o prazo, o status muda automaticamente para `EXPIRED`, o que descarta a ação e registra o evento no log de auditoria.

### 8. Integridade de Dot Packs v1.1 e Defesa contra Prompt Injection
- Manifestos exportados recebem hash criptográfico `sha256_checksum` gerado a partir do conteúdo canônico normalizado.
- Na importação (`POST /api/dots/import-pack`), a integridade do pacote é verificada antes da persistência e os blocos de `core_memory` são auditados contra padrões de subversão de instrução de sistema (Prompt Injection).

### 9. Isolamento Estrito de Terminal (STRICT_SANDBOX)
- Sob a diretiva `STRICT_SANDBOX=true`, o executor de terminal recusa comandos caso o binário `bwrap` não esteja disponível no ambiente. O sistema retorna o código de saída 126 com erro de governança e não permite fallbacks em processos desprotegidos.

---

## 3. Relato Responsável de Vulnerabilidades

Caso você identifique uma vulnerabilidade de segurança no piDots, **não abra uma issue pública**. Siga o protocolo de divulgação responsável:

1. **Canal de Comunicação:**
   Envie um relatório confidencial detalhado para o mantenedor do projeto (**lyon christopher**) ou abra um **Security Advisory** privado diretamente na aba de segurança do repositório no GitHub.

2. **Informações Necessárias no Relatório:**
   - Descrição clara da vulnerabilidade e seu potencial de impacto.
   - Prova de conceito (PoC) com passos reproduzíveis.
   - Versão do piDots, versão do Python e distribuição Linux utilizada.
   - Indicação se a vulnerabilidade permite escape de sandbox, evasão da governança HITL ou exposição de credenciais.

3. **Prazo de Resposta:**
   - Confirmação inicial de recebimento: até **48 horas**.
   - Análise de causa raiz e plano de mitigação: até **5 dias úteis**.
   - Publicação de patch de correção: coordenado em conjunto com o pesquisador antes de qualquer divulgação pública.
