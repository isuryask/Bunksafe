import base64
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import math
import os
import time
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


def save_cached_section(dept_sec_key, data):
  cache = load_cached_sections()
  cache[dept_sec_key] = data
  with open(CACHE_FILE, "w") as f:
    json.dump(cache, f, indent=2)


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>BunkSafe • Precision Attendance OS</title>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #090a0f;
    --surface: #11141d;
    --surface-elevated: #161b27;
    --border: rgba(255, 255, 255, 0.08);
    --border-hover: rgba(255, 255, 255, 0.16);
    --primary: #38bdf8;
    --safe: #10b981;
    --safe-dim: rgba(16, 185, 129, 0.12);
    --danger: #f43f5e;
    --danger-dim: rgba(244, 63, 94, 0.12);
    --text-high: #f8fafc;
    --text-med: #94a3b8;
    --text-low: #64748b;
    --radius: 12px;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
  body { background: var(--bg); color: var(--text-high); padding: 20px 16px 110px; min-height: 100vh; }
  .shell { max-width: 520px; margin: 0 auto; }
  
  .top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 14px; border-bottom: 1px solid var(--border); }
  .logo-box { display: flex; align-items: center; gap: 10px; }
  .logo-icon { width: 28px; height: 28px; background: linear-gradient(135deg, #0284c7, #38bdf8); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.85rem; }
  .logo-title { font-weight: 700; font-size: 0.95rem; }
  .badge { font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; padding: 3px 8px; border-radius: 999px; background: rgba(255,255,255,0.04); border: 1px solid var(--border); color: var(--text-low); }

  .panel { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 18px; margin-bottom: 14px; }
  
  .hero-panel { display: none; background: linear-gradient(180deg, #161b27, #11141d); border: 1px solid var(--border-hover); border-radius: 18px; padding: 22px 18px; text-align: center; margin-bottom: 16px; }
  .hero-metric { display: flex; align-items: center; justify-content: center; gap: 24px; margin: 14px 0; }
  .hero-pct { font-family: 'JetBrains Mono', monospace; font-size: 2.3rem; font-weight: 800; }
  .hero-detail { text-align: left; }
  .hero-label { font-size: 0.7rem; color: var(--text-low); text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; }
  .hero-val { font-family: 'JetBrains Mono', monospace; font-size: 1.15rem; font-weight: 700; }
  
  .label-title { font-size: 0.74rem; font-weight: 700; color: var(--text-med); text-transform: uppercase; margin-bottom: 6px; }
  select, input[type="date"], input[type="text"] {
    width: 100%; background: var(--bg); border: 1px solid var(--border); color: var(--text-high);
    padding: 11px 13px; border-radius: 10px; font-size: 0.86rem; margin-bottom: 12px; outline: none;
  }
  select:focus, input:focus { border-color: var(--primary); }
  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }

  .dropzone {
    border: 1.5px dashed var(--border-hover); background: rgba(255,255,255,0.02);
    border-radius: 10px; padding: 16px; text-align: center; position: relative; margin-bottom: 12px;
  }
  .dropzone.ready { border-style: solid; border-color: rgba(16, 185, 129, 0.4); background: var(--safe-dim); }
  .dropzone input[type="file"] { position: absolute; inset: 0; opacity: 0; width: 100%; height: 100%; cursor: pointer; }
  
  .card-sub { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px; margin-bottom: 10px; }
  .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
  .sub-title { font-size: 0.9rem; font-weight: 700; }
  .sub-pill { font-family: 'JetBrains Mono', monospace; font-size: 0.74rem; font-weight: 800; padding: 2px 7px; border-radius: 6px; }
  .pill-safe { background: var(--safe-dim); color: var(--safe); }
  .pill-danger { background: var(--danger-dim); color: var(--danger); }
  
  .progress-bg { height: 6px; background: var(--bg); border-radius: 999px; overflow: hidden; margin-bottom: 10px; }
  .progress-bar { height: 100%; border-radius: 999px; }
  
  .sub-meta { display: grid; grid-template-columns: 1fr 1fr; font-size: 0.76rem; color: var(--text-med); gap: 4px; }
  .sub-meta b { color: var(--text-high); font-family: 'JetBrains Mono', monospace; }
  .insight { grid-column: span 2; padding: 6px 9px; border-radius: 6px; font-size: 0.74rem; margin-top: 4px; font-weight: 600; }
  .insight-safe { background: var(--safe-dim); color: #6ee7b7; }
  .insight-danger { background: var(--danger-dim); color: #fda4af; }

  .actions-shelf { display: flex; flex-wrap: wrap; gap: 6px; min-height: 24px; margin-top: 8px; }
  .action-chip { font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; font-weight: 600; padding: 2px 8px; border-radius: 6px; background: var(--danger-dim); color: #fda4af; border: 1px solid rgba(244,63,94,0.3); }

  .fixed-bar {
    position: fixed; bottom: 0; left: 0; right: 0; background: rgba(9, 10, 15, 0.9);
    backdrop-filter: blur(14px); padding: 12px 16px env(safe-area-inset-bottom); border-top: 1px solid var(--border);
  }
  .btn-calc {
    width: 100%; max-width: 520px; display: block; margin: 0 auto;
    background: linear-gradient(180deg, #0284c7, #0369a1); border: 1px solid rgba(255,255,255,0.2);
    color: #fff; padding: 14px; border-radius: 12px; font-size: 0.92rem; font-weight: 700; cursor: pointer;
  }
  #statusMsg { text-align: center; font-size: 0.75rem; color: var(--primary); margin-top: 5px; min-height: 1em; }
</style>
</head>
<body>
<div class="shell">
  <div class="top-bar">
    <div class="logo-box">
      <div class="logo-icon">B</div>
      <div class="logo-title">BunkSafe OS</div>
    </div>
    <div class="badge">Adaptive Section Memory</div>
  </div>

  <div class="hero-panel" id="heroCard">
    <div style="font-size:0.75rem; font-weight:700; color:var(--text-med); text-transform:uppercase;">Overall Attendance Score</div>
    <div class="hero-metric">
      <div class="hero-pct" id="heroPct">--%</div>
      <div class="hero-detail">
        <div class="hero-label">Attended Periods</div>
        <div class="hero-val" id="heroCount">-- / --</div>
        <div class="hero-label" style="margin-top:4px;">Target Rule</div>
        <div class="hero-val" style="font-size:0.85rem; color:var(--text-med);">80.0% Minimum</div>
      </div>
    </div>
  </div>

  <div class="panel">
    <div class="label-title">Saved Sections Memory</div>
    <select id="sectionSelect" onchange="onSectionSelect(this.value)">
      <option value="">-- Select Saved Department & Section --</option>
    </select>

    <div class="grid-2">
      <div>
        <div class="label-title">Department</div>
        <input type="text" id="deptInput" value="ECE">
      </div>
      <div>
        <div class="label-title">Section</div>
        <input type="text" id="secInput" value="Section C2">
      </div>
    </div>

    <div class="dropzone" id="uploadCard">
      <input type="file" id="imageInput" accept="image/*">
      <div id="dropText">
        <div style="font-size:1.3rem;">📷</div>
        <div style="font-weight:700; font-size:0.85rem;">Upload Timetable Image</div>
        <div style="font-size:0.72rem; color:var(--text-low);">Extracts schedule & caches to Section Memory</div>
      </div>
      <div id="dropReady" style="display:none; font-size:0.8rem; font-weight:700; color:var(--safe);">
        ✓ Timetable Image Selected
      </div>
    </div>

    <div class="grid-2">
      <div>
        <div class="label-title">Batch Setup</div>
        <select id="yearBatchSelect">
          <option value="Senior" selected>2nd, 3rd, 4th Year (Sat Off)</option>
          <option value="Fresher">1st Year (Sat Working)</option>
        </select>
      </div>
      <div>
        <div class="label-title">Today's Date</div>
        <input type="date" id="todayDate">
      </div>
    </div>

    <div style="margin-top:4px;">
      <div class="label-title">Record Personal Absence Date</div>
      <div style="display:flex; gap:8px;">
        <input type="date" id="absentPicker" style="margin-bottom:0;">
        <button type="button" onclick="addAbsence()" style="padding:0 14px; background:var(--surface-elevated); border:1px solid var(--border); color:#fff; border-radius:10px; font-weight:700; cursor:pointer;">+ Add</button>
      </div>
      <div class="actions-shelf" id="absentShelf"></div>
    </div>
  </div>

  <div id="resultsContainer"></div>
</div>

<div class="fixed-bar">
  <button class="btn-calc" id="calcBtn" onclick="calculateAll()">Calculate Attendance Architecture</button>
  <div id="statusMsg"></div>
</div>

<script>
  document.getElementById('todayDate').valueAsDate = new Date();

  let absentDates = new Set(JSON.parse(localStorage.getItem('user_absents') || "[]"));
  function renderAbsents() {
    const shelf = document.getElementById('absentShelf');
    shelf.innerHTML = absentDates.size === 0 ? '<span style="font-size:0.72rem; color:var(--text-low);">No personal leaves recorded.</span>' : '';
    Array.from(absentDates).sort().forEach(d => {
      shelf.innerHTML += `<div class="action-chip">${d} <span style="cursor:pointer;" onclick="delAbsence('${d}')">&times;</span></div>`;
    });
    localStorage.setItem('user_absents', JSON.stringify(Array.from(absentDates)));
  }
  function addAbsence() {
    const v = document.getElementById('absentPicker').value;
    if (v) { absentDates.add(v); renderAbsents(); document.getElementById('absentPicker').value = ""; }
  }
  function delAbsence(d) {
    absentDates.delete(d);
    renderAbsents();
  }
  renderAbsents();

  let cachedSections = {};
  async function loadSections() {
    try {
      const res = await fetch('/api/sections');
      cachedSections = await res.json();
      const sel = document.getElementById('sectionSelect');
      sel.innerHTML = '<option value="">-- Select Saved Department & Section --</option>';
      for (const k in cachedSections) {
        const opt = document.createElement('option');
        opt.value = k;
        opt.innerText = k;
        sel.appendChild(opt);
      }
    } catch(e) {}
  }
  loadSections();

  let activeTimetable = null;
  let imageBase64 = null;

  function onSectionSelect(key) {
    if (cachedSections[key]) {
      activeTimetable = cachedSections[key].timetable || cachedSections[key];
      document.getElementById('statusMsg').innerText = `✓ Loaded: ${key}`;
    }
  }

  document.getElementById('imageInput').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (!file) return;
    document.getElementById('dropText').style.display = "none";
    document.getElementById('dropReady').style.display = "block";
    document.getElementById('uploadCard').classList.add('ready');

    const reader = new FileReader();
    reader.onload = function(evt) {
      const img = new Image();
      img.onload = function() {
        const canvas = document.createElement('canvas');
        const MAX_W = 1000;
        let w = img.width, h = img.height;
        if (w > MAX_W) { h = Math.round((h * MAX_W) / w); w = MAX_W; }
        canvas.width = w; canvas.height = h;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, w, h);
        imageBase64 = canvas.toDataURL('image/jpeg', 0.8).split(',')[1];
        activeTimetable = null;
      };
      img.src = evt.target.result;
    };
    reader.readAsDataURL(file);
  });

  async function calculateAll() {
    const status = document.getElementById('statusMsg');
    const dept = document.getElementById('deptInput').value.trim() || "ECE";
    const sec = document.getElementById('secInput').value.trim() || "Section C2";

    if (!activeTimetable && !imageBase64) {
      alert("Please choose a saved Section or select a timetable picture.");
      return;
    }

    if (!activeTimetable && imageBase64) {
      status.innerText = "Analyzing schedule via adaptive AQ engine...";
      try {
        const res = await fetch('/api/parse_timetable', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ image_b64: imageBase64, department: dept, section: sec })
        });
        const data = await res.json();
        activeTimetable = data.timetable;
        await loadSections();
      } catch(err) {
        status.innerText = "Error: " + err.message;
        return;
      }
    }

    status.innerText = "";
    runCompute();
  }

  function runCompute() {
    if (!activeTimetable) return;

    const start = new Date("2026-07-01");
    const today = new Date(document.getElementById('todayDate').value);
    const isFresher = document.getElementById('yearBatchSelect').value === "Fresher";

    const days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
    const held = {}, att = {};
    let totHeld = 0, totAtt = 0;

    for (let d = new Date(start); d <= today; d.setDate(d.getDate() + 1)) {
      const idx = d.getDay();
      if (idx === 0) continue;
      if (idx === 6 && !isFresher) continue;

      const dStr = d.toISOString().split('T')[0];
      const isAbsent = absentDates.has(dStr);
      const periods = activeTimetable[days[idx]] || [];

      periods.forEach(sub => {
        held[sub] = (held[sub] || 0) + 1;
        totHeld += 1;
        if (!isAbsent) {
          att[sub] = (att[sub] || 0) + 1;
          totAtt += 1;
        }
      });
    }

    const overallPct = totHeld > 0 ? (totAtt / totHeld * 100) : 100.0;
    const heroCard = document.getElementById('heroCard');
    heroCard.style.display = "block";
    const hPct = document.getElementById('heroPct');
    hPct.innerText = `${overallPct.toFixed(1)}%`;
    hPct.style.color = overallPct >= 80 ? "var(--safe)" : "var(--danger)";
    document.getElementById('heroCount').innerText = `${totAtt} / ${totHeld}`;

    const container = document.getElementById('resultsContainer');
    container.innerHTML = "";

    Object.keys(held).sort().forEach(sub => {
      const h = held[sub] || 0;
      const a = att[sub] || 0;
      const pct = h > 0 ? (a / h * 100) : 100.0;
      const isSafe = pct >= 80;
      const needed = Math.max(0, Math.ceil(4 * h - 5 * a));
      const bunks = isSafe ? Math.max(0, Math.floor(a / 0.8 - h)) : 0;

      const card = document.createElement('div');
      card.className = 'card-sub';
      card.innerHTML = `
        <div class="card-header">
          <div class="sub-title">${sub}</div>
          <span class="sub-pill ${isSafe ? 'pill-safe' : 'pill-danger'}">${pct.toFixed(1)}%</span>
        </div>
        <div class="progress-bg">
          <div class="progress-bar" style="width:${Math.min(100, pct)}%; background:${isSafe ? 'var(--safe)' : 'var(--danger)'};"></div>
        </div>
        <div class="sub-meta">
          <div>Attended: <b>${a} / ${h}</b></div>
          <div style="text-align:right;">Status: <b style="color:${isSafe ? 'var(--safe)' : 'var(--danger)'};">${isSafe ? 'SAFE' : 'SHORTAGE'}</b></div>
          ${!isSafe 
            ? `<div class="insight insight-danger">⚠️ Attend next <b>${needed}</b> consecutive classes to hit 80%.</div>`
            : `<div class="insight insight-safe">🛡️ Safe Buffer: Can bunk up to <b>${bunks}</b> class(es).</div>`
          }
        </div>
      `;
      container.appendChild(card);
    });

    heroCard.scrollIntoView({ behavior: 'smooth' });
  }
</script>
</body>
</html>
"""

DEFAULT_SYLLABUS = {
    "Monday": [
        "Signals & Systems",
        "Signals & Systems",
        "Electromagnetic Fields",
        "Digital Logic",
        "Digital Logic Lab",
    ],
    "Tuesday": [
        "Analog Circuits",
        "Linear Integrated Circuits",
        "Signals & Systems",
        "Analog Circuits Lab",
        "Analog Circuits Lab",
    ],
    "Wednesday": [
        "Electromagnetic Fields",
        "Analog Circuits",
        "Digital Logic",
        "Linear Integrated Circuits",
        "Tutorial",
    ],
    "Thursday": [
        "Digital Logic",
        "Signals & Systems",
        "Linear Integrated Circuits",
        "Signals Lab",
        "Signals Lab",
    ],
    "Friday": [
        "Analog Circuits",
        "Electromagnetic Fields",
        "Signals & Systems",
        "Digital Logic",
        "Mentoring",
    ],
    "Saturday": [],
}


def extract_with_gemini(image_b64, dept, sec):
  prompt = f"Extract weekly schedule JSON for Dept '{dept}' Section '{sec}': keys Monday to Saturday."
  req_body = {
      "contents": [{
          "parts": [
              {"text": prompt},
              {"inlineData": {"mimeType": "image/jpeg", "data": image_b64}},
          ]
      }],
      "generationConfig": {"responseMimeType": "application/json"},
  }

  url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
  headers = {"Content-Type": "application/json"}
  if GEMINI_API_KEY:
    headers["x-goog-api-key"] = GEMINI_API_KEY
    headers["Authorization"] = f"Bearer {GEMINI_API_KEY}"

  parsed_tt = None
  try:
    req = urllib.request.Request(
        url,
        data=json.dumps(req_body).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
      data = json.loads(resp.read().decode("utf-8"))
      parsed_tt = json.loads(
          data["candidates"][0]["content"]["parts"][0]["text"]
      ).get("timetable", None)
  except Exception as e:
    print(f"Extraction fallback triggered: {e}")
    parsed_tt = DEFAULT_SYLLABUS

  dept_sec_key = f"{dept} - {sec}"
  save_cached_section(
      dept_sec_key,
      {
          "department": dept,
          "section": sec,
          "timetable": parsed_tt or DEFAULT_SYLLABUS,
      },
  )
  return parsed_tt or DEFAULT_SYLLABUS


class AppHandler(BaseHTTPRequestHandler):

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
      dept = body.get("department", "ECE")
      sec = body.get("section", "Section C2")
      timetable = extract_with_gemini(body.get("image_b64", ""), dept, sec)
      self.send_response(200)
      self.send_header("Content-type", "application/json")
      self.end_headers()
      self.wfile.write(json.dumps({"timetable": timetable}).encode("utf-8"))


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 8080))
  server = HTTPServer(("0.0.0.0", port), AppHandler)
  print(f"Serving BunkSafe on port {port}")
  try:
    server.serve_forever()
  except KeyboardInterrupt:
    pass
