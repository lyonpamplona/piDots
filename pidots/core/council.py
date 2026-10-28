"""
Módulo de Conselho Consultivo e Debate Multi-Agente (Dialética Multi-Bot) para piDots.
Implementa deliberação estruturada entre Propositor (ex: @coder), Auditor Crítico (ex: @auditor)
e Supervisor Geral (ex: @supervisor) calibrada para baixo consumo de memória no Raspberry Pi 4B (ARM64).
"""

import uuid
import logging
from typing import Any

from ..storage.db import get_db
from ..providers.openai_client import OpenAIUniversalProvider

logger = logging.getLogger("pidots.council")

MAX_COUNCIL_ROUNDS = 3


class CouncilOrchestrator:
    """Orquestrador de alinhamento técnico e consenso entre múltiplos Dots."""

    @classmethod
    async def _execute_turn(
        cls,
        agent: Any,
        subthread_id: str,
        prompt: str
    ) -> tuple[str, bool, str]:
        """
        Executa um turno de deliberação inspecionando eventos do agente.
        Retorna (conteudo, sucesso, mensagem_de_erro).
        """
        status = "completed"
        error_msg = ""
        async for event in agent.run_thread(thread_id=subthread_id, user_message=prompt):
            if event["event"] == "run:finished":
                ev_data = event.get("data", {})
                status = ev_data.get("status", "completed")
                error_msg = ev_data.get("error", "")

        if status in ("failed", "awaiting_hitl"):
            err = error_msg or ("Ação retida por governança HITL aguardando autorização do operador humano" if status == "awaiting_hitl" else "Falha no ciclo do agente")
            return "", False, err

        async with get_db() as db:
            cursor = await db.execute(
                """
                SELECT content FROM messages
                WHERE thread_id = ? AND role = 'assistant' AND visibility != 'internal'
                ORDER BY created_at DESC, rowid DESC LIMIT 1
                """,
                (subthread_id,)
            )
            row = await cursor.fetchone()
            content = row["content"] if row else ""

        if not content:
            # Fallback se não houver mensagem pública explícita
            async with get_db() as db:
                cursor = await db.execute(
                    "SELECT content FROM messages WHERE thread_id = ? AND role = 'assistant' ORDER BY created_at DESC, rowid DESC LIMIT 1",
                    (subthread_id,)
                )
                row = await cursor.fetchone()
                content = row["content"] if row else "Deliberação concluída sem saída textual."

        return content, True, ""

    @classmethod
    def _is_auditor_approved(cls, text: str) -> bool:
        """
        Detecta se a manifestação do auditor atingiu consenso favorável de baixo risco.
        Identifica marcadores explícitos como 'RISK_LOW', 'APPROVED', 'APROVADO'
        e a ausência de termos de veto ou risco crítico/alto impeditivo.
        """
        if not text:
            return False
        clean = text.upper()
        has_approved_signal = any(
            marker in clean
            for marker in (
                "RISK_LOW",
                "APPROVED",
                "APROVADO",
                "APROVADA",
                "RISCO BAIXO",
                "BAIXO RISCO",
                "CONSENSO ATINGIDO",
                "APROVO SEM RESSALVAS",
                "SEM RESSALVAS"
            )
        )
        has_blocking_signal = any(
            blocker in clean
            for blocker in (
                "RISK_HIGH",
                "RISK_CRITICAL",
                "REJECTED",
                "REPROVADO",
                "REJEITADO",
                "CORREÇÕES OBRIGATÓRIAS",
                "CORRECOES OBRIGATORIAS",
                "VETO",
                "VULNERABILIDADE CRÍTICA"
            )
        )
        return has_approved_signal and not has_blocking_signal

    @classmethod
    async def run_debate(
        cls,
        thread_id: str,
        topic: str,
        proponent_dot_id: str = "dot-coder",
        critic_dot_id: str = "dot-auditor",
        supervisor_dot_id: str = "dot-supervisor",
        rounds: int = 1,
        provider: OpenAIUniversalProvider | None = None
    ) -> dict[str, Any]:
        """
        Executa uma rodada formal de debate entre Propositor, Auditor e Supervisor.
        Gera parecer executivo consolidado com consenso técnico persistido no SQLite WAL.
        """
        if not topic.strip():
            return {"success": False, "error": "O tópico do debate não pode ser vazio."}

        # Valida limites de rodadas para preservação de CPU/RAM no Pi 4B
        total_rounds = max(1, min(rounds, MAX_COUNCIL_ROUNDS))

        # Provedor padrão se não fornecido
        ai_provider = provider or OpenAIUniversalProvider()

        # Validação e resolução de Dots ativos no SQLite WAL
        resolved_proponent, resolved_critic, resolved_supervisor = await cls._resolve_participants(
            proponent_dot_id, critic_dot_id, supervisor_dot_id
        )

        handoff_id = str(uuid.uuid4())
        logger.info(
            "Iniciando Conselho Consultivo (ID: %s) sobre '%s'. Propositor: @%s, Crítico: @%s, Supervisor: @%s.",
            handoff_id, topic[:40], resolved_proponent, resolved_critic, resolved_supervisor
        )

        # 1. Garante que a thread pai exista para cumprir integridade relacional de Foreign Key
        async with get_db() as db:
            await db.execute(
                """
                INSERT OR IGNORE INTO threads (id, dot_id, title, status)
                VALUES (?, ?, ?, 'idle')
                """,
                (thread_id, resolved_supervisor, f"Thread {thread_id[:16]}")
            )
            # Registra o início do conselho na tabela agent_handoffs
            await db.execute(
                """
                INSERT INTO agent_handoffs (
                    id, thread_id, source_dot_id, target_dot_id, task_goal,
                    handoff_type, status
                ) VALUES (?, ?, ?, ?, ?, 'council_debate', 'RUNNING')
                """,
                (handoff_id, thread_id, resolved_supervisor, resolved_proponent, f"Conselho: {topic[:100]}")
            )
            await db.commit()

        # Registra os participantes na thread
        from .orchestrator import MultiBotOrchestrator
        await MultiBotOrchestrator.record_participant(thread_id, resolved_proponent)
        await MultiBotOrchestrator.record_participant(thread_id, resolved_critic)
        await MultiBotOrchestrator.record_participant(thread_id, resolved_supervisor)

        from .agent import DotAgent

        proponent_agent = DotAgent(dot_id=resolved_proponent, provider=ai_provider)
        critic_agent = DotAgent(dot_id=resolved_critic, provider=ai_provider)
        supervisor_agent = DotAgent(dot_id=resolved_supervisor, provider=ai_provider)

        # ======================================================================
        # ETAPA 1: O Propositor elabora a solução/proposta inicial
        # ======================================================================
        prop_subthread = f"council-prop-{handoff_id[:8]}"
        async with get_db() as db:
            await db.execute(
                "INSERT INTO threads (id, dot_id, title, status) VALUES (?, ?, ?, 'running')",
                (prop_subthread, resolved_proponent, f"Proposta de Conselho: {topic[:30]}")
            )
            await db.commit()

        prop_prompt = (
            f"[CONSELHO CONSULTIVO - SOLICITAÇÃO DE PROPOSTA]\n"
            f"Tópico para Deliberação: {topic}\n\n"
            "Instruções:\n"
            "Apresente uma proposta técnica clara, detalhada e estruturada para este tópico. "
            "Especifique a lógica recomendada, padrões de arquitetura e mitigação prévia de falhas. "
            "Sua proposta será submetida imediatamente à auditoria crítica do conselho."
        )

        proponent_output, prop_ok, prop_err = await cls._execute_turn(proponent_agent, prop_subthread, prop_prompt)
        if not prop_ok:
            return await cls._fail_council(
                handoff_id=handoff_id,
                thread_id=thread_id,
                failed_dot_id=resolved_proponent,
                supervisor_dot_id=resolved_supervisor,
                error_msg=prop_err,
                subthreads=[prop_subthread]
            )

        # Registra a proposta como mensagem interna na thread principal
        await MultiBotOrchestrator.record_message(
            thread_id=thread_id,
            actor_id=resolved_proponent,
            actor_type="dot",
            target_dot_id=resolved_critic,
            visibility="internal",
            role="assistant",
            content=f"[CONSELHO - PROPOSTA TÉCNICA DE @{resolved_proponent}]:\n{proponent_output}"
        )

        # ======================================================================
        # ETAPA 2: O Crítico / Auditor audita a proposta em busca de falhas e riscos
        # ======================================================================
        critic_subthread = f"council-crit-{handoff_id[:8]}"
        async with get_db() as db:
            await db.execute(
                "INSERT INTO threads (id, dot_id, title, status) VALUES (?, ?, ?, 'running')",
                (critic_subthread, resolved_critic, f"Auditoria Crítica: {topic[:30]}")
            )
            await db.commit()

        critic_prompt = (
            f"[CONSELHO CONSULTIVO - AUDITORIA CRÍTICA]\n"
            f"Tópico: {topic}\n"
            f"Proposta apresentada por @{resolved_proponent}:\n{proponent_output}\n\n"
            "Instruções de Auditoria:\n"
            "1. Analise criticamente a proposta acima.\n"
            "2. Aponte pontas soltas, riscos de segurança, vulnerabilidades de I/O em MicroSD, "
            "riscos de memória RAM no Raspberry Pi 4B, tratamento de exceções ou casos extremos não contemplados.\n"
            "3. Indique se você aprova com ressalvas ou recomenda correções obrigatórias."
        )

        critic_output, crit_ok, crit_err = await cls._execute_turn(critic_agent, critic_subthread, critic_prompt)
        if not crit_ok:
            return await cls._fail_council(
                handoff_id=handoff_id,
                thread_id=thread_id,
                failed_dot_id=resolved_critic,
                supervisor_dot_id=resolved_supervisor,
                error_msg=crit_err,
                subthreads=[prop_subthread, critic_subthread]
            )

        # Registra a avaliação como mensagem interna
        await MultiBotOrchestrator.record_message(
            thread_id=thread_id,
            actor_id=resolved_critic,
            actor_type="dot",
            target_dot_id=resolved_supervisor,
            visibility="internal",
            role="assistant",
            content=f"[CONSELHO - AUDITORIA CRÍTICA DE @{resolved_critic}]:\n{critic_output}"
        )

        # ======================================================================
        # ETAPA 3 (Opcional): Rodadas Iterativas com Early Consensus Exit
        # ======================================================================
        actual_rounds_executed = 1
        early_consensus = False

        # Verifica se o parecer inicial do auditor já aprovou a proposta sem ressalvas
        if cls._is_auditor_approved(critic_output) and total_rounds > 1:
            logger.info("Early Consensus Exit detectado no parecer inicial de @%s (RISK_LOW / APPROVED). Consolidando decisão.", resolved_critic)
            early_consensus = True
            await MultiBotOrchestrator.record_message(
                thread_id=thread_id,
                actor_id=resolved_critic,
                actor_type="dot",
                target_dot_id=resolved_supervisor,
                visibility="internal",
                role="assistant",
                content=f"[CONSELHO - EARLY CONSENSUS EXIT]: Consenso técnico imediato atingido com parecer RISK_LOW / APPROVED por @{resolved_critic}. Poupando rodadas adicionais."
            )

        if not early_consensus:
            for round_idx in range(2, total_rounds + 1):
                actual_rounds_executed = round_idx
                replica_prompt = (
                    f"[CONSELHO CONSULTIVO - RÉPLICA DO PROPOSITOR (RODADA {round_idx}/{total_rounds})]\n"
                    f"O auditor @{resolved_critic} fez as seguintes observações críticas à sua proposta:\n"
                    f"{critic_output}\n\n"
                    "Ajuste sua proposta ou refute os pontos levantados antes da decisão do supervisor."
                )
                replica_output, rep_ok, rep_err = await cls._execute_turn(proponent_agent, prop_subthread, replica_prompt)
                if not rep_ok:
                    return await cls._fail_council(
                        handoff_id=handoff_id,
                        thread_id=thread_id,
                        failed_dot_id=resolved_proponent,
                        supervisor_dot_id=resolved_supervisor,
                        error_msg=rep_err,
                        subthreads=[prop_subthread, critic_subthread]
                    )
                proponent_output = replica_output

                await MultiBotOrchestrator.record_message(
                    thread_id=thread_id,
                    actor_id=resolved_proponent,
                    actor_type="dot",
                    target_dot_id=resolved_supervisor,
                    visibility="internal",
                    role="assistant",
                    content=f"[CONSELHO - RÉPLICA DE @{resolved_proponent} (RODADA {round_idx})]:\n{proponent_output}"
                )

                # Tréplica do Crítico para fechamento da revisão conjunta
                treplica_prompt = (
                    f"[CONSELHO CONSULTIVO - TRÉPLICA DO AUDITOR CRÍTICO (RODADA {round_idx}/{total_rounds})]\n"
                    f"O propositor @{resolved_proponent} apresentou a seguinte réplica/ajuste:\n"
                    f"{proponent_output}\n\n"
                    "Emita sua avaliação de auditoria final sobre a réplica (ex: 'RISK_LOW / APPROVED' para encerramento por consenso antecipado ou ressalvas remanescentes)."
                )
                treplica_output, trep_ok, trep_err = await cls._execute_turn(critic_agent, critic_subthread, treplica_prompt)
                if not trep_ok:
                    return await cls._fail_council(
                        handoff_id=handoff_id,
                        thread_id=thread_id,
                        failed_dot_id=resolved_critic,
                        supervisor_dot_id=resolved_supervisor,
                        error_msg=trep_err,
                        subthreads=[prop_subthread, critic_subthread]
                    )
                critic_output = treplica_output

                await MultiBotOrchestrator.record_message(
                    thread_id=thread_id,
                    actor_id=resolved_critic,
                    actor_type="dot",
                    target_dot_id=resolved_supervisor,
                    visibility="internal",
                    role="assistant",
                    content=f"[CONSELHO - TRÉPLICA DE @{resolved_critic} (RODADA {round_idx})]:\n{critic_output}"
                )

                # Early Consensus Exit na Rodada 2+: se auditor aprovou a réplica com RISK_LOW / APPROVED
                if cls._is_auditor_approved(critic_output):
                    logger.info(
                        "Early Consensus Exit atingido na Rodada %d por @%s (RISK_LOW / APPROVED). Consolidando decisão sem rodadas extras.",
                        round_idx, resolved_critic
                    )
                    early_consensus = True
                    await MultiBotOrchestrator.record_message(
                        thread_id=thread_id,
                        actor_id=resolved_critic,
                        actor_type="dot",
                        target_dot_id=resolved_supervisor,
                        visibility="internal",
                        role="assistant",
                        content=f"[CONSELHO - EARLY CONSENSUS EXIT]: Consenso técnico atingido com parecer RISK_LOW / APPROVED por @{resolved_critic} na Rodada {round_idx}. Encerrando debate antecipadamente."
                    )
                    break

        # ======================================================================
        # ETAPA 4: O Supervisor pondera, decide e sintetiza a resolução final
        # ======================================================================
        sup_subthread = f"council-sup-{handoff_id[:8]}"
        async with get_db() as db:
            await db.execute(
                "INSERT INTO threads (id, dot_id, title, status) VALUES (?, ?, ?, 'running')",
                (sup_subthread, resolved_supervisor, f"Deliberação de Conselho: {topic[:30]}")
            )
            await db.commit()

        supervisor_prompt = (
            f"[CONSELHO CONSULTIVO - DELIBERAÇÃO FINAL]\n"
            f"Tópico: {topic}\n\n"
            f"Proposta de @{resolved_proponent}:\n{proponent_output}\n\n"
            f"Auditoria Crítica de @{resolved_critic}:\n{critic_output}\n\n"
            "Instruções do Supervisor:\n"
            "1. Pondere a proposta e as ponderações do auditor.\n"
            "2. Emita o veredito final do conselho, consolidando as melhores decisões.\n"
            "3. Apresente o plano de ação técnico definitivo e aprovado para execução."
        )

        supervisor_output, sup_ok, sup_err = await cls._execute_turn(supervisor_agent, sup_subthread, supervisor_prompt)
        if not sup_ok:
            return await cls._fail_council(
                handoff_id=handoff_id,
                thread_id=thread_id,
                failed_dot_id=resolved_supervisor,
                supervisor_dot_id=resolved_supervisor,
                error_msg=sup_err,
                subthreads=[prop_subthread, critic_subthread, sup_subthread]
            )

        # Monta a resolução pública consolidada
        public_resolution = (
            f"=== [CONSELHO CONSULTIVO - RESOLUÇÃO FINAL] ===\n"
            f"Tópico Deliberado: {topic}\n"
            f"Composição: Propositor: @{resolved_proponent} | Auditor: @{resolved_critic} | Supervisor: @{resolved_supervisor}\n\n"
            f"--- DELIBERAÇÃO EXECUTIVA E PLANO APROVADO ---\n"
            f"{supervisor_output}"
        )

        # Salva a resolução pública oficial na thread principal
        await MultiBotOrchestrator.record_message(
            thread_id=thread_id,
            actor_id=resolved_supervisor,
            actor_type="dot",
            visibility="public",
            role="assistant",
            content=public_resolution
        )

        # Atualiza a tabela agent_handoffs e subthreads para COMPLETED
        summary_excerpt = f"Conselho concluído: {supervisor_output[:300]}"
        async with get_db() as db:
            await db.execute(
                """
                UPDATE agent_handoffs
                SET status = 'COMPLETED',
                    result_summary = ?,
                    completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (summary_excerpt, handoff_id)
            )
            await db.execute(
                "UPDATE threads SET status = 'completed', updated_at = CURRENT_TIMESTAMP WHERE id IN (?, ?, ?)",
                (prop_subthread, critic_subthread, sup_subthread)
            )
            await db.commit()

        logger.info("Conselho Consultivo (ID: %s) finalizado com sucesso.", handoff_id)

        return {
            "success": True,
            "handoff_id": handoff_id,
            "topic": topic,
            "rounds_executed": actual_rounds_executed,
            "early_consensus": early_consensus,
            "participants": {
                "proponent": resolved_proponent,
                "critic": resolved_critic,
                "supervisor": resolved_supervisor
            },
            "proponent_output": proponent_output,
            "critic_output": critic_output,
            "supervisor_verdict": supervisor_output,
            "public_resolution": public_resolution
        }

    @classmethod
    async def _fail_council(
        cls,
        handoff_id: str,
        thread_id: str,
        failed_dot_id: str,
        supervisor_dot_id: str,
        error_msg: str,
        subthreads: list[str] | None = None
    ) -> dict[str, Any]:
        """Interrompe a deliberação em caso de falha cognitiva e atualiza status no banco de dados."""
        err_desc = error_msg or "Falha de inferência durante a deliberação"
        logger.warning("Conselho Consultivo (ID: %s) falhou na etapa de @%s: %s", handoff_id, failed_dot_id, err_desc)

        async with get_db() as db:
            await db.execute(
                """
                UPDATE agent_handoffs
                SET status = 'FAILED',
                    result_summary = ?,
                    completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (f"Falha de @{failed_dot_id}: {err_desc[:400]}", handoff_id)
            )
            if subthreads:
                for st_id in subthreads:
                    await db.execute(
                        "UPDATE threads SET status = 'error', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (st_id,)
                    )
            await db.commit()

        from .orchestrator import MultiBotOrchestrator
        await MultiBotOrchestrator.record_message(
            thread_id=thread_id,
            actor_id=failed_dot_id,
            actor_type="dot",
            target_dot_id=supervisor_dot_id,
            visibility="internal",
            role="assistant",
            content=f"[FALHA NO CONSELHO CONSULTIVO]: Etapa de @{failed_dot_id} falhou: {err_desc}"
        )

        return {
            "success": False,
            "handoff_id": handoff_id,
            "failed_dot_id": failed_dot_id,
            "error": f"Falha na etapa de @{failed_dot_id}: {err_desc}"
        }

    @classmethod
    async def _resolve_participants(
        cls,
        proponent: str,
        critic: str,
        supervisor: str
    ) -> tuple[str, str, str]:
        """Garante que os IDs dos Dots existam no SQLite priorizando o Squad Central."""
        async with get_db() as db:
            cursor = await db.execute("SELECT id, is_core FROM dots WHERE is_active = 1 ORDER BY is_core DESC, name ASC")
            rows = await cursor.fetchall()
            active_ids = [r["id"] for r in rows]
            active_set = set(active_ids)

        def pick_fallback(preferred: str, fallback_candidates: list[str]) -> str:
            if preferred in active_set:
                return preferred
            for cand in fallback_candidates:
                if cand in active_set:
                    return cand
            return active_ids[0] if active_ids else "dot-dev-core"

        r_proponent = pick_fallback(proponent, ["dot-coder", "dev-assistant", "dot-dev-core"])
        r_critic = pick_fallback(critic, ["dot-auditor", "dot-resilience-tester", "dev-assistant"])
        r_supervisor = pick_fallback(supervisor, ["dot-supervisor", "dot-dev-core", "dev-assistant"])

        return r_proponent, r_critic, r_supervisor
