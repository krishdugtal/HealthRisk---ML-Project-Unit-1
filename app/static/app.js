// HealthRisk Frontend Application Engine (Phase 3 Readability Pass)
document.addEventListener("DOMContentLoaded", () => {
  initApp();
});

// App State
let appData = {
  user: { id: 1, email: "demo@healthrisk.edu" },
  isAuthenticated: false,
  conditions: {},
  symptoms: [],
  selectedSymptoms: new Set(),
  activeAssessment: null,
  mathViewMode: "simple" // "simple" (default) or "full"
};

async function initApp() {
  setupNavigation();
  setupAgeSync();
  await checkAuth();
  setupAuthHandlers();
  await fetchConditionsAndSymptoms();
  setupComputeHandler();
  setupStatsHandler();
  setupHistoryHandler();
  setupViewToggleHandlers();
}

/* 1. AUTHENTICATION & USER SESSION */
async function checkAuth() {
  try {
    const res = await fetch("/api/me");
    const data = await res.json();
    appData.isAuthenticated = data.authenticated;
    appData.user = data.user;
    updateAuthUI();
  } catch (err) {
    console.error("Auth check failed:", err);
  }
}

function updateAuthUI() {
  const badge = document.getElementById("user-badge-email");
  const actionBtn = document.getElementById("btn-auth-action");

  if (appData.isAuthenticated) {
    badge.textContent = appData.user.email;
    actionBtn.textContent = "Logout";
  } else {
    badge.textContent = "demo@healthrisk.edu (Demo Mode)";
    actionBtn.textContent = "Login / Register";
  }
}

function setupAuthHandlers() {
  const actionBtn = document.getElementById("btn-auth-action");
  const modal = document.getElementById("auth-modal");
  const closeBtn = document.getElementById("btn-close-auth");
  const loginBtn = document.getElementById("btn-submit-login");
  const registerBtn = document.getElementById("btn-submit-register");

  actionBtn.addEventListener("click", () => {
    if (appData.isAuthenticated) {
      logoutUser();
    } else {
      modal.classList.remove("hidden");
    }
  });

  closeBtn.addEventListener("click", () => {
    modal.classList.add("hidden");
  });

  loginBtn.addEventListener("click", () => handleAuthSubmit("/api/login"));
  registerBtn.addEventListener("click", () => handleAuthSubmit("/api/register"));
}

async function handleAuthSubmit(endpoint) {
  const email = document.getElementById("auth-email").value.trim();
  const password = document.getElementById("auth-password").value;
  const errorMsg = document.getElementById("auth-error-msg");

  errorMsg.classList.add("hidden");

  if (!email || !password) {
    errorMsg.textContent = "Please fill in email and password.";
    errorMsg.classList.remove("hidden");
    return;
  }

  try {
    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });

    const data = await res.json();
    if (!res.ok) {
      errorMsg.textContent = data.detail || "Authentication failed.";
      errorMsg.classList.remove("hidden");
      return;
    }

    appData.isAuthenticated = true;
    appData.user = data.user;
    updateAuthUI();
    document.getElementById("auth-modal").classList.add("hidden");

    loadHistoricalAssessments();
    loadUserTrends();
  } catch (err) {
    errorMsg.textContent = "Server connection error.";
    errorMsg.classList.remove("hidden");
  }
}

async function logoutUser() {
  try {
    await fetch("/api/logout", { method: "POST" });
    appData.isAuthenticated = false;
    appData.user = { id: 1, email: "demo@healthrisk.edu" };
    updateAuthUI();
    loadHistoricalAssessments();
    loadUserTrends();
  } catch (err) {
    console.error("Logout failed:", err);
  }
}

/* 2. NAVIGATION & TABS */
function setupNavigation() {
  const navBtns = document.querySelectorAll(".nav-btn");
  navBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetTab = btn.getAttribute("data-tab");
      switchTab(targetTab);
    });
  });
}

