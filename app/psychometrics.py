"""
psychometrics.py
Motor Psicométrico e Estatístico Computadorizado
Calcula Escores Padronizados (Z, Percentil, QI μ=100 σ=15), Índices de Validade (SVT/PVT)
e Radar Neurocognitivo por Domínio.
"""

import math
from typing import Dict, Any, List
from .questionnaire_data import (
    FENOMENOLOGICO_ITEMS, MATRIZES_ITEMS, CORSI_CONFIG,
    VELOCIDADE_ITEMS, WCST_ANCHORS, WCST_RULE_SCHEDULE,
    ASSOCIACAO_ITEMS, METACOGNICAO_ITEMS
)

def norm_cdf(z: float) -> float:
    """Função de Distribuição Cumulativa Normal Padrão via math.erf (pura, sem dependências externas)"""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))

def clamp(val, min_val, max_val):
    return max(min_val, min(max_val, val))

class PsychometricEngine:

    # Normas de referência para população geral (médias e desvios-padrão normativos simulados para calibração)
    NORMS = {
        "gf": {"mean": 3.2, "sd": 1.2, "max": 6},
        "gwm": {"mean": 4.8, "sd": 1.1, "max": 8},
        "gs": {"mean": 13.5, "sd": 2.8, "max": 20},
        "flexibilidade": {"mean": 11.0, "sd": 2.5, "max": 18},
        "divergente": {"mean": 2.6, "sd": 1.1, "max": 5},
        "metacognicao": {"mean": 1.3, "sd": 0.8, "max": 3}
    }

    @classmethod
    def evaluate_session(cls, responses: List[Dict[str, Any]], telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recebe a lista de respostas e telemetria da sessão e processa todo o laudo psicométrico.
        """
        # Mapeia respostas por item_id e por módulo
        resp_by_item = {r.get("item_id"): r for r in responses}
        resp_by_module = {}
        for r in responses:
            mod = r.get("module_name")
            resp_by_module.setdefault(mod, []).append(r)

        # 1. Avaliação do Módulo Fenomenológico (Likert 1 a 5)
        fen_scores = cls._calc_fenomenologico(resp_by_module.get("fenomenologico", []))

        # 2. Avaliação de Raciocínio Fluido - Gf (Matrizes)
        gf_result = cls._calc_matrizes(resp_by_module.get("matrizes", []))

        # 3. Avaliação de Memória Operacional - Gwm (Corsi Blocks)
        gwm_result = cls._calc_corsi(resp_by_module.get("corsi", []))

        # 4. Avaliação de Velocidade de Processamento - Gs
        gs_result = cls._calc_velocidade(resp_by_module.get("velocidade", []))

        # 5. Avaliação de Flexibilidade Cognitiva - WCST
        flex_result = cls._calc_wcst(resp_by_module.get("wcst", []))

        # 6. Avaliação de Pensamento Divergente - RAT
        div_result = cls._calc_associacao(resp_by_module.get("associacao", []))

        # 7. Avaliação de Metacognição e Desafios do PDF
        meta_result = cls._calc_metacognicao(resp_by_module.get("metacognicao", []))

        # 8. Análise de Validade do Teste (SVT / PVT e Telemetria)
        validity_report = cls._calc_validity(responses, telemetry, fen_scores.get("pvt_passed", True))

        # 9. Cálculo de Z-scores, Percentis e QI Estimado para os domínios de desempenho cognitivo
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
                "raw_score": raw_val,
                "max_possible": norm["max"],
                "z_score": z,
                "percentile": pct,
                "t_score": t_score,
                "estimated_iq": iq_est
            }

        # Escore Cognitivo Geral Composto (G Geral)
        avg_z = sum(z_list) / len(z_list) if z_list else 0.0
        # Em índices compostos, a dispersão é reduzida pela covariância entre domínios (fórmula clássica de Spearman/Wechsler):
        composite_z = round(clamp(avg_z * 1.15, -3.5, 3.5), 2)
        composite_pct = round(norm_cdf(composite_z) * 100, 1)
        composite_iq = round(100 + 15 * composite_z)

        # 10. Perfil Neurocognitivo e Hiperexcitabilidades (Radar de 0 a 100)
        radar_data = {
            "Raciocínio Fluido (Gf)": round(min(100, max(0, (gf_result["raw_score"] / cls.NORMS["gf"]["max"]) * 100))),
            "Memória Operacional (Gwm)": round(min(100, max(0, (gwm_result["max_span"] / cls.NORMS["gwm"]["max"]) * 100))),
            "Velocidade Processamento": round(min(100, max(0, (gs_result["raw_score"] / cls.NORMS["gs"]["max"]) * 100))),
            "Flexibilidade Cognitiva": round(min(100, max(0, (flex_result["raw_score"] / cls.NORMS["flexibilidade"]["max"]) * 100))),
            "Pensamento Divergente": round(min(100, max(0, (div_result["raw_score"] / cls.NORMS["divergente"]["max"]) * 100))),
            "Metacognição": round(min(100, max(0, (meta_result["raw_score"] / cls.NORMS["metacognicao"]["max"]) * 100)))
        }

        # Síntese Qualitativa
        qualitative_summary = cls._generate_qualitative_interpretation(
            composite_iq, standardized_scores, fen_scores, flex_result, validity_report
        )

        return {
            "composite": {
                "general_iq_estimate": composite_iq,
                "general_percentile": composite_pct,
                "general_z_score": composite_z,
                "classification": cls._classify_iq(composite_iq)
            },
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
                # O item armadilha pedia expressamente opção 1
                if val != 1:
                    pvt_passed = False
                continue

            item_def = fen_dict.get(item_id)
            if item_def and item_def["category"] in cat_scores:
                cat_scores[item_def["category"]].append(val)

        # Médias de 1.0 a 5.0
        averages = {}
        for cat, vals in cat_scores.items():
            averages[cat] = round(sum(vals) / len(vals), 2) if vals else 1.0

        # Intensidade das 5 hiperexcitabilidades de Dabrowski
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
        """Calcula acertos e tempos no teste de Matrizes Raven"""
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
        """Avalia capacidade máxima de Span no Corsi Blocks"""
        max_span = 0
        successful_trials = 0
        
        # Test sequences configuradas
        span_by_level = {s["level"]: s["span"] for s in CORSI_CONFIG["test_sequences"]}

        for r in responses:
            item_id = r.get("item_id")
            # user_answer é lista ou string de inteiros
            user_seq = r.get("user_answer")
            target_seq = r.get("raw_data", {}).get("target_sequence")
            level = r.get("raw_data", {}).get("level", 1)

            if isinstance(user_seq, list) and isinstance(target_seq, list):
                if user_seq == target_seq:
                    successful_trials += 1
                    span = span_by_level.get(level, len(target_seq))
                    if span > max_span:
                        max_span = span

        # Se não fez nenhum acerto, span mínimo padrão
        if max_span == 0 and responses:
            max_span = 2

        return {
            "max_span": max_span,
            "successful_trials": successful_trials,
            "total_trials": len(CORSI_CONFIG["test_sequences"])
        }

    @staticmethod
    def _calc_velocidade(responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Avalia tarefa de velocidade de pareamento de símbolos"""
        gabarito = {v["id"]: v["is_match"] for v in VELOCIDADE_ITEMS}
        correct_count = 0
        times = []

        for r in responses:
            item_id = r.get("item_id")
            ans = r.get("user_answer")
            rt = float(r.get("reaction_time_ms", 0.0))
            times.append(rt)

            # boolean check
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
        """Calcula flexibilidade cognitiva e erros perseverativos no WCST"""
        # Mapeia regra ativa para cada trial
        rule_map = {}
        for s in WCST_RULE_SCHEDULE:
            for t in range(s["start"], s["end"] + 1):
                rule_map[t] = s["rule"]

        correct_count = 0
        perseverative_errors = 0
        prev_rule = None

        for r in responses:
            trial_num = r.get("raw_data", {}).get("trial", 1)
            active_rule = rule_map.get(trial_num, "color")
            is_correct = r.get("is_correct", False)

            if is_correct:
                correct_count += 1
            else:
                # Checa se o erro correspondeu à regra anterior (erro perseverativo)
                chosen_anchor = r.get("raw_data", {}).get("chosen_anchor", {})
                card = r.get("raw_data", {}).get("card", {})
                
                # Se mudou de regra e o usuário continuou escolhendo pela regra anterior
                if trial_num > 6 and trial_num <= 12:
                    # regra anterior era color
                    if chosen_anchor.get("color") == card.get("color"):
                        perseverative_errors += 1
                elif trial_num > 12:
                    # regra anterior era shape
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
        """Avalia respostas ao teste de associação remota"""
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
        """Avalia as respostas aos 3 desafios do PDF"""
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
    def _calc_validity(responses: List[Dict[str, Any]], telemetry: Dict[str, Any], pvt_passed: bool) -> Dict[str, Any]:
        """
        Calcula o índice de validade da sessão:
        - Malingering / PVT (Symptom Validity)
        - Chutes hiper-rápidos (< 150 ms)
        - Perdas de foco de tela (blur / troca de abas)
        - Padrão estático de resposta
        """
        fast_clicks = 0
        times = []
        for r in responses:
            rt = float(r.get("reaction_time_ms", 0.0))
            if rt > 0:
                times.append(rt)
                if rt < 150.0:
                    fast_clicks += 1

        focus_loss_count = telemetry.get("focus_loss_count", 0) if telemetry else 0
        blur_events = telemetry.get("blur_events", 0) if telemetry else 0

        # Verifica se houve padrão estático
        answers = [str(r.get("user_answer")) for r in responses if r.get("user_answer")]
        is_repetitive = False
        if len(answers) >= 10:
            most_common = max(set(answers), key=answers.count)
            if answers.count(most_common) / len(answers) > 0.85:
                is_repetitive = True

        # Determina confiabilidade geral
        issues = []
        if not pvt_passed:
            issues.append("Falha no item armadilha de verificação (PVT) - possível desatenção ou ruído.")
        if fast_clicks >= 4:
            issues.append(f"{fast_clicks} respostas com latência inferior a 150 ms (sugere chutes sem leitura).")
        if focus_loss_count >= 5:
            issues.append(f"{focus_loss_count} perdas de foco de tela detectadas (trocas de janela/aba).")
        if is_repetitive:
            issues.append("Padrão de resposta excessivamente repetitivo ou invariante.")

        if not issues:
            status = "Índice de Validade Ótimo (Dados Fidedignos)"
            badge = "valid"
        elif len(issues) == 1 and pvt_passed:
            status = "Índice de Validade Adequado com Pequenos Desvios"
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
        cls, composite_iq: int, domains: Dict[str, Any],
        fen: Dict[str, Any], flex: Dict[str, Any], val: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Gera a síntese qualitativa e interpretativa sobre a mente superdotada avaliada"""
        obs = []
        strengths = []
        challenges = []

        # Raciocínio Fluido & Abstração
        gf_iq = domains.get("Gf (Raciocínio Fluido)", {}).get("estimated_iq", 100)
        if gf_iq >= 125:
            strengths.append("Capacidade excepcional de abstração visual, indução lógica e reconhecimento veloz de regras matriciais (Gf).")
        
        # Memória Operacional
        gwm_iq = domains.get("Gwm (Memória Operacional)", {}).get("estimated_iq", 100)
        if gwm_iq >= 125:
            strengths.append("Elevada capacidade de sustentação ativa e manipulação visuoespacial de dados em memória de trabalho (Gwm).")

        # Flexibilidade
        if flex.get("flexibility_rating") == "Alta":
            strengths.append("Alta flexibilidade cognitiva e rapidez no desengajamento de regras antigas frente a novos contextos (WCST).")
        else:
            challenges.append("Tendência à perseveração conceitual inicial antes de reorganizar o modelo mental.")

        # Hiperexcitabilidades de Dabrowski
        oe = fen.get("overexcitabilities", {})
        top_oe = sorted(oe.items(), key=lambda x: x[1], reverse=True)
        predominant_oe = [k for k, v in top_oe if v >= 3.8]

        avg_fen = fen.get("averages", {})
        if avg_fen.get("aprendizado", 1.0) >= 4.0:
            obs.append("Padrão de hiperfoco autodidata acentuado com desmotivação/tédio intenso diante de repetições lineares.")
        
        if avg_fen.get("paralisia", 1.0) >= 3.8:
            challenges.append("Risco elevado de paralisia por análise e perfeccionismo gerado pela antecipação exaustiva de variáveis.")

        if avg_fen.get("discronia", 1.0) >= 3.8:
            challenges.append("Sensação evidente de discronia interna (desenvolvimento cognitivo avançando muito além do suporte emocional/social).")

        if avg_fen.get("comunicacao", 1.0) >= 3.8:
            challenges.append("Sensação frequente de operar em frequência distinta, com sobrecarga para traduzir pensamentos holísticos em linguagem linear cadenciada.")

        # Conclusão clínica sintética
        if composite_iq >= 130:
            profile_title = "Perfil Compatível com Altas Habilidades / Superdotação (AH/SD)"
            description = (
                "O desempenho nos domínios neurocognitivos e as respostas na escala de rastreio fenomenológico "
                "apresentam fortes marcadores da arquitetura da mente superdotada: alta velocidade associativa, "
                "hiperexcitabilidade evidente e pensamento holístico/em árvore com grande capacidade de síntese."
            )
        elif composite_iq >= 120:
            profile_title = "Perfil Cognitivo Superior com Destaques Específicos"
            description = (
                "Identificam-se habilidades cognitivas acima da média populacional, com bom desempenho em abstração "
                "e traços característicos de curiosidade voraz e intensidade de processamento."
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
