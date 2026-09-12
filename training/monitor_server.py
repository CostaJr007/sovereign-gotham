"""
Sovereign Gotham - Real-Time Training Progress Live Monitor Server
Runs a lightweight web server on http://localhost:8888.
Renders an executive Palantir-styled dark-mode dashboard displaying:
  - Real-time training progress percentage (0% -> 100%).
  - Step counter, Current Epoch, Loss progression.
  - VRAM allocation gauge (10 GB target / 16 GB RX 7600 XT).
  - Estimated Time Remaining (ETA) and elapsed duration.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

STATUS_FILE = Path("D:/sovereign_models/training_status.json") if Path("D:/").exists() else Path("./models/training_status.json")


def get_current_status():
    default_status = {
        "status": "INITIALIZING",
        "progress_pct": 0.0,
        "current_step": 0,
        "total_steps": 1000,
        "epoch": 0.0,
        "total_epochs": 3,
        "loss": None,
        "loss_history": [],
        "elapsed_seconds": 0,
        "eta_seconds": 0,
        "vram_target": "14.0 GB",
        "gpu_name": "AMD Radeon RX 7600 XT (16 GB)",
        "model_id": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
        "dataset_samples": 1788,
    }
    if STATUS_FILE.exists():
        try:
            return json.loads(STATUS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return default_status
    return default_status


HTML_PAGE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Sovereign Gotham // Live Training Monitor</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700;800&family=Outfit:wght@400;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #07090e;
      --card-bg: rgba(15, 20, 32, 0.75);
      --border: rgba(0, 240, 255, 0.15);
      --accent: #00f0ff;
      --accent-glow: rgba(0, 240, 255, 0.35);
      --success: #00ff88;
      --warning: #ffb700;
      --text-main: #e2e8f0;
      --text-muted: #64748b;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg);
      color: var(--text-main);
      font-family: 'Outfit', sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 30px 20px;
      overflow-x: hidden;
      background-image: radial-gradient(circle at 50% 0%, rgba(0, 240, 255, 0.08) 0%, transparent 60%);
    }
    .header {
      width: 100%;
      max-width: 1000px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 30px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 20px;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .brand-icon {
      width: 40px;
      height: 40px;
      background: linear-gradient(135deg, var(--accent), #0077ff);
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      color: #000;
      font-family: 'JetBrains Mono', monospace;
    }
    .brand-title {
      font-size: 20px;
      font-weight: 700;
      letter-spacing: 1px;
      text-transform: uppercase;
    }
    .brand-sub {
      font-size: 12px;
      color: var(--accent);
      font-family: 'JetBrains Mono', monospace;
      letter-spacing: 0.5px;
    }
    .status-badge {
      font-family: 'JetBrains Mono', monospace;
      font-size: 13px;
      padding: 6px 16px;
      border-radius: 20px;
      background: rgba(0, 255, 136, 0.1);
      border: 1px solid var(--success);
      color: var(--success);
      display: flex;
      align-items: center;
      gap: 8px;
      text-transform: uppercase;
      font-weight: 600;
    }
    .pulse-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--success);
      box-shadow: 0 0 10px var(--success);
      animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
      0% { opacity: 0.4; }
      50% { opacity: 1; }
      100% { opacity: 0.4; }
    }
    .main-grid {
      width: 100%;
      max-width: 1000px;
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 20px;
      margin-bottom: 25px;
    }
    .metric-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px;
      backdrop-filter: blur(12px);
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .metric-title {
      font-size: 12px;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.8px;
      font-weight: 600;
    }
    .metric-value {
      font-size: 28px;
      font-weight: 700;
      font-family: 'JetBrains Mono', monospace;
      color: #fff;
    }
    .metric-foot {
      font-size: 12px;
      color: var(--accent);
      font-family: 'JetBrains Mono', monospace;
    }
    .progress-section {
      width: 100%;
      max-width: 1000px;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 30px;
      backdrop-filter: blur(12px);
      margin-bottom: 25px;
    }
    .prog-header {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      margin-bottom: 15px;
    }
    .prog-title {
      font-size: 16px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1px;
    }
    .prog-pct {
      font-size: 42px;
      font-weight: 800;
      font-family: 'JetBrains Mono', monospace;
      color: var(--accent);
      text-shadow: 0 0 20px var(--accent-glow);
    }
    .bar-container {
      width: 100%;
      height: 18px;
      background: rgba(255, 255, 255, 0.05);
      border-radius: 10px;
      overflow: hidden;
      border: 1px solid rgba(255, 255, 255, 0.1);
      position: relative;
    }
    .bar-fill {
      height: 100%;
      width: 0%;
      background: linear-gradient(90deg, #0077ff, var(--accent), var(--success));
      border-radius: 10px;
      box-shadow: 0 0 15px var(--accent-glow);
      transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .vram-gauge {
      width: 100%;
      max-width: 1000px;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 24px;
      backdrop-filter: blur(12px);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .vram-info {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .vram-tag {
      font-family: 'JetBrains Mono', monospace;
      font-size: 13px;
      color: var(--warning);
      background: rgba(255, 183, 0, 0.1);
      border: 1px solid var(--warning);
      padding: 4px 10px;
      border-radius: 6px;
      display: inline-block;
      width: fit-content;
    }
  </style>
</head>
<body>
  <div class="header">
    <div class="brand">
      <div class="brand-icon">AGY</div>
      <div>
        <div class="brand-title">Sovereign Gotham</div>
        <div class="brand-sub">DeepSeek-R1-Distill-Qwen-7B // Live Cognitive Training</div>
      </div>
    </div>
    <div class="status-badge" id="badgeContainer">
      <div class="pulse-dot" id="pulseDot"></div>
      <span id="statusText">TREINANDO</span>
    </div>
  </div>

  <div class="main-grid">
    <div class="metric-card">
      <div class="metric-title">Passo / Total</div>
      <div class="metric-value" id="stepCounter">0 / 0</div>
      <div class="metric-foot" id="epochText">Época 0.0 de 3.0</div>
    </div>
    <div class="metric-card">
      <div class="metric-title">Tempo Estimado (ETA)</div>
      <div class="metric-value" id="etaCounter">Calculando...</div>
      <div class="metric-foot" id="elapsedText">Decorrido: 0s</div>
    </div>
    <div class="metric-card">
      <div class="metric-title">Loss da Rede</div>
      <div class="metric-value" id="lossCounter">--</div>
      <div class="metric-foot">Convergência Neural</div>
    </div>
    <div class="metric-card">
      <div class="metric-title">Alocação VRAM</div>
      <div class="metric-value" id="vramCounter">14.0 GB</div>
      <div class="metric-foot">AMD RX 7600 XT (16 GB)</div>
    </div>
  </div>

  <div class="progress-section">
    <div class="prog-header">
      <div class="prog-title">Progresso Geral do Treinamento</div>
      <div class="prog-pct" id="progressPct">0.0%</div>
    </div>
    <div class="bar-container">
      <div class="bar-fill" id="progressBar"></div>
    </div>
  </div>

  <div class="vram-gauge">
    <div class="vram-info">
      <div style="font-weight:700; font-size:15px; margin-bottom:4px;">Perfil de Memória Dedicado (Alta Performance)</div>
      <div style="font-size:13px; color:var(--text-muted);">Alocação agressiva de 14 GB de VRAM aproveitando ao máximo a sua RX 7600 XT de 16 GB.</div>
    </div>
    <div class="vram-tag" id="hardwareTag">AMD Radeon RX 7600 XT (16 GB GDDR6)</div>
  </div>

  <script>
    function formatTime(secs) {
      if (!secs || secs <= 0) return "0s";
      const h = Math.floor(secs / 3600);
      const m = Math.floor((secs % 3600) / 60);
      const s = secs % 60;
      if (h > 0) return `${h}h ${m}m ${s}s`;
      if (m > 0) return `${m}m ${s}s`;
      return `${s}s`;
    }

    async function updateStatus() {
      try {
        const res = await fetch('/api/status');
        if (!res.ok) return;
        const data = await res.json();

        // Update progress
        const pct = data.progress_pct || 0;
        document.getElementById('progressPct').innerText = `${pct.toFixed(1)}%`;
        document.getElementById('progressBar').style.width = `${Math.min(pct, 100)}%`;

        // Update Steps
        document.getElementById('stepCounter').innerText = `${data.current_step} / ${data.total_steps}`;
        document.getElementById('epochText').innerText = `Época ${(data.epoch || 0).toFixed(2)} de ${data.total_epochs || 3}`;

        // Update Times
        document.getElementById('etaCounter').innerText = data.eta_seconds > 0 ? formatTime(data.eta_seconds) : "Calculando...";
        document.getElementById('elapsedText').innerText = `Decorrido: ${formatTime(data.elapsed_seconds)}`;

        // Update Loss
        document.getElementById('lossCounter').innerText = data.loss ? data.loss.toFixed(4) : "--";

        // Update VRAM Allocation
        const targetVram = data.vram_target ? (data.vram_target.toUpperCase().includes('GB') ? data.vram_target : data.vram_target + ' GB') : '14.0 GB';
        document.getElementById('vramCounter').innerText = targetVram;

        // Update Badge
        document.getElementById('statusText').innerText = data.status || "INICIANDO";
        if (data.status === "COMPLETED" || data.status === "CONCLUÍDO") {
          document.getElementById('badgeContainer').style.borderColor = "#00ff88";
          document.getElementById('statusText').innerText = "CONCLUÍDO";
        }
      } catch (err) {
        console.error("Monitor polling error:", err);
      }
    }

    setInterval(updateStatus, 1500);
    updateStatus();
  </script>
</body>
</html>
"""


class MonitorHTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            status_json = json.dumps(get_current_status()).encode("utf-8")
            self.wfile.write(status_json)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        return  # Suppress console HTTP access logs to keep terminal clean


def run_monitor_server(port: int = 8888):
    server = HTTPServer(("0.0.0.0", port), MonitorHTTPHandler)
    print(f"[*] Sovereign Gotham Live Training Monitor running at: http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_monitor_server()
