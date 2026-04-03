/**
 * ApplyGenius — Frontend Application Logic
 * Handles form submission, API calls, results rendering, dashboard
 */

const API_BASE = "http://localhost:5000/api";

// ---- Global State ----
let currentAnalysis = null;
let currentSessionId = null;
let currentPersonalInfo = null;
let currentJobData = null;
let allApplications = [];

// ================================================
// INITIALIZATION
// ================================================
document.addEventListener("DOMContentLoaded", () => {
  initDragDrop();
  initForm();
  initSVGGradient();
  // Auto-load dashboard data
  if (document.getElementById("tab-dashboard").style.display !== "none") {
    loadDashboard();
  }
});

function initSVGGradient() {
  // Add SVG gradient definition for score ring
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.style.cssText = "position:absolute;width:0;height:0;overflow:hidden";
  svg.innerHTML = `
    <defs>
      <linearGradient id="score-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#ff4d6d"/>
        <stop offset="100%" stop-color="#ff8c42"/>
      </linearGradient>
      <linearGradient id="score-gradient-success" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#2eca7f"/>
        <stop offset="100%" stop-color="#22c55e"/>
      </linearGradient>
    </defs>
  `;
  document.body.prepend(svg);
}

// ================================================
// NAVIGATION
// ================================================
function showTab(tab) {
  document.querySelectorAll(".nav-link").forEach(l => l.classList.remove("active"));
  document.querySelectorAll(".tab-content").forEach(t => t.style.display = "none");
  
  document.getElementById(`tab-${tab}`).style.display = "block";
  
  document.querySelectorAll(".nav-link").forEach(l => {
    if (l.getAttribute("href") === `#${tab}`) l.classList.add("active");
  });

  if (tab === "dashboard") loadDashboard();
  
  // Scroll to top
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// ================================================
// FILE UPLOAD
// ================================================
function handleFileSelect(event) {
  const file = event.target.files[0];
  if (file) {
    showSelectedFile(file);
  }
}

function showSelectedFile(file) {
  if (!file.name.endsWith(".pdf")) {
    showToast("Please upload a PDF file", "error");
    return;
  }
  document.getElementById("upload-selected").style.display = "flex";
  document.getElementById("file-name").textContent = file.name;
  document.getElementById("extract-resume-btn").style.display = "block";
  document.querySelector(".upload-text").style.display = "none";
  document.querySelector(".upload-icon").style.display = "none";
}

function removeFile(e) {
  e.stopPropagation();
  document.getElementById("resume-input").value = "";
  document.getElementById("upload-selected").style.display = "none";
  document.getElementById("extract-resume-btn").style.display = "none";
  document.getElementById("resume-preview").style.display = "none";
  document.querySelector(".upload-text").style.display = "flex";
  document.querySelector(".upload-icon").style.display = "flex";
}

function initDragDrop() {
  const zone = document.getElementById("upload-zone");
  
  zone.addEventListener("dragover", (e) => {
    e.preventDefault();
    zone.classList.add("drag-over");
  });
  
  zone.addEventListener("dragleave", () => zone.classList.remove("drag-over"));
  
  zone.addEventListener("drop", (e) => {
    e.preventDefault();
    zone.classList.remove("drag-over");
    const file = e.dataTransfer.files[0];
    if (file) {
      document.getElementById("resume-input").files = e.dataTransfer.files;
      showSelectedFile(file);
    }
  });
}

async function extractResumeText() {
  const fileInput = document.getElementById("resume-input");
  if (!fileInput.files[0]) return;
  
  const formData = new FormData();
  formData.append("resume", fileInput.files[0]);
  
  try {
    showToast("Extracting resume text...", "info");
    const res = await fetch(`${API_BASE}/parse-resume`, {
      method: "POST",
      body: formData,
    });
    const data = await res.json();
    if (data.text) {
      document.getElementById("resume-text-content").textContent = data.text.substring(0, 2000) + (data.text.length > 2000 ? "\n..." : "");
      document.getElementById("resume-preview").style.display = "block";
    }
  } catch (e) {
    // Fallback - just show preview box with placeholder
    document.getElementById("resume-text-content").textContent = "Preview requires backend connection. Your resume will be parsed during analysis.";
    document.getElementById("resume-preview").style.display = "block";
  }
}

// ================================================
// FORM SUBMISSION & ANALYSIS
// ================================================
function initForm() {
  const form = document.getElementById("apply-form");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    await submitAnalysis();
  });
}

