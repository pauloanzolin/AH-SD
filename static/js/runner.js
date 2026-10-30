// runner.js - Motor de Aplicação Neuropsicológica com Detecção de Inatividade e Pausa Ativa

let sessionId = null;
let sessionData = null;
let currentModuleIndex = 0;
const MODULE_ORDER = ["fenomenologico", "matrizes", "corsi", "velocidade", "wcst", "associacao", "metacognicao"];

// Telemetria, Foco e Tempos
let telemetry = {
  focus_loss_count: 0,
  blur_events: 0,
  fast_clicks: 0
};

let activeSeconds = 0;
let idleSeconds = 0;
let isPaused = false;
let pauseStartTime = null;
let pauseIntervalSeconds = 0;
let pauseEvents = [];

let idleTimeoutTimer = null;
const IDLE_LIMIT_MS = 60000; // 60 segundos sem interação aciona a pausa automática

let stimulusStartTime = 0;
let currentModuleResponses = [];
let currentModuleData = null;
let currentTrialRestartHandler = null;

document.addEventListener("DOMContentLoaded", async () => {
  const pathParts = window.location.pathname.split("/").filter(Boolean);
  sessionId = pathParts[pathParts.length - 1];

  setupActivityAndTelemetryListeners();
  await initSession();
  startMasterClock();
});

// ----------------- DETECTOR DE INATIVIDADE E FOCO -----------------

function setupActivityAndTelemetryListeners() {
  const resetActivity = () => {
    if (!isPaused) {
      clearTimeout(idleTimeoutTimer);
      idleTimeoutTimer = setTimeout(() => {
        pauseTest("Inatividade detectada (mais de 60 segundos sem nenhuma interação com o teclado ou mouse).");
      }, IDLE_LIMIT_MS);
    }
  };

  // Eventos de interação do usuário
  ["mousemove", "mousedown", "keydown", "touchstart", "scroll", "click"].forEach(evt => {
    window.addEventListener(evt, resetActivity, { passive: true });
  });

  // Perda de foco / troca de aba ou janela
  window.addEventListener("blur", () => {
    if (!isPaused) {
      telemetry.blur_events++;
      pauseTest("Você saiu da janela do teste ou trocou de aplicativo.");
    }
  });

  document.addEventListener("visibilitychange", () => {
    if (document.hidden && !isPaused) {
      telemetry.focus_loss_count++;
      pauseTest("A aba do teste foi minimizada ou ocultada.");
    }
  });

  resetActivity();
}

function startMasterClock() {
  setInterval(() => {
    if (!isPaused) {
      activeSeconds++;
      updateActiveTimerDisplay();
    } else {
      idleSeconds++;
      pauseIntervalSeconds++;
      updatePauseTimerDisplay();
    }
  }, 1000);
}

function updateActiveTimerDisplay() {
  const display = document.getElementById("timerDisplay");
  if (!display) return;
  const mins = String(Math.floor(activeSeconds / 60)).padStart(2, "0");
  const secs = String(activeSeconds % 60).padStart(2, "0");
  display.textContent = `${mins}:${secs}`;
}

function updatePauseTimerDisplay() {
  const display = document.getElementById("pauseTimerDisplay");
  if (!display) return;
  const mins = String(Math.floor(pauseIntervalSeconds / 60)).padStart(2, "0");
  const secs = String(pauseIntervalSeconds % 60).padStart(2, "0");
  display.textContent = `${mins}:${secs}`;
}

function triggerManualPause() {
  pauseTest("Pausa solicitada manualmente pelo participante.");
}

function pauseTest(reason) {
  if (isPaused) return;
  isPaused = true;
  pauseStartTime = new Date();
  pauseIntervalSeconds = 0;

  clearTimeout(idleTimeoutTimer);

  const modal = document.getElementById("pauseModal");
  const reasonText = document.getElementById("pauseReasonText");
  const restartBtn = document.getElementById("btnRestartCurrentBlock");

  if (reasonText) reasonText.textContent = reason;

  // Em módulos de memória imediata e flexibilidade, destaca o botão de reiniciar bloco
  const currentMod = MODULE_ORDER[currentModuleIndex];
  if (restartBtn) {
    if (currentMod === "corsi" || currentMod === "wcst") {
      restartBtn.style.display = "block";
      restartBtn.textContent = `🔄 Reiniciar Sequência de ${currentMod === "corsi" ? "Memória (Corsi)" : "Classificação (WCST)"}`;
    } else {
      restartBtn.style.display = "none";
    }
  }

  updatePauseTimerDisplay();
  if (modal) modal.style.display = "flex";
}

function resumeTest() {
  if (!isPaused) return;

  const now = new Date();
  const durationSec = Math.round((now - pauseStartTime) / 1000);

  pauseEvents.push({
    paused_at: pauseStartTime.toISOString(),
    resumed_at: now.toISOString(),
    duration_seconds: durationSec,
    module: MODULE_ORDER[currentModuleIndex]
  });

  isPaused = false;
  const modal = document.getElementById("pauseModal");
  if (modal) modal.style.display = "none";

  // Reseta carimbo de estímulo para a pausa NÃO inflar a latência do item atual
  stimulusStartTime = performance.now();

  // Reinicia detector de inatividade
  clearTimeout(idleTimeoutTimer);
  idleTimeoutTimer = setTimeout(() => {
    pauseTest("Inatividade detectada (mais de 60 segundos sem interação).");
  }, IDLE_LIMIT_MS);
}

function restartCurrentTrialOrBlock() {
  resumeTest();
  if (typeof currentTrialRestartHandler === "function") {
    currentTrialRestartHandler();
  }
}

