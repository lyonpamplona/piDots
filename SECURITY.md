# Politica de Seguranca (SECURITY)

A seguranca da infraestrutura e o controle deterministico sobre a execucao de ferramentas sao prioridades absolutas no ecossistema **piDots**. Como a plataforma opera agentes autonomos com capacidade de execucao de comandos em sistemas de borda persistentes, adotamos medidas rigorosas de isolamento em camadas.

---

## 1. Versoes com Suporte Ativo

Correcoes de seguranca sao aplicadas exclusivamente nas seguintes versoes:

| Versao | Status de Suporte |
| :--- | :--- |
| `0.1.x` | Suportada ativamente com correcoes prioritarias |
| `< 0.1.0` | Descontinuada / Nao suportada |

---

## 2. Modelo de Ameacas e Fronteiras de Seguranca

O piDots implementa o principio de defesa em profundidade estruturado em tres barreiras independentes:

### 1. Isolamento via Sandbox Bubblewrap (`bwrap`)
- Comandos de terminal despachados pelos agentes sao executados dentro de namespaces isolados do kernel Linux (`CLONE_NEWNS`, `CLONE_NEWPID`, `CLONE_NEWIPC`, `CLONE_NEWUTS`).
- O sistema operacional hospedeiro e montado com permissao estrita de somente leitura (`ro-bind`).
- Apenas o subdiretorio atribuido ao workspace especifico do agente (`workspaces/<dot_id>`) possui permissao de escrita.
- O parametro `--die-with-parent` impede a persistencia de processos orfaos ou daemons nao autorizados em segundo plano.

### 2. Governanca Human-in-the-Loop (HITL)
- O motor de avaliacao de risco analisa sintaticamente todas as chamadas de ferramentas.
- Comandos que envolvam remocao recursiva (`rm -rf`), elevacao de privilegios (`sudo`, `su`), alteracao de permissoes (`chmod`, `chown`), operacoes de rede de baixo nivel ou reinicializacao do sistema sao retidos imediatamente em fila de governanca.
- Nenhuma acao de risco critico e executada sem a confirmacao explicita do operador humano autenticado via interface web ou CLI.

### 3. Protecao de Segredos e Variaveis de Ambiente
- Chaves de API de provedores de inferencia sao injetadas exclusivamente via variaveis de ambiente ou arquivo `.env`.
- Arquivos `.env`, bancos de dados SQLite com dados transacionais e workspaces de usuarios sao rigorosamente bloqueados no `.gitignore` e no `.dockerignore`, impedindo commit acidental em repositorios publicos.

---

## 3. Reporte Responsavel de Vulnerabilidades

Caso voce identifique uma vulnerabilidade de seguranca no piDots, solicitamos que **nao abra uma issue publica**. Siga o protocolo de divulgacao responsavel:

1. **Canal de Comunicacao:**
   Envie um relatorio confidencial detalhado para o mantenedor do projeto (**lyon christopher**) ou abra um **Security Advisory** privado diretamente na aba de seguranca do repositorio no GitHub.

2. **Informacoes Necessarias no Relatorio:**
   - Descricao clara da vulnerabilidade e seu potencial de impacto.
   - Prova de conceito (PoC) com passos reproduziveis.
   - Versao do piDots, versao do Python e distribuicao Linux utilizada.
   - Indicacao se a vulnerabilidade permite escape de sandbox, evasao da governanca HITL ou exposicao de credenciais.

3. **Prazo de Resposta:**
   - Confirmacao inicial de recebimento: ate **48 horas**.
   - Analise de causa raiz e plano de mitigacao: ate **5 dias uteis**.
   - Publicacao de patch de correcao: coordenado em conjunto com o pesquisador antes de qualquer divulgacao publica.