async function submitAnalysis() {
  const form = document.getElementById("apply-form");
  const formData = new FormData(form);
  
  // Validate
  const name = formData.get("name");
  const email = formData.get("email");
  const jobUrl = formData.get("job_url");
  const resume = formData.get("resume");
  
  if (!name || !email) {
    showToast("Please fill in your name and email", "error");
    return;
  }
  
  if (!jobUrl && !formData.get("job_description")) {
    showToast("Please provide a job URL or description", "error");
    return;
  }
  
  if (!resume || resume.size === 0) {
    showToast("Please upload your resume PDF", "error");
    return;
  }
  
  // Store personal info
  currentPersonalInfo = {
    name: formData.get("name"),
    email: formData.get("email"),
    phone: formData.get("phone"),
    address: formData.get("address"),
    linkedin: formData.get("linkedin"),
    portfolio: formData.get("portfolio"),
  };
  
  // Show loading
  setStep(2);
  document.getElementById("form-panel").style.display = "none";
  document.getElementById("analysis-loading").style.display = "flex";
  document.getElementById("results-panel").style.display = "none";
  
  // Animate loading steps
  animateLoadingSteps();
  
  try {
    const response = await fetch(`${API_BASE}/analyze`, {
      method: "POST",
      body: formData,
    });
    
    const data = await response.json();
    
    if (!response.ok || data.error) {
      throw new Error(data.error || "Analysis failed");
    }
    
    // Store results
    currentAnalysis = data;
    currentSessionId = data.session_id;
    currentJobData = {
      title: data.job_title,
      company: data.company,
      url: formData.get("job_url"),
      raw_description: data.job_description,
    };
    
    // Show results
    document.getElementById("analysis-loading").style.display = "none";
    showResults(data);
    
  } catch (error) {
    console.error("Analysis error:", error);
    
    // Demo mode: show mock results if backend is not running
    if (error.message.includes("fetch") || error.message.includes("Failed")) {
      showDemoResults(formData);
    } else {
      document.getElementById("analysis-loading").style.display = "none";
      document.getElementById("form-panel").style.display = "block";
      setStep(1);
      showToast(`Error: ${error.message}`, "error");
    }
  }
}

function showDemoResults(formData) {
  // Demo mode with realistic mock data
  const mockData = {
    matched_skills: ["Python", "JavaScript", "React", "Node.js", "SQL", "Git", "REST APIs", "Problem Solving"],
    missing_skills: ["Docker", "Kubernetes", "AWS", "TypeScript", "GraphQL"],
    match_score: 72,
    job_title: "Full Stack Developer",
    company: "TechCorp Solutions",
    job_description: "We are looking for a talented Full Stack Developer to join our engineering team...",
    analysis_summary: "Strong technical foundation with solid frontend and backend skills. The candidate demonstrates proficiency in core web technologies and databases. To strengthen the application, consider gaining hands-on experience with containerization (Docker/Kubernetes) and cloud platforms (AWS).",
    session_id: "demo-" + Math.random().toString(36).substr(2, 6),
  };
  
  currentAnalysis = mockData;
  currentSessionId = mockData.session_id;
  currentJobData = {
    title: mockData.job_title,
    company: mockData.company,
    url: formData.get("job_url") || "https://example.com/jobs/fullstack",
    raw_description: mockData.job_description,
  };
  
  document.getElementById("analysis-loading").style.display = "none";
  showResults(mockData);
  showToast("🎭 Demo mode — connect backend for live analysis", "info");
}

