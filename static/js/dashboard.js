// dashboard.js - Lógica de Projetos e Participantes

document.addEventListener("DOMContentLoaded", () => {
  loadProjects();
});

async function loadProjects() {
  const container = document.getElementById("projectsList");
  const countLabel = document.getElementById("projectsCount");
  container.innerHTML = `<div style="text-align: center; padding: 2rem; color: var(--text-muted);">Carregando projetos...</div>`;

  try {
    const res = await fetch("/api/projects");
    const projects = await res.json();
    countLabel.textContent = `${projects.length} projeto(s) cadastrado(s)`;

    if (projects.length === 0) {
      container.innerHTML = `
        <div style="background-color: var(--bg-surface); border: 1px dashed var(--border-subtle); border-radius: var(--radius-md); padding: 3rem; text-align: center;">
          <h4 style="margin-bottom: 0.5rem;">Nenhum projeto encontrado</h4>
          <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">Crie seu primeiro projeto para organizar os testes e participantes (ex.: "Teste 1").</p>
          <button class="btn btn-primary" onclick="openNewProjectModal()">+ Criar Primeiro Projeto</button>
        </div>
      `;
      return;
    }

    container.innerHTML = "";
    for (const p of projects) {
      // Carrega os detalhes do projeto com participantes e sessões
      const detRes = await fetch(`/api/projects/${p.id}`);
      const projectDetails = await detRes.json();
      renderProjectCard(projectDetails, container);
    }
  } catch (err) {
    console.error("Erro ao carregar projetos:", err);
    container.innerHTML = `<div style="color: var(--accent-rose); padding: 1rem;">Erro ao conectar ao servidor. Verifique se o container está ativo.</div>`;
  }
}

function renderProjectCard(proj, container) {
  const card = document.createElement("div");
  card.className = "project-card";

  const dateStr = new Date(proj.created_at).toLocaleDateString("pt-BR", {
    day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit"
  });

  const sessions = proj.sessions || [];

  let sessionsHtml = "";
  if (sessions.length === 0) {
    sessionsHtml = `
      <div style="padding: 1rem; color: var(--text-muted); font-size: 0.9rem; font-style: italic;">
        Nenhum participante ou teste registrado neste projeto ainda.
      </div>
    `;
  } else {
    sessionsHtml = sessions.map(s => {
      let badgeClass = "badge-not_started";
      let statusLabel = "Não Iniciado";
      let actionBtn = `<a href="/test/${s.id}" class="btn btn-primary" style="padding: 0.4rem 0.8rem; font-size: 0.85rem;">Iniciar Teste</a>`;

      if (s.status === "in_progress") {
        badgeClass = "badge-in_progress";
        statusLabel = "Em Andamento";
        actionBtn = `<a href="/test/${s.id}" class="btn btn-secondary" style="padding: 0.4rem 0.8rem; font-size: 0.85rem;">Continuar</a>`;
      } else if (s.status === "completed") {
        badgeClass = "badge-completed";
        statusLabel = "Concluído";
        const iq = s.results_summary?.composite?.general_iq_estimate || "—";
        actionBtn = `
          <span style="font-weight: 700; color: var(--accent-cyan); font-size: 0.9rem; margin-right: 0.5rem;">QI Est: ${iq}</span>
          <a href="/report/${s.id}" class="btn btn-primary" style="padding: 0.4rem 0.8rem; font-size: 0.85rem; background: #059669;">Ver Laudo</a>
        `;
      }

      return `
        <div class="participant-item">
          <div class="participant-info">
            <h4>
              👤 ${escapeHtml(s.participant_name)}
              <span class="badge ${badgeClass}">${statusLabel}</span>
            </h4>
            <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.25rem;">
              ${s.age ? `Idade: ${s.age} anos • ` : ""}${s.education_level ? `Escolaridade: ${escapeHtml(s.education_level)} • ` : ""}
              Módulo: <code>${s.current_module}</code>
            </div>
          </div>
          <div class="participant-actions">
            ${actionBtn}
            <button class="btn btn-danger" style="padding: 0.4rem 0.6rem; font-size: 0.8rem;" onclick="deleteSession(${s.id})">✕</button>
          </div>
        </div>
      `;
    }).join("");
  }

  card.innerHTML = `
    <div class="project-top">
      <div>
        <div class="project-title">📁 ${escapeHtml(proj.name)}</div>
        ${proj.description ? `<div class="project-desc">${escapeHtml(proj.description)}</div>` : ""}
        <div class="project-meta">
          <span>Criado em: ${dateStr}</span>
          <span>•</span>
          <span>${sessions.length} teste(s) registrado(s)</span>
        </div>
      </div>
      <div style="display: flex; gap: 0.5rem;">
        <button class="btn btn-primary" style="padding: 0.4rem 0.9rem; font-size: 0.85rem;" onclick="openNewParticipantModal(${proj.id})">
          + Novo Teste / Participante
        </button>
        <button class="btn btn-danger" style="padding: 0.4rem 0.6rem; font-size: 0.85rem;" onclick="deleteProject(${proj.id})">
          Excluir
        </button>
      </div>
    </div>

    <div style="margin-top: 1rem; border-top: 1px solid var(--border-subtle); padding-top: 0.75rem;">
      <h5 style="font-size: 0.85rem; color: var(--text-secondary); text-transform: uppercase; margin-bottom: 0.5rem;">Participantes & Testes Atribuídos</h5>
      <div class="participants-list">
        ${sessionsHtml}
      </div>
    </div>
  `;

  container.appendChild(card);
}