function switchTab(tabId) {
  document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
  document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

  const targetBtn = document.querySelector(`.nav-btn[data-tab="${tabId}"]`);
  const targetPane = document.getElementById(tabId);

  if (targetBtn) targetBtn.classList.add("active");
  if (targetPane) targetPane.classList.add("active");

  if (tabId === "tab-stats") {
    loadPopulationStats();
  } else if (tabId === "tab-history") {
    loadHistoricalAssessments();
    loadUserTrends();
  }
}

/* 3. FORM HELPERS & RESET TO DEMO PATIENT (STEP 3) */
function setupAgeSync() {
  const ageInput = document.getElementById("patient-age");
  const ageGrpDisplay = document.getElementById("age-group-display");

  const updateBracket = () => {
    const age = parseInt(ageInput.value, 10) || 0;
    if (age < 30) {
      ageGrpDisplay.value = "<30";
    } else if (age <= 50) {
      ageGrpDisplay.value = "30-50";
    } else {
      ageGrpDisplay.value = ">50";
    }
  };

  ageInput.addEventListener("input", updateBracket);
  updateBracket();
}

function resetDemoPatient() {
  document.getElementById("patient-name").value = "Rahul Sharma";
  document.getElementById("patient-age").value = 45;
  document.getElementById("age-group-display").value = "30-50";

  const radioYes = document.querySelector("input[name='family_history'][value='yes']");
  if (radioYes) radioYes.checked = true;

  document.querySelectorAll("input[name='condition']").forEach(cb => {
    cb.checked = (cb.value === "cardiovascular" || cb.value === "diabetes_t2");
  });

  // Reference symptom combination for 88.96% Cardio
  const targetSymptoms = new Set(["unexplained_fatigue", "chest_tightness", "dizziness_headaches"]);
  appData.selectedSymptoms = targetSymptoms;

  document.querySelectorAll(".symptom-card").forEach(card => {
    const symId = card.dataset.symId;
    const checkbox = card.querySelector("input[type='checkbox']");
    if (targetSymptoms.has(symId)) {
      checkbox.checked = true;
      card.classList.add("selected");
    } else {
      checkbox.checked = false;
      card.classList.remove("selected");
    }
  });

  runAssessment();
}

/* 4. FETCH CONDITIONS & SYMPTOMS */
async function fetchConditionsAndSymptoms() {
  try {
    const res = await fetch("/api/conditions");
    const data = await res.json();
    appData.conditions = data.conditions;
    appData.symptoms = data.symptoms;
    renderSymptomsGrid(data.symptoms);
  } catch (err) {
    console.error("Failed to load condition/symptom metadata:", err);
  }
}

function renderSymptomsGrid(symptoms) {
  const container = document.getElementById("symptoms-container");
  container.innerHTML = "";

  symptoms.forEach(sym => {
    const card = document.createElement("div");
    card.className = "symptom-card";
    card.dataset.symId = sym.id;

    card.innerHTML = `
      <input type="checkbox" id="sym-${sym.id}" value="${sym.id}">
      <div class="symptom-info">
        <h4>${sym.name}</h4>
      </div>
    `;

    const checkbox = card.querySelector("input[type='checkbox']");

    card.addEventListener("click", (e) => {
      if (e.target !== checkbox) {
        checkbox.checked = !checkbox.checked;
      }
      if (checkbox.checked) {
        appData.selectedSymptoms.add(sym.id);
        card.classList.add("selected");
      } else {
        appData.selectedSymptoms.delete(sym.id);
        card.classList.remove("selected");
      }
    });

    container.appendChild(card);
  });
}

/* 5. COMPUTE BAYESIAN RISK */
function setupComputeHandler() {
  const btnCompute = document.getElementById("btn-compute");
  const btnReset = document.getElementById("btn-reset-demo");

  if (btnCompute) btnCompute.addEventListener("click", runAssessment);
  if (btnReset) btnReset.addEventListener("click", resetDemoPatient);
}