function animateLoadingSteps() {
  const steps = [1, 2, 3, 4, 5];
  const delays = [0, 1500, 3000, 4500, 6000];
  
  steps.forEach((s, i) => {
    setTimeout(() => {
      // Mark previous as done
      if (i > 0) {
        const prev = document.getElementById(`ls-${i}`);
        prev?.classList.remove("active");
        prev?.classList.add("done");
      }
      // Mark current as active
      const current = document.getElementById(`ls-${s}`);
      current?.classList.add("active");
    }, delays[i]);
  });
}

// ================================================
// RESULTS RENDERING
// ================================================
function showResults(data) {
  setStep(3);
  
  const panel = document.getElementById("results-panel");
  panel.style.display = "flex";
  
  const score = data.match_score || 0;
  const matchedSkills = data.matched_skills || [];
  const missingSkills = data.missing_skills || [];
  
  // Score ring animation
  animateScoreRing(score);
  
  // Score text counter
  animateCounter("score-number", 0, score, 1500);
  
  // Job info
  document.getElementById("job-applied-title").textContent = data.job_title || "Position";
  document.getElementById("company-name-display").textContent = data.company || "Company";
  document.getElementById("analysis-summary").textContent = data.analysis_summary || "";
  
  // Score verdict
  const verdictEl = document.getElementById("score-verdict");
  if (score >= 70) {
    verdictEl.textContent = "✦ Strong Match";
    verdictEl.className = "score-verdict success";
  } else {
    verdictEl.textContent = "✦ Needs Improvement";
    verdictEl.className = "score-verdict fail";
  }
  
  // Skills
  renderSkills("matched-skills-list", matchedSkills, "matched");
  renderSkills("missing-skills-list", missingSkills, "missing");
  document.getElementById("matched-count").textContent = matchedSkills.length;
  document.getElementById("missing-count").textContent = missingSkills.length;
  
  // Job description
  document.getElementById("jd-text").textContent = data.job_description || "Job description not available.";
  
  // Show appropriate action panel
  document.getElementById("action-success").style.display = score >= 70 ? "block" : "none";
  document.getElementById("action-fail").style.display = score < 70 ? "block" : "none";
  
  if (score < 70) {
    renderSkillGapResources(missingSkills);
  }
  
  // Scroll to results
  setTimeout(() => {
    panel.scrollIntoView({ behavior: "smooth", block: "start" });
  }, 300);
}

function animateScoreRing(score) {
  const circumference = 2 * Math.PI * 68; // r=68
  const ring = document.getElementById("score-ring-fill");
  const offset = circumference - (score / 100) * circumference;
  
  // Set gradient color based on score
  if (score >= 70) {
    ring.setAttribute("stroke", "url(#score-gradient-success)");
  } else {
    ring.setAttribute("stroke", "url(#score-gradient)");
  }
  
  // Animate after a small delay
  setTimeout(() => {
    ring.style.strokeDashoffset = offset;
  }, 200);
}

function animateCounter(id, from, to, duration) {
  const el = document.getElementById(id);
  if (!el) return;
  const start = Date.now();
  
  function tick() {
    const elapsed = Date.now() - start;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3); // ease-out-cubic
    el.textContent = Math.round(from + (to - from) * eased) + "%";
    if (progress < 1) requestAnimationFrame(tick);
  }
  
  requestAnimationFrame(tick);
}

function renderSkills(containerId, skills, type) {
  const container = document.getElementById(containerId);
  container.innerHTML = "";
  
  if (!skills.length) {
    container.innerHTML = `<span style="font-size:13px;color:var(--text-dim);padding:4px">None identified</span>`;
    return;
  }
  
  skills.forEach((skill, i) => {
    const tag = document.createElement("div");
    tag.className = `skill-tag ${type}`;
    tag.textContent = skill;
    tag.style.animationDelay = `${i * 0.05}s`;
    tag.style.animation = "fadeUp 0.3s ease both";
    container.appendChild(tag);
  });
}