// Modais
function openNewProjectModal() {
  document.getElementById("projName").value = "";
  document.getElementById("projDesc").value = "";
  document.getElementById("projectModal").style.display = "flex";
  document.getElementById("projName").focus();
}

function openNewParticipantModal(projectId) {
  document.getElementById("modalProjectId").value = projectId;
  document.getElementById("partName").value = "";
  document.getElementById("partAge").value = "";
  document.getElementById("partEdu").value = "";
  document.getElementById("partNotes").value = "";
  document.getElementById("participantModal").style.display = "flex";
  document.getElementById("partName").focus();
}

function closeModal(modalId) {
  document.getElementById(modalId).style.display = "none";
}

// Handlers de criação
async function handleCreateProject(e) {
  e.preventDefault();
  const name = document.getElementById("projName").value.trim();
  const description = document.getElementById("projDesc").value.trim();

  if (!name) return;

  try {
    const res = await fetch("/api/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, description })
    });
    if (res.ok) {
      closeModal("projectModal");
      loadProjects();
    } else {
      alert("Erro ao criar projeto.");
    }
  } catch (err) {
    console.error(err);
    alert("Erro na requisição.");
  }
}

async function handleCreateParticipant(e) {
  e.preventDefault();
  const projectId = document.getElementById("modalProjectId").value;
  const name = document.getElementById("partName").value.trim();
  const age = document.getElementById("partAge").value ? parseInt(document.getElementById("partAge").value) : null;
  const education_level = document.getElementById("partEdu").value;
  const notes = document.getElementById("partNotes").value.trim();

  if (!name) return;

  try {
    const res = await fetch(`/api/projects/${projectId}/participants`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, age, education_level, notes })
    });

    if (res.ok) {
      const data = await res.json();
      closeModal("participantModal");
      // Redireciona imediatamente para a sessão criada do participante
      window.location.href = `/test/${data.session_id}`;
    } else {
      alert("Erro ao criar participante.");
    }
  } catch (err) {
    console.error(err);
    alert("Erro na requisição.");
  }
}

async function deleteProject(id) {
  if (!confirm("Tem certeza que deseja excluir este projeto e todos os seus testes vinculados?")) return;
  try {
    const res = await fetch(`/api/projects/${id}`, { method: "DELETE" });
    if (res.ok) loadProjects();
  } catch (err) {
    console.error(err);
  }
}

async function deleteSession(id) {
  if (!confirm("Tem certeza que deseja excluir este teste?")) return;
  try {
    const res = await fetch(`/api/sessions/${id}`, { method: "DELETE" });
    if (res.ok) loadProjects();
  } catch (err) {
    console.error(err);
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/[&<>'"]/g, 
    tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
  );
}
