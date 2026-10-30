// report.js - Renderização do Laudo Psicométrico Calibrado com Gráfico Radar e Telemetria de Pausa

let currentSessionId = null;

document.addEventListener("DOMContentLoaded", async () => {
  const pathParts = window.location.pathname.split("/").filter(Boolean);
  currentSessionId = pathParts[pathParts.length - 1];

  try {
    const res = await fetch(`/api/sessions/${currentSessionId}/report`);
    if (!res.ok) {
      alert("Não foi possível carregar o laudo.");
      window.location.href = "/";
      return;
    }
    const data = await res.json();
    renderReport(data);
  } catch (err) {
    console.error("Erro ao carregar laudo:", err);
  }
});

function renderReport(data) {
  const p = data.participant || {};
  const res = data.results || {};
  const comp = res.composite || {};
  const tm = res.time_metrics || {};

  // Cabeçalho
  document.getElementById("participantTitle").textContent = p.name || "Participante";
  document.getElementById("participantMeta").textContent = `
    ${p.age ? `Idade: ${p.age} anos • ` : ""}
    ${p.education_level ? `Escolaridade: ${p.education_level} • ` : ""}
    Projeto: ${data.project_name || "Geral"}
  `;
  document.getElementById("reportDate").textContent = data.completed_at ? new Date(data.completed_at).toLocaleDateString("pt-BR") : "Hoje";
  
  // Tempos de Sessão (Ativo vs Pausa)
  const actMins = tm.active_minutes !== undefined ? tm.active_minutes : (data.duration_minutes || 0);
  const idleMins = tm.idle_minutes !== undefined ? tm.idle_minutes : 0;
  document.getElementById("reportActiveTime").textContent = `${actMins} min`;
  document.getElementById("reportIdleTime").textContent = idleMins > 0 ? `${idleMins} min (${tm.pause_events_count || 0} pausa(s))` : "Sem pausas";
  document.getElementById("reportSessionId").textContent = `#${data.session_id}`;

  // Resumo Geral Convencional
  document.getElementById("statIq").textContent = comp.general_iq_estimate || "—";
  document.getElementById("statClassification").textContent = comp.classification || "—";
  document.getElementById("statPercentile").textContent = `${comp.general_percentile || 0}º`;
  document.getElementById("statZScore").textContent = `${comp.general_z_score > 0 ? '+' : ''}${comp.general_z_score || 0} σ`;

  // Alerta de Dispersão Intra-Individual (Scatter)
  const scatter = res.scatter_analysis;
  if (scatter && scatter.has_scatter) {
    const alertBox = document.getElementById("scatterAlertBox");
    const alertMsg = document.getElementById("scatterAlertMsg");
    if (alertBox && alertMsg) {
      alertBox.style.display = "block";
      alertMsg.innerHTML = `
        <strong>${escapeHtml(scatter.message)}</strong><br>
        <span style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.3rem; display: block;">
          Pico Superior: <strong>${escapeHtml(scatter.max_domain)}</strong> vs Menor Escore: <strong>${escapeHtml(scatter.min_domain)}</strong>.
        </span>
      `;
    }
  }

  // Card do Índice de Aptidão Geral Expurgado (IAG)
  const expComp = res.expurgated_composite;
  if (expComp) {
    const expCard = document.getElementById("expurgatedCard");
    const expIqEl = document.getElementById("statExpurgatedIq");
    const expClassEl = document.getElementById("statExpurgatedClass");
    if (expCard && expIqEl && expClassEl) {
      expCard.style.display = "block";
      expIqEl.textContent = expComp.estimated_iq;
      expClassEl.innerHTML = `
        <span>${escapeHtml(expComp.classification)}</span><br>
        <span style="font-size: 0.75rem; color: var(--text-muted); font-weight: normal;">(Expurga subteste com pausa)</span>
      `;
    }
  }

  // Validade e Auditoria
  const val = res.validity || {};
  const valBadgeEl = document.getElementById("statValidityBadge");
  const valTextEl = document.getElementById("statValidityText");

  if (val.badge === "valid") {
    valBadgeEl.innerHTML = `<span class="badge badge-completed">Ótimo</span>`;
    valTextEl.textContent = "Dados Fidedignos";
  } else if (val.badge === "warning") {
    valBadgeEl.innerHTML = `<span class="badge badge-in_progress">Atenção</span>`;
    valTextEl.textContent = val.has_extended_pause ? "Pausa Externa Detectada" : "Leves Desvios";
  } else {
    valBadgeEl.innerHTML = `<span class="badge" style="background: rgba(244,63,94,0.2); color:#fda4af;">Alerta</span>`;
    valTextEl.textContent = "Possível Ruído";
  }

  // Tabela Normativa por Domínio com Botão de Reaplicação
  const domains = res.domains || {};
  const tbody = document.getElementById("domainsTableBody");
  tbody.innerHTML = "";

  const domainModuleMap = {
    "gf": "matrizes",
    "gwm": "corsi",
    "gs": "velocidade",
    "flexibilidade": "wcst",
    "divergente": "associacao",
    "metacognicao": "metacognicao"
  };

  for (const [domName, d] of Object.entries(domains)) {
    const tr = document.createElement("tr");
    const modKey = domainModuleMap[d.key] || "matrizes";
    
    // Destaque visual para pontos fortes
    const isStrength = d.z_score >= 1.33;
    const isOutlier = d.z_score <= -1.8;

    tr.innerHTML = `
      <td style="font-weight: 600;">
        ${escapeHtml(domName)}
        ${isStrength ? ' <span class="badge" style="background:rgba(56,189,248,0.2); color:#38bdf8; font-size:0.65rem;">DESTAQUE</span>' : ''}
        ${isOutlier ? ' <span class="badge" style="background:rgba(245,158,11,0.2); color:#fbbf24; font-size:0.65rem;">QUEBRA DE RETENÇÃO</span>' : ''}
      </td>
      <td><code>${d.raw_score} / ${d.max_possible}</code></td>
      <td>${d.z_score > 0 ? '+' : ''}${d.z_score}</td>
      <td>${d.t_score}</td>
      <td>${d.percentile}º</td>
      <td style="font-weight: 700; color: ${isStrength ? '#38bdf8' : (isOutlier ? '#fbbf24' : 'var(--text-primary)')};">${d.estimated_iq}</td>
      <td class="no-print">
        <button class="btn btn-secondary" style="padding: 0.25rem 0.6rem; font-size: 0.75rem;" onclick="retestSingleModule('${modKey}', '${escapeHtml(domName)}')">
          🔄 Refazer
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  }

  // Gráfico Radar (Canvas 2D sem corte de texto)
  if (res.radar_chart) {
    drawCalibratedRadarChart("radarChart", res.radar_chart);
  }

  // Hiperexcitabilidades de Dabrowski
  renderOverexcitabilities(res.fenomenologico);

  // Síntese Qualitativa
  const qual = res.qualitative_summary || {};
  document.getElementById("qualitativeTitle").textContent = qual.profile_title || "Perfil Neurocognitivo Mapeado";
  document.getElementById("qualitativeDesc").textContent = qual.description || "";

  const ulStrengths = document.getElementById("qualitativeStrengths");
  ulStrengths.innerHTML = (qual.strengths || []).map(s => `<li>${escapeHtml(s)}</li>`).join("") || "<li>Sem picos extremos na amostragem.</li>";

  const ulChallenges = document.getElementById("qualitativeChallenges");
  ulChallenges.innerHTML = (qual.challenges || []).map(c => `<li>${escapeHtml(c)}</li>`).join("") || "<li>Sem desafios atípicos reportados.</li>";

  // Desafios Metacognitivos
  renderMetacognitionDetails(res.module_details?.metacognicao);

  // Telemetria Detalhada
  renderTelemetry(val, tm);

  // Disclaimer
  if (res.disclaimer) {
    document.getElementById("disclaimerText").textContent = res.disclaimer;
  }
}

// Reaplicar um único módulo
async function retestSingleModule(moduleKey, moduleTitle) {
  if (!confirm(`Deseja limpar as respostas e refazer apenas o subteste de "${moduleTitle}"?\n\nOs outros módulos já concluídos serão preservados e o laudo será recalculado ao finalizar.`)) {
    return;
  }

  try {
    const res = await fetch(`/api/sessions/${currentSessionId}/module/${moduleKey}/reset`, {
      method: "POST"
    });
    if (res.ok) {
      window.location.href = `/test/${currentSessionId}`;
    } else {
      alert("Erro ao reiniciar módulo.");
    }
  } catch (err) {
    console.error(err);
    alert("Falha de conexão com o servidor.");
  }
}

function renderOverexcitabilities(fen) {
  const container = document.getElementById("overexcitabilitiesBars");
  if (!fen || !fen.overexcitabilities) {
    container.innerHTML = `<div style="color: var(--text-muted);">Dados não disponíveis.</div>`;
    return;
  }

  const oe = fen.overexcitabilities;
  let html = "";

  const colorMap = {
    "Intelectual": "#38bdf8",
    "Emocional": "#f43f5e",
    "Imaginativa": "#a855f7",
    "Sensorial": "#f59e0b",
    "Psicomotora": "#10b981"
  };

  for (const [name, score] of Object.entries(oe)) {
    const pct = Math.round((score / 5.0) * 100);
    const color = colorMap[name] || "#0ea5e9";

    html += `
      <div>
        <div style="display: flex; justify-content: space-between; font-size: 0.9rem; margin-bottom: 0.35rem;">
          <span style="font-weight: 600;">Hiperexcitabilidade ${escapeHtml(name)}</span>
          <span style="color: ${color}; font-weight: 700;">${score.toFixed(1)} / 5.0 (${pct}%)</span>
        </div>
        <div style="height: 10px; background: var(--bg-input); border-radius: 999px; overflow: hidden;">
          <div style="height: 100%; width: ${pct}%; background: ${color}; border-radius: 999px;"></div>
        </div>
      </div>
    `;
  }

  const avg = fen.averages || {};
  html += `
    <div style="margin-top: 1.5rem; display: flex; flex-wrap: wrap; gap: 0.75rem;">
      <span class="badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; padding: 0.4rem 0.8rem;">
        Hiperfoco Autodidata: <strong>${(avg.aprendizado || 1).toFixed(1)} / 5.0</strong>
      </span>
      <span class="badge" style="background: rgba(245, 158, 11, 0.15); color: #fbbf24; padding: 0.4rem 0.8rem;">
        Paralisia por Análise: <strong>${(avg.paralisia || 1).toFixed(1)} / 5.0</strong>
      </span>
      <span class="badge" style="background: rgba(168, 85, 247, 0.15); color: #c084fc; padding: 0.4rem 0.8rem;">
        Discronia Interna: <strong>${(avg.discronia || 1).toFixed(1)} / 5.0</strong>
      </span>
      <span class="badge" style="background: rgba(244, 63, 94, 0.15); color: #fda4af; padding: 0.4rem 0.8rem;">
        Descompasso de Ritmo: <strong>${(avg.comunicacao || 1).toFixed(1)} / 5.0</strong>
      </span>
    </div>
  `;

  container.innerHTML = html;
}

function renderMetacognitionDetails(meta) {
  const container = document.getElementById("metaDetails");
  if (!meta) {
    container.innerHTML = `<div style="color: var(--text-muted);">Sem registros.</div>`;
    return;
  }

  const itemsInfo = [
    {
      id: "meta_1",
      title: "1. A Ilha dos Olhos Azuis (Conhecimento Comum & Indução Lógica)",
      desc: "Problema clássico de indução matemática. Resposta ótima: Todos os 100 lógicos saem juntos exatamente na 100ª noite à meia-noite."
    },
    {
      id: "meta_2",
      title: "2. As Duas Cordas de 45 minutos (Modelagem Não-Linear Temporal)",
      desc: "Pensamento lateral prático. Resposta ótima: Acender corda 1 por ambas as pontas e corda 2 por uma ponta (30 min); aos 30 min, acender a outra ponta da corda 2 (+15 min = 45 min)."
    },
    {
      id: "meta_3",
      title: "3. Analogia Estrutural Átomos/Cristais e Notas/Acordes (Pensamento em Rede)",
      desc: "Identificação da regra abstrata invariante: Emergência de propriedades qualitativas de ordem superior a partir de regras combinatórias rigorosas entre unidades discretas elementares."
    }
  ];

  const breakdown = meta.breakdown || {};
  let html = "";

  itemsInfo.forEach(info => {
    const b = breakdown[info.id] || {};
    const isCorrect = b.correct;
    const badge = isCorrect 
      ? `<span class="badge badge-completed">Acertou (Raciocínio Ótimo)</span>`
      : `<span class="badge" style="background: rgba(245, 158, 11, 0.2); color: #fbbf24;">Não Ótimo</span>`;

    html += `
      <div style="background-color: var(--bg-input); padding: 1.25rem; border-radius: var(--radius-sm); border: 1px solid var(--border-subtle);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
          <h4 style="font-size: 1rem; color: var(--text-primary);">${info.title}</h4>
          ${badge}
        </div>
        <p style="font-size: 0.88rem; color: var(--text-secondary); line-height: 1.5;">${info.desc}</p>
        <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.5rem;">
          Resposta selecionada pelo participante: <strong>Opção ${b.user_answer || "—"}</strong>
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
}

function renderTelemetry(val, tm) {
  const container = document.getElementById("telemetryDetails");
  const issues = val.detected_issues || [];

  const pausesList = tm.pause_events || [];
  let pausesHtml = "";
  if (pausesList.length > 0) {
    pausesHtml = `
      <div style="margin-top: 0.75rem; background: var(--bg-surface); padding: 0.75rem; border-radius: var(--radius-sm); border: 1px solid var(--border-subtle);">
        <strong style="color: #fbbf24; font-size: 0.82rem;">Histórico de Pausas Registradas:</strong>
        <ul style="margin-left: 1.2rem; font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.25rem;">
          ${pausesList.map((p, idx) => `
            <li>Pausa #${idx + 1}: Duração de <strong>${Math.round(p.duration_seconds / 60)} min</strong> (${p.duration_seconds}s) no módulo <em>${p.module || 'geral'}</em>.</li>
          `).join("")}
        </ul>
      </div>
    `;
  }

  container.innerHTML = `
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1rem;">
      <div style="background: var(--bg-input); padding: 0.85rem; border-radius: var(--radius-sm);">
        <div style="font-size: 0.8rem; color: var(--text-muted);">Tempo Ativo de Interação</div>
        <div style="font-size: 1.1rem; font-weight: 700; color: #38bdf8;">
          ${tm.active_minutes || 0} min (${tm.active_seconds || 0}s)
        </div>
      </div>

      <div style="background: var(--bg-input); padding: 0.85rem; border-radius: var(--radius-sm);">
        <div style="font-size: 0.8rem; color: var(--text-muted);">Tempo em Espera / Ausência</div>
        <div style="font-size: 1.1rem; font-weight: 700; color: ${tm.idle_minutes > 5 ? '#fbbf24' : '#34d399'};">
          ${tm.idle_minutes || 0} min (${tm.pause_events_count || 0} pausas)
        </div>
      </div>

      <div style="background: var(--bg-input); padding: 0.85rem; border-radius: var(--radius-sm);">
        <div style="font-size: 0.8rem; color: var(--text-muted);">Verificação PVT (Item Armadilha)</div>
        <div style="font-size: 1.1rem; font-weight: 700; color: ${val.pvt_passed ? '#34d399' : '#f43f5e'};">
          ${val.pvt_passed ? '✔ Aprovado' : '✖ Atenção'}
        </div>
      </div>

      <div style="background: var(--bg-input); padding: 0.85rem; border-radius: var(--radius-sm);">
        <div style="font-size: 0.8rem; color: var(--text-muted);">Respostas Ultrarrápidas (<150ms)</div>
        <div style="font-size: 1.1rem; font-weight: 700; color: ${val.fast_clicks_count === 0 ? '#34d399' : '#fbbf24'};">
          ${val.fast_clicks_count || 0} ocorrência(s)
        </div>
      </div>
    </div>

    ${pausesHtml}

    ${issues.length > 0 ? `
      <div style="margin-top: 1rem; background: rgba(245, 158, 11, 0.1); border-left: 3px solid var(--accent-amber); padding: 0.75rem 1rem; border-radius: var(--radius-sm); color: #fbbf24; font-size: 0.85rem;">
        <strong>Apontamentos da Auditoria Psicométrica:</strong>
        <ul style="margin-left: 1.2rem; margin-top: 0.25rem;">
          ${issues.map(i => `<li>${escapeHtml(i)}</li>`).join("")}
        </ul>
      </div>
    ` : `
      <div style="color: #34d399; font-size: 0.85rem; margin-top: 0.5rem;">
        ✔ Nenhuma anomalia de atenção ou viés metodológico registrado durante a sessão.
      </div>
    `}
  `;
}

// =========================================================================
// DESENHO DO GRÁFICO RADAR CALIBRADO (Sem Recorte de Texto)
// =========================================================================

function drawCalibratedRadarChart(canvasId, dataPoints) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  const dpr = window.devicePixelRatio || 1;
  const width = 640;
  const height = 480;

  canvas.width = width * dpr;
  canvas.height = height * dpr;
  canvas.style.width = `${width}px`;
  canvas.style.height = `${height}px`;
  ctx.scale(dpr, dpr);

  const centerX = width / 2;
  const centerY = height / 2;
  const radius = 135; // Raio confortável que deixa 185px de margem nas bordas para os textos

  const rawLabels = Object.keys(dataPoints);
  const values = Object.values(dataPoints);
  const numAxes = rawLabels.length;
  const angleStep = (Math.PI * 2) / numAxes;

  ctx.clearRect(0, 0, width, height);

  // Mapeamento de rótulos formatados em duas linhas para não estourar Canvas
  const formattedLabels = [
    ["Raciocínio Fluido", "(Gf)"],
    ["Memória Operacional", "(Gwm)"],
    ["Velocidade Processamento", "(Gs)"],
    ["Flexibilidade Cognitiva", "(WCST)"],
    ["Pensamento Divergente", "(RAT)"],
    ["Metacognição", "Sistêmica"]
  ];

  // 1. Anéis poligonais (níveis 20%, 40%, 60%, 80%, 100%)
  const levels = [0.2, 0.4, 0.6, 0.8, 1.0];
  ctx.strokeStyle = "#334155";
  ctx.lineWidth = 1;

  levels.forEach(level => {
    ctx.beginPath();
    for (let i = 0; i < numAxes; i++) {
      const angle = i * angleStep - Math.PI / 2;
      const x = centerX + Math.cos(angle) * (radius * level);
      const y = centerY + Math.sin(angle) * (radius * level);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.stroke();

    // Rótulo da escala percentual
    ctx.font = "10px monospace";
    ctx.fillStyle = "#64748b";
    ctx.fillText(`${Math.round(level * 100)}%`, centerX + 4, centerY - (radius * level) - 2);
  });

  // 2. Eixos radiais e rótulos
  ctx.strokeStyle = "#475569";
  for (let i = 0; i < numAxes; i++) {
    const angle = i * angleStep - Math.PI / 2;
    const x = centerX + Math.cos(angle) * radius;
    const y = centerY + Math.sin(angle) * radius;
    
    ctx.beginPath();
    ctx.moveTo(centerX, centerY);
    ctx.lineTo(x, y);
    ctx.stroke();

    // Rótulos externos com distância radial segura
    const labelDistance = radius + 32;
    const lx = centerX + Math.cos(angle) * labelDistance;
    const ly = centerY + Math.sin(angle) * labelDistance;

    const lines = formattedLabels[i] || [rawLabels[i]];
    const scoreVal = values[i];

    ctx.font = "bold 11px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto";
    ctx.textAlign = (lx < centerX - 20) ? "right" : ((lx > centerX + 20) ? "left" : "center");
    ctx.textBaseline = "middle";

    // Linha 1 (Título)
    ctx.fillStyle = "#e2e8f0";
    ctx.fillText(lines[0], lx, ly - 7);

    // Linha 2 (Sigla e pontuação percentual)
    ctx.font = "bold 10px monospace";
    ctx.fillStyle = "#38bdf8";
    ctx.fillText(`${lines[1]} • ${scoreVal}%`, lx, ly + 8);
  }

  // 3. Polígono de dados preenchido
  ctx.beginPath();
  values.forEach((val, i) => {
    const factor = Math.max(0.05, Math.min(1.0, val / 100));
    const angle = i * angleStep - Math.PI / 2;
    const x = centerX + Math.cos(angle) * (radius * factor);
    const y = centerY + Math.sin(angle) * (radius * factor);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.closePath();

  ctx.fillStyle = "rgba(14, 165, 233, 0.28)";
  ctx.fill();

  ctx.strokeStyle = "#0ea5e9";
  ctx.lineWidth = 3;
  ctx.stroke();

  // 4. Vértices luminosos
  values.forEach((val, i) => {
    const factor = Math.max(0.05, Math.min(1.0, val / 100));
    const angle = i * angleStep - Math.PI / 2;
    const x = centerX + Math.cos(angle) * (radius * factor);
    const y = centerY + Math.sin(angle) * (radius * factor);

    ctx.beginPath();
    ctx.arc(x, y, 5, 0, Math.PI * 2);
    ctx.fillStyle = "#38bdf8";
    ctx.fill();
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 2;
    ctx.stroke();
  });
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str).replace(/[&<>'"]/g, 
    tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
  );
}