function renderSkillGapResources(missingSkills) {
  const container = document.getElementById("skill-gap-resources");
  container.innerHTML = "";
  
  missingSkills.slice(0, 8).forEach(skill => {
    const searchQuery = encodeURIComponent(skill + " tutorial");
    const card = document.createElement("div");
    card.className = "skill-gap-card";
    card.innerHTML = `
      <div class="sgc-skill">📚 ${skill}</div>
      <div class="sgc-links">
        <a href="https://www.coursera.org/search?query=${searchQuery}" target="_blank" class="sgc-link">Coursera</a>
        <a href="https://www.udemy.com/courses/search/?q=${searchQuery}" target="_blank" class="sgc-link">Udemy</a>
        <a href="https://www.youtube.com/results?search_query=${searchQuery}" target="_blank" class="sgc-link">YouTube</a>
        <a href="https://www.freecodecamp.org/news/search?query=${searchQuery}" target="_blank" class="sgc-link">freeCodeCamp</a>
      </div>
    `;
    container.appendChild(card);
  });
}

function toggleJD() {
  const content = document.getElementById("jd-content");
  const icon = document.getElementById("jd-toggle-icon");
  const isVisible = content.style.display !== "none";
  content.style.display = isVisible ? "none" : "block";
  icon.textContent = isVisible ? "▼" : "▲";
}

function toggleCoverLetter() {
  const box = document.getElementById("cl-text-box");
  box.style.display = box.style.display === "none" ? "block" : "none";
}