async function runAssessment() {
  const patientName = document.getElementById("patient-name").value || "Anonymous Patient";
  const age = parseInt(document.getElementById("patient-age").value, 10) || 45;
  const ageGroup = document.getElementById("age-group-display").value;
  const familyHistory = document.querySelector("input[name='family_history']:checked").value;

  const selectedConditions = Array.from(
    document.querySelectorAll("input[name='condition']:checked")
  ).map(cb => cb.value);

  if (selectedConditions.length === 0) {
    alert("Please select at least one target condition to evaluate.");
    return;
  }

  const payload = {
    patient_name: patientName,
    age: age,
    age_group: ageGroup,
    family_history: familyHistory,
    symptoms: Array.from(appData.selectedSymptoms),
    condition_ids: selectedConditions
  };

  try {
    const res = await fetch("/api/assess", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    appData.activeAssessment = data;
    renderAssessmentDashboard(data);
    switchTab("tab-dashboard");
  } catch (err) {
    console.error("Assessment error:", err);
    alert("Error calculating Bayesian posterior probabilities.");
  }
}

/* 6. VIVA MATH INSPECTOR VIEW TOGGLE (STEP 1) */
function setupViewToggleHandlers() {
  const btnSimple = document.getElementById("btn-view-simple");
  const btnFull = document.getElementById("btn-view-full");

  if (btnSimple && btnFull) {
    btnSimple.addEventListener("click", () => {
      appData.mathViewMode = "simple";
      btnSimple.classList.add("active");
      btnSimple.style.background = "var(--accent-primary)";
      btnSimple.style.color = "#FFFFFF";

      btnFull.classList.remove("active");
      btnFull.style.background = "transparent";
      btnFull.style.color = "var(--text-secondary)";

      if (appData.activeAssessment) {
        renderAssessmentDashboard(appData.activeAssessment);
      }
    });

    btnFull.addEventListener("click", () => {
      appData.mathViewMode = "full";
      btnFull.classList.add("active");
      btnFull.style.background = "var(--accent-primary)";
      btnFull.style.color = "#FFFFFF";

      btnSimple.classList.remove("active");
      btnSimple.style.background = "transparent";
      btnSimple.style.color = "var(--text-secondary)";

      if (appData.activeAssessment) {
        renderAssessmentDashboard(appData.activeAssessment);
      }
    });
  }
}

/* 7. RENDER DASHBOARD & VIVA MATH INSPECTOR */
function renderAssessmentDashboard(data) {
  document.getElementById("no-results-placeholder").classList.add("hidden");
  document.getElementById("results-container").classList.remove("hidden");

  // Summary bar
  document.getElementById("res-patient-name").textContent = data.patient.name;
  document.getElementById("res-patient-age").textContent = `${data.patient.age} years (${data.patient.age_group})`;
  document.getElementById("res-patient-family").textContent = data.patient.family_history.toUpperCase();
  document.getElementById("res-symptoms-count").textContent = `${data.reported_symptoms.length} Symptoms Selected`;
  document.getElementById("res-db-id").textContent = `#${data.assessment_id}`;

  // Risk Bars
  const riskBarsContainer = document.getElementById("risk-bars-container");
  riskBarsContainer.innerHTML = "";

  // Viva Math Inspector container
  const mathContainer = document.getElementById("math-breakdown-container");
  mathContainer.innerHTML = "";

  Object.keys(data.results).forEach(condId => {
    const res = data.results[condId];

    // Risk Bar Card
    const barCard = document.createElement("div");
    barCard.className = "risk-card glass-card";

    let riskClass = "risk-low";
    if (res.risk_level === "Moderate Risk") riskClass = "risk-moderate";
    else if (res.risk_level === "Elevated Risk") riskClass = "risk-elevated";
    else if (res.risk_level === "High Risk") riskClass = "risk-high";

    let fillGradient = "linear-gradient(90deg, #34C759, #28A745)";
    if (res.risk_level === "Moderate Risk") fillGradient = "linear-gradient(90deg, #FF9500, #E08200)";
    else if (res.risk_level === "Elevated Risk") fillGradient = "linear-gradient(90deg, #FF6B00, #D95300)";
    else if (res.risk_level === "High Risk") fillGradient = "linear-gradient(90deg, #FF3B30, #D70015)";

    barCard.innerHTML = `
      <div class="risk-card-header">
        <h3>${res.condition_name}</h3>
        <span class="risk-level-tag ${riskClass}">${res.risk_level}</span>
      </div>
      <div class="bar-wrapper">
        <div class="bar-fill" style="width: ${Math.max(4, res.posterior_percentage)}%; background: ${fillGradient};"></div>
      </div>
      <div style="display: flex; justify-content: space-between; align-items: baseline;">
        <span class="risk-percentage">${res.posterior_percentage}%</span>
        <span style="font-size: 0.85rem; color: var(--text-secondary);">Posterior P(C|S)</span>
      </div>
    `;
    riskBarsContainer.appendChild(barCard);

    // Math Viva Card
    const mathCard = document.createElement("div");
    mathCard.className = "math-condition-card glass-card";

    if (appData.mathViewMode === "simple") {
      // SIMPLE VIEW (STEP 1): High-level 4-step summary for clean first-glance demo
      mathCard.innerHTML = `
        <div class="card-header">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--accent-primary)" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          <div>
            <h3 style="font-size: 1.15rem; font-weight: 600;">Mathematical Summary: ${res.condition_name}</h3>
            <p>Simple Overview Mode • Toggle "Full Math View" above to inspect Bernoulli table & detailed products</p>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin-bottom: 1rem;">
          <div class="math-step-block">
            <div class="math-step-title">STEP 1: Prior P(C)</div>
            <div class="math-formula-box" style="font-size: 0.85rem;">P(C) = ${res.prior_step.adjusted_prior_p_c}</div>
          </div>

          <div class="math-step-block">
            <div class="math-step-title">STEP 2: Likelihood P(S|C)</div>
            <div class="math-formula-box" style="font-size: 0.85rem;">P(S|C) = ${res.joint_likelihood_given_c.toExponential(3)}</div>
          </div>

          <div class="math-step-block">
            <div class="math-step-title">STEP 3: Evidence P(S)</div>
            <div class="math-formula-box" style="font-size: 0.85rem;">P(S) = ${res.evidence_marginal_p_s.toExponential(3)}</div>
          </div>

          <div class="math-step-block" style="border-color: rgba(52, 199, 89, 0.4); background: var(--accent-emerald-tint);">
            <div class="math-step-title" style="color: #1E8E3E;">STEP 4: Posterior P(C|S)</div>
            <div class="math-formula-box" style="font-size: 0.95rem; font-weight: 700; border-left-color: #34C759;">${res.posterior_percentage}%</div>
          </div>
        </div>
      `;
    } else {
      // FULL MATH VIEW: Complete step-by-step breakdown & table with Step 2 Relabeled Note
      let symptomRowsHtml = res.symptoms_evaluated.map(sym => `
        <tr>
          <td><strong>${sym.symptom_name}</strong></td>
          <td><span class="code-badge">${sym.present ? "PRESENT (S=1)" : "ABSENT (S=0)"}</span></td>
          <td style="font-family: var(--font-mono);">${sym.p_s_given_c} ${sym.present ? '' : '<span style="font-size:0.75rem; color:var(--text-muted);">(1-P)</span>'}</td>
          <td style="font-family: var(--font-mono);">${sym.p_s_given_not_c} ${sym.present ? '' : '<span style="font-size:0.75rem; color:var(--text-muted);">(1-P)</span>'}</td>
        </tr>
      `).join("");

      mathCard.innerHTML = `
        <div class="card-header">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--accent-primary)" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          <div>
            <h3 style="font-size: 1.15rem; font-weight: 600;">Full Mathematical Derivation: ${res.condition_name}</h3>
            <p>Manual Naive-Bayes Chaining across reported & evaluated symptoms</p>
          </div>
        </div>

        <!-- Step 1: Prior -->
        <div class="math-step-block">
          <div class="math-step-title">
            <span>STEP 1: Dynamic Prior Probability P(C)</span>
          </div>
          <p style="font-size: 0.88rem; color: var(--text-secondary);">
            P(C) = P<sub>base</sub> (${res.prior_step.base_prior}) × Factor<sub>age</sub> (${res.prior_step.age_factor}) × Factor<sub>family</sub> (${res.prior_step.family_history_factor})
          </p>
          <div class="math-formula-box">${res.math_formula_steps.step_1_prior}</div>
        </div>

        <!-- Step 2: Symptom Bernoulli Likelihoods (STEP 2 NOTE & RELABELING) -->
        <div class="math-step-block">
          <div class="math-step-title">
            <span>STEP 2: Bernoulli Conditional Likelihoods P(S<sub>i</sub>|C)</span>
          </div>
          
          <p style="font-size: 0.82rem; color: var(--text-primary); margin-top: 0.4rem; margin-bottom: 0.75rem; background: var(--accent-primary-tint); padding: 0.6rem 0.85rem; border-radius: 8px; border-left: 3px solid var(--accent-primary);">
            💡 <strong>Likelihood Table Note:</strong> For reported symptoms (S<sub>i</sub>=1), table displays conditional likelihood P(S<sub>i</sub>=1|C) directly. For absent symptoms (S<sub>i</sub>=0), table displays derived complement probability P(S<sub>i</sub>=0|C) = 1 - P(S<sub>i</sub>=1|C).
          </p>

          <div class="table-responsive margin-bottom-lg">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Symptom Evaluated</th>
                  <th>Observation</th>
                  <th>P(Observed State | C)</th>
                  <th>P(Observed State | ¬C)</th>
                </tr>
              </thead>
              <tbody>${symptomRowsHtml}</tbody>
            </table>
          </div>
          <p style="font-size: 0.85rem; color: var(--text-secondary);">
            Joint Likelihood Product P(S|C) = ∏ P(S<sub>i</sub>|C):
          </p>
          <div class="math-formula-box">${res.math_formula_steps.step_2_likelihood}</div>
        </div>

        <!-- Step 3: Evidence Denominator -->
        <div class="math-step-block">
          <div class="math-step-title">
            <span>STEP 3: Marginal Likelihood / Evidence Denominator P(S)</span>
          </div>
          <p style="font-size: 0.85rem; color: var(--text-secondary);">
            P(S) = P(S|C)·P(C) + P(S|¬C)·P(¬C) [Law of Total Probability]
          </p>
          <div class="math-formula-box">${res.math_formula_steps.step_3_evidence}</div>
        </div>

        <!-- Step 4: Final Posterior -->
        <div class="math-step-block" style="border-color: rgba(56, 189, 248, 0.4); background: rgba(56, 189, 248, 0.05);">
          <div class="math-step-title" style="color: var(--accent-emerald);">
            <span>STEP 4: Final Bayes' Rule Posterior P(C|S)</span>
          </div>
          <div class="math-formula-box" style="border-left-color: var(--accent-emerald); font-size: 0.95rem; font-weight: 600;">
${res.math_formula_steps.step_4_posterior}
          </div>
        </div>
      `;
    }

    mathContainer.appendChild(mathCard);
  });
}

/* 8. POPULATION STATS & CSV IMPORT */
function setupStatsHandler() {
  const refreshBtn = document.getElementById("btn-refresh-stats");
  const uploadBtn = document.getElementById("btn-upload-csv");
  const fileInput = document.getElementById("csv-file-input");

  if (refreshBtn) refreshBtn.addEventListener("click", loadPopulationStats);
  if (uploadBtn && fileInput) {
    uploadBtn.addEventListener("click", () => fileInput.click());
    fileInput.addEventListener("change", handleCSVUpload);
  }
}

async function handleCSVUpload(e) {
  const file = e.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch("/population_stats/upload_csv", {
      method: "POST",
      body: formData
    });

    const data = await res.json();
    if (!res.ok) {
      alert(`CSV Upload Error: ${data.detail || "Invalid CSV format."}`);
      return;
    }

    alert(data.message);
    loadPopulationStats();
  } catch (err) {
    console.error("CSV upload failed:", err);
    alert("Failed to upload CSV file.");
  }
}

