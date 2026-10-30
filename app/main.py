import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import engine, Base, get_db
from .models import Project, Participant, TestSession, TestResponse
from .schemas import (
    ProjectCreate, ProjectOut, ParticipantCreate, ParticipantOut,
    TestSessionOut, ModuleSubmitRequest, SessionCompleteRequest
)
from .questionnaire_data import (
    FENOMENOLOGICO_ITEMS, MATRIZES_ITEMS, CORSI_CONFIG,
    VELOCIDADE_ITEMS, WCST_ANCHORS, WCST_TRIALS, WCST_RULE_SCHEDULE,
    ASSOCIACAO_ITEMS, METACOGNICAO_ITEMS
)
from .psychometrics import PsychometricEngine

# Inicializa as tabelas do banco de dados SQLite
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Plataforma de Avaliação Neurocognitiva AH/SD",
    description="Sistema Psicométrico Computadorizado para Mente Superdotada",
    version="1.1.0"
)

# Habilita CORS para ambientes de desenvolvimento e integração
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Caminho dos arquivos estáticos
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ----------------- ROTAS DAS PÁGINAS HTML -----------------

@app.get("/")
def serve_home():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/test/{session_id}")
def serve_test_runner(session_id: int):
    return FileResponse(os.path.join(STATIC_DIR, "test_runner.html"))

@app.get("/report/{session_id}")
def serve_report(session_id: int):
    return FileResponse(os.path.join(STATIC_DIR, "report.html"))

@app.get("/api/health")
def healthcheck():
    return {"status": "ok", "service": "ahsd-assessment-engine", "time": datetime.utcnow().isoformat()}

# ----------------- ROTAS DE PROJETOS -----------------