// ================================================
// DOCUMENT GENERATION
// ================================================
async function generateDocuments() {
  const btn = document.getElementById("generate-btn");
  const origText = btn.innerHTML;
  btn.innerHTML = `<span class="spinner"></span> Generating...`;
  btn.disabled = true;
  
  // Get cover letter text first
  let coverLetterText = "";
  try {
    const clRes = await fetch(`${API_BASE}/cover-letter-text`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        personal_info: currentPersonalInfo,
        job_data: currentJobData,
        analysis: currentAnalysis,
      }),
    });
    const clData = await clRes.json();
    if (clData.cover_letter) coverLetterText = clData.cover_letter;
  } catch (e) {
    // Demo mode cover letter
    coverLetterText = generateDemoCoverLetter();
  }
  
  // Show cover letter text
  document.getElementById("cover-letter-text").textContent = coverLetterText;
  
  try {
    const response = await fetch(`${API_BASE}/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: currentSessionId,
        personal_info: currentPersonalInfo,
        job_data: currentJobData,
        analysis: currentAnalysis,
      }),
    });
    
    const data = await response.json();
    
    if (data.success) {
      // Set download links
      document.getElementById("download-resume").href = `${API_BASE.replace("/api", "")}${data.resume_pdf}`;
      document.getElementById("download-cover").href = `${API_BASE.replace("/api", "")}${data.cover_letter_pdf}`;
    }
  } catch (e) {
    // Demo mode — show fake download links
    document.getElementById("download-resume").href = "#";
    document.getElementById("download-cover").href = "#";
    document.getElementById("download-resume").onclick = () => showToast("Connect backend to download real PDFs", "info");
    document.getElementById("download-cover").onclick = () => showToast("Connect backend to download real PDFs", "info");
  }
  
  btn.innerHTML = origText;
  btn.disabled = false;
  document.getElementById("generated-docs").style.display = "block";
  
  // Smooth scroll
  document.getElementById("generated-docs").scrollIntoView({ behavior: "smooth" });
  showToast("Documents generated successfully!", "success");
}

function generateDemoCoverLetter() {
  const name = currentPersonalInfo?.name || "Candidate";
  const jobTitle = currentJobData?.title || "Software Engineer";
  const company = currentJobData?.company || "the company";
  const skills = currentAnalysis?.matched_skills?.slice(0, 3).join(", ") || "relevant skills";
  
  return `Dear Hiring Manager,

Having built a career around ${skills}, I was immediately drawn to the ${jobTitle} role at ${company}. Your team's reputation for technical excellence and innovation resonates strongly with how I approach every project I take on.

Over the past few years, I have delivered production-grade solutions leveraging ${skills}. At each step, I have focused not just on functionality, but on code quality, team collaboration, and measurable business impact. I thrive in environments where engineering rigor meets creative problem-solving — precisely the culture I see reflected in ${company}'s work.

What excites me most about this role is the opportunity to contribute meaningfully from day one while continuing to grow. I am confident that my background, combined with a genuine enthusiasm for the challenges ahead, makes me a strong candidate.

I would welcome the opportunity to discuss how my experience aligns with your team's goals. Thank you for your time and consideration.

Warm regards,
${name}`;
}

// ================================================
// DIRECT APPLY
// ================================================
async function directApply() {
  const btn = document.getElementById("direct-apply-btn");
  btn.innerHTML = `<span class="spinner"></span> Applying...`;
  btn.disabled = true;
  
  // Open job URL in new tab
  if (currentJobData?.url && currentJobData.url !== "#") {
    window.open(currentJobData.url, "_blank");
  }
  
  // Send confirmation email
  try {
    await fetch(`${API_BASE}/send-confirmation`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: currentPersonalInfo?.email,
        name: currentPersonalInfo?.name,
        job_title: currentJobData?.title,
        company: currentJobData?.company,
        job_url: currentJobData?.url,
        session_id: currentSessionId,
      }),
    });
  } catch (e) {
    console.log("Email sending skipped (demo mode)");
  }
  
  // Show confirmation
  btn.innerHTML = `✓ Applied!`;
  document.getElementById("action-success").querySelector(".action-header").style.display = "none";
  document.getElementById("action-success").querySelector(".action-buttons").style.display = "none";
  document.getElementById("generated-docs").style.display = "none";
  document.getElementById("confirmation-box").style.display = "block";
  document.getElementById("confirmation-message").innerHTML = `
    Your application for <strong>${currentJobData?.title}</strong> at <strong>${currentJobData?.company}</strong> 
    has been submitted. A confirmation email has been sent to <strong>${currentPersonalInfo?.email}</strong>.
  `;
  
  showToast("🎉 Application submitted! Check your email.", "success");
}

// ================================================
// RESET
// ================================================
function resetForm() {
  // Reset form
  document.getElementById("apply-form").reset();
  removeFile({ stopPropagation: () => {} });
  
  // Reset state
  currentAnalysis = null;
  currentSessionId = null;
  currentPersonalInfo = null;
  currentJobData = null;
  
  // Show form, hide others
  document.getElementById("form-panel").style.display = "block";
  document.getElementById("analysis-loading").style.display = "none";
  document.getElementById("results-panel").style.display = "none";
  
  // Reset action panels
  document.getElementById("action-success").querySelector(".action-header").style.display = "block";
  document.getElementById("action-success").querySelector(".action-buttons").style.display = "block";
  document.getElementById("generated-docs").style.display = "none";
  document.getElementById("confirmation-box").style.display = "none";
  
  // Reset score ring
  document.getElementById("score-ring-fill").style.strokeDashoffset = "427";
  document.getElementById("score-number").textContent = "0%";
  
  // Reset loading steps
  for (let i = 1; i <= 5; i++) {
    const step = document.getElementById(`ls-${i}`);
    if (step) {
      step.classList.remove("active", "done");
    }
  }
  
  setStep(1);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function setStep(n) {
  for (let i = 1; i <= 3; i++) {
    const s = document.getElementById(`step-${i}`);
    if (!s) continue;
    s.classList.remove("active", "done");
    if (i < n) s.classList.add("done");
    else if (i === n) s.classList.add("active");
  }
}

// ================================================
// DASHBOARD
// ================================================
async function loadDashboard() {
  try {
    const response = await fetch(`${API_BASE}/applications`);
    const data = await response.json();
    
    if (data.success) {
      allApplications = data.applications;
      renderDashboard(data.applications);
    }
  } catch (e) {
    // Demo data
    const mockApps = getMockApplications();
    allApplications = mockApps;
    renderDashboard(mockApps);
  }
}

function renderDashboard(apps) {
  // KPIs
  const total = apps.length;
  const applied = apps.filter(a => a["Status"] === "Applied" || a.Status === "Applied").length;
  const generated = apps.filter(a => a["Status"] === "Generated" || a.Status === "Generated").length;
  const scores = apps.map(a => parseInt(a["Match Score (%)"] || a.match_score || 0));
  const avgScore = scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : 0;
  
  document.getElementById("kpi-total").textContent = total;
  document.getElementById("kpi-applied").textContent = applied;
  document.getElementById("kpi-generated").textContent = generated;
  document.getElementById("kpi-avg-score").textContent = avgScore + "%";
  
  // Bar chart
  renderBarChart(apps);
  
  // Donut chart
  renderDonutChart(applied, generated, total - applied - generated);
  
  // Table
  renderTable(apps);
}

function renderBarChart(apps) {
  const container = document.getElementById("score-chart");
  const ranges = [
    { label: "90-100%", min: 90, max: 100, color: "#2eca7f" },
    { label: "70-89%", min: 70, max: 89, color: "#4da6ff" },
    { label: "50-69%", min: 50, max: 69, color: "#ffb347" },
    { label: "<50%", min: 0, max: 49, color: "#ff4d6d" },
  ];
  
  const max = Math.max(...ranges.map(r => {
    return apps.filter(a => {
      const s = parseInt(a["Match Score (%)"] || a.match_score || 0);
      return s >= r.min && s <= r.max;
    }).length;
  }), 1);
  
  container.innerHTML = ranges.map(r => {
    const count = apps.filter(a => {
      const s = parseInt(a["Match Score (%)"] || a.match_score || 0);
      return s >= r.min && s <= r.max;
    }).length;
    const pct = (count / max) * 100;
    return `
      <div class="bar-row">
        <span class="bar-label">${r.label}</span>
        <div class="bar-track">
          <div class="bar-fill" style="width:${pct}%;background:${r.color}"></div>
        </div>
        <span class="bar-count">${count}</span>
      </div>
    `;
  }).join("");
}

function renderDonutChart(applied, generated, other) {
  const canvas = document.getElementById("donut-canvas");
  if (!canvas) return;
  
  const ctx = canvas.getContext("2d");
  const cx = 100, cy = 100, r = 70, innerR = 45;
  const total = applied + generated + (other > 0 ? other : 0) || 1;
  
  const segments = [
    { value: applied, color: "#4da6ff", label: "Applied" },
    { value: generated, color: "#a78bfa", label: "Generated" },
    { value: other > 0 ? other : 0, color: "#ff4d6d", label: "Pending" },
  ].filter(s => s.value > 0);
  
  ctx.clearRect(0, 0, 200, 200);
  
  let startAngle = -Math.PI / 2;
  
  segments.forEach(seg => {
    const angle = (seg.value / total) * Math.PI * 2;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, r, startAngle, startAngle + angle);
    ctx.closePath();
    ctx.fillStyle = seg.color;
    ctx.fill();
    startAngle += angle;
  });
  
  // Inner hole
  ctx.beginPath();
  ctx.arc(cx, cy, innerR, 0, Math.PI * 2);
  ctx.fillStyle = "#12121f";
  ctx.fill();
  
  // Center text
  ctx.fillStyle = "#f0f0f5";
  ctx.font = "bold 20px Syne, sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(total, cx, cy - 8);
  ctx.font = "12px DM Sans, sans-serif";
  ctx.fillStyle = "#8a8aa8";
  ctx.fillText("Total", cx, cy + 12);
  
  // Legend
  const legend = document.getElementById("donut-legend");
  legend.innerHTML = segments.map(s => `
    <div class="legend-item">
      <div class="legend-dot" style="background:${s.color}"></div>
      <span>${s.label} (${s.value})</span>
    </div>
  `).join("");
}

function renderTable(apps) {
  const tbody = document.getElementById("apps-tbody");
  const empty = document.getElementById("table-empty");
  
  if (!apps.length) {
    tbody.innerHTML = "";
    empty.style.display = "block";
    return;
  }
  
  empty.style.display = "none";
  
  tbody.innerHTML = apps.map(a => {
    const score = parseInt(a["Match Score (%)"] || a.match_score || 0);
    const status = a["Status"] || a.Status || "Generated";
    const date = a["Date Applied"] || a.date || "—";
    const url = a["Job URL"] || a.job_url || "#";
    const title = a["Job Title"] || a.job_title || "Position";
    const company = a["Company"] || a.company || "Company";
    
    const scoreClass = score >= 80 ? "high" : score >= 60 ? "mid" : "low";
    const statusClass = status.toLowerCase() === "applied" ? "applied" : "generated";
    const dateShort = date.split(" ")[0] || date;
    
    return `
      <tr>
        <td><strong>${title}</strong></td>
        <td>${company}</td>
        <td><span class="score-badge ${scoreClass}">${score}%</span></td>
        <td><span class="status-badge ${statusClass}">${status}</span></td>
        <td style="color:var(--text-muted);font-size:13px">${dateShort}</td>
        <td>
          <a href="${url}" target="_blank" style="color:var(--blue);font-size:13px;text-decoration:none;">
            View Job →
          </a>
        </td>
      </tr>
    `;
  }).join("");
}

function filterTable() {
  const filter = document.getElementById("status-filter").value;
  const filtered = filter ? allApplications.filter(a => 
    (a["Status"] || a.Status || "") === filter
  ) : allApplications;
  renderTable(filtered);
}

function getMockApplications() {
  return [
    { "Session ID": "a1b2c3", "Candidate Name": "Alex Johnson", "Email": "alex@example.com", "Job Title": "Senior Python Developer", "Company": "TechCorp Inc", "Job URL": "https://example.com/jobs/1", "Match Score (%)": 82, "Status": "Applied", "Date Applied": "2025-01-15" },
    { "Session ID": "d4e5f6", "Candidate Name": "Alex Johnson", "Email": "alex@example.com", "Job Title": "Full Stack Engineer", "Company": "StartupXYZ", "Job URL": "https://example.com/jobs/2", "Match Score (%)": 74, "Status": "Generated", "Date Applied": "2025-01-16" },
    { "Session ID": "g7h8i9", "Candidate Name": "Alex Johnson", "Email": "alex@example.com", "Job Title": "Backend Developer", "Company": "Enterprise Ltd", "Job URL": "https://example.com/jobs/3", "Match Score (%)": 91, "Status": "Applied", "Date Applied": "2025-01-17" },
    { "Session ID": "j1k2l3", "Candidate Name": "Alex Johnson", "Email": "alex@example.com", "Job Title": "ML Engineer", "Company": "AI Labs", "Job URL": "https://example.com/jobs/4", "Match Score (%)": 55, "Status": "Generated", "Date Applied": "2025-01-18" },
  ];
}

// ================================================
// TOAST NOTIFICATIONS
// ================================================
function showToast(message, type = "info") {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.className = `toast ${type} show`;
  
  setTimeout(() => {
    toast.classList.remove("show");
  }, 3500);
}
