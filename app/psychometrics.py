"""
psychometrics.py
Motor Psicométrico e Estatístico Computadorizado (V2 Calibrado)
Calcula Escores Padronizados (Z, Percentil, QI μ=100 σ=15), Análise de Dispersão (Scatter),
Índice de Aptidão Geral Expurgado de Interrupções (IAG) e Telemetria de Pausas Ativas.
"""

import math
from typing import Dict, Any, List, Optional
from .questionnaire_data import (
    FENOMENOLOGICO_ITEMS, MATRIZES_ITEMS, CORSI_CONFIG,
    VELOCIDADE_ITEMS, WCST_ANCHORS, WCST_RULE_SCHEDULE,
    ASSOCIACAO_ITEMS, METACOGNICAO_ITEMS
)

def norm_cdf(z: float) -> float:
    """Função de Distribuição Cumulativa Normal Padrão via math.erf (pura)"""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))

def clamp(val, min_val, max_val):
    return max(min_val, min(max_val, val))

class PsychometricEngine:

    # Normas de referência para população geral (médias e desvios-padrão normativos)
    NORMS = {
        "gf": {"mean": 3.2, "sd": 1.2, "max": 6, "name": "Raciocínio Fluido (Gf)"},
        "gwm": {"mean": 4.8, "sd": 1.1, "max": 8, "name": "Memória Operacional (Gwm)"},
        "gs": {"mean": 13.5, "sd": 2.8, "max": 20, "name": "Velocidade Processamento (Gs)"},
        "flexibilidade": {"mean": 11.0, "sd": 2.5, "max": 18, "name": "Flexibilidade Cognitiva"},
        "divergente": {"mean": 2.6, "sd": 1.1, "max": 5, "name": "Pensamento Divergente"},
        "metacognicao": {"mean": 1.3, "sd": 0.8, "max": 3, "name": "Metacognição & Síntese"}
    }

    @classmethod
    def evaluate_session(cls, responses: List[Dict[str, Any]], telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recebe a lista de respostas e telemetria da sessão e processa todo o laudo psicométrico.
        """
        resp_by_item = {r.get("item_id"): r for r in responses}
        resp_by_module = {}
        for r in responses:
            mod = r.get("module_name")
            resp_by_module.setdefault(mod, []).append(r)

        # 1. Avaliação de cada módulo
        fen_scores = cls._calc_fenomenologico(resp_by_module.get("fenomenologico", []))
        gf_result = cls._calc_matrizes(resp_by_module.get("matrizes", []))
        gwm_result = cls._calc_corsi(resp_by_module.get("corsi", []))
        gs_result = cls._calc_velocidade(resp_by_module.get("velocidade", []))
        flex_result = cls._calc_wcst(resp_by_module.get("wcst", []))
        div_result = cls._calc_associacao(resp_by_module.get("associacao", []))
        meta_result = cls._calc_metacognicao(resp_by_module.get("metacognicao", []))

        # 2. Métricas de Tempo e Telemetria (Ativo vs Pausa)
        active_time_ms = telemetry.get("active_time_ms", 0.0) if telemetry else 0.0
        # Se não tiver ativo explícito, soma o tempo dos itens
        if active_time_ms <= 0:
            active_time_ms = sum(float(r.get("reaction_time_ms", 0.0)) for r in responses)

        idle_time_ms = telemetry.get("idle_time_ms", 0.0) if telemetry else 0.0
        total_time_ms = active_time_ms + idle_time_ms

        time_metrics = {
            "active_seconds": round(active_time_ms / 1000, 1),
            "active_minutes": round((active_time_ms / 1000) / 60, 1),
            "idle_seconds": round(idle_time_ms / 1000, 1),
            "idle_minutes": round((idle_time_ms / 1000) / 60, 1),
            "total_seconds": round(total_time_ms / 1000, 1),
            "total_minutes": round((total_time_ms / 1000) / 60, 1),
            "pause_events_count": len(telemetry.get("pause_events", [])) if telemetry else 0,
            "pause_events": telemetry.get("pause_events", []) if telemetry else []
        }

        # 3. Análise de Validade do Teste (SVT / PVT e Telemetria de Pausa)
        validity_report = cls._calc_validity(responses, telemetry, fen_scores.get("pvt_passed", True), time_metrics)

        # 4. Cálculo de Z-scores, Percentis e QI Estimado por domínio
        domains = {
            "Gf (Raciocínio Fluido)": gf_result["raw_score"],
            "Gwm (Memória Operacional)": gwm_result["max_span"],
            "Gs (Velocidade Processamento)": gs_result["raw_score"],
            "Flexibilidade Cognitiva": flex_result["raw_score"],
            "Pensamento Divergente": div_result["raw_score"],
            "Metacognição & Síntese": meta_result["raw_score"]
        }

        domain_keys = {
            "Gf (Raciocínio Fluido)": "gf",
            "Gwm (Memória Operacional)": "gwm",
            "Gs (Velocidade Processamento)": "gs",
            "Flexibilidade Cognitiva": "flexibilidade",
            "Pensamento Divergente": "divergente",
            "Metacognição & Síntese": "metacognicao"
        }

        standardized_scores = {}
        z_list = []

        for d_name, raw_val in domains.items():
            k = domain_keys[d_name]
            norm = cls.NORMS[k]
            z = (raw_val - norm["mean"]) / norm["sd"]
            z = round(clamp(z, -3.5, 3.5), 2)
            z_list.append(z)
            pct = round(norm_cdf(z) * 100, 1)
            t_score = round(50 + 10 * z, 1)
            iq_est = round(100 + 15 * z)

            standardized_scores[d_name] = {
                "key": k,
                "raw_score": raw_val,
                "max_possible": norm["max"],
                "z_score": z,
                "percentile": pct,
                "t_score": t_score,
                "estimated_iq": iq_est
            }

        # 5. Escore Cognitivo Geral Convencional (Média Composta)
        avg_z = sum(z_list) / len(z_list) if z_list else 0.0
        composite_z = round(clamp(avg_z * 1.15, -3.5, 3.5), 2)
        composite_pct = round(norm_cdf(composite_z) * 100, 1)
        composite_iq = round(100 + 15 * composite_z)

        # 6. Análise de Dispersão Intra-Individual (Scatter)
        iq_values = [d["estimated_iq"] for d in standardized_scores.values()]
        max_iq_item = max(standardized_scores.items(), key=lambda x: x[1]["estimated_iq"])
        min_iq_item = min(standardized_scores.items(), key=lambda x: x[1]["estimated_iq"])
        iq_diff = max_iq_item[1]["estimated_iq"] - min_iq_item[1]["estimated_iq"]
        has_scatter = iq_diff >= 22 # > 1.5 desvios padrão de dispersão

        scatter_analysis = {
            "has_scatter": has_scatter,
            "iq_difference": iq_diff,
            "max_domain": f"{max_iq_item[0]} (QI {max_iq_item[1]['estimated_iq']})",
            "min_domain": f"{min_iq_item[0]} (QI {min_iq_item[1]['estimated_iq']})",
            "message": (
                f"Dispersão extrema detectada entre domínios (diferença de {iq_diff} pontos de QI). "
                "Na neuropsicologia clínica (teorema de Wechsler), quando a dispersão intra-individual ultrapassa 22 pontos, "
                "o QI Composto Geral perde validade descritiva e não reflete adequadamente a capacidade real do indivíduo."
            ) if has_scatter else "Dispersão homogênea entre os domínios avaliados."
        }

        # 7. Cálculo do Índice de Capacidade Geral Expurgado (IAG / Outlier Rejection)
        # Identifica subtestes corrompidos por quebra de retenção/pausa externa
        # Critério neuropsicológico: queda >= 22 pontos (1.5σ) abaixo do pico com Z <= 0.0
        expurgated_composite = None
        outlier_keys = []
        for d_name, d_info in standardized_scores.items():
            drop_from_peak = max_iq_item[1]["estimated_iq"] - d_info["estimated_iq"]
            if drop_from_peak >= 22 and d_info["z_score"] <= 0.0:
                outlier_keys.append(d_name)

        if outlier_keys and (has_scatter or time_metrics["idle_minutes"] >= 15 or time_metrics["total_minutes"] >= 45):
            valid_z_scores = [d["z_score"] for name, d in standardized_scores.items() if name not in outlier_keys]
            if valid_z_scores:
                exp_avg_z = sum(valid_z_scores) / len(valid_z_scores)
                exp_comp_z = round(clamp(exp_avg_z, -3.5, 3.5), 2)
                exp_comp_pct = round(norm_cdf(exp_comp_z) * 100, 1)
                exp_comp_iq = round(100 + 15 * exp_comp_z)

                expurgated_composite = {
                    "estimated_iq": exp_comp_iq,
                    "percentile": exp_comp_pct,
                    "z_score": exp_comp_z,
                    "classification": cls._classify_iq(exp_comp_iq),
                    "excluded_domains": outlier_keys,
                    "rationale": (
                        f"Índice de Capacidade Geral (IAG) calculado expurgando o(s) subteste(s) {', '.join(outlier_keys)}. "
                        "A quebra de retenção provocada por pausas externas ou interrupções de sessão afeta tarefas de curtíssimo prazo, "
                        "mas não anula a alta capacidade demonstrada nos domínios cognitivos preservados."
                    )
                }

        # 8. Gráfico Radar (0 a 100% relativo à pontuação máxima)
        # Normalização rigorosa: (raw_score / max_score) * 100
        radar_data = {
            "Raciocínio Fluido (Gf)": round(min(100, max(0, (gf_result["raw_score"] / cls.NORMS["gf"]["max"]) * 100))),
            "Memória Operacional (Gwm)": round(min(100, max(0, (gwm_result["max_span"] / cls.NORMS["gwm"]["max"]) * 100))),
            "Velocidade Processamento (Gs)": round(min(100, max(0, (gs_result["raw_score"] / cls.NORMS["gs"]["max"]) * 100))),
            "Flexibilidade Cognitiva (WCST)": round(min(100, max(0, (flex_result["raw_score"] / cls.NORMS["flexibilidade"]["max"]) * 100))),
            "Pensamento Divergente (RAT)": round(min(100, max(0, (div_result["raw_score"] / cls.NORMS["divergente"]["max"]) * 100))),
            "Metacognição Sistêmica": round(min(100, max(0, (meta_result["raw_score"] / cls.NORMS["metacognicao"]["max"]) * 100)))
        }

        # 9. Síntese Interpretativa e Identificação de Pontos Fortes Calibrados
        qualitative_summary = cls._generate_qualitative_interpretation(
            composite_iq, expurgated_composite, standardized_scores, fen_scores, flex_result, validity_report, has_scatter
        )

        return {
            "composite": {
                "general_iq_estimate": composite_iq,
                "general_percentile": composite_pct,
                "general_z_score": composite_z,
                "classification": cls._classify_iq(composite_iq)
            },
            "expurgated_composite": expurgated_composite,
            "scatter_analysis": scatter_analysis,
            "time_metrics": time_metrics,
            "domains": standardized_scores,
            "radar_chart": radar_data,
            "fenomenologico": fen_scores,
            "validity": validity_report,
            "module_details": {
                "matrizes": gf_result,
                "corsi": gwm_result,
                "velocidade": gs_result,
                "wcst": flex_result,
                "associacao": div_result,
                "metacognicao": meta_result
            },
            "qualitative_summary": qualitative_summary,
            "disclaimer": (
                "DECLARAÇÃO DEONTOLÓGICA E LIMITAÇÕES: Este sistema constitui uma ferramenta psicométrica computadorizada "
                "de triagem e mapeamento cognitivo experimental baseada em modelos da neuropsicologia computacional. "
                "Os índices estatísticos e a estimativa de QI expressos neste relatório possuem finalidade estritamente informativa "
                "e de autoavaliação, NÃO substituindo um laudo pericial formal emitido por neuropsicólogo(a) ou equipe multidisciplinar "
                "através de baterias clínicas presenciais padronizadas (como WAIS-IV, WISC, Raven Avançado e anamnese clínica)."
            )
        }

    @staticmethod
    def _calc_fenomenologico(responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcula médias por categoria da autoavaliação fenomenológica"""
        cat_scores = {
            "aprendizado": [],
            "intelectual": [],
            "emocional": [],
            "imaginativa": [],
            "sensorial": [],
            "psicomotora": [],
            "discronia": [],
            "paralisia": [],
            "comunicacao": []
        }
        pvt_passed = True
        fen_dict = {item["id"]: item for item in FENOMENOLOGICO_ITEMS}

        for r in responses:
            item_id = r.get("item_id")
            val = r.get("user_answer")
            try:
                val = int(val)
            except (ValueError, TypeError):
                continue

            if item_id == "fen_trap":
                if val != 1:
                    pvt_passed = False
                continue

            item_def = fen_dict.get(item_id)
            if item_def and item_def["category"] in cat_scores:
                cat_scores[item_def["category"]].append(val)

        averages = {}
        for cat, vals in cat_scores.items():
            averages[cat] = round(sum(vals) / len(vals), 2) if vals else 1.0

        overexcitabilities = {
            "Intelectual": averages.get("intelectual", 1.0),
            "Emocional": averages.get("emocional", 1.0),
            "Imaginativa": averages.get("imaginativa", 1.0),
            "Sensorial": averages.get("sensorial", 1.0),
            "Psicomotora": averages.get("psicomotora", 1.0)
        }

        return {
            "averages": averages,
            "overexcitabilities": overexcitabilities,
            "pvt_passed": pvt_passed,
            "high_traits": [cat for cat, avg in averages.items() if avg >= 4.0]
        }

    @staticmethod
    def _calc_matrizes(responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        gabarito = {m["id"]: m["correct_id"] for m in MATRIZES_ITEMS}
        correct_count = 0
        total_time = 0.0
        times = []

        for r in responses:
            item_id = r.get("item_id")
            ans = str(r.get("user_answer", "")).strip().upper()
            rt = float(r.get("reaction_time_ms", 0.0))
            times.append(rt)
            total_time += rt
            if gabarito.get(item_id) == ans:
                correct_count += 1

        avg_rt = round(total_time / len(times)) if times else 0
        return {
            "raw_score": correct_count,
            "total_items": len(MATRIZES_ITEMS),
            "accuracy_pct": round((correct_count / len(MATRIZES_ITEMS)) * 100, 1),
            "avg_reaction_time_ms": avg_rt
        }

    @staticmethod
    def _calc_corsi(responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        max_span = 0
        successful_trials = 0
        span_by_level = {s["level"]: s["span"] for s in CORSI_CONFIG["test_sequences"]}

        for r in responses:
            user_seq = r.get("user_answer")
            target_seq = r.get("raw_data", {}).get("target_sequence")
            level = r.get("raw_data", {}).get("level", 1)

            if isinstance(user_seq, list) and isinstance(target_seq, list):
                if user_seq == target_seq:
                    successful_trials += 1
                    span = span_by_level.get(level, len(target_seq))
                    if span > max_span:
                        max_span = span

        if max_span == 0 and responses:
            max_span = 2

        return {
            "max_span": max_span,
            "successful_trials": successful_trials,
            "total_trials": len(CORSI_CONFIG["test_sequences"])
        }

    @staticmethod
    def _calc_velocidade(responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        gabarito = {v["id"]: v["is_match"] for v in VELOCIDADE_ITEMS}
        correct_count = 0
        times = []

        for r in responses:
            item_id = r.get("item_id")
            ans = r.get("user_answer")
            rt = float(r.get("reaction_time_ms", 0.0))
            times.append(rt)

            if item_id in gabarito:
                is_match_expected = gabarito[item_id]
                ans_bool = True if str(ans).lower() in ["true", "1", "igual", "sim"] else False
                if ans_bool == is_match_expected:
                    correct_count += 1

        avg_rt = round(sum(times) / len(times)) if times else 0
        return {
            "raw_score": correct_count,
            "total_items": len(VELOCIDADE_ITEMS),
            "accuracy_pct": round((correct_count / len(VELOCIDADE_ITEMS)) * 100, 1) if VELOCIDADE_ITEMS else 0,
            "avg_reaction_time_ms": avg_rt
        }

    @staticmethod
    def _calc_wcst(responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        rule_map = {}
        for s in WCST_RULE_SCHEDULE:
            for t in range(s["start"], s["end"] + 1):
                rule_map[t] = s["rule"]

        correct_count = 0
        perseverative_errors = 0

        for r in responses:
            trial_num = r.get("raw_data", {}).get("trial", 1)
            is_correct = r.get("is_correct", False)

            if is_correct:
                correct_count += 1
            else:
                chosen_anchor = r.get("raw_data", {}).get("chosen_anchor", {})
                card = r.get("raw_data", {}).get("card", {})
                
                if trial_num > 6 and trial_num <= 12:
                    if chosen_anchor.get("color") == card.get("color"):
                        perseverative_errors += 1
                elif trial_num > 12:
                    if chosen_anchor.get("shape") == card.get("shape"):
                        perseverative_errors += 1

        return {
            "raw_score": correct_count,
            "total_trials": len(responses) if responses else 18,
            "perseverative_errors": perseverative_errors,
            "flexibility_rating": "Alta" if perseverative_errors <= 2 else ("Moderada" if perseverative_errors <= 4 else "Rígida / Baixa")
        }

    @staticmethod
    def _calc_associacao(responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        gabarito = {a["id"]: a["accepted_answers"] for a in ASSOCIACAO_ITEMS}
        correct_count = 0
        times = []

        for r in responses:
            item_id = r.get("item_id")
            ans = str(r.get("user_answer", "")).strip().lower()
            rt = float(r.get("reaction_time_ms", 0.0))
            times.append(rt)

            accepted = gabarito.get(item_id, [])
            if any(acc.lower() in ans for acc in accepted) and len(ans) > 1:
                correct_count += 1

        avg_rt = round(sum(times) / len(times)) if times else 0
        return {
            "raw_score": correct_count,
            "total_items": len(ASSOCIACAO_ITEMS),
            "avg_reaction_time_ms": avg_rt
        }

    @staticmethod
    def _calc_metacognicao(responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        gabarito = {m["id"]: m["correct_id"] for m in METACOGNICAO_ITEMS}
        score = 0
        breakdown = {}

        for r in responses:
            item_id = r.get("item_id")
            ans = str(r.get("user_answer", "")).strip().upper()
            expected = gabarito.get(item_id)
            correct = (ans == expected)
            if correct:
                score += 1
            breakdown[item_id] = {
                "user_answer": ans,
                "correct": correct,
                "optimal_answer": expected
            }

        return {
            "raw_score": score,
            "total_items": len(METACOGNICAO_ITEMS),
            "breakdown": breakdown
        }

    @staticmethod
    def _calc_validity(
        responses: List[Dict[str, Any]], telemetry: Dict[str, Any], pvt_passed: bool, time_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        fast_clicks = 0
        for r in responses:
            rt = float(r.get("reaction_time_ms", 0.0))
            if 0 < rt < 150.0:
                fast_clicks += 1

        focus_loss_count = telemetry.get("focus_loss_count", 0) if telemetry else 0
        blur_events = telemetry.get("blur_events", 0) if telemetry else 0

        # Verifica padrão estático
        answers = [str(r.get("user_answer")) for r in responses if r.get("user_answer")]
        is_repetitive = False
        if len(answers) >= 10:
            most_common = max(set(answers), key=answers.count)
            if answers.count(most_common) / len(answers) > 0.85:
                is_repetitive = True

        issues = []
        if not pvt_passed:
            issues.append("Falha no item armadilha de verificação (PVT) - possível desatenção ou ruído.")
        if fast_clicks >= 4:
            issues.append(f"{fast_clicks} respostas com latência inferior a 150 ms (sugere chutes sem leitura).")
        if focus_loss_count >= 5:
            issues.append(f"{focus_loss_count} perdas de foco de tela detectadas (trocas de janela/aba).")
        if is_repetitive:
            issues.append("Padrão de resposta excessivamente repetitivo ou invariante.")

        # Auditoria de tempo e pausas (Página 12 e 14 do PDF)
        idle_mins = time_metrics.get("idle_minutes", 0)
        total_mins = time_metrics.get("total_minutes", 0)
        has_extended_pause = (idle_mins >= 15.0 or total_mins >= 45.0)

        if has_extended_pause:
            issues.append(
                f"Sessão com pausa prolongada detectada (Tempo Inativo: {idle_mins} min, Tempo Total: {total_mins} min). "
                "Quebras de contexto e interrupções externas esvaziam a memória de trabalho de curto prazo."
            )

        if not issues:
            status = "Índice de Validade Ótimo (Dados Fidedignos)"
            badge = "valid"
        elif has_extended_pause or (len(issues) == 1 and pvt_passed):
            status = "Sessão Concluída com Pausa / Interrupção Externa" if has_extended_pause else "Índice de Validade Adequado com Pequenos Desvios"
            badge = "warning"
        else:
            status = "Índice de Validade Comprometido / Atenção Requerida"
            badge = "invalid"

        return {
            "status": status,
            "badge": badge,
            "pvt_passed": pvt_passed,
            "fast_clicks_count": fast_clicks,
            "focus_loss_count": focus_loss_count,
            "has_extended_pause": has_extended_pause,
            "is_repetitive": is_repetitive,
            "detected_issues": issues
        }

    @staticmethod
    def _classify_iq(iq: int) -> str:
        if iq >= 130:
            return "Muito Superior / Faixa de Altas Habilidades (AH/SD)"
        elif iq >= 120:
            return "Superior"
        elif iq >= 110:
            return "Médio Superior"
        elif iq >= 90:
            return "Médio"
        elif iq >= 80:
            return "Médio Inferior"
        else:
            return "Limítrofe"

    @classmethod
    def _generate_qualitative_interpretation(
        cls, composite_iq: int, expurgated_composite: Optional[Dict[str, Any]],
        domains: Dict[str, Any], fen: Dict[str, Any], flex: Dict[str, Any],
        val: Dict[str, Any], has_scatter: bool
    ) -> Dict[str, Any]:
        """
        Gera síntese interpretativa calibrada:
        - Destaca pontos fortes a partir de Z >= 1.33 (QI >= 120) e Z >= 1.0 (QI >= 115)
        - Considera o Índice de Capacidade Geral Expurgado quando há scatter e interrupções
        """
        obs = []
        strengths = []
        challenges = []

        domain_descriptions = {
            "Gf (Raciocínio Fluido)": "Raciocínio Fluido: alta capacidade de indução lógica e abstração visual matricial",
            "Gwm (Memória Operacional)": "Memória Operacional: grande sustentação e manipulação ativa de carga visuoespacial de curto prazo",
            "Gs (Velocidade Processamento)": "Velocidade de Processamento: agilidade perceptual extrema e rápida condução neural de impulsos",
            "Flexibilidade Cognitiva": "Flexibilidade Cognitiva: rapidez em desengajar de regras antigas e ajustar modelos conceituais",
            "Pensamento Divergente": "Pensamento Divergente: raciocínio associativo veloz, salto intuitivo e conectividade semântica em rede",
            "Metacognição & Síntese": "Metacognição Sistêmica: alta facilidade em capturar propriedades emergentes e regras invariantes complexas"
        }

        # 1. Avaliação Dinâmica de Pontos Fortes por Domínio (Calibração Z >= 1.33 e Z >= 1.0)
        for d_name, d_info in domains.items():
            z = d_info["z_score"]
            iq = d_info["estimated_iq"]
            desc = domain_descriptions.get(d_name, d_name)

            if z >= 1.33 or iq >= 120:
                strengths.append(f"Ponto Forte Marcante em {desc} (QI {iq}, Percentil {d_info['percentile']}º).")
            elif z >= 0.95 or iq >= 114:
                strengths.append(f"Desempenho Acima da Média em {desc} (QI {iq}, Percentil {d_info['percentile']}º).")

        # Se não atingiu corte, garante mensagem adequada
        if not strengths:
            strengths.append("Desempenho distribuído na faixa normativa média em todos os domínios avaliados.")

        # 2. Desafios Observados
        for d_name, d_info in domains.items():
            if d_info["z_score"] <= -1.5:
                challenges.append(f"Queda em {d_name} (QI {d_info['estimated_iq']}) — passível de impacto por interrupção de contexto ou fadiga.")

        if flex.get("flexibility_rating") != "Alta":
            challenges.append("Tendência à perseveração conceitual inicial antes de reorganizar o modelo mental sob mudança de regras.")

        # 3. Hiperexcitabilidades de Dabrowski
        oe = fen.get("overexcitabilities", {})
        top_oe = sorted(oe.items(), key=lambda x: x[1], reverse=True)
        predominant_oe = [k for k, v in top_oe if v >= 3.8]

        avg_fen = fen.get("averages", {})
        if avg_fen.get("aprendizado", 1.0) >= 4.0:
            obs.append("Padrão de hiperfoco autodidata acentuado com aversão intensa à redundância e explicações lentas.")
        
        if avg_fen.get("paralisia", 1.0) >= 3.8:
            challenges.append("Risco elevado de paralisia por análise e perfeccionismo gerado pela antecipação exaustiva de variáveis.")

        if avg_fen.get("discronia", 1.0) >= 3.8:
            challenges.append("Sensação evidente de discronia interna (desenvolvimento cognitivo avançando muito além do suporte emocional/social).")

        if avg_fen.get("comunicacao", 1.0) >= 3.8:
            challenges.append("Sensação frequente de operar em frequência distinta, com sobrecarga para traduzir pensamentos holísticos em linguagem linear cadenciada.")

        # 4. Título e Perfil Geral
        target_iq = expurgated_composite["estimated_iq"] if expurgated_composite else composite_iq

        if has_scatter:
            profile_title = "Perfil Cognitivo Heterogêneo com Dispersão Intra-Individual (Scatter)"
            description = (
                f"O perfil apresenta forte dispersão entre subtestes. Enquanto áreas como {strengths[0] if strengths else 'determinados domínios'} "
                "revelam alta capacidade neurocognitiva, a média composta global foi puxada para baixo por subteste(s) com anomalia de contexto ou interrupção. "
                + (f"O Índice de Capacidade Geral Expurgado aponta um desempenho efetivo na faixa de QI {expurgated_composite['estimated_iq']} ({expurgated_composite['classification']})." if expurgated_composite else "")
            )
        elif target_iq >= 130:
            profile_title = "Perfil Compatível com Altas Habilidades / Superdotação (AH/SD)"
            description = (
                "O desempenho nos domínios neurocognitivos e as respostas na escala de rastreio fenomenológico "
                "apresentam fortes marcadores da arquitetura da mente superdotada: alta velocidade associativa, "
                "hiperexcitabilidade evidente e pensamento holístico/em árvore com grande capacidade de síntese."
            )
        elif target_iq >= 120:
            profile_title = "Perfil Cognitivo Superior com Destaques Marcantes"
            description = (
                "Identificam-se habilidades cognitivas acima da média populacional, com destaques expressivos em velocidade, "
                "pensamento divergente e traços característicos de curiosidade voraz e intensidade de processamento."
            )
        else:
            profile_title = "Perfil Cognitivo Médio Padronizado"
            description = (
                "Os indicadores situam-se dentro da média normativa para a maior parte dos domínios avaliados."
            )

        return {
            "profile_title": profile_title,
            "description": description,
            "strengths": strengths,
            "challenges": challenges,
            "observations": obs,
            "predominant_overexcitabilities": predominant_oe
        }
