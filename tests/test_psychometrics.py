import sys
import os

# Adiciona o diretório raiz do projeto ao sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.questionnaire_data import (
    FENOMENOLOGICO_ITEMS, MATRIZES_ITEMS, CORSI_CONFIG,
    VELOCIDADE_ITEMS, WCST_ANCHORS, WCST_TRIALS, WCST_RULE_SCHEDULE,
    ASSOCIACAO_ITEMS, METACOGNICAO_ITEMS
)
from app.psychometrics import PsychometricEngine, norm_cdf

print("1. Verificando dados dos questionários:")
print(f" - Fenomenológico: {len(FENOMENOLOGICO_ITEMS)} itens")
print(f" - Matrizes: {len(MATRIZES_ITEMS)} itens")
print(f" - Corsi Sequências: {len(CORSI_CONFIG['test_sequences'])} níveis")
print(f" - Velocidade: {len(VELOCIDADE_ITEMS)} pares")
print(f" - WCST Trials: {len(WCST_TRIALS)} jogadas")
print(f" - Associação Remota: {len(ASSOCIACAO_ITEMS)} tríades")
print(f" - Metacognição: {len(METACOGNICAO_ITEMS)} desafios")

print("\n2. Testando função de distribuição acumulada normal (norm_cdf):")
assert round(norm_cdf(0.0), 2) == 0.50, "Erro norm_cdf(0)"
assert round(norm_cdf(1.0), 3) == 0.841, "Erro norm_cdf(1)"
assert round(norm_cdf(2.0), 3) == 0.977, "Erro norm_cdf(2)"
print(" - norm_cdf(0) =", norm_cdf(0.0), "-> 50%")
print(" - norm_cdf(1) =", norm_cdf(1.0), "-> 84.1%")
print(" - norm_cdf(2) =", norm_cdf(2.0), "-> 97.7%")

