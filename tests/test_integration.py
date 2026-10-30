import sys
import os
import json

os.environ["DATABASE_URL"] = "sqlite:///./data/test_ahsd.db"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine

Base.metadata.create_all(bind=engine)
client = TestClient(app)

print("--- INICIANDO TESTES DE INTEGRACAO DA API ---")

# 1. Healthcheck
res = client.get("/api/health")
assert res.status_code == 200, f"Healthcheck falhou: {res.text}"
print("[OK] [1/9] Healthcheck OK:", res.json())

# 2. Criar Projeto "Teste 1"
res = client.post("/api/projects", json={
    "name": "Teste 1",
    "description": "Primeira rodada de testagem AH/SD"
})
assert res.status_code == 200, f"Erro ao criar projeto: {res.text}"
project = res.json()
project_id = project["id"]
print(f"[OK] [2/9] Projeto criado com sucesso: ID={project_id}, Nome={project['name']}")

# 3. Listar Projetos
res = client.get("/api/projects")
assert res.status_code == 200
projects = res.json()
assert len(projects) >= 1
print(f"[OK] [3/9] Listagem de projetos OK: {len(projects)} projeto(s) encontrado(s)")

# 4. Criar Participante "Paulo" dentro do projeto "Teste 1"
res = client.post(f"/api/projects/{project_id}/participants", json={
    "name": "Paulo",
    "age": 32,
    "education_level": "Superior Completo",
    "notes": "Avaliacao voluntaria de perfil cognitivo"
})
assert res.status_code == 200, f"Erro ao criar participante: {res.text}"
part_data = res.json()
session_id = part_data["session_id"]
participant_name = part_data["participant"]["name"]
print(f"[OK] [4/9] Participante criado e vinculado ao projeto: Nome='{participant_name}', Sessao ID={session_id}")

# 5. Obter itens do modulo sem expor gabarito
res = client.get(f"/api/sessions/{session_id}/module/matrizes")
assert res.status_code == 200
matrix_data = res.json()
assert len(matrix_data["items"]) > 0
for m in matrix_data["items"]:
    assert "correct_id" not in m, "GABARITO VAZOU NO FRONTEND!"
print("[OK] [5/9] Entrega de estimulos sanitizada (Gabarito 100% isolado no backend)")

# 6. Testar checagem interativa do WCST
res = client.post(f"/api/sessions/{session_id}/wcst_check", json={
    "trial": 1,
    "anchor_id": 1
})
assert res.status_code == 200
wcst_feedback = res.json()
print("[OK] [6/9] WCST Feedback interativo:", wcst_feedback)

# 7. Submeter respostas do modulo fenomenologico
sample_fen_resp = [
    {"item_id": "fen_1", "user_answer": 5, "reaction_time_ms": 2800},
    {"item_id": "fen_2", "user_answer": 5, "reaction_time_ms": 2500},
    {"item_id": "fen_3", "user_answer": 4, "reaction_time_ms": 3100},
    {"item_id": "fen_4", "user_answer": 5, "reaction_time_ms": 2900},
    {"item_id": "fen_5", "user_answer": 5, "reaction_time_ms": 3200},
    {"item_id": "fen_6", "user_answer": 5, "reaction_time_ms": 2400},
    {"item_id": "fen_7", "user_answer": 4, "reaction_time_ms": 2700},
    {"item_id": "fen_8", "user_answer": 4, "reaction_time_ms": 2600},
    {"item_id": "fen_9", "user_answer": 4, "reaction_time_ms": 3300},
    {"item_id": "fen_10", "user_answer": 4, "reaction_time_ms": 3000},
    {"item_id": "fen_11", "user_answer": 5, "reaction_time_ms": 3100},
    {"item_id": "fen_trap", "user_answer": 1, "reaction_time_ms": 2500}
]
res = client.post(f"/api/sessions/{session_id}/module/fenomenologico/submit", json={
    "responses": sample_fen_resp,
    "telemetry": {"focus_loss_count": 0, "blur_events": 0, "fast_clicks": 0}
})
assert res.status_code == 200
print("[OK] [7/9] Submissao de modulo e telemetria gravados com sucesso")

# 8. Finalizar sessao e gerar laudo psicometrico
res = client.post(f"/api/sessions/{session_id}/complete", json={})
assert res.status_code == 200
comp_data = res.json()
print("[OK] [8/9] Sessao completada com sucesso:", comp_data)

# 9. Consultar laudo persistido
res = client.get(f"/api/sessions/{session_id}/report")
assert res.status_code == 200
report = res.json()
assert report["participant"]["name"] == "Paulo"
assert "results" in report
assert "composite" in report["results"]
print(f"[OK] [9/9] Consulta do Laudo Persistido:")
print(f"  - Participante: {report['participant']['name']}")
print(f"  - Projeto: {report['project_name']}")
print(f"  - QI Composto Estimado: {report['results']['composite']['general_iq_estimate']}")
print(f"  - Percentil: {report['results']['composite']['general_percentile']}%")
print(f"  - Classificacao: {report['results']['composite']['classification']}")
print(f"  - Hiperexcitabilidades Mapeadas: {list(report['results']['fenomenologico']['overexcitabilities'].keys())}")

print("\n--- TODOS OS 9 TESTES DE INTEGRACAO PASSARAM COM 100% DE SUCESSO! ---")