async function loadPopulationStats() {
  try {
    const [expVarRes, covRes, fullStatsRes] = await Promise.all([
      fetch("/population_stats/expectation_variance").then(r => r.json()),
      fetch("/population_stats/covariance").then(r => r.json()),
      fetch("/api/statistics").then(r => r.json())
    ]);

    document.getElementById("active-dataset-label").textContent = 
      `${fullStatsRes.dataset_name || 'Active Dataset'} — Used strictly for population-level RV statistics, separate from per-patient Bayesian inference.`;

    document.getElementById("stat-e-risk").textContent = `${expVarRes.mean}%`;
    document.getElementById("stat-var-risk").textContent = `${expVarRes.variance}`;
    document.getElementById("stat-sd-risk").textContent = `${expVarRes.standard_deviation}`;

    if (fullStatsRes.expectation && fullStatsRes.expectation.bmi) {
      document.getElementById("stat-e-bmi").textContent = `${fullStatsRes.expectation.bmi.mean || fullStatsRes.expectation.bmi.expected_value} kg/m²`;
      document.getElementById("stat-e-bp").textContent = `${fullStatsRes.expectation.systolic_bp.mean || fullStatsRes.expectation.systolic_bp.expected_value} mmHg`;

      document.getElementById("stat-var-bmi").textContent = `${fullStatsRes.variance.bmi.variance} (SD: ${fullStatsRes.variance.bmi.standard_deviation})`;
      document.getElementById("stat-var-bp").textContent = `${fullStatsRes.variance.systolic_bp.variance} (SD: ${fullStatsRes.variance.systolic_bp.standard_deviation})`;
    }

    document.getElementById("stat-cov-val").textContent = `${covRes.covariance}`;
    document.getElementById("stat-cov-n").textContent = `${covRes.n}`;
    document.getElementById("stat-cov-interp").textContent = covRes.interpretation;

    document.getElementById("formula-box-expectation").textContent = 
      `E[X] = (1/${expVarRes.n}) * ∑ x_i = ${expVarRes.mean}%`;
    document.getElementById("formula-box-variance").textContent = 
      `Var(X) = (1/${expVarRes.n}) * ∑ (x_i - ${expVarRes.mean})² = ${expVarRes.variance} (SD = ${expVarRes.standard_deviation})`;
    document.getElementById("formula-box-covariance").textContent = 
      `Cov(BMI, BP) = (1/${covRes.n}) * ∑ (BMI_i - ${covRes.mean_x})(BP_i - ${covRes.mean_y}) = ${covRes.covariance}\n→ Interpretation: ${covRes.interpretation}`;

    if (fullStatsRes.records) {
      renderScatterPlot(fullStatsRes.records, covRes.mean_x, covRes.mean_y);
      renderPopulationTable(fullStatsRes.records);
    }
  } catch (err) {
    console.error("Failed to fetch statistics:", err);
  }
}

