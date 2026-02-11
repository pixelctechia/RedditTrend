"""
view_logs.py — Gera um dashboard HTML interativo com o histórico de todas as automações.

Uso:
    python execution/view_logs.py

Entradas:
    - .tmp/logs/run_history.json (gerado automaticamente pelos scripts)

Saídas:
    - .tmp/logs/dashboard.html (abrir no navegador)
"""

import json
import os
import sys
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
TMP_DIR = os.getenv("TMP_DIR", ".tmp")
LOGS_DIR = Path(TMP_DIR) / "logs"
HISTORY_FILE = LOGS_DIR / "run_history.json"
OUTPUT_HTML = LOGS_DIR / "dashboard.html"


def load_history() -> list[dict]:
    """Carrega o histórico de runs."""
    if not HISTORY_FILE.exists():
        print("❌ Nenhum log encontrado. Execute as automações primeiro.")
        sys.exit(1)

    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_html(history: list[dict]) -> str:
    """Gera o HTML completo do dashboard."""

    # Estatísticas gerais
    total_runs = len(history)
    success_runs = sum(1 for r in history if r["status"] == "success")
    error_runs = sum(1 for r in history if r["status"] == "error")
    avg_duration = sum(r.get("duration_seconds", 0) for r in history) / max(total_runs, 1)

    # Serializar dados para JS
    history_json = json.dumps(history, ensure_ascii=False)

    generated_at = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 Logs das Automações — Reddit Top Posts</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: #0f0f13;
            --bg-secondary: #1a1a24;
            --bg-card: #1e1e2e;
            --bg-card-hover: #252538;
            --border: #2a2a3e;
            --text-primary: #e4e4ef;
            --text-secondary: #9494b0;
            --text-muted: #6b6b88;
            --accent-purple: #8b5cf6;
            --accent-purple-glow: rgba(139, 92, 246, 0.15);
            --accent-green: #10b981;
            --accent-green-glow: rgba(16, 185, 129, 0.15);
            --accent-red: #ef4444;
            --accent-red-glow: rgba(239, 68, 68, 0.15);
            --accent-amber: #f59e0b;
            --accent-amber-glow: rgba(245, 158, 11, 0.15);
            --accent-blue: #3b82f6;
            --radius: 12px;
            --radius-sm: 8px;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Inter', -apple-system, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }}

        /* Header */
        .header {{
            text-align: center;
            margin-bottom: 2.5rem;
            padding: 2rem 0;
        }}

        .header h1 {{
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent-purple), #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }}

        .header .subtitle {{
            color: var(--text-secondary);
            font-size: 0.9rem;
        }}

        /* Stats Grid */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}

        .stat-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 1.25rem;
            text-align: center;
            transition: all 0.2s ease;
        }}

        .stat-card:hover {{
            border-color: var(--accent-purple);
            box-shadow: 0 0 20px var(--accent-purple-glow);
            transform: translateY(-2px);
        }}

        .stat-value {{
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }}

        .stat-label {{
            font-size: 0.8rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .stat-card.success .stat-value {{ color: var(--accent-green); }}
        .stat-card.error .stat-value {{ color: var(--accent-red); }}
        .stat-card.total .stat-value {{ color: var(--accent-purple); }}
        .stat-card.time .stat-value {{ color: var(--accent-amber); }}

        /* Filter Bar */
        .filter-bar {{
            display: flex;
            gap: 0.75rem;
            margin-bottom: 1.5rem;
            flex-wrap: wrap;
        }}

        .filter-btn {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 0.5rem 1rem;
            color: var(--text-secondary);
            font-size: 0.85rem;
            cursor: pointer;
            transition: all 0.2s ease;
            font-family: inherit;
        }}

        .filter-btn:hover, .filter-btn.active {{
            background: var(--accent-purple);
            color: white;
            border-color: var(--accent-purple);
        }}

        /* Run Cards */
        .run-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            margin-bottom: 1rem;
            overflow: hidden;
            transition: all 0.2s ease;
        }}

        .run-card:hover {{
            border-color: var(--accent-purple);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }}

        .run-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 1rem 1.25rem;
            cursor: pointer;
            user-select: none;
            flex-wrap: wrap;
            gap: 0.5rem;
        }}

        .run-header:hover {{
            background: var(--bg-card-hover);
        }}

        .run-info {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            flex-wrap: wrap;
        }}

        .status-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.3rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .status-badge.success {{
            background: var(--accent-green-glow);
            color: var(--accent-green);
            border: 1px solid rgba(16, 185, 129, 0.3);
        }}

        .status-badge.error {{
            background: var(--accent-red-glow);
            color: var(--accent-red);
            border: 1px solid rgba(239, 68, 68, 0.3);
        }}

        .status-badge.running {{
            background: var(--accent-amber-glow);
            color: var(--accent-amber);
            border: 1px solid rgba(245, 158, 11, 0.3);
        }}

        .run-script {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.9rem;
            color: var(--text-primary);
            font-weight: 500;
        }}

        .run-meta {{
            display: flex;
            align-items: center;
            gap: 1rem;
            color: var(--text-muted);
            font-size: 0.8rem;
        }}

        .run-meta span {{
            display: flex;
            align-items: center;
            gap: 0.3rem;
        }}

        .chevron {{
            transition: transform 0.2s ease;
            color: var(--text-muted);
            font-size: 1.2rem;
        }}

        .chevron.open {{
            transform: rotate(90deg);
        }}

        /* Run Details */
        .run-details {{
            display: none;
            padding: 0 1.25rem 1.25rem;
            border-top: 1px solid var(--border);
        }}

        .run-details.open {{
            display: block;
        }}

        /* Metrics */
        .metrics-grid {{
            display: flex;
            gap: 0.75rem;
            flex-wrap: wrap;
            margin: 1rem 0;
        }}

        .metric-pill {{
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            padding: 0.5rem 0.85rem;
            font-size: 0.8rem;
        }}

        .metric-pill .key {{
            color: var(--text-muted);
            margin-right: 0.4rem;
        }}

        .metric-pill .val {{
            color: var(--accent-purple);
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
        }}

        /* Log Entries */
        .log-section-title {{
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-muted);
            margin: 1rem 0 0.5rem;
        }}

        .log-entries {{
            background: var(--bg-primary);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            padding: 0.75rem;
            max-height: 400px;
            overflow-y: auto;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.78rem;
            line-height: 1.8;
        }}

        .log-entry {{
            padding: 0.15rem 0.5rem;
            border-radius: 4px;
        }}

        .log-entry:hover {{
            background: var(--bg-secondary);
        }}

        .log-time {{
            color: var(--text-muted);
            margin-right: 0.5rem;
        }}

        .log-level {{
            font-weight: 600;
            margin-right: 0.5rem;
            padding: 0.1rem 0.4rem;
            border-radius: 4px;
            font-size: 0.7rem;
        }}

        .log-level.INFO {{ color: var(--accent-blue); }}
        .log-level.WARN {{ color: var(--accent-amber); background: var(--accent-amber-glow); }}
        .log-level.ERROR {{ color: var(--accent-red); background: var(--accent-red-glow); }}

        .log-msg {{
            color: var(--text-secondary);
        }}

        /* Error Message */
        .error-box {{
            background: var(--accent-red-glow);
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: var(--radius-sm);
            padding: 0.75rem 1rem;
            color: var(--accent-red);
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            margin: 0.75rem 0;
        }}

        /* Scrollbar */
        ::-webkit-scrollbar {{ width: 6px; }}
        ::-webkit-scrollbar-track {{ background: var(--bg-primary); }}
        ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: var(--text-muted); }}

        /* Empty State */
        .empty-state {{
            text-align: center;
            padding: 3rem;
            color: var(--text-muted);
        }}

        .empty-state .icon {{ font-size: 3rem; margin-bottom: 1rem; }}

        /* Footer */
        .footer {{
            text-align: center;
            padding: 2rem 0;
            color: var(--text-muted);
            font-size: 0.75rem;
        }}

        @media (max-width: 600px) {{
            .container {{ padding: 1rem; }}
            .header h1 {{ font-size: 1.5rem; }}
            .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .run-meta {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>📊 Dashboard de Logs — Automações Reddit</h1>
            <p class="subtitle">Histórico completo de execuções • Gerado em {generated_at}</p>
        </div>

        <!-- Stats -->
        <div class="stats-grid">
            <div class="stat-card total">
                <div class="stat-value">{total_runs}</div>
                <div class="stat-label">Total de Execuções</div>
            </div>
            <div class="stat-card success">
                <div class="stat-value">{success_runs}</div>
                <div class="stat-label">✅ Sucesso</div>
            </div>
            <div class="stat-card error">
                <div class="stat-value">{error_runs}</div>
                <div class="stat-label">❌ Erros</div>
            </div>
            <div class="stat-card time">
                <div class="stat-value">{avg_duration:.1f}s</div>
                <div class="stat-label">⏱ Duração Média</div>
            </div>
        </div>

        <!-- Filters -->
        <div class="filter-bar">
            <button class="filter-btn active" onclick="filterRuns('all')">Todos</button>
            <button class="filter-btn" onclick="filterRuns('success')">✅ Sucesso</button>
            <button class="filter-btn" onclick="filterRuns('error')">❌ Erros</button>
            <button class="filter-btn" onclick="filterRuns('fetch_reddit_posts')">📡 Fetch</button>
            <button class="filter-btn" onclick="filterRuns('format_posts')">📝 Format</button>
        </div>

        <!-- Run List -->
        <div id="runs-container"></div>

        <div class="footer">
            Top 5 Reddit Posts Automation • {total_runs} run(s) registradas
        </div>
    </div>

    <script>
        const history = {history_json};

        function formatTime(isoStr) {{
            if (!isoStr) return '—';
            const d = new Date(isoStr);
            return d.toLocaleString('pt-BR', {{
                day: '2-digit', month: '2-digit', year: 'numeric',
                hour: '2-digit', minute: '2-digit', second: '2-digit'
            }});
        }}

        function formatLogTime(isoStr) {{
            if (!isoStr) return '';
            const d = new Date(isoStr);
            return d.toLocaleTimeString('pt-BR', {{ hour: '2-digit', minute: '2-digit', second: '2-digit' }});
        }}

        function toggleDetails(id) {{
            const el = document.getElementById('details-' + id);
            const chev = document.getElementById('chevron-' + id);
            if (el) {{
                el.classList.toggle('open');
                chev.classList.toggle('open');
            }}
        }}

        function filterRuns(filter) {{
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            event.target.classList.add('active');
            renderRuns(filter);
        }}

        function renderRuns(filter = 'all') {{
            const container = document.getElementById('runs-container');
            let runs = [...history].reverse(); // Mais recente primeiro

            if (filter === 'success') runs = runs.filter(r => r.status === 'success');
            else if (filter === 'error') runs = runs.filter(r => r.status === 'error');
            else if (filter !== 'all') runs = runs.filter(r => r.script === filter);

            if (runs.length === 0) {{
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="icon">📭</div>
                        <p>Nenhuma execução encontrada para este filtro.</p>
                    </div>`;
                return;
            }}

            container.innerHTML = runs.map((run, idx) => {{
                const statusIcon = run.status === 'success' ? '●' : run.status === 'error' ? '●' : '◉';

                // Metrics
                const metricsHtml = run.metrics && Object.keys(run.metrics).length > 0
                    ? `<div class="metrics-grid">` +
                      Object.entries(run.metrics).map(([k, v]) =>
                          `<div class="metric-pill"><span class="key">${{k}}:</span><span class="val">${{v}}</span></div>`
                      ).join('') + `</div>`
                    : '';

                // Error
                const errorHtml = run.error
                    ? `<div class="error-box">❌ ${{run.error}}</div>`
                    : '';

                // Log entries
                const logsHtml = run.log_entries && run.log_entries.length > 0
                    ? `<div class="log-section-title">Log de execução (${{run.log_entries.length}} entradas)</div>
                       <div class="log-entries">` +
                      run.log_entries.map(e =>
                          `<div class="log-entry">` +
                          `<span class="log-time">${{formatLogTime(e.time)}}</span>` +
                          `<span class="log-level ${{e.level}}">${{e.level}}</span>` +
                          `<span class="log-msg">${{e.message}}</span>` +
                          `</div>`
                      ).join('') + `</div>`
                    : '';

                return `
                <div class="run-card" data-status="${{run.status}}" data-script="${{run.script}}">
                    <div class="run-header" onclick="toggleDetails(${{idx}})">
                        <div class="run-info">
                            <span class="status-badge ${{run.status}}">${{statusIcon}} ${{run.status}}</span>
                            <span class="run-script">${{run.script}}</span>
                        </div>
                        <div class="run-meta">
                            <span>📅 ${{formatTime(run.started_at)}}</span>
                            <span>⏱ ${{run.duration_seconds}}s</span>
                            <span class="chevron" id="chevron-${{idx}}">▶</span>
                        </div>
                    </div>
                    <div class="run-details" id="details-${{idx}}">
                        ${{errorHtml}}
                        ${{metricsHtml}}
                        ${{logsHtml}}
                    </div>
                </div>`;
            }}).join('');
        }}

        // Render inicial
        renderRuns();
    </script>
</body>
</html>"""

    return html


def main():
    history = load_history()
    html = generate_html(history)

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    abs_path = OUTPUT_HTML.resolve()
    print(f"✅ Dashboard gerado: {abs_path}")
    print(f"📊 {len(history)} execuções registradas")

    # Tentar abrir no navegador
    try:
        webbrowser.open(f"file://{abs_path}")
        print("🌐 Abrindo no navegador...")
    except Exception:
        print(f"   Abra manualmente: file://{abs_path}")


if __name__ == "__main__":
    main()