// ----------------- INICIALIZAÇÃO DA SESSÃO -----------------

async function initSession() {
  try {
    const res = await fetch(`/api/sessions/${sessionId}`);
    if (!res.ok) {
      alert("Sessão não encontrada.");
      window.location.href = "/";
      return;
    }
    sessionData = await res.json();

    if (sessionData.status === "completed") {
      window.location.href = `/report/${sessionId}`;
      return;
    }

    document.getElementById("topParticipantName").textContent = sessionData.participant_name;
    document.getElementById("topProjectName").textContent = `Projeto: ${sessionData.project_name || "Geral"}`;

    const savedMod = sessionData.current_module || "fenomenologico";
    const modIdx = MODULE_ORDER.indexOf(savedMod);
    currentModuleIndex = modIdx >= 0 ? modIdx : 0;

    loadCurrentModule();
  } catch (err) {
    console.error("Erro ao iniciar sessão:", err);
  }
}

function updateProgress(stepIdx, totalSteps) {
  const percent = Math.round(((stepIdx + 1) / totalSteps) * 100);
  document.getElementById("progressFill").style.width = `${percent}%`;
  document.getElementById("progressPercentage").textContent = `${percent}%`;
  document.getElementById("moduleIndicator").textContent = `Módulo ${currentModuleIndex + 1} de ${MODULE_ORDER.length}`;
}

async function loadCurrentModule() {
  if (currentModuleIndex >= MODULE_ORDER.length) {
    await finishAllTests();
    return;
  }

  const moduleName = MODULE_ORDER[currentModuleIndex];
  updateProgress(currentModuleIndex, MODULE_ORDER.length);

  const res = await fetch(`/api/sessions/${sessionId}/module/${moduleName}`);
  const data = await res.json();
  currentModuleData = data;
  currentModuleResponses = [];
  currentTrialRestartHandler = null;

  switch (moduleName) {
    case "fenomenologico":
      renderFenomenologicoIntro(data);
      break;
    case "matrizes":
      renderMatrizesIntro(data);
      break;
    case "corsi":
      renderCorsiIntro(data);
      break;
    case "velocidade":
      renderVelocidadeIntro(data);
      break;
    case "wcst":
      renderWcstIntro(data);
      break;
    case "associacao":
      renderAssociacaoIntro(data);
      break;
    case "metacognicao":
      renderMetacognicaoIntro(data);
      break;
  }
}