function renderScatterPlot(records, meanX, meanY) {
  const canvas = document.getElementById("scatter-canvas");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;

  ctx.clearRect(0, 0, width, height);

  const padding = { top: 30, right: 30, bottom: 40, left: 50 };
  const graphWidth = width - padding.left - padding.right;
  const graphHeight = height - padding.top - padding.bottom;

  const bmiValues = records.map(r => r.bmi);
  const bpValues = records.map(r => r.systolic_bp);

  const minX = Math.floor(Math.min(...bmiValues) - 2);
  const maxX = Math.ceil(Math.max(...bmiValues) + 2);
  const minY = Math.floor(Math.min(...bpValues) - 10);
  const maxY = Math.ceil(Math.max(...bpValues) + 10);

  const scaleX = x => padding.left + ((x - minX) / (maxX - minX)) * graphWidth;
  const scaleY = y => padding.top + graphHeight - ((y - minY) / (maxY - minY)) * graphHeight;

  ctx.strokeStyle = "rgba(0, 0, 0, 0.08)";
  ctx.lineWidth = 1;

  for (let x = Math.ceil(minX); x <= maxX; x += 5) {
    const px = scaleX(x);
    ctx.beginPath();
    ctx.moveTo(px, padding.top);
    ctx.lineTo(px, height - padding.bottom);
    ctx.stroke();

    ctx.fillStyle = "#86868B";
    ctx.font = "10px -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif";
    ctx.fillText(`${x}`, px - 6, height - padding.bottom + 15);
  }

  for (let y = Math.ceil(minY); y <= maxY; y += 10) {
    const py = scaleY(y);
    ctx.beginPath();
    ctx.moveTo(padding.left, py);
    ctx.lineTo(width - padding.right, py);
    ctx.stroke();

    ctx.fillStyle = "#86868B";
    ctx.font = "10px -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif";
    ctx.fillText(`${y}`, padding.left - 30, py + 3);
  }

  ctx.fillStyle = "#1D1D1F";
  ctx.font = "12px -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif";
  ctx.fillText("BMI (kg/m²)", width / 2 - 30, height - 8);

  ctx.save();
  ctx.translate(15, height / 2 + 30);
  ctx.rotate(-Math.PI / 2);
  ctx.fillText("Systolic BP (mmHg)", 0, 0);
  ctx.restore();

  records.forEach(r => {
    const cx = scaleX(r.bmi);
    const cy = scaleY(r.systolic_bp);

    ctx.beginPath();
    ctx.arc(cx, cy, 5, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(0, 113, 227, 0.75)";
    ctx.fill();
    ctx.strokeStyle = "#0071E3";
    ctx.lineWidth = 1.5;
    ctx.stroke();
  });

  const meanPx = scaleX(meanX);
  const meanPy = scaleY(meanY);

  ctx.beginPath();
  ctx.arc(meanPx, meanPy, 11, 0, Math.PI * 2);
  ctx.fillStyle = "rgba(255, 149, 0, 0.25)";
  ctx.fill();
  ctx.strokeStyle = "#FF9500";
  ctx.lineWidth = 2;
  ctx.stroke();

  ctx.beginPath();
  ctx.arc(meanPx, meanPy, 5, 0, Math.PI * 2);
  ctx.fillStyle = "#FF9500";
  ctx.fill();

  ctx.fillStyle = "#B25900";
  ctx.font = "600 11px ui-monospace, SFMono-Regular, monospace";
  ctx.fillText(`Mean Point (E[BMI]: ${meanX.toFixed(1)}, E[BP]: ${meanY.toFixed(1)})`, meanPx + 14, meanPy + 4);
}

function renderPopulationTable(records) {
  const tbody = document.getElementById("population-table-body");
  const desc = document.getElementById("dataset-table-desc");
  if (!tbody) return;

  if (desc) desc.textContent = `Showing ${records.length} active records.`;

  tbody.innerHTML = records.map(r => `
    <tr>
      <td><span class="code-badge">${r.patient_id}</span></td>
      <td>${r.age}</td>
      <td>${r.bmi}</td>
      <td>${r.systolic_bp}</td>
      <td><strong style="color: var(--accent-primary);">${r.risk_score}%</strong></td>
    </tr>
  `).join("");
}

/* 9. PERSONAL RISK TRENDS */
async function loadUserTrends() {
  const container = document.getElementById("user-trends-container");
  if (!container) return;

  try {
    const res = await fetch("/api/user_trends");
    const data = await res.json();

    if (!data.has_trends) {
      container.innerHTML = `
        <div class="text-center padding-xl" style="background: var(--bg-body); border-radius: var(--radius-sm); border: 1px solid var(--border-color);">
          <p style="color: #B25900; font-weight: 600;">ℹ️ Insufficient Time-Series Data for Personal Trends</p>
          <p style="font-size: 0.88rem; color: var(--text-secondary); margin-top: 0.4rem;">
            ${data.message}
          </p>
        </div>
      `;
      return;
    }

    let trendCardsHtml = "";
    Object.keys(data.trends).forEach(condId => {
      const t = data.trends[condId];
      trendCardsHtml += `
        <div class="stat-card glass-card" style="margin-bottom: 1rem; background: #FFFFFF;">
          <div class="stat-card-header">
            <span class="stat-label">${t.condition_name.toUpperCase()} TIME-SERIES</span>
            <span class="stat-formula">n = ${t.scores_history.length} Runs</span>
          </div>
          <div style="display: flex; gap: 2.5rem; align-items: baseline; margin-top: 0.5rem; flex-wrap: wrap;">
            <div>
              <span class="meta-label">EXPECTATION E[Risk]</span>
              <span class="stat-value" style="font-size: 1.75rem; color: #1E8E3E;">${t.mean}%</span>
            </div>
            <div>
              <span class="meta-label">VARIANCE Var(Risk)</span>
              <span class="stat-value" style="font-size: 1.75rem; color: var(--accent-primary);">${t.variance}</span>
            </div>
            <div>
              <span class="meta-label">STD DEV SD(Risk)</span>
              <span class="stat-value" style="font-size: 1.75rem; color: #B25900;">${t.standard_deviation}</span>
            </div>
          </div>
          <div style="font-size: 0.82rem; font-family: var(--font-mono); color: var(--text-secondary); margin-top: 0.75rem; background: var(--bg-body); padding: 0.55rem 0.85rem; border-radius: 6px;">
            Personal Scores History: [ ${t.scores_history.join("%, ")}% ]
          </div>
        </div>
      `;
    });

    container.innerHTML = trendCardsHtml;
  } catch (err) {
    console.error("Failed to load user trends:", err);
  }
}

/* 10. HISTORICAL ASSESSMENTS LOG */
function setupHistoryHandler() {
  const refreshBtn = document.getElementById("btn-refresh-history");
  if (refreshBtn) {
    refreshBtn.addEventListener("click", () => {
      loadHistoricalAssessments();
      loadUserTrends();
    });
  }
}

async function loadHistoricalAssessments() {
  const tbody = document.getElementById("history-table-body");
  if (!tbody) return;

  tbody.innerHTML = `<tr><td colspan="8" class="text-center">Loading audit log...</td></tr>`;

  try {
    const res = await fetch("/api/assessments");
    const data = await res.json();

    if (data.assessments.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" class="text-center">No assessments saved for your account yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = data.assessments.map(item => {
      const dateStr = new Date(item.created_at).toLocaleString();
      const symptomsList = item.symptoms.length > 0 ? item.symptoms.join(", ") : "None";
      
      let resultsSummary = [];
      Object.keys(item.results).forEach(k => {
        const r = item.results[k];
        resultsSummary.push(`${r.condition_name}: ${r.posterior_percentage}%`);
      });

      return `
        <tr>
          <td><span class="code-badge">#${item.id}</span></td>
          <td style="font-size: 0.8rem; color: var(--text-secondary);">${dateStr}</td>
          <td><strong>${item.patient_name}</strong></td>
          <td>${item.age} (${item.age_group})</td>
          <td>${item.family_history.toUpperCase()}</td>
          <td style="font-size: 0.8rem;">${symptomsList}</td>
          <td style="font-size: 0.8rem; color: var(--accent-primary);">${resultsSummary.join(" | ")}</td>
          <td>
            <button class="btn-secondary" style="padding: 0.25rem 0.6rem; font-size: 0.75rem;" onclick="viewHistoryItem(${item.id})">
              Inspect Math
            </button>
          </td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    console.error("Error loading historical assessments:", err);
    tbody.innerHTML = `<tr><td colspan="8" class="text-center" style="color: var(--accent-crimson);">Failed to load audit history.</td></tr>`;
  }
}

async function viewHistoryItem(id) {
  try {
    const res = await fetch(`/api/assessments/${id}`);
    const item = await res.json();
    
    const formattedData = {
      assessment_id: item.id,
      patient: {
        name: item.patient_name,
        age: item.age,
        age_group: item.age_group,
        family_history: item.family_history
      },
      reported_symptoms: item.symptoms,
      results: item.results
    };

    appData.activeAssessment = formattedData;
    renderAssessmentDashboard(formattedData);
    switchTab("tab-dashboard");
  } catch (err) {
    console.error("Failed to load history item:", err);
  }
}
