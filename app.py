import base64
import json
import math
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.error
import urllib.request

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

CACHE_FILE = "cached_timetables.json"


def load_cached_sections():
  if os.path.exists(CACHE_FILE):
    try:
      with open(CACHE_FILE, "r") as f:
        return json.load(f)
    except Exception:
      return {}
  return {}


def save_cached_section(section_name, timetable):
  data = load_cached_sections()
  data[section_name] = timetable
  with open(CACHE_FILE, "w") as f:
    json.dump(data, f, indent=2)


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
<title>BunkSafe • Precision Attendance Operating System</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #090a0f;
    --surface: #11141d;
    --surface-elevated: #161b27;
    --surface-subtle: rgba(255, 255, 255, 0.03);
    --border: rgba(255, 255, 255, 0.08);
    --border-hover: rgba(255, 255, 255, 0.15);
    --border-focus: rgba(56, 189, 248, 0.5);
    
    --primary: #38bdf8;
    --primary-dim: rgba(56, 189, 248, 0.12);
    
    --safe: #10b981;
    --safe-dim: rgba(16, 185, 129, 0.12);
    --safe-border: rgba(16, 185, 129, 0.3);
    
    --danger: #f43f5e;
    --danger-dim: rgba(244, 63, 94, 0.12);
    --danger-border: rgba(244, 63, 94, 0.3);
    
    --exam: #f59e0b;
    --exam-dim: rgba(245, 158, 11, 0.12);
    
    --placement: #06b6d4;
    --placement-dim: rgba(6, 182, 212, 0.12);
    
    --holiday: #a855f7;
    --holiday-dim: rgba(168, 85, 247, 0.12);
    
    --text-high: #f8fafc;
    --text-med: #94a3b8;
    --text-low: #64748b;
    
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --radius-xl: 22px;
    
    --transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  }

  * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif; -webkit-tap-highlight-color: transparent; }
  
  body {
    background-color: var(--bg);
    color: var(--text-high);
    min-height: 100vh;
    padding: 24px 16px 120px;
    background-image: 
      radial-gradient(circle at 50% -100px, rgba(56, 189, 248, 0.08) 0%, transparent 600px),
      radial-gradient(circle at 100% 400px, rgba(168, 85, 247, 0.03) 0%, transparent 400px);
    background-repeat: no-repeat;
  }

  .shell {
    max-width: 540px;
    margin: 0 auto;
  }

  /* App Bar */
  .top-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border);
  }
  .app-identity {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .app-logo {
    width: 28px;
    height: 28px;
    background: linear-gradient(135deg, #0284c7 0%, #38bdf8 100%);
    border-radius: var(--radius-sm);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.85rem;
    font-weight: 800;
    color: #fff;
    box-shadow: 0 2px 10px rgba(2, 132, 199, 0.3);
  }
  .app-title {
    font-size: 0.95rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--text-high);
  }
  .sys-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 999px;
    background: var(--surface-subtle);
    border: 1px solid var(--border);
    color: var(--text-low);
  }

  /* Cards */
  .panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 18px;
    margin-bottom: 14px;
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.4);
    transition: var(--transition);
  }

  /* Command Center Hero */
  .hero-panel {
    display: none;
    position: relative;
    overflow: hidden;
    background: linear-gradient(180deg, rgba(22, 27, 39, 0.9) 0%, rgba(17, 20, 29, 0.9) 100%);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-xl);
    padding: 24px 20px;
    margin-bottom: 18px;
    text-align: center;
    box-shadow: 0 12px 36px -8px rgba(0, 0, 0, 0.6);
  }
  .hero-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }
  .hero-label {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-med);
  }
  .hero-status-tag {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 700;
  }
  .tag-healthy { background: var(--safe-dim); color: var(--safe); border: 1px solid var(--safe-border); }
  .tag-critical { background: var(--danger-dim); color: var(--danger); border: 1px solid var(--danger-border); }
  
  .hero-metric-wrap {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 24px;
    margin: 12px 0 16px;
  }
  .radial-holder {
    position: relative;
    width: 100px;
    height: 100px;
  }
  .radial-svg {
    transform: rotate(-90deg);
    width: 100px;
    height: 100px;
  }
  .radial-bg {
    stroke: rgba(255, 255, 255, 0.06);
    stroke-width: 8;
    fill: transparent;
  }
  .radial-meter {
    stroke-width: 8;
    stroke-linecap: round;
    fill: transparent;
    stroke-dasharray: 264;
    stroke-dashoffset: 264;
    transition: stroke-dashoffset 0.8s cubic-bezier(0.16, 1, 0.3, 1), stroke 0.3s;
  }
  .radial-center-text {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.25rem;
    font-weight: 800;
  }
  .hero-stats-grid {
    text-align: left;
  }
  .stat-unit-label {
    font-size: 0.68rem;
    font-weight: 600;
    color: var(--text-low);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  .stat-unit-val {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text-high);
    margin-bottom: 6px;
  }
  .hero-footer-meta {
    padding-top: 12px;
    border-top: 1px solid var(--border);
    font-size: 0.78rem;
    color: var(--text-med);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  /* Form Elements */
  .control-label {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.75rem;
    font-weight: 700;
    color: var(--text-med);
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  .control-label span.hint {
    font-size: 0.68rem;
    color: var(--text-low);
    text-transform: none;
    font-weight: 500;
  }

  select, input[type="date"], input[type="text"], input[type="number"] {
    width: 100%;
    background: var(--bg);
    border: 1px solid var(--border);
    color: var(--text-high);
    padding: 11px 14px;
    border-radius: var(--radius-md);
    font-size: 0.88rem;
    font-weight: 500;
    margin-bottom: 12px;
    outline: none;
    transition: var(--transition);
  }
  select:focus, input:focus {
    border-color: var(--primary);
    box-shadow: 0 0 0 3px var(--primary-dim);
  }

  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }

  /* Upload Zone */
  .dropzone {
    position: relative;
    border: 1.5px dashed var(--border-hover);
    background: var(--surface-subtle);
    border-radius: var(--radius-md);
    padding: 18px 14px;
    text-align: center;
    cursor: pointer;
    transition: var(--transition);
    margin-bottom: 14px;
  }
  .dropzone:hover {
    border-color: var(--primary);
    background: var(--primary-dim);
  }
  .dropzone.ready {
    border-style: solid;
    border-color: var(--safe-border);
    background: var(--safe-dim);
  }
  .dropzone input[type="file"] {
    position: absolute;
    inset: 0;
    opacity: 0;
    width: 100%;
    height: 100%;
    cursor: pointer;
    z-index: 5;
  }
  .dropzone-state-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
  }
  .dz-icon {
    font-size: 1.3rem;
    margin-bottom: 2px;
  }
  .dz-title {
    font-size: 0.84rem;
    font-weight: 700;
    color: var(--text-high);
  }
  .dz-sub {
    font-size: 0.72rem;
    color: var(--text-low);
  }
  .dropzone-state-loaded {
    display: none;
    align-items: center;
    gap: 12px;
    text-align: left;
  }
  .dz-thumb {
    width: 42px;
    height: 42px;
    border-radius: var(--radius-sm);
    object-fit: cover;
    border: 1px solid var(--border);
  }
  .dz-meta {
    flex: 1;
    min-width: 0;
  }
  .dz-filename {
    font-size: 0.82rem;
    font-weight: 700;
    color: var(--text-high);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .dz-tag {
    font-size: 0.7rem;
    font-weight: 700;
    color: var(--safe);
    display: flex;
    align-items: center;
    gap: 4px;
    margin-top: 2px;
  }

  /* Progressive Disclosure Collapsibles */
  .disclosure-panel {
    background: var(--surface-elevated);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    margin-bottom: 10px;
    overflow: hidden;
  }
  .disclosure-header {
    padding: 12px 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
    user-select: none;
    font-size: 0.8rem;
    font-weight: 700;
    color: var(--text-high);
    transition: var(--transition);
  }
  .disclosure-header:hover {
    background: var(--surface-subtle);
  }
  .disclosure-counter {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 2px 7px;
    border-radius: 999px;
    color: var(--text-med);
    margin-left: 8px;
  }
  .disclosure-arrow {
    font-size: 0.7rem;
    color: var(--text-low);
    transition: transform 0.2s ease;
  }
  .disclosure-panel.open .disclosure-arrow {
    transform: rotate(180deg);
  }
  .disclosure-body {
    display: none;
    padding: 12px 14px 14px;
    border-top: 1px solid var(--border);
  }
  .disclosure-panel.open .disclosure-body {
    display: block;
  }

  /* Segmented Controls */
  .seg-control {
    display: flex;
    background: var(--bg);
    padding: 3px;
    border-radius: var(--radius-sm);
    border: 1px solid var(--border);
    margin-bottom: 10px;
  }
  .seg-btn {
    flex: 1;
    background: transparent;
    border: none;
    color: var(--text-med);
    padding: 6px 4px;
    font-size: 0.72rem;
    font-weight: 600;
    border-radius: 6px;
    cursor: pointer;
    transition: var(--transition);
  }
  .seg-btn.active {
    background: var(--surface-elevated);
    color: var(--text-high);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
  }

  .inline-row {
    display: flex;
    gap: 8px;
    align-items: center;
  }
  .inline-row input, .inline-row select {
    margin-bottom: 0;
    flex: 1;
  }
  .action-btn {
    padding: 10px 14px;
    background: var(--surface-elevated);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    color: var(--text-high);
    font-size: 0.78rem;
    font-weight: 700;
    cursor: pointer;
    white-space: nowrap;
    transition: var(--transition);
  }
  .action-btn:active {
    transform: scale(0.97);
  }

  /* Tokenized Chips Shelf */
  .tags-shelf {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    min-height: 28px;
    margin-top: 10px;
  }
  .tag-item {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: var(--radius-sm);
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }
  .tag-item span {
    cursor: pointer;
    opacity: 0.6;
  }
  .tag-item span:hover { opacity: 1; }
  
  .tag-absent { background: var(--danger-dim); border: 1px solid var(--danger-border); color: #fda4af; }
  .tag-exam { background: var(--exam-dim); border: 1px solid rgba(245, 158, 11, 0.3); color: #fde68a; }
  .tag-placement { background: var(--placement-dim); border: 1px solid rgba(6, 182, 212, 0.3); color: #a5f3fc; }
  .tag-holiday { background: var(--holiday-dim); border: 1px solid rgba(168, 85, 247, 0.3); color: #d8b4fe; }

  /* Calendar Inspector Matrix */
  .cal-matrix {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 10px;
    margin-top: 10px;
  }
  .cal-matrix-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }
  .cal-matrix-title {
    font-size: 0.8rem;
    font-weight: 700;
  }
  .cal-nav-btn {
    background: var(--surface-elevated);
    border: 1px solid var(--border);
    color: var(--text-high);
    padding: 3px 8px;
    border-radius: var(--radius-sm);
    font-size: 0.72rem;
    cursor: pointer;
  }
  .cal-grid-row {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 3px;
    text-align: center;
  }
  .cal-col-lbl {
    font-size: 0.62rem;
    font-weight: 700;
    color: var(--text-low);
    padding: 2px 0;
  }
  .cal-cell-day {
    aspect-ratio: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.72rem;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 600;
    border-radius: 6px;
    cursor: pointer;
    border: 1px solid transparent;
    color: var(--text-high);
    background: rgba(255, 255, 255, 0.02);
  }
  .cal-cell-day.empty { background: transparent; cursor: default; }
  .cal-cell-day.is-holiday {
    background: var(--holiday-dim);
    border-color: rgba(168, 85, 247, 0.5);
    color: #d8b4fe;
    font-weight: 800;
  }
  .cal-cell-day.is-sun {
    color: var(--text-low);
    opacity: 0.4;
  }

  /* What-If Bunk Simulator */
  .simulator-card {
    display: none;
    margin-bottom: 16px;
  }
  .sim-metric-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }
  .sim-val-display {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.88rem;
    font-weight: 700;
    color: var(--primary);
  }
  input[type="range"] {
    width: 100%;
    accent-color: var(--primary);
    cursor: pointer;
    background: transparent;
    margin-bottom: 0;
  }

  /* Subject Cards */
  .subject-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 16px;
    margin-bottom: 12px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
    transition: var(--transition);
  }
  .subject-card:hover {
    border-color: var(--border-hover);
  }
  .subject-head {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 10px;
  }
  .subject-name {
    font-size: 0.92rem;
    font-weight: 700;
    color: var(--text-high);
    line-height: 1.3;
  }
  .subject-pct-pill {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem;
    font-weight: 800;
    padding: 3px 8px;
    border-radius: 6px;
    white-space: nowrap;
  }

  /* Target Progress Gauge */
  .gauge-track {
    position: relative;
    height: 7px;
    background: var(--bg);
    border-radius: 999px;
    margin-bottom: 12px;
    border: 1px solid rgba(255, 255, 255, 0.04);
  }
  .gauge-fill {
    height: 100%;
    border-radius: 999px;
    transition: width 0.3s ease;
  }
  .gauge-pin-80 {
    position: absolute;
    top: -3px;
    bottom: -3px;
    left: 80%;
    width: 2px;
    background: #fff;
    box-shadow: 0 0 6px rgba(255, 255, 255, 0.8);
    z-index: 2;
  }
  .gauge-pin-text {
    position: absolute;
    right: calc(20% - 10px);
    top: -15px;
    font-size: 0.58rem;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 800;
    color: var(--text-low);
  }

  .subject-detail-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
    font-size: 0.78rem;
    color: var(--text-med);
  }
  .subject-detail-grid b { color: var(--text-high); font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; }
  
  .insight-box {
    grid-column: span 2;
    padding: 7px 10px;
    border-radius: var(--radius-sm);
    font-size: 0.76rem;
    font-weight: 600;
    margin-top: 4px;
  }
  .insight-safe { background: var(--safe-dim); border: 1px solid var(--safe-border); color: #6ee7b7; }
  .insight-danger { background: var(--danger-dim); border: 1px solid var(--danger-border); color: #fda4af; }

  .proj-strip {
    grid-column: span 2;
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: var(--primary);
    font-size: 0.76rem;
    font-weight: 600;
    margin-top: 2px;
    font-family: 'JetBrains Mono', monospace;
  }

  /* Floating Action Trigger */
  .mobile-float-bar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: rgba(9, 10, 15, 0.85);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-top: 1px solid var(--border);
    padding: 12px 16px calc(12px + env(safe-area-inset-bottom));
    z-index: 50;
  }
  .float-inner {
    max-width: 540px;
    margin: 0 auto;
  }
  .btn-calculate {
    width: 100%;
    background: linear-gradient(180deg, #0284c7 0%, #0369a1 100%);
    color: #fff;
    border: 1px solid rgba(255, 255, 255, 0.15);
    padding: 14px;
    border-radius: var(--radius-md);
    font-size: 0.92rem;
    font-weight: 700;
    letter-spacing: -0.01em;
    cursor: pointer;
    box-shadow: 0 4px 20px rgba(2, 132, 199, 0.4);
    transition: var(--transition);
  }
  .btn-calculate:active { transform: scale(0.98); }
  .btn-calculate:disabled { opacity: 0.5; cursor: not-allowed; }

  #status {
    font-size: 0.78rem;
    color: var(--primary);
    text-align: center;
    margin-top: 6px;
    min-height: 1.2em;
    font-weight: 600;
  }
</style>
</head>
<body>
<div class="shell">

  <!-- Application Bar -->
  <div class="top-bar">
    <div class="app-identity">
      <div class="app-logo">B</div>
      <div class="app-title">BunkSafe OS</div>
    </div>
    <div class="sys-badge">v3.5 Flash Engine</div>
  </div>

  <!-- Hero Command Center -->
  <div class="hero-panel" id="heroCard">
    <div class="hero-header">
      <div class="hero-label">Institutional Status</div>
      <div class="hero-status-tag" id="heroBadge">--</div>
    </div>

    <div class="hero-metric-wrap">
      <div class="radial-holder">
        <svg class="radial-svg" viewBox="0 0 100 100">
          <circle class="radial-bg" cx="50" cy="50" r="42" />
          <circle class="radial-meter" id="radialMeter" cx="50" cy="50" r="42" />
        </svg>
        <div class="radial-center-text" id="heroPct">--%</div>
      </div>

      <div class="hero-stats-grid">
        <div class="stat-unit-label">Completed Periods</div>
        <div class="stat-unit-val" id="heroAttended">-- / --</div>
        <div class="stat-unit-label">Target Standard</div>
        <div class="stat-unit-val" style="font-size:0.95rem; color:var(--text-med);">80.0% Minimum</div>
      </div>
    </div>

    <div class="hero-footer-meta">
      <span id="heroMeta">Calculated with CAE, Placement, and Calendar rules</span>
      <span style="font-family:'JetBrains Mono',monospace; font-size:0.72rem; color:var(--safe);">● SYNCHRONIZED</span>
    </div>
  </div>

  <!-- What-If Simulator Panel -->
  <div class="panel simulator-card" id="simBox">
    <div class="sim-metric-row">
      <div class="control-label" style="margin-bottom:0;">What-If Class Simulator</div>
      <div class="sim-val-display" id="simValDisplay">+10 classes</div>
    </div>
    <input type="range" id="futureSlider" min="1" max="40" value="10" oninput="onSliderChange(this.value)">
  </div>

  <!-- Setup Panel -->
  <div class="panel">
    <div class="control-label">
      <span>Batch & Section</span>
      <span class="hint">Governs Saturday rule</span>
    </div>
    <div class="grid-2">
      <div>
        <select id="yearBatchSelect" onchange="saveYearBatch(this.value)">
          <option value="Senior" selected>2nd, 3rd, 4th Year (Sat Off)</option>
          <option value="Fresher">1st Year (Sat Working)</option>
        </select>
      </div>
      <div>
        <select id="sectionSelect" onchange="onSectionSelect(this.value)">
          <option value="">-- Choose Section --</option>
        </select>
      </div>
    </div>

    <!-- Upload Dropzone -->
    <div class="dropzone" id="uploadBox">
      <input type="file" id="imageInput" accept="image/*">
      
      <div class="dropzone-state-empty" id="uploadInitial">
        <div class="dz-icon">📷</div>
        <div class="dz-title">Upload Timetable Screenshot</div>
        <div class="dz-sub">Automated grid extraction via Gemini 3.5 Flash</div>
      </div>

      <div class="dropzone-state-loaded" id="uploadPreview">
        <img id="previewImg" class="dz-thumb" alt="Preview">
        <div class="dz-meta">
          <div class="dz-filename" id="previewFileName">timetable.png</div>
          <div class="dz-tag">✓ Ready for calculation</div>
        </div>
      </div>
    </div>

    <!-- Semester Term Dates -->
    <div class="grid-2">
      <div>
        <div class="control-label">Semester Start</div>
        <input type="date" id="startDate" value="2026-07-01">
      </div>
      <div>
        <div class="control-label">Today's Date</div>
        <input type="date" id="todayDate">
      </div>
    </div>

    <!-- Progressive Disclosure: Absents -->
    <div class="disclosure-panel" id="discAbsent">
      <div class="disclosure-header" onclick="toggleDisclosure('discAbsent')">
        <span>1. Personal Leaves <span class="disclosure-counter" id="absentCount">0</span></span>
        <span class="disclosure-arrow">▼</span>
      </div>
      <div class="disclosure-body">
        <div class="seg-control">
          <button type="button" class="seg-btn active" id="absentSingleBtn" onclick="setMode('absent', 'single')">Single Day</button>
          <button type="button" class="seg-btn" id="absentRangeBtn" onclick="setMode('absent', 'range')">Date Range</button>
        </div>
        <div class="inline-row" id="absentSingleInput">
          <input type="date" id="absentPicker">
          <button type="button" class="action-btn" onclick="addSingleDate('absent')">+ Add</button>
        </div>
        <div class="inline-row" id="absentRangeInput" style="display:none;">
          <input type="date" id="absentFrom">
          <span style="font-size:0.75rem; color:var(--text-low);">to</span>
          <input type="date" id="absentTo">
          <button type="button" class="action-btn" onclick="addDateRange('absent')">+ Add All</button>
        </div>
        <div class="tags-shelf" id="absentChipsContainer"></div>
      </div>
    </div>

    <!-- Progressive Disclosure: CAE Exams -->
    <div class="disclosure-panel" id="discExam">
      <div class="disclosure-header" onclick="toggleDisclosure('discExam')">
        <span style="color:var(--exam);">2. CAE Exams <span class="disclosure-counter" id="examCount">0</span></span>
        <span class="disclosure-arrow">▼</span>
      </div>
      <div class="disclosure-body">
        <div class="seg-control">
          <button type="button" class="seg-btn active" id="examSingleBtn" onclick="setMode('exam', 'single')">Single Exam</button>
          <button type="button" class="seg-btn" id="examRangeBtn" onclick="setMode('exam', 'range')">Exam Week Block</button>
        </div>
        <div class="inline-row" id="examSingleInput">
          <input type="date" id="examPicker">
          <button type="button" class="action-btn" onclick="addSingleDate('exam')">+ Add</button>
        </div>
        <div class="inline-row" id="examRangeInput" style="display:none;">
          <input type="date" id="examFrom">
          <span style="font-size:0.75rem; color:var(--text-low);">to</span>
          <input type="date" id="examTo">
          <button type="button" class="action-btn" onclick="addDateRange('exam')">+ Add Week</button>
        </div>
        <div class="tags-shelf" id="examChipsContainer"></div>
      </div>
    </div>

    <!-- Progressive Disclosure: Placement Training -->
    <div class="disclosure-panel" id="discPlacement">
      <div class="disclosure-header" onclick="toggleDisclosure('discPlacement')">
        <span style="color:var(--placement);">3. Placement Training <span class="disclosure-counter" id="placementCount">0</span></span>
        <span class="disclosure-arrow">▼</span>
      </div>
      <div class="disclosure-body">
        <div class="seg-control">
          <button type="button" class="seg-btn active" id="placementSingleBtn" onclick="setMode('placement', 'single')">Single Day</button>
          <button type="button" class="seg-btn" id="placementRangeBtn" onclick="setMode('placement', 'range')">Block</button>
          <button type="button" class="seg-btn" id="placementAltBtn" onclick="setMode('placement', 'alt')">Alternate (1 On, 1 Off)</button>
        </div>
        <div class="inline-row" id="placementSingleInput">
          <input type="date" id="placementPicker">
          <button type="button" class="action-btn" onclick="addSingleDate('placement')">+ Add</button>
        </div>
        <div class="inline-row" id="placementRangeInput" style="display:none;">
          <input type="date" id="placementFrom">
          <span style="font-size:0.75rem; color:var(--text-low);">to</span>
          <input type="date" id="placementTo">
          <button type="button" class="action-btn" onclick="addDateRange('placement', false)">+ Add Block</button>
        </div>
        <div class="inline-row" id="placementAltInput" style="display:none;">
          <input type="date" id="placementAltFrom">
          <span style="font-size:0.75rem; color:var(--text-low);">to</span>
          <input type="date" id="placementAltTo">
          <button type="button" class="action-btn" onclick="addDateRange('placement', true)">+ Add Alternate</button>
        </div>
        <div class="tags-shelf" id="placementChipsContainer"></div>
      </div>
    </div>

    <!-- Progressive Disclosure: Official Holidays -->
    <div class="disclosure-panel" id="discHoliday">
      <div class="disclosure-header" onclick="toggleDisclosure('discHoliday')">
        <span style="color:var(--holiday);">4. Holidays & Events <span class="disclosure-counter" id="holidayCount">0</span></span>
        <span class="disclosure-arrow">▼</span>
      </div>
      <div class="disclosure-body">
        <div class="seg-control">
          <button type="button" class="seg-btn active" id="holidaySingleBtn" onclick="setMode('holiday', 'single')">Single Day</button>
          <button type="button" class="seg-btn" id="holidayRangeBtn" onclick="setMode('holiday', 'range')">Date Range</button>
        </div>
        <select id="holidayScope" style="font-size:0.78rem;">
          <option value="All">Scope: All University (Festivals/Govt)</option>
          <option value="2nd Year">Scope: 2nd Year Only</option>
          <option value="3rd Year">Scope: 3rd Year Only</option>
          <option value="4th Year">Scope: 4th Year Only</option>
          <option value="Dept Only">Scope: Department Only</option>
        </select>
        <div class="inline-row" id="holidaySingleInput">
          <input type="date" id="holidayPicker">
          <button type="button" class="action-btn" onclick="addHoliday(false)">+ Add</button>
        </div>
        <div class="inline-row" id="holidayRangeInput" style="display:none;">
          <input type="date" id="holidayFrom">
          <span style="font-size:0.75rem; color:var(--text-low);">to</span>
          <input type="date" id="holidayTo">
          <button type="button" class="action-btn" onclick="addHoliday(true)">+ Add Range</button>
        </div>
        <div class="tags-shelf" id="holidayChipsContainer"></div>
      </div>
    </div>

    <!-- Progressive Disclosure: Academic Calendar Matrix -->
    <div class="disclosure-panel" id="discCal">
      <div class="disclosure-header" onclick="toggleDisclosure('discCal')">
        <span>📅 Academic Calendar Matrix</span>
        <span class="disclosure-arrow">▼</span>
      </div>
      <div class="disclosure-body">
        <div class="cal-matrix">
          <div class="cal-matrix-header">
            <button type="button" class="cal-nav-btn" onclick="navMonth(-1)">&larr; Prev</button>
            <div class="cal-matrix-title" id="calMonthTitle">July 2026</div>
            <button type="button" class="cal-nav-btn" onclick="navMonth(1)">Next &rarr;</button>
          </div>
          <div class="cal-grid-row">
            <div class="cal-col-lbl">Su</div>
            <div class="cal-col-lbl">Mo</div>
            <div class="cal-col-lbl">Tu</div>
            <div class="cal-col-lbl">We</div>
            <div class="cal-col-lbl">Th</div>
            <div class="cal-col-lbl">Fr</div>
            <div class="cal-col-lbl">Sa</div>
          </div>
          <div class="cal-grid-row" id="calCells"></div>
        </div>
      </div>
    </div>
  </div>

  <!-- Dynamic Results Area -->
  <div id="results"></div>

</div>

<!-- Sticky Bottom Floating Controller -->
<div class="mobile-float-bar">
  <div class="float-inner">
    <button id="calcBtn" class="btn-calculate" onclick="calculateAll()">Calculate Attendance Architecture</button>
    <div id="status"></div>
  </div>
</div>

<script>
  document.getElementById('todayDate').valueAsDate = new Date();

  const savedBatch = localStorage.getItem('my_year_batch') || "Senior";
  document.getElementById('yearBatchSelect').value = savedBatch;

  function saveYearBatch(val) {
    localStorage.setItem('my_year_batch', val);
  }

  function toggleDisclosure(id) {
    const el = document.getElementById(id);
    el.classList.toggle('open');
  }

  const userAbsents = new Set(JSON.parse(localStorage.getItem('my_absents') || "[]"));
  const userExams = new Set(JSON.parse(localStorage.getItem('my_exams') || "[]"));
  const userPlacements = new Set(JSON.parse(localStorage.getItem('my_placements') || "[]"));
  let userHolidays = JSON.parse(localStorage.getItem('my_holidays_map') || "{}");

  function saveUserState() {
    localStorage.setItem('my_absents', JSON.stringify(Array.from(userAbsents)));
    localStorage.setItem('my_exams', JSON.stringify(Array.from(userExams)));
    localStorage.setItem('my_placements', JSON.stringify(Array.from(userPlacements)));
    localStorage.setItem('my_holidays_map', JSON.stringify(userHolidays));
    updateCounters();
  }

  function updateCounters() {
    document.getElementById('absentCount').innerText = userAbsents.size;
    document.getElementById('examCount').innerText = userExams.size;
    document.getElementById('placementCount').innerText = userPlacements.size;
    document.getElementById('holidayCount').innerText = Object.keys(userHolidays).length;
  }

  function setMode(category, mode) {
    if (category === 'placement') {
      document.getElementById('placementSingleBtn').classList.toggle('active', mode === 'single');
      document.getElementById('placementRangeBtn').classList.toggle('active', mode === 'range');
      document.getElementById('placementAltBtn').classList.toggle('active', mode === 'alt');
      document.getElementById('placementSingleInput').style.display = mode === 'single' ? 'flex' : 'none';
      document.getElementById('placementRangeInput').style.display = mode === 'range' ? 'flex' : 'none';
      document.getElementById('placementAltInput').style.display = mode === 'alt' ? 'flex' : 'none';
      return;
    }
    document.getElementById(`${category}SingleBtn`).classList.toggle('active', mode === 'single');
    document.getElementById(`${category}RangeBtn`).classList.toggle('active', mode === 'range');
    document.getElementById(`${category}SingleInput`).style.display = mode === 'single' ? 'flex' : 'none';
    document.getElementById(`${category}RangeInput`).style.display = mode === 'range' ? 'flex' : 'none';
  }

  function addSingleDate(category) {
    const val = document.getElementById(`${category}Picker`).value;
    if (!val) return;
    if (category === 'absent') userAbsents.add(val);
    if (category === 'exam') userExams.add(val);
    if (category === 'placement') userPlacements.add(val);
    saveUserState();
    renderAllChips();
    document.getElementById(`${category}Picker`).value = "";
  }

  function addDateRange(category, isAlternate = false) {
    let fromVal, toVal;
    if (category === 'placement' && isAlternate) {
      fromVal = document.getElementById('placementAltFrom').value;
      toVal = document.getElementById('placementAltTo').value;
    } else {
      fromVal = document.getElementById(`${category}From`).value;
      toVal = document.getElementById(`${category}To`).value;
    }
    if (!fromVal || !toVal) return;

    let curr = new Date(fromVal);
    const end = new Date(toVal);
    let stepCount = 0;

    while (curr <= end) {
      if (curr.getDay() !== 0) {
        if (!isAlternate || (stepCount % 2 === 0)) {
          const dStr = curr.toISOString().split('T')[0];
          if (category === 'absent') userAbsents.add(dStr);
          if (category === 'exam') userExams.add(dStr);
          if (category === 'placement') userPlacements.add(dStr);
        }
        stepCount++;
      }
      curr.setDate(curr.getDate() + 1);
    }
    saveUserState();
    renderAllChips();
  }

  function addHoliday(isRange) {
    const scope = document.getElementById('holidayScope').value;
    if (!isRange) {
      const val = document.getElementById('holidayPicker').value;
      if (!val) return;
      userHolidays[val] = scope;
      document.getElementById('holidayPicker').value = "";
    } else {
      const fromVal = document.getElementById('holidayFrom').value;
      const toVal = document.getElementById('holidayTo').value;
      if (!fromVal || !toVal) return;
      let curr = new Date(fromVal);
      const end = new Date(toVal);
      while (curr <= end) {
        if (curr.getDay() !== 0) {
          userHolidays[curr.toISOString().split('T')[0]] = scope;
        }
        curr.setDate(curr.getDate() + 1);
      }
    }
    saveUserState();
    renderAllChips();
    renderCalendar();
  }

  function renderAllChips() {
    const aCont = document.getElementById('absentChipsContainer');
    aCont.innerHTML = userAbsents.size === 0 ? '<span style="color:var(--text-low); font-size:0.75rem;">No leaves added.</span>' : '';
    Array.from(userAbsents).sort().forEach(d => {
      aCont.innerHTML += `<div class="tag-item tag-absent">${d} <span onclick="removeDate('absent', '${d}')">&times;</span></div>`;
    });

    const eCont = document.getElementById('examChipsContainer');
    eCont.innerHTML = userExams.size === 0 ? '<span style="color:var(--text-low); font-size:0.75rem;">No exam dates.</span>' : '';
    Array.from(userExams).sort().forEach(d => {
      eCont.innerHTML += `<div class="tag-item tag-exam">CAE: ${d} <span onclick="removeDate('exam', '${d}')">&times;</span></div>`;
    });

    const pCont = document.getElementById('placementChipsContainer');
    pCont.innerHTML = userPlacements.size === 0 ? '<span style="color:var(--text-low); font-size:0.75rem;">No placement drives.</span>' : '';
    Array.from(userPlacements).sort().forEach(d => {
      pCont.innerHTML += `<div class="tag-item tag-placement">Placement: ${d} <span onclick="removeDate('placement', '${d}')">&times;</span></div>`;
    });

    const hCont = document.getElementById('holidayChipsContainer');
    const hKeys = Object.keys(userHolidays).sort();
    hCont.innerHTML = hKeys.length === 0 ? '<span style="color:var(--text-low); font-size:0.75rem;">No holidays tagged.</span>' : '';
    hKeys.forEach(d => {
      const sc = userHolidays[d];
      hCont.innerHTML += `<div class="tag-item tag-holiday">${d} (${sc}) <span onclick="removeDate('holiday', '${d}')">&times;</span></div>`;
    });
    updateCounters();
  }

  function removeDate(cat, d) {
    if (cat === 'absent') userAbsents.delete(d);
    if (cat === 'exam') userExams.delete(d);
    if (cat === 'placement') userPlacements.delete(d);
    if (cat === 'holiday') delete userHolidays[d];
    saveUserState();
    renderAllChips();
    renderCalendar();
  }

  let calDate = new Date(2026, 6, 1);
  function navMonth(delta) {
    calDate.setMonth(calDate.getMonth() + delta);
    renderCalendar();
  }

  function toggleCalHoliday(dStr) {
    if (userHolidays[dStr]) {
      delete userHolidays[dStr];
    } else {
      userHolidays[dStr] = document.getElementById('holidayScope').value || "All";
    }
    saveUserState();
    renderAllChips();
    renderCalendar();
  }

  function renderCalendar() {
    const title = document.getElementById('calMonthTitle');
    const container = document.getElementById('calCells');
    container.innerHTML = "";

    const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    title.innerText = `${monthNames[calDate.getMonth()]} ${calDate.getFullYear()}`;

    const firstDay = new Date(calDate.getFullYear(), calDate.getMonth(), 1).getDay();
    const daysInMonth = new Date(calDate.getFullYear(), calDate.getMonth() + 1, 0).getDate();

    for (let i = 0; i < firstDay; i++) {
      const empty = document.createElement('div');
      empty.className = 'cal-cell-day empty';
      container.appendChild(empty);
    }

    for (let d = 1; d <= daysInMonth; d++) {
      const cur = new Date(calDate.getFullYear(), calDate.getMonth(), d);
      const curStr = cur.toISOString().split('T')[0];
      const isSun = cur.getDay() === 0;
      const isHol = !!userHolidays[curStr];

      const cell = document.createElement('div');
      cell.className = `cal-cell-day ${isSun ? 'is-sun' : ''} ${isHol ? 'is-holiday' : ''}`;
      cell.innerText = d;
      cell.onclick = () => toggleCalHoliday(curStr);
      container.appendChild(cell);
    }
  }

  renderAllChips();
  renderCalendar();

  let serverSections = {};
  async function loadSectionsList() {
    try {
      const res = await fetch('/api/sections');
      serverSections = await res.json();
      const select = document.getElementById('sectionSelect');
      select.innerHTML = '<option value="">-- Choose Section --</option>';
      for (const sec in serverSections) {
        const opt = document.createElement('option');
        opt.value = sec;
        opt.innerText = sec;
        select.appendChild(opt);
      }
    } catch(e) {}
  }
  loadSectionsList();

  let activeTimetable = null;
  let selectedBase64 = null;

  function onSectionSelect(secName) {
    if (serverSections[secName]) {
      activeTimetable = serverSections[secName];
      document.getElementById('status').innerText = `✓ Loaded ${secName}`;
    }
  }

  function optimizeImage(file, callback) {
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        const MAX_WIDTH = 1100;
        let width = img.width;
        let height = img.height;
        if (width > MAX_WIDTH) {
          height = Math.round((height * MAX_WIDTH) / width);
          width = MAX_WIDTH;
        }
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, width, height);
        callback(canvas.toDataURL('image/jpeg', 0.82).split(',')[1]);
      };
      img.src = e.target.result;
    };
    reader.readAsDataURL(file);
  }

  document.getElementById('imageInput').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (!file) return;

    document.getElementById('previewFileName').innerText = file.name;
    document.getElementById('previewImg').src = URL.createObjectURL(file);
    document.getElementById('uploadInitial').style.display = "none";
    document.getElementById('uploadPreview').style.display = "flex";
    document.getElementById('uploadBox').classList.add('ready');

    optimizeImage(file, (b64) => {
      selectedBase64 = b64;
      activeTimetable = null;
    });
  });

  async function calculateAll() {
    const statusEl = document.getElementById('status');
    const calcBtn = document.getElementById('calcBtn');

    if (!activeTimetable && !selectedBase64) {
      alert("Please select a class section or upload a timetable screenshot.");
      return;
    }

    if (!activeTimetable && selectedBase64) {
      calcBtn.disabled = true;
      statusEl.innerText = "Analyzing timetable grid with Gemini 3.5 Flash...";
      try {
        const res = await fetch('/api/parse_timetable', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ image_b64: selectedBase64 })
        });
        const data = await res.json();
        if (!res.ok || data.error) throw new Error(data.error);
        activeTimetable = data.timetable;
        loadSectionsList();
      } catch (err) {
        calcBtn.disabled = false;
        statusEl.innerText = "Error: " + err.message;
        return;
      }
    }

    calcBtn.disabled = false;
    statusEl.innerText = "";
    runClientCalculation();
  }

  function runClientCalculation() {
    if (!activeTimetable) return;

    const start = new Date(document.getElementById('startDate').value);
    const today = new Date(document.getElementById('todayDate').value);
    const futureN = parseInt(document.getElementById('futureSlider').value) || 10;
    const isFresher = document.getElementById('yearBatchSelect').value === "Fresher";

    const dayMap = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
    const subHeld = {};
    const subAtt = {};
    let overallHeld = 0;
    let overallAtt = 0;

    for (let d = new Date(start); d <= today; d.setDate(d.getDate() + 1)) {
      const dStr = d.toISOString().split('T')[0];
      const dayIndex = d.getDay();
      const dayName = dayMap[dayIndex];
      const periods = activeTimetable[dayName] || [];

      const isHoliday = !!userHolidays[dStr];
      const isAbsent = userAbsents.has(dStr);
      const isExam = userExams.has(dStr);
      const isPlacement = userPlacements.has(dStr);

      if (dayIndex === 0) continue;

      if (dayIndex === 6 && !isFresher && !isPlacement) {
        continue;
      }

      if (isHoliday) continue;

      if (periods.length > 0 || isPlacement) {
        if (isPlacement) {
          const dayPeriods = periods.length > 0 ? periods.length : 5;
          overallHeld += dayPeriods;
          if (!isAbsent) overallAtt += dayPeriods;
          continue;
        }

        if (isExam) {
          overallHeld += 2;
          if (!isAbsent) overallAtt += 2;
          const regular = periods.slice(2);
          regular.forEach(sub => {
            subHeld[sub] = (subHeld[sub] || 0) + 1;
            overallHeld += 1;
            if (!isAbsent) {
              subAtt[sub] = (subAtt[sub] || 0) + 1;
              overallAtt += 1;
            }
          });
        } else {
          periods.forEach(sub => {
            subHeld[sub] = (subHeld[sub] || 0) + 1;
            overallHeld += 1;
            if (!isAbsent) {
              subAtt[sub] = (subAtt[sub] || 0) + 1;
              overallAtt += 1;
            }
          });
        }
      }
    }

    const subjects = Object.keys(subHeld).sort().map(sub => {
      const held = subHeld[sub] || 0;
      const att = subAtt[sub] || 0;
      const pct = held > 0 ? (att / held * 100) : 100.0;

      const needed80 = Math.max(0, Math.ceil(4 * held - 5 * att));
      const bunks = pct >= 80 ? Math.max(0, Math.floor(att / 0.8 - held)) : 0;

      const projHeld = held + futureN;
      const projAtt = att + futureN;
      const projPct = projHeld > 0 ? (projAtt / projHeld * 100) : pct;

      return {
        subject: sub,
        held: held,
        attended: att,
        pct: pct.toFixed(1),
        status: pct >= 80 ? "SAFE" : "SHORTAGE",
        needed_for_80: needed80,
        bunks_available: bunks,
        projected_pct: projPct.toFixed(1),
        gain: (projPct - pct).toFixed(1)
      };
    });

    const overallPct = overallHeld > 0 ? (overallAtt / overallHeld * 100) : 100.0;
    renderResults({
      overall: { held: overallHeld, attended: overallAtt, pct: overallPct.toFixed(1) },
      subjects: subjects
    }, futureN);
  }

  function onSliderChange(val) {
    document.getElementById('simValDisplay').innerText = `+${val} classes`;
    runClientCalculation();
  }

  function renderResults(data, futureN) {
    const heroCard = document.getElementById('heroCard');
    const heroPct = document.getElementById('heroPct');
    const heroAttended = document.getElementById('heroAttended');
    const heroBadge = document.getElementById('heroBadge');
    const radialMeter = document.getElementById('radialMeter');
    const simBox = document.getElementById('simBox');
    const container = document.getElementById('results');

    heroCard.style.display = "block";
    simBox.style.display = "block";
    container.innerHTML = "";

    const overall = data.overall;
    const isOverallSafe = parseFloat(overall.pct) >= 80.0;

    heroPct.innerText = `${overall.pct}%`;
    heroPct.style.color = isOverallSafe ? "var(--safe)" : "var(--danger)";
    heroAttended.innerText = `${overall.attended} / ${overall.held}`;

    // SVG Radial Arc Animation
    const circumference = 2 * Math.PI * 42; // ~263.89
    const fillValue = Math.min(100, Math.max(0, parseFloat(overall.pct)));
    const offset = circumference - (fillValue / 100) * circumference;
    radialMeter.style.strokeDashoffset = offset;
    radialMeter.style.stroke = isOverallSafe ? "var(--safe)" : "var(--danger)";

    heroBadge.className = `hero-status-tag ${isOverallSafe ? 'tag-healthy' : 'tag-critical'}`;
    heroBadge.innerText = isOverallSafe ? "● Above Target (Safe)" : "● Shortage Warning";

    data.subjects.forEach(item => {
      const isSafe = item.status === "SAFE";
      const div = document.createElement('div');
      div.className = 'subject-card';

      div.innerHTML = `
        <div class="subject-head">
          <div class="subject-name">${item.subject}</div>
          <span class="subject-pct-pill ${isSafe ? 'tag-healthy' : 'tag-critical'}">
            ${item.pct}%
          </span>
        </div>

        <div class="gauge-track">
          <div class="gauge-pin-text">80%</div>
          <div class="gauge-pin-80"></div>
          <div class="gauge-fill" style="width: ${Math.min(100, parseFloat(item.pct))}%; background: ${isSafe ? 'var(--safe)' : 'var(--danger)'};"></div>
        </div>

        <div class="subject-detail-grid">
          <div>Attended: <b>${item.attended} / ${item.held}</b></div>
          <div style="text-align:right;">Status: <b style="color:${isSafe ? 'var(--safe)' : 'var(--danger)'};">${item.status}</b></div>

          ${!isSafe 
            ? `<div class="insight-box insight-danger">⚠️ Must attend next <b>${item.needed_for_80}</b> consecutive classes to achieve 80%.</div>`
            : `<div class="insight-box insight-safe">🛡️ Safe Buffer: Can safely bunk up to <b>${item.bunks_available}</b> class(es).</div>`
          }

          <div class="proj-strip">
            <span>Projection (+${futureN} classes):</span>
            <b>${item.projected_pct}% (+${item.gain}%)</b>
          </div>
        </div>
      `;
      container.appendChild(div);
    });

    // Smooth view scroll to top hero dashboard
    heroCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
</script>
</body>
</html>
"""


def extract_with_gemini_35(image_b64):
  url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={GEMINI_API_KEY}"

  prompt = """Analyze this university timetable image.
Find the class Section name (e.g. 'Section C2') and weekly schedule for Monday to Saturday.
- If a lab/subject occupies 2 continuous periods, list it twice.
- Map course codes to full subject names (e.g. 'Signals and Systems (SECB1302)').
- Omit Break and Lunch.
Respond ONLY with JSON:
{
  "section": "Section C2",
  "timetable": {
    "Monday": ["Sub1", "Sub2"],
    "Tuesday": [],
    "Wednesday": [],
    "Thursday": [],
    "Friday": [],
    "Saturday": []
  }
}"""

  req_data = {
      "contents": [{
          "parts": [
              {"text": prompt},
              {"inlineData": {"mimeType": "image/jpeg", "data": image_b64}},
          ]
      }],
      "generationConfig": {
          "responseMimeType": "application/json",
          "thinkingConfig": {"thinkingLevel": "minimal"},
      },
  }

  last_error = None
  for attempt in range(3):
    req = urllib.request.Request(
        url,
        data=json.dumps(req_data).encode("utf-8"),


headers = {"Content-Type": "application/json"}
if GEMINI_API_KEY.startswith("AQ."):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent"
    headers["Authorization"] = f"Bearer {GEMINI_API_KEY}"
else:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={GEMINI_API_KEY}"
        method="POST",
    )
    try:
      with urllib.request.urlopen(req, timeout=30) as resp:
        res_json = json.loads(resp.read().decode("utf-8"))
        raw = res_json["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(raw)
        section = parsed.get("section", "Uploaded Section")
        tt = parsed.get("timetable", parsed)
        save_cached_section(section, tt)
        return tt
    except urllib.error.HTTPError as e:
      last_error = e.read().decode("utf-8")
      if e.code in [503, 429]:
        time.sleep(2 * (attempt + 1))
        continue
      break
    except Exception as e:
      last_error = str(e)
      time.sleep(2)

  raise Exception(f"Gemini 3.5 Flash Error: {last_error}")


class RequestHandler(BaseHTTPRequestHandler):

  def do_GET(self):
    if self.path == "/api/sections":
      sections = load_cached_sections()
      self.send_response(200)
      self.send_header("Content-type", "application/json")
      self.end_headers()
      self.wfile.write(json.dumps(sections).encode("utf-8"))
    else:
      self.send_response(200)
      self.send_header("Content-type", "text/html")
      self.end_headers()
      self.wfile.write(HTML_PAGE.encode("utf-8"))

  def do_POST(self):
    length = int(self.headers.get("Content-Length", 0))
    body = json.loads(self.rfile.read(length).decode("utf-8"))

    if self.path == "/api/parse_timetable":
      try:
        timetable = extract_with_gemini_35(body["image_b64"])
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"timetable": timetable}).encode("utf-8"))
      except Exception as e:
        self.send_response(500)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), RequestHandler)
    print(f"Serving on port {port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