async function submitModuleAndNext(moduleName, responses) {
  try {
    await fetch(`/api/sessions/${sessionId}/module/${moduleName}/submit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        responses: responses,
        telemetry: {
          active_time_ms: activeSeconds * 1000,
          idle_time_ms: idleSeconds * 1000,
          pause_events: pauseEvents,
          focus_loss_count: telemetry.focus_loss_count,
          blur_events: telemetry.blur_events,
          fast_clicks: telemetry.fast_clicks
        }
      })
    });

    // Zera telemetria incremental de contadores
    telemetry.focus_loss_count = 0;
    telemetry.blur_events = 0;
    telemetry.fast_clicks = 0;
    pauseEvents = [];

    currentModuleIndex++;
    loadCurrentModule();
  } catch (err) {
    console.error("Erro ao enviar módulo:", err);
    alert("Erro ao gravar dados do módulo. Tente novamente.");
  }
}

async function finishAllTests() {
  const box = document.getElementById("testBox");
  box.innerHTML = `
    <div style="text-align: center; padding: 4rem;">
      <div style="font-size: 3rem; margin-bottom: 1rem;">⚙️</div>
      <h3>Processando Cálculos Psicométricos & Análise de Scatter...</h3>
      <p style="color: var(--text-secondary); margin-top: 0.5rem;">
        Normalizando escores Z, calculando tempo ativo vs inativo e identificando picos cognitivos.
      </p>
    </div>
  `;

  try {
    const res = await fetch(`/api/sessions/${sessionId}/complete`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({})
    });
    const result = await res.json();
    window.location.href = result.report_url || `/report/${sessionId}`;
  } catch (err) {
    console.error("Erro ao finalizar:", err);
  }
}

// =========================================================================
// 1. MÓDULO FENOMENOLÓGICO (Escala Likert)
// =========================================================================

function renderFenomenologicoIntro(data) {
  const box = document.getElementById("testBox");
  box.innerHTML = `
    <div>
      <span class="badge badge-in_progress">Módulo 1 • Autoavaliação Fenomenológica</span>
      <h2 style="font-size: 1.6rem; margin: 0.75rem 0;">Padrões de Vivência e Hiperexcitabilidade</h2>
      <p style="color: var(--text-secondary); margin-bottom: 1.5rem; line-height: 1.6;">
        A mente com Altas Habilidades / Superdotação opera sob uma arquitetura qualitativamente diferente:
        mielinização e velocidade de processamento, pensamento em árvore e hiperexcitabilidades de Dabrowski.
      </p>
      <div style="background-color: var(--bg-input); border-radius: var(--radius-sm); padding: 1.25rem; margin-bottom: 2rem;">
        <h4 style="color: var(--accent-cyan); margin-bottom: 0.5rem;">Instruções:</h4>
        <p style="font-size: 0.9rem; color: var(--text-secondary);">
          Responda a cada afirmação com a opção que melhor reflete sua vivência espontânea. 
          Se precisar fazer uma pausa, o sistema congelará seu tempo ativo automaticamente.
        </p>
      </div>
    </div>
    <div style="display: flex; justify-content: flex-end;">
      <button class="btn btn-primary" onclick="startFenomenologicoTest(${JSON.stringify(data.items).replace(/"/g, '&quot;')})">
        Iniciar Questionário →
      </button>
    </div>
  `;
}

function startFenomenologicoTest(items) {
  let curIndex = 0;
  const total = items.length;

  function showQuestion() {
    if (curIndex >= total) {
      submitModuleAndNext("fenomenologico", currentModuleResponses);
      return;
    }

    const item = items[curIndex];
    stimulusStartTime = performance.now();

    const box = document.getElementById("testBox");
    box.innerHTML = `
      <div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
          <span style="font-size: 0.85rem; color: var(--text-muted); text-transform: uppercase;">Questão ${curIndex + 1} de ${total}</span>
          <span class="badge badge-in_progress" style="font-size: 0.75rem;">${escapeHtml(item.title)}</span>
        </div>
        <h3 style="font-size: 1.3rem; font-weight: 600; line-height: 1.4; margin-bottom: 1.5rem;">
          ${escapeHtml(item.question)}
        </h3>

        <div class="likert-group">
          ${item.options.map(opt => `
            <div class="likert-option" onclick="chooseLikertAnswer('${item.id}', ${opt.value})">
              <span style="display: inline-block; width: 26px; height: 26px; border-radius: 50%; background: #334155; text-align: center; line-height: 26px; font-weight: bold; font-size: 0.85rem;">${opt.value}</span>
              <span style="font-size: 0.95rem;">${escapeHtml(opt.label)}</span>
            </div>
          `).join("")}
        </div>
      </div>
    `;
  }

  window.chooseLikertAnswer = (itemId, val) => {
    const rt = performance.now() - stimulusStartTime;
    if (rt < 150) telemetry.fast_clicks++;

    currentModuleResponses.push({
      item_id: itemId,
      user_answer: val,
      reaction_time_ms: Math.round(rt)
    });
    curIndex++;
    showQuestion();
  };

  showQuestion();
}

// =========================================================================
// 2. MÓDULO MATRIZES PROGRESSIVAS (Raciocínio Fluido - Gf)
// =========================================================================

function renderMatrizesIntro(data) {
  const box = document.getElementById("testBox");
  box.innerHTML = `
    <div>
      <span class="badge badge-in_progress">Módulo 2 • Raciocínio Fluido (Gf)</span>
      <h2 style="font-size: 1.6rem; margin: 0.75rem 0;">Matrizes Progressivas Não-Verbais</h2>
      <p style="color: var(--text-secondary); margin-bottom: 1.5rem; line-height: 1.6;">
        Avaliação de indução lógica e dedução de padrões abstratos conforme a taxonomia formal de matrizes
        (Carpenter, Just & Shell, 1990).
      </p>

      <div style="background-color: var(--bg-input); border-radius: var(--radius-sm); padding: 1.25rem; margin-bottom: 2rem;">
        <h4 style="color: var(--accent-cyan); margin-bottom: 0.5rem;">Instruções:</h4>
        <p style="font-size: 0.9rem; color: var(--text-secondary);">
          Identifique qual das alternativas abaixo completa logicamente o padrão das linhas e colunas no espaço (<span style="color:var(--accent-amber); font-weight:bold;">?</span>).
        </p>
      </div>
    </div>
    <div style="display: flex; justify-content: flex-end;">
      <button class="btn btn-primary" onclick="startMatrizesTest(${JSON.stringify(data.items).replace(/"/g, '&quot;')})">
        Iniciar Matrizes →
      </button>
    </div>
  `;
}

function startMatrizesTest(items) {
  let curIndex = 0;

  function showMatrix() {
    if (curIndex >= items.length) {
      submitModuleAndNext("matrizes", currentModuleResponses);
      return;
    }

    const item = items[curIndex];
    stimulusStartTime = performance.now();

    const box = document.getElementById("testBox");
    box.innerHTML = `
      <div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
          <span style="font-size: 0.85rem; color: var(--text-muted); text-transform: uppercase;">Matriz ${curIndex + 1} de ${items.length}</span>
          <span class="badge badge-in_progress">Dificuldade: Nível ${item.difficulty}</span>
        </div>
        <p style="color: var(--text-secondary); font-size: 0.95rem; margin-bottom: 1.25rem;">
          ${escapeHtml(item.description)}
        </p>

        <div class="matrix-container">
          <div class="matrix-grid-3x3">
            ${item.grid.flat().map(cell => {
              if (cell.type === "missing") {
                return `<div class="matrix-cell missing">?</div>`;
              }
              return `<div class="matrix-cell">${renderSvgShape(cell)}</div>`;
            }).join("")}
          </div>

          <div style="text-align: center;">
            <div style="font-size: 0.8rem; color: var(--text-secondary); text-transform: uppercase; margin-bottom: 0.5rem;">Selecione a alternativa correta:</div>
            <div class="matrix-options-grid">
              ${item.options.map(opt => `
                <button class="matrix-opt-btn" onclick="chooseMatrixAnswer('${item.id}', '${opt.id}')">
                  <div style="width: 55px; height: 55px; display: flex; align-items: center; justify-content: center;">
                    ${renderSvgShape(opt.item)}
                  </div>
                  <span style="font-weight: 700; color: var(--accent-cyan); font-size: 0.8rem; margin-top: 4px;">Opção ${opt.id}</span>
                </button>
              `).join("")}
            </div>
          </div>
        </div>
      </div>
    `;
  }

  window.chooseMatrixAnswer = (itemId, choice) => {
    const rt = performance.now() - stimulusStartTime;
    if (rt < 150) telemetry.fast_clicks++;

    currentModuleResponses.push({
      item_id: itemId,
      user_answer: choice,
      reaction_time_ms: Math.round(rt)
    });
    curIndex++;
    showMatrix();
  };

  showMatrix();
}

function renderSvgShape(cell) {
  if (!cell) return "";
  const t = cell.type;

  if (t === "circle") {
    const f = cell.fill || 25;
    const isDouble = cell.special === "full_double";
    return `
      <svg width="50" height="50" viewBox="0 0 50 50">
        <circle cx="25" cy="25" r="20" stroke="#0ea5e9" stroke-width="2" fill="${f > 100 ? '#0ea5e9' : 'transparent'}" />
        ${f <= 100 ? `<circle cx="25" cy="25" r="${(f / 100) * 18}" fill="#0ea5e9" />` : ''}
        ${isDouble ? `<circle cx="25" cy="25" r="14" stroke="#ffffff" stroke-width="2" fill="#0284c7" />` : ''}
      </svg>
    `;
  }

  if (t === "arrow") {
    const rot = cell.rot || 0;
    return `
      <svg width="50" height="50" viewBox="0 0 50 50" style="transform: rotate(${rot}deg);">
        <line x1="25" y1="42" x2="25" y2="10" stroke="#38bdf8" stroke-width="4" stroke-linecap="round" />
        <polyline points="15,20 25,10 35,20" fill="none" stroke="#38bdf8" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
    `;
  }

  if (t === "cross_h") return `<svg width="50" height="50"><line x1="10" y1="25" x2="40" y2="25" stroke="#f43f5e" stroke-width="4"/></svg>`;
  if (t === "cross_v") return `<svg width="50" height="50"><line x1="25" y1="10" x2="25" y2="40" stroke="#f43f5e" stroke-width="4"/></svg>`;
  if (t === "cross_plus") return `<svg width="50" height="50"><line x1="10" y1="25" x2="40" y2="25" stroke="#f43f5e" stroke-width="4"/><line x1="25" y1="10" x2="25" y2="40" stroke="#f43f5e" stroke-width="4"/></svg>`;
  if (t === "diag_l") return `<svg width="50" height="50"><line x1="12" y1="12" x2="38" y2="38" stroke="#10b981" stroke-width="4"/></svg>`;
  if (t === "diag_r") return `<svg width="50" height="50"><line x1="38" y1="12" x2="12" y2="38" stroke="#10b981" stroke-width="4"/></svg>`;
  if (t === "cross_x") return `<svg width="50" height="50"><line x1="12" y1="12" x2="38" y2="38" stroke="#10b981" stroke-width="4"/><line x1="38" y1="12" x2="12" y2="38" stroke="#10b981" stroke-width="4"/></svg>`;
  if (t === "box_open_top") return `<svg width="50" height="50"><polyline points="12,12 12,38 38,38 38,12" fill="none" stroke="#a855f7" stroke-width="4"/></svg>`;
  if (t === "line_top") return `<svg width="50" height="50"><line x1="12" y1="12" x2="38" y2="12" stroke="#a855f7" stroke-width="4"/></svg>`;
  if (t === "box_closed") return `<svg width="50" height="50"><rect x="12" y="12" width="26" height="26" fill="none" stroke="#a855f7" stroke-width="4"/></svg>`;
  if (t === "box_open_bottom") return `<svg width="50" height="50"><polyline points="12,38 12,12 38,12 38,38" fill="none" stroke="#a855f7" stroke-width="4"/></svg>`;
  if (t === "line_v") return `<svg width="50" height="50"><line x1="25" y1="12" x2="25" y2="38" stroke="#a855f7" stroke-width="4"/></svg>`;

  if (t === "shape") {
    const color = cell.p === "solid" ? "#38bdf8" : (cell.p === "striped" ? "#a855f7" : "#f59e0b");
    const fillStyle = cell.p === "solid" ? color : (cell.p === "striped" ? "url(#stripes)" : "none");

    let shapeSvg = "";
    if (cell.s === "circle") shapeSvg = `<circle cx="25" cy="25" r="16" fill="${fillStyle}" stroke="${color}" stroke-width="3"/>`;
    if (cell.s === "square") shapeSvg = `<rect x="10" y="10" width="30" height="30" fill="${fillStyle}" stroke="${color}" stroke-width="3"/>`;
    if (cell.s === "triangle") shapeSvg = `<polygon points="25,8 42,38 8,38" fill="${fillStyle}" stroke="${color}" stroke-width="3"/>`;
    if (cell.s === "star") shapeSvg = `<polygon points="25,6 30,19 44,19 33,28 37,42 25,33 13,42 17,28 6,19 20,19" fill="${fillStyle}" stroke="${color}" stroke-width="2"/>`;
    if (cell.s === "diamond") shapeSvg = `<polygon points="25,6 42,25 25,44 8,25" fill="${fillStyle}" stroke="${color}" stroke-width="3"/>`;
    if (cell.s === "hexagon") shapeSvg = `<polygon points="25,7 39,15 39,33 25,41 11,33 11,15" fill="${fillStyle}" stroke="${color}" stroke-width="3"/>`;

    return `
      <svg width="50" height="50" viewBox="0 0 50 50">
        <defs>
          <pattern id="stripes" width="6" height="6" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
            <line x1="0" y1="0" x2="0" y2="6" stroke="${color}" stroke-width="2" />
          </pattern>
        </defs>
        ${shapeSvg}
      </svg>
    `;
  }

  if (t === "concentric") {
    const rings = cell.rings || 1;
    const dot = cell.dot || false;
    let rSvg = "";
    for (let i = 1; i <= rings; i++) {
      rSvg += `<circle cx="25" cy="25" r="${i * 5}" fill="none" stroke="#38bdf8" stroke-width="2"/>`;
    }
    if (dot) rSvg += `<circle cx="25" cy="25" r="3" fill="#f43f5e"/>`;
    return `<svg width="50" height="50" viewBox="0 0 50 50">${rSvg}</svg>`;
  }

  return `<svg width="50" height="50"><rect x="10" y="10" width="30" height="30" fill="#38bdf8"/></svg>`;
}

// =========================================================================
// 3. MÓDULO MEMÓRIA OPERACIONAL (Corsi Blocks - Gwm)
// =========================================================================

const CORSI_POSITIONS = [
  { x: 30, y: 30 },  { x: 280, y: 35 }, { x: 155, y: 90 },
  { x: 50, y: 170 }, { x: 260, y: 160 },{ x: 160, y: 220 },
  { x: 35, y: 290 }, { x: 175, y: 300 },{ x: 280, y: 280 }
];

function renderCorsiIntro(data) {
  const box = document.getElementById("testBox");
  box.innerHTML = `
    <div>
      <span class="badge badge-in_progress">Módulo 3 • Memória Operacional (Gwm)</span>
      <h2 style="font-size: 1.6rem; margin: 0.75rem 0;">Corsi Blocks (Span Visuoespacial)</h2>
      <p style="color: var(--text-secondary); margin-bottom: 1.5rem; line-height: 1.6;">
        Avalia a capacidade de retenção e manipulação visuoespacial em tempo real.
      </p>

      <div style="background-color: var(--bg-input); border-radius: var(--radius-sm); padding: 1.25rem; margin-bottom: 2rem;">
        <h4 style="color: var(--accent-cyan); margin-bottom: 0.5rem;">Importante sobre Atenção Contínua:</h4>
        <p style="font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 0.5rem;">
          Testes de memória imediata dependem de buffer mental ininterrupto. Se você precisar se afastar,
          o sistema pausará automaticamente e você poderá reiniciar a sequência com a memória fresca ao retornar!
        </p>
      </div>
    </div>
    <div style="display: flex; justify-content: flex-end;">
      <button class="btn btn-primary" onclick="startCorsiTest(${JSON.stringify(data.config).replace(/"/g, '&quot;')})">
        Iniciar Corsi Blocks →
      </button>
    </div>
  `;
}

function startCorsiTest(config) {
  const sequences = config.test_sequences;
  let curTrialIdx = 0;
  let userClicks = [];
  let isPlayback = false;

  function renderBoard(title, instruction) {
    const box = document.getElementById("testBox");
    box.innerHTML = `
      <div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
          <span style="font-size: 0.85rem; color: var(--text-muted); text-transform: uppercase;">Sequência ${curTrialIdx + 1} de ${sequences.length}</span>
          <span class="badge badge-in_progress">Carga: Span ${sequences[curTrialIdx].span}</span>
        </div>
        <h3 id="corsiStatusMsg" style="font-size: 1.15rem; font-weight: 600; text-align: center; color: var(--accent-cyan); margin-bottom: 1rem;">
          ${instruction}
        </h3>

        <div class="corsi-board">
          ${CORSI_POSITIONS.map((pos, idx) => `
            <div id="corsi_block_${idx + 1}" class="corsi-block" style="left: ${pos.x}px; top: ${pos.y}px;" onclick="handleCorsiBlockClick(${idx + 1})">
              ${idx + 1}
            </div>
          `).join("")}
        </div>
        <div id="corsiUserProgress" style="text-align: center; color: var(--text-secondary); font-size: 0.9rem; min-height: 24px;"></div>
      </div>
    `;
  }

  async function playSequence() {
    isPlayback = true;
    userClicks = [];
    const seq = sequences[curTrialIdx].sequence;

    renderBoard("Atenção", "Observe a sequência dos blocos...");
    await sleep(800);

    for (const blockNum of seq) {
      if (isPaused) return; // Se pausou durante o playback, interrompe
      const el = document.getElementById(`corsi_block_${blockNum}`);
      if (el) el.classList.add("lit");
      await sleep(650);
      if (el) el.classList.remove("lit");
      await sleep(300);
    }

    isPlayback = false;
    stimulusStartTime = performance.now();
    const msg = document.getElementById("corsiStatusMsg");
    if (msg) {
      msg.textContent = "Sua vez! Clique nos blocos na mesma ordem:";
      msg.style.color = "#34d399";
    }
  }

  // Permite ao modal de pausa reiniciar a sequência atual
  currentTrialRestartHandler = () => {
    playSequence();
  };

  window.handleCorsiBlockClick = (blockNum) => {
    if (isPlayback || isPaused) return;

    userClicks.push(blockNum);
    const targetSeq = sequences[curTrialIdx].sequence;

    const el = document.getElementById(`corsi_block_${blockNum}`);
    if (el) {
      el.classList.add("lit");
      setTimeout(() => el.classList.remove("lit"), 200);
    }

    const progEl = document.getElementById("corsiUserProgress");
    if (progEl) progEl.textContent = `Blocos selecionados: ${userClicks.join(" → ")}`;

    if (userClicks.length === targetSeq.length) {
      const rt = performance.now() - stimulusStartTime;
      currentModuleResponses.push({
        item_id: `corsi_span_${sequences[curTrialIdx].span}`,
        user_answer: [...userClicks],
        reaction_time_ms: Math.round(rt),
        raw_data: {
          level: sequences[curTrialIdx].level,
          target_sequence: targetSeq
        }
      });

      curTrialIdx++;
      if (curTrialIdx < sequences.length) {
        setTimeout(playSequence, 600);
      } else {
        submitModuleAndNext("corsi", currentModuleResponses);
      }
    }
  };

  playSequence();
}

// =========================================================================
// 4. MÓDULO VELOCIDADE DE PROCESSAMENTO (Gs)
// =========================================================================

function renderVelocidadeIntro(data) {
  const box = document.getElementById("testBox");
  box.innerHTML = `
    <div>
      <span class="badge badge-in_progress">Módulo 4 • Velocidade de Processamento (Gs)</span>
      <h2 style="font-size: 1.6rem; margin: 0.75rem 0;">Pareamento e Discriminação Rápida</h2>
      <p style="color: var(--text-secondary); margin-bottom: 1.5rem; line-height: 1.6;">
        Avaliação da agilidade percepto-motora diante de símbolos abstratos.
      </p>

      <div style="background-color: var(--bg-input); border-radius: var(--radius-sm); padding: 1.25rem; margin-bottom: 2rem;">
        <h4 style="color: var(--accent-cyan); margin-bottom: 0.5rem;">Instruções:</h4>
        <p style="font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 0.5rem;">
          Dois símbolos serão mostrados lado a lado. Indique rapidamente se são <strong>IGUAIS</strong> ou <strong>DIFERENTES</strong>.
        </p>
        <p style="font-size: 0.85rem; color: var(--text-muted);">
          Teclas: <strong>[1] ou Seta Esquerda</strong> = IGUAL | <strong>[2] ou Seta Direita</strong> = DIFERENTE.
        </p>
      </div>
    </div>
    <div style="display: flex; justify-content: flex-end;">
      <button class="btn btn-primary" onclick="startVelocidadeTest(${JSON.stringify(data.items).replace(/"/g, '&quot;')})">
        Iniciar Teste de Velocidade →
      </button>
    </div>
  `;
}

function startVelocidadeTest(items) {
  let curIndex = 0;

  function handleKey(e) {
    if (isPaused) return;
    if (e.key === "1" || e.key === "ArrowLeft") chooseSpeedAnswer(true);
    else if (e.key === "2" || e.key === "ArrowRight") chooseSpeedAnswer(false);
  }

  window.addEventListener("keydown", handleKey);

  function showPair() {
    if (curIndex >= items.length) {
      window.removeEventListener("keydown", handleKey);
      submitModuleAndNext("velocidade", currentModuleResponses);
      return;
    }

    const item = items[curIndex];
    stimulusStartTime = performance.now();

    const box = document.getElementById("testBox");
    box.innerHTML = `
      <div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
          <span style="font-size: 0.85rem; color: var(--text-muted); text-transform: uppercase;">Item ${curIndex + 1} de ${items.length}</span>
          <span class="badge badge-in_progress">Responda rapidamente</span>
        </div>

        <div class="speed-pair-box">
          <span>${item.pair[0]}</span>
          <span style="font-size: 2rem; color: var(--text-muted);">vs</span>
          <span>${item.pair[1]}</span>
        </div>

        <div style="display: flex; justify-content: center; gap: 1.5rem;">
          <button class="btn btn-primary" style="padding: 1rem 2.5rem; font-size: 1.2rem; background: #0284c7;" onclick="chooseSpeedAnswer(true)">
            [1] IGUAIS
          </button>
          <button class="btn btn-secondary" style="padding: 1rem 2.5rem; font-size: 1.2rem; border-color: var(--accent-rose); color: #fda4af;" onclick="chooseSpeedAnswer(false)">
            [2] DIFERENTES
          </button>
        </div>
      </div>
    `;
  }

  window.chooseSpeedAnswer = (choice) => {
    if (isPaused) return;
    const rt = performance.now() - stimulusStartTime;
    if (rt < 150) telemetry.fast_clicks++;

    currentModuleResponses.push({
      item_id: items[curIndex].id,
      user_answer: choice,
      reaction_time_ms: Math.round(rt)
    });
    curIndex++;
    showPair();
  };

  showPair();
}

// =========================================================================
// 5. MÓDULO FLEXIBILIDADE COGNITIVA (WCST Digital)
// =========================================================================

function renderWcstIntro(data) {
  const box = document.getElementById("testBox");
  box.innerHTML = `
    <div>
      <span class="badge badge-in_progress">Módulo 5 • Flexibilidade Cognitiva & Funções Executivas</span>
      <h2 style="font-size: 1.6rem; margin: 0.75rem 0;">Classificação de Cartas Adaptativa (WCST)</h2>
      <p style="color: var(--text-secondary); margin-bottom: 1.5rem; line-height: 1.6;">
        Avaliação de alternância de set mental sob mudança oculta de regras.
      </p>

      <div style="background-color: var(--bg-input); border-radius: var(--radius-sm); padding: 1.25rem; margin-bottom: 2rem;">
        <h4 style="color: var(--accent-cyan); margin-bottom: 0.5rem;">Como Funciona:</h4>
        <p style="font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 0.5rem;">
          Combine a carta central com uma das 4 cartas do topo. A regra (Cor, Forma ou Número) muda de tempos em tempos.
        </p>
      </div>
    </div>
    <div style="display: flex; justify-content: flex-end;">
      <button class="btn btn-primary" onclick="startWcstTest(${JSON.stringify(data.anchors).replace(/"/g, '&quot;')}, ${JSON.stringify(data.trials).replace(/"/g, '&quot;')})">
        Iniciar WCST →
      </button>
    </div>
  `;
}

function startWcstTest(anchors, trials) {
  let curTrialIdx = 0;
  let isWaiting = false;

  function renderWcstTrial(feedbackText, feedbackClass) {
    if (curTrialIdx >= trials.length) {
      submitModuleAndNext("wcst", currentModuleResponses);
      return;
    }

    const trial = trials[curTrialIdx];
    stimulusStartTime = performance.now();

    const box = document.getElementById("testBox");
    box.innerHTML = `
      <div class="wcst-container">
        <div style="display: flex; justify-content: space-between; width: 100%; align-items: center;">
          <span style="font-size: 0.85rem; color: var(--text-muted); text-transform: uppercase;">Jogada ${curTrialIdx + 1} de ${trials.length}</span>
          <div class="wcst-feedback ${feedbackClass || ''}">${feedbackText || ''}</div>
          <span class="badge badge-in_progress">Classifique a Carta</span>
        </div>

        <div class="wcst-anchors">
          ${anchors.map(a => `
            <div class="wcst-card" onclick="handleWcstChoice(${a.anchor_id})">
              ${renderWcstCardContent(a.count, a.shape, a.color)}
            </div>
          `).join("")}
        </div>

        <div style="font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase;">
          ⬆️ Combine a carta abaixo com uma das 4 cartas acima ⬆️
        </div>

        <div class="wcst-target-card">
          ${renderWcstCardContent(trial.card.count, trial.card.shape, trial.card.color)}
        </div>
      </div>
    `;
  }

  currentTrialRestartHandler = () => {
    renderWcstTrial("", "");
  };

  window.handleWcstChoice = async (anchorId) => {
    if (isWaiting || isPaused) return;
    isWaiting = true;

    const rt = performance.now() - stimulusStartTime;
    const trial = trials[curTrialIdx];

    const res = await fetch(`/api/sessions/${sessionId}/wcst_check`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ trial: trial.trial, anchor_id: anchorId })
    });
    const checkData = await res.json();
    const chosenAnchor = anchors.find(a => a.anchor_id === anchorId);

    currentModuleResponses.push({
      item_id: `wcst_trial_${trial.trial}`,
      user_answer: anchorId,
      reaction_time_ms: Math.round(rt),
      raw_data: {
        trial: trial.trial,
        is_correct: checkData.is_correct,
        chosen_anchor: chosenAnchor,
        card: trial.card
      }
    });

    const feedbackText = checkData.is_correct ? "✔ CORRETO" : "✖ INCORRETO";
    const feedbackClass = checkData.is_correct ? "feedback-correct" : "feedback-wrong";
    renderWcstTrial(feedbackText, feedbackClass);

    setTimeout(() => {
      isWaiting = false;
      curTrialIdx++;
      renderWcstTrial("", "");
    }, 850);
  };

  renderWcstTrial("", "");
}

function renderWcstCardContent(count, shape, color) {
  const colorMap = { red: "#ef4444", green: "#22c55e", yellow: "#eab308", blue: "#3b82f6" };
  const hex = colorMap[color] || "#3b82f6";

  let shapeSvg = "";
  if (shape === "triangle") shapeSvg = `<polygon points="12,2 22,20 2,20" fill="${hex}"/>`;
  if (shape === "star") shapeSvg = `<polygon points="12,2 15,9 22,9 16,14 18,21 12,17 6,21 8,14 2,9 9,9" fill="${hex}"/>`;
  if (shape === "cross") shapeSvg = `<path d="M9 2h6v7h7v6h-7v7H9v-7H2V9h7V2z" fill="${hex}"/>`;
  if (shape === "circle") shapeSvg = `<circle cx="12" cy="12" r="10" fill="${hex}"/>`;

  let items = "";
  for (let i = 0; i < count; i++) {
    items += `<svg width="24" height="24" viewBox="0 0 24 24">${shapeSvg}</svg>`;
  }
  return items;
}

// =========================================================================
// 6. MÓDULO ASSOCIAÇÃO REMOTA (RAT - Criatividade)
// =========================================================================

function renderAssociacaoIntro(data) {
  const box = document.getElementById("testBox");
  box.innerHTML = `
    <div>
      <span class="badge badge-in_progress">Módulo 6 • Pensamento Divergente & Criatividade</span>
      <h2 style="font-size: 1.6rem; margin: 0.75rem 0;">Teste de Associação Remota (RAT)</h2>
      <p style="color: var(--text-secondary); margin-bottom: 1.5rem; line-height: 1.6;">
        Avaliação de salto intuitivo e conectividade semântica em redes associativas distantes.
      </p>

      <div style="background-color: var(--bg-input); border-radius: var(--radius-sm); padding: 1.25rem; margin-bottom: 2rem;">
        <h4 style="color: var(--accent-cyan); margin-bottom: 0.5rem;">Instruções:</h4>
        <p style="font-size: 0.9rem; color: var(--text-secondary);">
          Encontre <strong>uma única palavra</strong> que se conecte simultaneamente com as três palavras apresentadas.
        </p>
      </div>
    </div>
    <div style="display: flex; justify-content: flex-end;">
      <button class="btn btn-primary" onclick="startAssociacaoTest(${JSON.stringify(data.items).replace(/"/g, '&quot;')})">
        Iniciar Associação Remota →
      </button>
    </div>
  `;
}

function startAssociacaoTest(items) {
  let curIndex = 0;

  function showRAT() {
    if (curIndex >= items.length) {
      submitModuleAndNext("associacao", currentModuleResponses);
      return;
    }

    const item = items[curIndex];
    stimulusStartTime = performance.now();

    const box = document.getElementById("testBox");
    box.innerHTML = `
      <div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
          <span style="font-size: 0.85rem; color: var(--text-muted); text-transform: uppercase;">Tríade ${curIndex + 1} de ${items.length}</span>
          <span class="badge badge-in_progress">Dica: ${escapeHtml(item.hint)}</span>
        </div>

        <div style="display: flex; justify-content: center; gap: 1rem; margin: 3rem 0; flex-wrap: wrap;">
          ${item.words.map(w => `
            <div style="background: var(--bg-input); border: 2px solid var(--border-subtle); border-radius: var(--radius-md); padding: 1.25rem 2rem; font-size: 1.6rem; font-weight: 700; color: #fff;">
              ${escapeHtml(w)}
            </div>
          `).join("")}
        </div>

        <div style="max-width: 450px; margin: 0 auto;">
          <label style="font-size: 0.85rem; color: var(--text-secondary); display: block; margin-bottom: 0.4rem;">Palavra conectora comum:</label>
          <div style="display: flex; gap: 0.5rem;">
            <input type="text" id="ratInput" class="form-input" style="font-size: 1.2rem; text-align: center; text-transform: lowercase;" placeholder="Digite a palavra aqui..." autofocus autocomplete="off">
            <button class="btn btn-primary" onclick="submitRatAnswer('${item.id}')">Confirmar</button>
          </div>
        </div>
      </div>
    `;

    const inp = document.getElementById("ratInput");
    if (inp) {
      inp.focus();
      inp.addEventListener("keypress", (e) => {
        if (e.key === "Enter") submitRatAnswer(item.id);
      });
    }
  }

  window.submitRatAnswer = (itemId) => {
    if (isPaused) return;
    const inp = document.getElementById("ratInput");
    const val = inp ? inp.value.trim().toLowerCase() : "";
    if (!val) return;

    const rt = performance.now() - stimulusStartTime;
    currentModuleResponses.push({
      item_id: itemId,
      user_answer: val,
      reaction_time_ms: Math.round(rt)
    });

    curIndex++;
    showRAT();
  };

  showRAT();
}

// =========================================================================
// 7. MÓDULO METACOGNIÇÃO E DESAFIOS DO PDF
// =========================================================================

function renderMetacognicaoIntro(data) {
  const box = document.getElementById("testBox");
  box.innerHTML = `
    <div>
      <span class="badge badge-in_progress">Módulo 7 • Desafios Cognitivos Aprofundados</span>
      <h2 style="font-size: 1.6rem; margin: 0.75rem 0;">Problemas de Pensamento Lateral e Metacognição</h2>
      <p style="color: var(--text-secondary); margin-bottom: 1.5rem; line-height: 1.6;">
        Desafios de dedução lógica e modelagem sistêmica: <em>A Ilha dos Olhos Azuis</em>, <em>As Duas Cordas de 45 min</em> e 
        <em>A Analogia Estrutural Átomos/Cristais</em>.
      </p>
    </div>
    <div style="display: flex; justify-content: flex-end;">
      <button class="btn btn-primary" onclick="startMetacognicaoTest(${JSON.stringify(data.items).replace(/"/g, '&quot;')})">
        Iniciar Desafios Finais →
      </button>
    </div>
  `;
}

function startMetacognicaoTest(items) {
  let curIndex = 0;

  function showMeta() {
    if (curIndex >= items.length) {
      submitModuleAndNext("metacognicao", currentModuleResponses);
      return;
    }

    const item = items[curIndex];
    stimulusStartTime = performance.now();

    const box = document.getElementById("testBox");
    box.innerHTML = `
      <div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
          <span style="font-size: 0.85rem; color: var(--text-muted); text-transform: uppercase;">Desafio ${curIndex + 1} de ${items.length}</span>
          <span class="badge badge-in_progress">Metacognição Aguda</span>
        </div>

        <h3 style="font-size: 1.2rem; color: var(--accent-cyan); margin-bottom: 0.75rem;">${escapeHtml(item.title)}</h3>

        <div style="background-color: var(--bg-input); border-left: 4px solid var(--accent-indigo); padding: 1.25rem; border-radius: var(--radius-sm); margin-bottom: 1.5rem; font-size: 0.95rem; line-height: 1.6; white-space: pre-line;">
          ${escapeHtml(item.prompt)}
        </div>

        <div class="likert-group">
          ${item.options.map(opt => `
            <div class="likert-option" onclick="chooseMetaAnswer('${item.id}', '${opt.id}')">
              <span style="display: inline-block; width: 28px; height: 28px; border-radius: 50%; background: #334155; text-align: center; line-height: 28px; font-weight: bold; font-size: 0.85rem;">${opt.id}</span>
              <span style="font-size: 0.92rem; line-height: 1.5;">${escapeHtml(opt.label)}</span>
            </div>
          `).join("")}
        </div>
      </div>
    `;
  }

  window.chooseMetaAnswer = (itemId, choice) => {
    if (isPaused) return;
    const rt = performance.now() - stimulusStartTime;
    currentModuleResponses.push({
      item_id: itemId,
      user_answer: choice,
      reaction_time_ms: Math.round(rt)
    });
    curIndex++;
    showMeta();
  };

  showMeta();
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str).replace(/[&<>'"]/g, 
    tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
  );
}