@app.get("/api/projects", response_model=List[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    results = []
    for p in projects:
        results.append(ProjectOut(
            id=p.id,
            name=p.name,
            description=p.description,
            created_at=p.created_at,
            status=p.status,
            participant_count=len(p.participants),
            session_count=len(p.sessions)
        ))
    return results

@app.post("/api/projects", response_model=ProjectOut)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(
        name=data.name.strip(),
        description=data.description.strip() if data.description else ""
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return ProjectOut(
        id=project.id,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
        status=project.status,
        participant_count=0,
        session_count=0
    )

@app.get("/api/projects/{project_id}")
def get_project_details(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    sessions_data = []
    for s in project.sessions:
        p = s.participant
        sessions_data.append({
            "id": s.id,
            "participant_id": s.participant_id,
            "participant_name": p.name if p else "Anônimo",
            "age": p.age if p else None,
            "education_level": p.education_level if p else None,
            "status": s.status,
            "current_module": s.current_module,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            "duration_seconds": s.duration_seconds,
            "results_summary": s.get_results_summary()
        })

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "created_at": project.created_at.isoformat(),
        "status": project.status,
        "sessions": sessions_data
    }

@app.delete("/api/projects/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    db.delete(project)
    db.commit()
    return {"message": "Projeto excluído com sucesso"}

# ----------------- ROTAS DE PARTICIPANTES E TESTES -----------------

@app.post("/api/projects/{project_id}/participants")
def create_participant_and_session(
    project_id: int, data: ParticipantCreate, db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    participant = Participant(
        project_id=project_id,
        name=data.name.strip(),
        age=data.age,
        education_level=data.education_level,
        notes=data.notes
    )
    db.add(participant)
    db.commit()
    db.refresh(participant)

    # Cria a sessão de teste atribuída ao participante
    session = TestSession(
        project_id=project_id,
        participant_id=participant.id,
        status="not_started",
        current_module="fenomenologico",
        validity_data=json.dumps({"focus_loss_count": 0, "blur_events": 0, "fast_clicks": 0})
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "participant": {
            "id": participant.id,
            "name": participant.name,
            "project_id": participant.project_id
        },
        "session_id": session.id
    }

@app.get("/api/sessions/{session_id}")
def get_session_info(session_id: int, db: Session = Depends(get_db)):
    session = db.query(TestSession).filter(TestSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão de teste não encontrada")

    return {
        "id": session.id,
        "project_id": session.project_id,
        "project_name": session.project.name if session.project else "",
        "participant_id": session.participant_id,
        "participant_name": session.participant.name if session.participant else "Participante",
        "age": session.participant.age if session.participant else None,
        "education_level": session.participant.education_level if session.participant else "",
        "status": session.status,
        "current_module": session.current_module,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        "results_summary": session.get_results_summary()
    }

@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(TestSession).filter(TestSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    db.delete(session)
    db.commit()
    return {"message": "Sessão excluída com sucesso"}

# ----------------- ENTREGA DE ITENS SEM EXPOR GABARITO -----------------

@app.get("/api/sessions/{session_id}/module/{module_name}")
def get_module_stimuli(session_id: int, module_name: str, db: Session = Depends(get_db)):
    """
    Retorna os estímulos do módulo sanitizados (sem gabarito ou chaves secretas).
    """
    session = db.query(TestSession).filter(TestSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    if session.status == "not_started":
        session.status = "in_progress"
        session.started_at = datetime.utcnow()
        db.commit()

    if module_name == "fenomenologico":
        # Itens da escala Likert (1 a 5)
        return {"module": "fenomenologico", "title": "Rastreio Qualitativo de Padrões e Vivências (Dabrowski & Estilo Cognitivo)", "items": FENOMENOLOGICO_ITEMS}

    elif module_name == "matrizes":
        # Remove correct_id do frontend
        sanitized_matrices = []
        for m in MATRIZES_ITEMS:
            sanitized_matrices.append({
                "id": m["id"],
                "difficulty": m["difficulty"],
                "rule_type": m["rule_type"],
                "description": m["description"],
                "grid": m["grid"],
                "options": m["options"]
            })
        return {"module": "matrizes", "title": "Raciocínio Fluido (Gf) - Matrizes Progressivas Não-Verbais", "items": sanitized_matrices}

    elif module_name == "corsi":
        return {
            "module": "corsi",
            "title": "Memória Operacional (Gwm) - Span Visuoespacial (Corsi Blocks)",
            "config": CORSI_CONFIG
        }

    elif module_name == "velocidade":
        # Remove is_match do frontend
        sanitized_vel = [{"id": v["id"], "pair": v["pair"]} for v in VELOCIDADE_ITEMS]
        return {
            "module": "velocidade",
            "title": "Velocidade de Processamento (Gs) - Pareamento de Símbolos",
            "items": sanitized_vel,
            "duration_seconds": 45
        }

    elif module_name == "wcst":
        # Retorna cartas de referência e sequência de testes (sem expor a regra ativa)
        return {
            "module": "wcst",
            "title": "Flexibilidade Cognitiva - Adaptação de Regras (WCST Digital)",
            "anchors": WCST_ANCHORS,
            "trials": WCST_TRIALS
        }

    elif module_name == "associacao":
        # Remove accepted_answers do frontend
        sanitized_rat = [{"id": a["id"], "words": a["words"], "hint": a["hint"]} for a in ASSOCIACAO_ITEMS]
        return {
            "module": "associacao",
            "title": "Pensamento Divergente / Associação Remota Estruturada (RAT)",
            "items": sanitized_rat
        }

    elif module_name == "metacognicao":
        # Remove correct_id e rationale_optimal do frontend
        sanitized_meta = []
        for m in METACOGNICAO_ITEMS:
            sanitized_meta.append({
                "id": m["id"],
                "title": m["title"],
                "prompt": m["prompt"],
                "options": m["options"]
            })
        return {
            "module": "metacognicao",
            "title": "Metacognição, Pensamento Lateral e Modelagem em Rede",
            "items": sanitized_meta
        }
    else:
        raise HTTPException(status_code=400, detail="Módulo desconhecido")

# Rota interativa de feedback do WCST (computa se a carta combinou com a regra ativa sem expor a regra)
@app.post("/api/sessions/{session_id}/wcst_check")
def check_wcst_move(session_id: int, payload: Dict[str, Any]):
    trial_num = int(payload.get("trial", 1))
    anchor_id = int(payload.get("anchor_id", 1))

    # Determina a regra ativa para a jogada
    active_rule = "color"
    for s in WCST_RULE_SCHEDULE:
        if s["start"] <= trial_num <= s["end"]:
            active_rule = s["rule"]
            break

    # Pega a carta atual do trial
    trial_data = next((t for t in WCST_TRIALS if t["trial"] == trial_num), None)
    card = trial_data["card"] if trial_data else {}
    anchor = next((a for a in WCST_ANCHORS if a["anchor_id"] == anchor_id), None)

    is_correct = False
    if anchor and card:
        if active_rule == "color" and anchor["color"] == card["color"]:
            is_correct = True
        elif active_rule == "shape" and anchor["shape"] == card["shape"]:
            is_correct = True
        elif active_rule == "count" and anchor["count"] == card["count"]:
            is_correct = True

    return {
        "trial": trial_num,
        "is_correct": is_correct,
        "feedback_text": "Correto" if is_correct else "Incorreto"
    }

# ----------------- SUBMISSÃO DE RESPOSTAS E TELEMETRIA -----------------

@app.post("/api/sessions/{session_id}/module/{module_name}/submit")
def submit_module_responses(
    session_id: int, module_name: str, payload: ModuleSubmitRequest, db: Session = Depends(get_db)
):
    session = db.query(TestSession).filter(TestSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    # Remove respostas antigas desse módulo se houver (para evitar duplicidade em repetição)
    db.query(TestResponse).filter(
        TestResponse.session_id == session_id,
        TestResponse.module_name == module_name
    ).delete()

    # Salva cada resposta
    for item in payload.responses:
        # Se for WCST ou boolean, processa
        is_corr = None
        if item.raw_data and "is_correct" in item.raw_data:
            is_corr = item.raw_data["is_correct"]

        resp_record = TestResponse(
            session_id=session_id,
            module_name=module_name,
            item_id=item.item_id,
            user_answer=str(item.user_answer) if item.user_answer is not None else "",
            reaction_time_ms=item.reaction_time_ms,
            is_correct=is_corr,
            raw_data=json.dumps(item.raw_data, ensure_ascii=False) if item.raw_data else None
        )
        db.add(resp_record)

    # Atualiza telemetria da sessão
    current_val = session.get_validity_data()
    if payload.telemetry:
        current_val["focus_loss_count"] = current_val.get("focus_loss_count", 0) + payload.telemetry.get("focus_loss_count", 0)
        current_val["blur_events"] = current_val.get("blur_events", 0) + payload.telemetry.get("blur_events", 0)
        current_val["fast_clicks"] = current_val.get("fast_clicks", 0) + payload.telemetry.get("fast_clicks", 0)
        current_val["active_time_ms"] = current_val.get("active_time_ms", 0.0) + payload.telemetry.get("active_time_ms", 0.0)
        current_val["idle_time_ms"] = current_val.get("idle_time_ms", 0.0) + payload.telemetry.get("idle_time_ms", 0.0)
        
        # Concatena lista de eventos de pausa
        if "pause_events" in payload.telemetry and isinstance(payload.telemetry["pause_events"], list):
            existing_pauses = current_val.get("pause_events", [])
            existing_pauses.extend(payload.telemetry["pause_events"])
            current_val["pause_events"] = existing_pauses

    session.set_validity_data(current_val)

    # Atualiza módulo corrente
    next_modules = {
        "fenomenologico": "matrizes",
        "matrizes": "corsi",
        "corsi": "velocidade",
        "velocidade": "wcst",
        "wcst": "associacao",
        "associacao": "metacognicao",
        "metacognicao": "completed"
    }
    session.current_module = next_modules.get(module_name, "completed")
    db.commit()

    return {
        "message": f"Módulo {module_name} gravado com sucesso",
        "next_module": session.current_module
    }

# ----------------- REAPLICAÇÃO DE SUBTESTE ISOLADO -----------------

@app.post("/api/sessions/{session_id}/module/{module_name}/reset")
def reset_session_module(session_id: int, module_name: str, db: Session = Depends(get_db)):
    session = db.query(TestSession).filter(TestSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    # Limpa as respostas anteriores desse módulo específico
    deleted_count = db.query(TestResponse).filter(
        TestResponse.session_id == session_id,
        TestResponse.module_name == module_name
    ).delete()

    session.current_module = module_name
    session.status = "in_progress"
    db.commit()

    return {
        "message": f"Módulo {module_name} resetado com sucesso. Respostas limpas: {deleted_count}",
        "session_id": session.id,
        "module_name": module_name,
        "redirect_url": f"/test/{session.id}"
    }

# ----------------- FINALIZAÇÃO E GERAÇÃO DE LAUDO -----------------

@app.post("/api/sessions/{session_id}/complete")
def complete_session(session_id: int, payload: Optional[SessionCompleteRequest] = None, db: Session = Depends(get_db)):
    session = db.query(TestSession).filter(TestSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    session.status = "completed"
    session.completed_at = datetime.utcnow()
    if session.started_at:
        session.duration_seconds = (session.completed_at - session.started_at).total_seconds()

    # Coleta todas as respostas gravadas
    responses = db.query(TestResponse).filter(TestResponse.session_id == session_id).all()
    resp_dicts = []
    for r in responses:
        raw = {}
        if r.raw_data:
            try:
                raw = json.loads(r.raw_data)
            except Exception:
                pass
        resp_dicts.append({
            "module_name": r.module_name,
            "item_id": r.item_id,
            "user_answer": r.user_answer,
            "reaction_time_ms": r.reaction_time_ms,
            "is_correct": r.is_correct,
            "raw_data": raw
        })

    # Executa o Motor Psicométrico
    telemetry = session.get_validity_data()
    results = PsychometricEngine.evaluate_session(resp_dicts, telemetry)
    session.set_results_summary(results)

    db.commit()
    return {"message": "Teste concluído e laudo gerado com sucesso", "report_url": f"/report/{session.id}"}

@app.get("/api/sessions/{session_id}/report")
def get_session_report(session_id: int, db: Session = Depends(get_db)):
    session = db.query(TestSession).filter(TestSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    summary = session.get_results_summary()
    if not summary and session.responses:
        # Se ainda não foi finalizado formalmente, processa sob demanda
        resp_dicts = []
        for r in session.responses:
            raw = {}
            if r.raw_data:
                try:
                    raw = json.loads(r.raw_data)
                except Exception:
                    pass
            resp_dicts.append({
                "module_name": r.module_name,
                "item_id": r.item_id,
                "user_answer": r.user_answer,
                "reaction_time_ms": r.reaction_time_ms,
                "is_correct": r.is_correct,
                "raw_data": raw
            })
        summary = PsychometricEngine.evaluate_session(resp_dicts, session.get_validity_data())
        session.set_results_summary(summary)
        db.commit()

    return {
        "session_id": session.id,
        "project_name": session.project.name if session.project else "Geral",
        "participant": {
            "name": session.participant.name if session.participant else "Paulo",
            "age": session.participant.age if session.participant else None,
            "education_level": session.participant.education_level if session.participant else "",
            "notes": session.participant.notes if session.participant else ""
        },
        "status": session.status,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        "duration_minutes": round(session.duration_seconds / 60, 1) if session.duration_seconds else 0,
        "results": summary
    }