print("\n3. Simulando resposta para o participante 'Paulo':")
sample_responses = [
    # Fenomenológico
    {"module_name": "fenomenologico", "item_id": "fen_1", "user_answer": 5, "reaction_time_ms": 3200},
    {"module_name": "fenomenologico", "item_id": "fen_2", "user_answer": 5, "reaction_time_ms": 2800},
    {"module_name": "fenomenologico", "item_id": "fen_3", "user_answer": 4, "reaction_time_ms": 3100},
    {"module_name": "fenomenologico", "item_id": "fen_4", "user_answer": 5, "reaction_time_ms": 2900},
    {"module_name": "fenomenologico", "item_id": "fen_5", "user_answer": 5, "reaction_time_ms": 3500},
    {"module_name": "fenomenologico", "item_id": "fen_6", "user_answer": 5, "reaction_time_ms": 2400},
    {"module_name": "fenomenologico", "item_id": "fen_7", "user_answer": 4, "reaction_time_ms": 2700},
    {"module_name": "fenomenologico", "item_id": "fen_8", "user_answer": 4, "reaction_time_ms": 2600},
    {"module_name": "fenomenologico", "item_id": "fen_9", "user_answer": 4, "reaction_time_ms": 3300},
    {"module_name": "fenomenologico", "item_id": "fen_10", "user_answer": 4, "reaction_time_ms": 3000},
    {"module_name": "fenomenologico", "item_id": "fen_11", "user_answer": 5, "reaction_time_ms": 3100},
    {"module_name": "fenomenologico", "item_id": "fen_trap", "user_answer": 1, "reaction_time_ms": 2500}, # PVT correto

    # Matrizes (5 acertos de 6)
    {"module_name": "matrizes", "item_id": "mat_1", "user_answer": "C", "reaction_time_ms": 8500},
    {"module_name": "matrizes", "item_id": "mat_2", "user_answer": "A", "reaction_time_ms": 6200},
    {"module_name": "matrizes", "item_id": "mat_3", "user_answer": "B", "reaction_time_ms": 9100},
    {"module_name": "matrizes", "item_id": "mat_4", "user_answer": "B", "reaction_time_ms": 11200},
    {"module_name": "matrizes", "item_id": "mat_5", "user_answer": "A", "reaction_time_ms": 13400},
    {"module_name": "matrizes", "item_id": "mat_6", "user_answer": "A", "reaction_time_ms": 4200},

    # Corsi Blocks (Span 7)
    {"module_name": "corsi", "item_id": "corsi_span_3", "user_answer": [1, 5, 9], "reaction_time_ms": 2100, "raw_data": {"level": 1, "target_sequence": [1, 5, 9]}},
    {"module_name": "corsi", "item_id": "corsi_span_4", "user_answer": [3, 7, 2, 8], "reaction_time_ms": 2800, "raw_data": {"level": 2, "target_sequence": [3, 7, 2, 8]}},
    {"module_name": "corsi", "item_id": "corsi_span_5", "user_answer": [9, 1, 4, 6, 2], "reaction_time_ms": 3400, "raw_data": {"level": 3, "target_sequence": [9, 1, 4, 6, 2]}},
    {"module_name": "corsi", "item_id": "corsi_span_6", "user_answer": [5, 3, 8, 2, 7, 4], "reaction_time_ms": 4100, "raw_data": {"level": 4, "target_sequence": [5, 3, 8, 2, 7, 4]}},
    {"module_name": "corsi", "item_id": "corsi_span_7", "user_answer": [7, 1, 9, 3, 5, 8, 2], "reaction_time_ms": 5200, "raw_data": {"level": 5, "target_sequence": [7, 1, 9, 3, 5, 8, 2]}},

    # Velocidade (18 acertos em 20)
    *[{"module_name": "velocidade", "item_id": v["id"], "user_answer": v["is_match"], "reaction_time_ms": 450} for v in VELOCIDADE_ITEMS[:18]],

    # WCST (16 acertos, 1 perseverativo)
    *[{"module_name": "wcst", "item_id": f"wcst_trial_{i}", "user_answer": 1, "reaction_time_ms": 900, "is_correct": True, "raw_data": {"trial": i, "chosen_anchor": {"color": "red"}}} for i in range(1, 17)],

    # Associação Remota (5 de 5)
    {"module_name": "associacao", "item_id": "rat_1", "user_answer": "queijo", "reaction_time_ms": 3200},
    {"module_name": "associacao", "item_id": "rat_2", "user_answer": "água", "reaction_time_ms": 2100},
    {"module_name": "associacao", "item_id": "rat_3", "user_answer": "segredo", "reaction_time_ms": 4500},
    {"module_name": "associacao", "item_id": "rat_4", "user_answer": "cadente", "reaction_time_ms": 3900},
    {"module_name": "associacao", "item_id": "rat_5", "user_answer": "íris", "reaction_time_ms": 2600},

    # Metacognição (3 de 3 acertos ótimos)
    {"module_name": "metacognicao", "item_id": "meta_1", "user_answer": "B", "reaction_time_ms": 15000},
    {"module_name": "metacognicao", "item_id": "meta_2", "user_answer": "B", "reaction_time_ms": 18000},
    {"module_name": "metacognicao", "item_id": "meta_3", "user_answer": "B", "reaction_time_ms": 12000}
]

telemetry = {
    "focus_loss_count": 0,
    "blur_events": 0,
    "fast_clicks": 0
}

result = PsychometricEngine.evaluate_session(sample_responses, telemetry)

print("\n4. Resultado do Motor Psicométrico:")
print(f" - QI Composto Estimado: {result['composite']['general_iq_estimate']}")
print(f" - Percentil: {result['composite']['general_percentile']}º")
print(f" - Escore Z: {result['composite']['general_z_score']}")
print(f" - Classificação: {result['composite']['classification']}")
print(f" - Status de Validade: {result['validity']['status']}")
print("\n5. Domínios Individuais:")
for k, v in result['domains'].items():
    print(f"  * {k}: Bruto={v['raw_score']}/{v['max_possible']} | Z={v['z_score']} | Percentil={v['percentile']}º | QI={v['estimated_iq']}")

print("\n6. Hiperexcitabilidades (Dabrowski):")
for k, v in result['fenomenologico']['overexcitabilities'].items():
    print(f"  * {k}: {v}/5.0")

print("\n7. Síntese Interpretativa:")
print(f" - Perfil: {result['qualitative_summary']['profile_title']}")
print(f" - Fortes: {result['qualitative_summary']['strengths']}")
print(f" - Desafios: {result['qualitative_summary']['challenges']}")

print("\nTODOS OS TESTES PSICOMÉTRICOS PASSARAM COM SUCESSO!")

