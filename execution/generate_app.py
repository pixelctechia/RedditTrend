"""
generate_app.py — Gera um app web premium para visualizar os Top 5 posts do Reddit.

Design inspirado em dashboards modernos SaaS (estilo Arounda UI).
Fundo claro, cards brancos, acentos roxo/dourado, layout espaçoso.

Funcionalidades:
    - Dashboard com tabs por subreddit e stat cards
    - Modo "Top Relevantes" (ranking por engajamento)
    - Modo "Mais Recentes" (10 posts mais novos com filtro dia/semana/mês)
    - Página Posts (tabela comparativa geral)
    - Página Trends (gráficos de barras CSS)
    - Página Configurações (parâmetros do .env)
    - Página Logs (histórico de execuções)

Uso:
    python execution/generate_app.py

Entradas:
    - .tmp/formatted_posts.json     (top N por engajamento)
    - .tmp/formatted_all_posts.json (todos os posts — modo "Mais Recentes")

Saídas:
    - .tmp/app.html (abrir no navegador)
"""

import json
import os
import sys
import datetime
import base64
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
TMP_DIR = os.getenv("TMP_DIR", ".tmp")
DATA_FILE = Path(TMP_DIR) / "formatted_posts.json"
ALL_DATA_FILE = Path(TMP_DIR) / "formatted_all_posts.json"
LOGS_FILE = Path(TMP_DIR) / "logs" / "run_history.json"
OUTPUT_HTML = Path(TMP_DIR) / "app.html"


def load_data() -> list[dict]:
    if not DATA_FILE.exists():
        print("❌ Dados não encontrados. Execute o pipeline primeiro:")
        print("   python execution/fetch_reddit_posts.py")
        print("   python execution/format_posts.py")
        sys.exit(1)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_all_data() -> list[dict]:
    """Carrega TODOS os posts formatados (para modo 'Mais Recentes')."""
    if ALL_DATA_FILE.exists():
        with open(ALL_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # Fallback: se não existir, retorna lista vazia (o dashboard desabilita o modo)
    print("⚠️ formatted_all_posts.json não encontrado. Modo 'Mais Recentes' desabilitado.")
    return []


def load_config() -> dict:
    """Carrega configurações do .env para exibir na página Settings."""
    return {
        "TARGET_SUBREDDITS": os.getenv("TARGET_SUBREDDITS", "n8n,automation"),
        "FETCH_LIMIT": os.getenv("FETCH_LIMIT", "100"),
        "TOP_N": os.getenv("TOP_N", "5"),
        "PERIOD_DAYS": os.getenv("PERIOD_DAYS", "7"),
        "WEIGHT_SCORE": os.getenv("WEIGHT_SCORE", "1.0"),
        "WEIGHT_COMMENTS": os.getenv("WEIGHT_COMMENTS", "2.0"),
        "WEIGHT_RATIO": os.getenv("WEIGHT_RATIO", "50.0"),
        "TMP_DIR": os.getenv("TMP_DIR", ".tmp"),
    }


def load_logs() -> list[dict]:
    """Carrega histórico de execuções."""
    if LOGS_FILE.exists():
        try:
            with open(LOGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def generate_html(posts: list[dict], all_posts_data: list[dict]) -> str:
    config = load_config() # Load config here to pass to base64 encoding
    logs = load_logs() # Load logs here to pass to base64 encoding

    posts_json = base64.b64encode(json.dumps(posts, ensure_ascii=False).encode('utf-8')).decode('utf-8')
    all_posts_json = base64.b64encode(json.dumps(all_posts_data, ensure_ascii=False).encode('utf-8')).decode('utf-8')
    config_json = base64.b64encode(json.dumps(config, ensure_ascii=False).encode('utf-8')).decode('utf-8')
    logs_json = base64.b64encode(json.dumps(logs, ensure_ascii=False).encode('utf-8')).decode('utf-8')
    
    # Ler comunidades registradas no .env para garantir que apareçam nas tabs
    env_subs_raw = os.getenv("TARGET_SUBREDDITS", "")
    env_communities = [s.strip() for s in env_subs_raw.split(",") if s.strip()]
    env_communities_json = base64.b64encode(json.dumps(env_communities, ensure_ascii=False).encode('utf-8')).decode('utf-8')

    subs = {}
    for p in posts:
        s = p["subreddit"]
        if s not in subs:
            subs[s] = []
        subs[s].append(p)

    total_posts = len(posts)
    total_engagement = sum(p.get("engagement_score", 0) for p in posts)
    total_comments = sum(p.get("num_comments", 0) for p in posts)
    avg_ratio = sum(p.get("upvote_ratio", 0) for p in posts) / max(total_posts, 1)

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Top Reddit Posts — n8n & Automation Dashboard</title>
    <meta name="description" content="Dashboard dos 5 posts mais relevantes da semana sobre n8n e automação no Reddit">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-page: #f0eef6;
            --bg-sidebar: #ffffff;
            --bg-card: #ffffff;
            --bg-card-hover: #faf9ff;
            --bg-input: #f5f4f9;
            --bg-badge: #f3f0ff;

            --border: #ebe8f2;
            --border-hover: #c9c0e8;

            --text-primary: #1a1530;
            --text-secondary: #5e5a6e;
            --text-muted: #9490a3;
            --text-light: #b8b4c6;

            --purple-600: #6c3ce9;
            --purple-500: #7c4dff;
            --purple-400: #9b7aff;
            --purple-300: #c5b3ff;
            --purple-100: #ede8ff;
            --purple-50: #f7f5ff;

            --gold-500: #f5a623;
            --gold-400: #ffc857;
            --gold-100: #fff8eb;

            --green-500: #22c55e;
            --green-100: #ecfdf5;
            --blue-500: #3b82f6;
            --blue-100: #eff6ff;
            --red-500: #ef4444;
            --amber-500: #eab308;
            --amber-100: #fefce8;

            --radius-xl: 20px;
            --radius-lg: 16px;
            --radius-md: 12px;
            --radius-sm: 8px;
            --radius-xs: 6px;

            --shadow-sm: 0 1px 3px rgba(26, 21, 48, 0.04);
            --shadow-md: 0 4px 16px rgba(26, 21, 48, 0.06);
            --shadow-lg: 0 8px 32px rgba(26, 21, 48, 0.08);
            --shadow-card: 0 2px 12px rgba(26, 21, 48, 0.05);
            --shadow-hover: 0 8px 30px rgba(108, 60, 233, 0.1);

            --transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-page);
            color: var(--text-primary);
            min-height: 100vh;
            -webkit-font-smoothing: antialiased;
        }}

        /* ===== LAYOUT ===== */
        .layout {{
            display: flex;
            min-height: 100vh;
        }}

        /* ===== SIDEBAR ===== */
        .sidebar {{
            width: 72px;
            background: var(--bg-sidebar);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 1.5rem 0;
            gap: 0.5rem;
            position: fixed;
            top: 0;
            left: 0;
            height: 100vh;
            z-index: 10;
        }}

        .sidebar-logo {{
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, var(--purple-600), var(--purple-400));
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            color: white;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 12px rgba(108, 60, 233, 0.3);
        }}

        .sidebar-icon {{
            width: 42px;
            height: 42px;
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.15rem;
            color: var(--text-muted);
            cursor: pointer;
            transition: var(--transition);
        }}

        .sidebar-icon:hover {{
            background: var(--purple-50);
            color: var(--purple-600);
        }}

        .sidebar-icon.active {{
            background: var(--purple-100);
            color: var(--purple-600);
        }}

        .sidebar-spacer {{ flex: 1; }}

        /* ===== MAIN ===== */
        .main {{
            flex: 1;
            margin-left: 72px;
            padding: 2rem 2.5rem;
            max-width: 1200px;
        }}

        /* ===== TOP BAR ===== */
        .topbar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 2rem;
            animation: fadeIn 0.5s ease;
        }}

        .topbar-left {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        .topbar-left h1 {{
            font-size: 1.65rem;
            font-weight: 800;
            color: var(--text-primary);
            letter-spacing: -0.3px;
        }}


        /* Status indicator */
        .status-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.3rem 0.75rem;
            border-radius: 20px;
            font-size: 0.72rem;
            font-weight: 600;
            letter-spacing: 0.3px;
            text-transform: uppercase;
            transition: var(--transition);
        }}

        .status-badge.online {{
            background: rgba(34, 197, 94, 0.1);
            color: #16a34a;
            border: 1px solid rgba(34, 197, 94, 0.25);
        }}

        .status-badge.offline {{
            background: rgba(239, 68, 68, 0.1);
            color: #dc2626;
            border: 1px solid rgba(239, 68, 68, 0.25);
        }}

        .status-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            flex-shrink: 0;
        }}

        .status-badge.online .status-dot {{
            background: #22c55e;
            box-shadow: 0 0 6px rgba(34, 197, 94, 0.6);
            animation: pulse-dot 2s ease-in-out infinite;
        }}

        .status-badge.offline .status-dot {{
            background: #ef4444;
            box-shadow: 0 0 6px rgba(239, 68, 68, 0.4);
        }}

        @keyframes pulse-dot {{
            0%, 100% {{ opacity: 1; box-shadow: 0 0 6px rgba(34, 197, 94, 0.6); }}
            50% {{ opacity: 0.6; box-shadow: 0 0 12px rgba(34, 197, 94, 0.9); }}
        }}

        .topbar-right {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .search-box {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            background: var(--bg-input);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            padding: 0;
            min-width: 260px;
            transition: var(--transition);
            overflow: hidden;
        }}

        .search-box:focus-within {{
            border-color: var(--purple-400);
            box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
        }}

        .search-box .search-icon {{
            padding-left: 0.75rem;
            color: var(--text-muted);
            font-size: 0.85rem;
            flex-shrink: 0;
        }}

        .search-box input {{
            flex: 1;
            border: none;
            background: transparent;
            color: var(--text-primary);
            font-size: 0.85rem;
            font-family: inherit;
            padding: 0.55rem 0.75rem 0.55rem 0.3rem;
            outline: none;
        }}

        .search-box input::placeholder {{
            color: var(--text-muted);
        }}

        .search-clear {{
            background: none;
            border: none;
            color: var(--text-light);
            cursor: pointer;
            padding: 0.4rem 0.65rem;
            font-size: 0.85rem;
            transition: var(--transition);
            display: none;
        }}

        .search-clear.visible {{
            display: block;
        }}

        .search-clear:hover {{
            color: var(--text-primary);
        }}

        .btn-primary {{
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            background: linear-gradient(135deg, var(--purple-600), var(--purple-500));
            color: white;
            border: none;
            border-radius: var(--radius-sm);
            padding: 0.6rem 1.2rem;
            font-size: 0.85rem;
            font-weight: 600;
            font-family: inherit;
            cursor: pointer;
            transition: var(--transition);
            box-shadow: 0 2px 8px rgba(108, 60, 233, 0.25);
        }}

        .btn-primary:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 16px rgba(108, 60, 233, 0.35);
        }}

        .btn-outline {{
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            background: var(--bg-card);
            color: var(--text-secondary);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            padding: 0.55rem 1rem;
            font-size: 0.85rem;
            font-weight: 500;
            font-family: inherit;
            cursor: pointer;
            transition: var(--transition);
        }}

        .btn-outline:hover {{
            border-color: var(--border-hover);
            background: var(--purple-50);
            color: var(--purple-600);
        }}

        /* ===== COMMUNITY CARDS ===== */
        .tabs-row {{
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 0.75rem;
            margin-bottom: 1.25rem;
            animation: fadeIn 0.5s ease 0.1s both;
        }}

        .tab-card {{
            position: relative;
            display: flex;
            align-items: center;
            gap: 0.65rem;
            background: var(--bg-card);
            border: 1.5px solid var(--border);
            border-radius: var(--radius-md);
            padding: 0.7rem 0.85rem;
            cursor: pointer;
            transition: var(--transition);
            overflow: hidden;
        }}

        .tab-card:hover {{
            border-color: var(--purple-300);
            transform: translateY(-2px);
            box-shadow: var(--shadow-hover);
        }}

        .tab-card.active {{
            background: linear-gradient(135deg, var(--purple-600), var(--purple-500));
            border-color: var(--purple-600);
            box-shadow: 0 4px 16px rgba(108, 60, 233, 0.3);
        }}

        .tab-card.active .tab-card-name,
        .tab-card.active .tab-card-count {{
            color: white;
        }}

        .tab-card.active .tab-card-count {{
            background: rgba(255,255,255,0.2);
            color: white;
        }}

        .tab-card-avatar {{
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: var(--bg-input);
            flex-shrink: 0;
            object-fit: cover;
            border: 1.5px solid var(--border);
        }}

        .tab-card.active .tab-card-avatar {{
            border-color: rgba(255,255,255,0.4);
        }}

        .tab-card-info {{
            flex: 1;
            min-width: 0;
        }}

        .tab-card-name {{
            font-size: 0.82rem;
            font-weight: 600;
            color: var(--text-primary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            line-height: 1.2;
        }}

        .tab-card-count {{
            display: inline-block;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.65rem;
            font-weight: 600;
            background: var(--bg-badge);
            color: var(--purple-500);
            border-radius: 4px;
            padding: 0.1rem 0.4rem;
            margin-top: 0.15rem;
        }}

        /* ===== MODE TOGGLE & TIME FILTERS ===== */
        .controls-row {{
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1.75rem;
            flex-wrap: wrap;
            animation: fadeIn 0.5s ease 0.12s both;
        }}

        .mode-toggle {{
            display: flex;
            align-items: center;
            gap: 0.25rem;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            padding: 0.25rem;
        }}

        .mode-btn, .filter-btn {{
            background: transparent;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 0.35rem 0.75rem;
            font-size: 0.75rem;
            color: var(--text-secondary);
            cursor: pointer;
            transition: var(--transition);
            display: flex;
            align-items: center;
            gap: 0.35rem;
            font-weight: 500;
        }}

        .mode-btn.active, .filter-btn.active {{
            background: var(--purple-100);
            border-color: var(--purple-300);
            color: var(--purple-700);
            font-weight: 600;
        }}

        .filter-group {{
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }}
        .mode-btn {{
            background: transparent;
            border: none;
            border-radius: var(--radius-sm);
            padding: 0.5rem 1.1rem;
            font-size: 0.82rem;
            font-weight: 500;
            font-family: inherit;
            color: var(--text-muted);
            cursor: pointer;
            transition: var(--transition);
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
        }}

        .mode-btn:hover {{
            color: var(--text-secondary);
            background: var(--bg-input);
        }}

        .mode-btn.active {{
            background: linear-gradient(135deg, var(--purple-600), var(--purple-500));
            color: white;
            font-weight: 600;
            box-shadow: 0 2px 8px rgba(108, 60, 233, 0.25);
        }}

        .time-filters {{
            display: flex;
            align-items: center;
            gap: 0.25rem;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            padding: 0.25rem;
            opacity: 0;
            transform: translateX(-8px);
            pointer-events: none;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        .time-filters.visible {{
            opacity: 1;
            transform: translateX(0);
            pointer-events: auto;
        }}

        .time-btn {{
            background: transparent;
            border: none;
            border-radius: var(--radius-sm);
            padding: 0.45rem 0.9rem;
            font-size: 0.78rem;
            font-weight: 500;
            font-family: inherit;
            color: var(--text-muted);
            cursor: pointer;
            transition: var(--transition);
        }}

        .time-btn:hover {{
            color: var(--text-secondary);
            background: var(--bg-input);
        }}

        .time-btn.active {{
            background: var(--gold-100);
            color: #b45309;
            font-weight: 600;
            border: 1px solid rgba(245, 166, 35, 0.3);
        }}

        .mode-label {{
            font-size: 0.75rem;
            color: var(--text-light);
            font-weight: 500;
            letter-spacing: 0.3px;
        }}

        /* ===== STATS ROW ===== */
        .stats-row {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
            margin-bottom: 1.75rem;
            animation: fadeIn 0.5s ease 0.15s both;
        }}

        .stat-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 1.25rem 1.5rem;
            transition: var(--transition);
            box-shadow: var(--shadow-sm);
        }}

        .stat-card:hover {{
            box-shadow: var(--shadow-hover);
            transform: translateY(-2px);
            border-color: var(--border-hover);
        }}

        .stat-card .label {{
            font-size: 0.78rem;
            color: var(--text-muted);
            font-weight: 500;
            margin-bottom: 0.5rem;
        }}

        .stat-card .value {{
            font-size: 1.6rem;
            font-weight: 800;
            color: var(--text-primary);
            font-family: 'JetBrains Mono', monospace;
            letter-spacing: -0.5px;
        }}

        .stat-card .sub {{
            font-size: 0.72rem;
            color: var(--text-light);
            margin-top: 0.25rem;
        }}

        .stat-card.purple .value {{ color: var(--purple-600); }}
        .stat-card.gold .value {{ color: var(--gold-500); }}
        .stat-card.green .value {{ color: var(--green-500); }}
        .stat-card.blue .value {{ color: var(--blue-500); }}

        /* ===== POSTS TABLE / CARDS ===== */
        .section-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1rem;
            animation: fadeIn 0.5s ease 0.2s both;
        }}

        .section-title {{
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--text-primary);
        }}

        .view-all {{
            font-size: 0.82rem;
            color: var(--purple-500);
            font-weight: 500;
            cursor: pointer;
            text-decoration: none;
            transition: var(--transition);
        }}

        .view-all:hover {{ color: var(--purple-600); }}

        .posts-list {{
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
            animation: fadeIn 0.5s ease 0.25s both;
        }}

        .post-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 1.5rem;
            transition: var(--transition);
            box-shadow: var(--shadow-card);
            animation: slideUp 0.4s ease both;
            position: relative;
            overflow: hidden;
        }}

        .post-card::after {{
            content: '';
            position: absolute;
            left: 0; top: 0;
            width: 4px;
            height: 100%;
            border-radius: 0 4px 4px 0;
            background: transparent;
            transition: var(--transition);
        }}

        .post-card:hover {{
            border-color: var(--border-hover);
            box-shadow: var(--shadow-hover);
            transform: translateY(-2px);
        }}

        .post-card:hover::after {{
            background: linear-gradient(180deg, var(--purple-500), var(--purple-300));
        }}

        .post-card:nth-child(1) {{ animation-delay: 0.05s; }}
        .post-card:nth-child(2) {{ animation-delay: 0.1s; }}
        .post-card:nth-child(3) {{ animation-delay: 0.15s; }}
        .post-card:nth-child(4) {{ animation-delay: 0.2s; }}
        .post-card:nth-child(5) {{ animation-delay: 0.25s; }}

        .post-top {{
            display: flex;
            align-items: flex-start;
            gap: 1rem;
        }}

        /* Rank */
        .rank-badge {{
            flex-shrink: 0;
            width: 40px; height: 40px;
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 1rem;
            font-family: 'JetBrains Mono', monospace;
        }}

        .rank-badge.r1 {{
            background: linear-gradient(135deg, #fde68a, #fbbf24);
            color: #92400e;
            box-shadow: 0 3px 12px rgba(251, 191, 36, 0.3);
        }}

        .rank-badge.r2 {{
            background: linear-gradient(135deg, #e2e8f0, #94a3b8);
            color: #334155;
        }}

        .rank-badge.r3 {{
            background: linear-gradient(135deg, #fed7aa, #f97316);
            color: #7c2d12;
        }}

        .rank-badge.r4, .rank-badge.r5 {{
            background: var(--bg-input);
            color: var(--text-muted);
            border: 1px solid var(--border);
        }}

        .post-content {{
            flex: 1;
            min-width: 0;
        }}

        .post-title {{
            font-size: 1rem;
            font-weight: 700;
            line-height: 1.45;
            margin-bottom: 0.4rem;
            color: var(--text-primary);
        }}

        .post-title a {{
            color: inherit;
            text-decoration: none;
            transition: var(--transition);
        }}

        .post-title a:hover {{ color: var(--purple-600); }}

        .post-excerpt {{
            font-size: 0.82rem;
            color: var(--text-muted);
            line-height: 1.6;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            margin-bottom: 0.9rem;
        }}

        .post-flair {{
            display: inline-block;
            background: var(--purple-100);
            color: var(--purple-600);
            border-radius: var(--radius-xs);
            padding: 0.2rem 0.6rem;
            font-size: 0.7rem;
            font-weight: 600;
            margin-bottom: 0.9rem;
        }}

        /* Stats Pills */
        .post-stats {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            flex-wrap: wrap;
        }}

        .pill {{
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            border-radius: var(--radius-xs);
            padding: 0.35rem 0.7rem;
            font-size: 0.78rem;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
        }}

        .pill-icon {{ font-size: 0.85rem; }}

        .pill.engagement {{
            background: var(--gold-100);
            color: #b45309;
        }}

        .pill.score {{
            background: var(--green-100);
            color: #166534;
        }}

        .pill.comments {{
            background: var(--blue-100);
            color: #1e40af;
        }}

        .pill.ratio-high {{
            background: var(--green-100);
            color: #166534;
        }}

        .pill.ratio-mid {{
            background: var(--amber-100);
            color: #a16207;
        }}

        .pill.ratio-low {{
            background: rgba(239, 68, 68, 0.08);
            color: #dc2626;
        }}

        /* Engagement Progress */
        .engagement-bar {{
            margin-top: 0.85rem;
            height: 5px;
            background: var(--bg-input);
            border-radius: 3px;
            overflow: hidden;
        }}

        .engagement-fill {{
            height: 100%;
            border-radius: 3px;
            background: linear-gradient(90deg, var(--purple-500), var(--gold-400));
            transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        /* Post Footer */
        .post-footer {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-top: 0.9rem;
            padding-top: 0.75rem;
            border-top: 1px solid var(--border);
        }}

        .post-author {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.8rem;
            color: var(--text-muted);
        }}

        .author-avatar {{
            width: 24px; height: 24px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--purple-300), var(--purple-500));
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 0.6rem;
            font-weight: 700;
        }}

        .author-name {{ color: var(--purple-600); font-weight: 600; }}

        .post-date {{
            font-size: 0.75rem;
            color: var(--text-light);
            font-family: 'JetBrains Mono', monospace;
        }}

        .post-link {{
            display: inline-flex;
            align-items: center;
            gap: 0.3rem;
            font-size: 0.8rem;
            color: var(--purple-500);
            text-decoration: none;
            font-weight: 600;
            transition: var(--transition);
            padding: 0.3rem 0.7rem;
            border-radius: var(--radius-xs);
        }}

        .post-link:hover {{
            background: var(--purple-50);
            color: var(--purple-600);
        }}

        /* ===== PAGE VIEWS ===== */
        .page {{ display: none; }}
        .page.active {{ display: block; animation: fadeIn 0.4s ease; }}

        /* Trends page */
        .chart-card {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 1.5rem; box-shadow: var(--shadow-card); margin-bottom: 1rem; }}
        .chart-card h3 {{ font-size: 0.95rem; font-weight: 700; margin-bottom: 1rem; color: var(--text-primary); }}
        .bar-chart {{ display: flex; flex-direction: column; gap: 0.6rem; }}
        .bar-row {{ display: flex; align-items: center; gap: 0.75rem; }}
        .bar-label {{ width: 180px; font-size: 0.78rem; color: var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex-shrink: 0; }}
        .bar-track {{ flex: 1; height: 24px; background: var(--bg-input); border-radius: 6px; overflow: hidden; position: relative; }}
        .bar-fill {{ height: 100%; border-radius: 6px; transition: width 0.8s ease; display: flex; align-items: center; justify-content: flex-end; padding-right: 0.5rem; font-size: 0.7rem; font-weight: 700; color: white; font-family: 'JetBrains Mono', monospace; }}
        .bar-fill.purple {{ background: linear-gradient(90deg, var(--purple-500), var(--purple-400)); }}
        .bar-fill.gold {{ background: linear-gradient(90deg, var(--gold-500), var(--gold-400)); }}
        .bar-fill.blue {{ background: linear-gradient(90deg, var(--blue-500), #60a5fa); }}
        .bar-fill.green {{ background: linear-gradient(90deg, var(--green-500), #4ade80); }}
        .charts-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}

        /* Settings page */
        .settings-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
        .setting-item {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 1.25rem; box-shadow: var(--shadow-card); }}
        .setting-item .s-label {{ font-size: 0.75rem; color: var(--text-muted); font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.4rem; }}
        .setting-item .s-value {{ font-size: 1.1rem; font-weight: 700; color: var(--text-primary); font-family: 'JetBrains Mono', monospace; }}
        .setting-item .s-desc {{ font-size: 0.75rem; color: var(--text-light); margin-top: 0.3rem; }}
        .formula-card {{ background: var(--purple-50); border: 1px solid var(--purple-100); border-radius: var(--radius-lg); padding: 1.5rem; margin-bottom: 1.5rem; }}
        .formula-card h3 {{ color: var(--purple-600); font-size: 0.95rem; margin-bottom: 0.75rem; }}
        .formula-code {{ font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; color: var(--purple-600); background: white; padding: 0.75rem 1rem; border-radius: var(--radius-sm); border: 1px solid var(--purple-100); }}

        /* Logs page */
        .log-card {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 1.25rem; box-shadow: var(--shadow-card); margin-bottom: 0.75rem; cursor: pointer; transition: var(--transition); }}
        .log-card:hover {{ border-color: var(--border-hover); box-shadow: var(--shadow-hover); }}
        .log-top {{ display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem; }}
        .log-badge {{ display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.25rem 0.6rem; border-radius: 12px; font-size: 0.72rem; font-weight: 600; }}
        .log-badge.success {{ background: var(--green-100); color: var(--green-500); }}
        .log-badge.error {{ background: rgba(239,68,68,0.08); color: var(--red-500); }}
        .log-script {{ font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; font-weight: 600; color: var(--text-primary); }}
        .log-meta {{ font-size: 0.75rem; color: var(--text-muted); display: flex; gap: 1rem; }}
        .log-details {{ margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid var(--border); display: none; }}
        .log-details.open {{ display: block; }}
        .log-metrics {{ display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.5rem; }}
        .log-mpill {{ background: var(--bg-input); border-radius: var(--radius-xs); padding: 0.3rem 0.6rem; font-size: 0.72rem; }}
        .log-mpill .k {{ color: var(--text-muted); }}
        .log-mpill .v {{ color: var(--purple-600); font-weight: 600; font-family: 'JetBrains Mono', monospace; }}
        .log-entries-list {{ background: var(--bg-input); border-radius: var(--radius-sm); padding: 0.5rem 0.75rem; max-height: 200px; overflow-y: auto; font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; line-height: 1.8; }}
        .le-time {{ color: var(--text-light); }}
        .le-lvl {{ font-weight: 600; }}
        .le-lvl.INFO {{ color: var(--blue-500); }}
        .le-lvl.WARN {{ color: var(--amber-500); }}
        .le-lvl.ERROR {{ color: var(--red-500); }}

        /* Posts table page */
        .table-card {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); box-shadow: var(--shadow-card); overflow: hidden; }}
        .posts-table {{ width: 100%; border-collapse: collapse; font-size: 0.82rem; }}
        .posts-table th {{ background: var(--bg-input); padding: 0.75rem 1rem; text-align: left; font-weight: 600; color: var(--text-secondary); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid var(--border); }}
        .posts-table td {{ padding: 0.85rem 1rem; border-bottom: 1px solid var(--border); color: var(--text-secondary); vertical-align: middle; }}
        .posts-table tr:last-child td {{ border-bottom: none; }}
        .posts-table tr:hover td {{ background: var(--purple-50); }}
        .posts-table .td-title {{ color: var(--text-primary); font-weight: 600; max-width: 350px; }}
        .posts-table .td-title a {{ color: inherit; text-decoration: none; }} .posts-table .td-title a:hover {{ color: var(--purple-600); }}
        .posts-table .mono {{ font-family: 'JetBrains Mono', monospace; font-weight: 600; }}

        /* Convert to MD button */
        .btn-convert {{ display: inline-flex; align-items: center; gap: 0.3rem; background: var(--bg-input); border: 1px solid var(--border); border-radius: var(--radius-xs); padding: 0.3rem 0.65rem; font-size: 0.72rem; font-weight: 600; font-family: inherit; color: var(--text-muted); cursor: pointer; transition: var(--transition); }}
        .btn-convert:hover {{ background: var(--purple-50); border-color: var(--purple-300); color: var(--purple-600); }}
        .btn-convert.done {{ background: var(--green-100); border-color: transparent; color: var(--green-500); cursor: default; }}

        /* Articles page */
        .article-card {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); box-shadow: var(--shadow-card); margin-bottom: 1rem; overflow: hidden; animation: slideUp 0.3s ease both; }}
        .article-header {{ padding: 1.25rem 1.5rem; display: flex; align-items: center; justify-content: space-between; cursor: pointer; transition: var(--transition); }}
        .article-header:hover {{ background: var(--purple-50); }}
        .article-info {{ display: flex; align-items: center; gap: 0.75rem; flex: 1; min-width: 0; }}
        .article-sub {{ display: inline-flex; align-items: center; padding: 0.2rem 0.5rem; border-radius: var(--radius-xs); background: var(--purple-100); color: var(--purple-600); font-size: 0.7rem; font-weight: 700; flex-shrink: 0; }}
        .article-name {{ font-size: 0.9rem; font-weight: 600; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .article-actions {{ display: flex; gap: 0.5rem; flex-shrink: 0; }}
        .btn-save {{ display: inline-flex; align-items: center; gap: 0.3rem; background: linear-gradient(135deg, var(--purple-600), var(--purple-500)); color: white; border: none; border-radius: var(--radius-xs); padding: 0.4rem 0.8rem; font-size: 0.75rem; font-weight: 600; font-family: inherit; cursor: pointer; transition: var(--transition); box-shadow: 0 2px 6px rgba(108,60,233,0.2); }}
        .btn-save:hover {{ transform: translateY(-1px); box-shadow: 0 4px 12px rgba(108,60,233,0.3); }}
        .btn-preview {{ display: inline-flex; align-items: center; gap: 0.3rem; background: var(--bg-card); color: var(--text-secondary); border: 1px solid var(--border); border-radius: var(--radius-xs); padding: 0.4rem 0.8rem; font-size: 0.75rem; font-weight: 500; font-family: inherit; cursor: pointer; transition: var(--transition); }}
        .btn-preview:hover {{ border-color: var(--border-hover); background: var(--purple-50); color: var(--purple-600); }}
        .article-preview {{ display: none; padding: 1.25rem 1.5rem; border-top: 1px solid var(--border); background: var(--bg-input); }}
        .article-preview.open {{ display: block; }}
        .article-preview pre {{ background: white; border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 1rem; font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; line-height: 1.7; white-space: pre-wrap; word-wrap: break-word; max-height: 400px; overflow-y: auto; color: var(--text-secondary); }}
        .articles-stats {{ display: flex; gap: 1rem; margin-bottom: 1.5rem; }}
        .articles-stats .stat-card {{ flex: 1; }}
        .convert-all-bar {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 1rem 1.5rem; margin-bottom: 1.5rem; display: flex; align-items: center; justify-content: space-between; box-shadow: var(--shadow-card); }}
        .convert-all-bar .info {{ font-size: 0.85rem; color: var(--text-secondary); }}
        .convert-all-bar .info strong {{ color: var(--text-primary); }}
        .empty-articles {{ text-align: center; padding: 4rem 2rem; color: var(--text-muted); }}
        .empty-articles .empty-icon {{ font-size: 3rem; margin-bottom: 1rem; }}
        .empty-articles p {{ font-size: 0.9rem; margin-bottom: 1.5rem; }}

        /* ===== IMPORT MODAL ===== */
        .modal-overlay {{
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(26, 21, 48, 0.55);
            backdrop-filter: blur(6px);
            z-index: 1000;
            align-items: center;
            justify-content: center;
            animation: fadeIn 0.2s ease;
        }}

        .modal-overlay.open {{
            display: flex;
        }}

        .modal-box {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-xl);
            width: 580px;
            max-width: 95vw;
            max-height: 90vh;
            overflow-y: auto;
            box-shadow: 0 24px 64px rgba(26, 21, 48, 0.25);
            animation: slideUp 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        .modal-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 1.25rem 1.5rem;
            border-bottom: 1px solid var(--border);
        }}

        .modal-header h2 {{
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .modal-close {{
            width: 32px; height: 32px;
            border-radius: 50%;
            border: none;
            background: var(--bg-input);
            color: var(--text-muted);
            font-size: 1.1rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: var(--transition);
        }}

        .modal-close:hover {{
            background: rgba(239, 68, 68, 0.1);
            color: var(--red-500);
        }}

        .modal-body {{
            padding: 1.5rem;
        }}

        .input-row {{
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }}

        .input-field {{
            flex: 1;
            padding: 0.7rem 1rem;
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            color: var(--text-primary);
            background: var(--bg-input);
            outline: none;
            transition: var(--transition);
        }}

        .input-field:focus {{
            border-color: var(--purple-400);
            box-shadow: 0 0 0 3px rgba(108, 60, 233, 0.1);
        }}

        .input-field::placeholder {{
            color: var(--text-light);
        }}

        .btn-fetch {{
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            background: linear-gradient(135deg, var(--purple-600), var(--purple-500));
            color: white;
            border: none;
            border-radius: var(--radius-sm);
            padding: 0.7rem 1.3rem;
            font-size: 0.85rem;
            font-weight: 600;
            font-family: inherit;
            cursor: pointer;
            transition: var(--transition);
            box-shadow: 0 2px 8px rgba(108, 60, 233, 0.25);
            white-space: nowrap;
        }}

        .btn-fetch:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 16px rgba(108, 60, 233, 0.35);
        }}

        .btn-fetch:disabled {{
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }}

        .fetch-status {{
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-bottom: 1rem;
            min-height: 1.2rem;
        }}

        .fetch-status.error {{
            color: var(--red-500);
        }}

        /* Post Preview inside modal */
        .preview-card {{
            background: var(--bg-input);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 1.25rem;
            animation: slideUp 0.3s ease;
        }}

        .preview-card .pc-title {{
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--text-primary);
            line-height: 1.45;
            margin-bottom: 0.6rem;
        }}

        .preview-card .pc-title a {{
            color: inherit;
            text-decoration: none;
        }}

        .preview-card .pc-title a:hover {{ color: var(--purple-600); }}

        .preview-card .pc-excerpt {{
            font-size: 0.8rem;
            color: var(--text-muted);
            line-height: 1.6;
            margin-bottom: 0.75rem;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}

        .preview-card .pc-stats {{
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            margin-bottom: 1rem;
        }}

        .preview-card .pc-meta {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 0.78rem;
            color: var(--text-muted);
            padding-top: 0.75rem;
            border-top: 1px solid var(--border);
        }}

        /* Community detection box */
        .community-box {{
            margin-top: 1rem;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 1.25rem;
            animation: slideUp 0.3s ease 0.1s both;
        }}

        .community-box.tracked {{
            border-color: var(--green-500);
            background: var(--green-100);
        }}

        .community-box.new {{
            border-color: var(--gold-500);
            background: var(--gold-100);
        }}

        .community-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.5rem;
        }}

        .community-name {{
            font-size: 1rem;
            font-weight: 700;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .community-tag {{
            display: inline-flex;
            align-items: center;
            gap: 0.25rem;
            padding: 0.2rem 0.6rem;
            border-radius: 12px;
            font-size: 0.7rem;
            font-weight: 600;
        }}

        .community-tag.active {{
            background: var(--green-100);
            color: var(--green-500);
        }}

        .community-tag.new-tag {{
            background: var(--gold-100);
            color: #b45309;
        }}

        .community-detail {{
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-bottom: 0.75rem;
        }}

        .btn-add-community {{
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            background: linear-gradient(135deg, var(--green-500), #16a34a);
            color: white;
            border: none;
            border-radius: var(--radius-sm);
            padding: 0.6rem 1.2rem;
            font-size: 0.85rem;
            font-weight: 600;
            font-family: inherit;
            cursor: pointer;
            transition: var(--transition);
            box-shadow: 0 2px 8px rgba(34, 197, 94, 0.3);
        }}

        .btn-add-community:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 16px rgba(34, 197, 94, 0.4);
        }}

        .btn-add-community:disabled {{
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }}

        .btn-add-community.done {{
            background: var(--green-100);
            color: var(--green-500);
            border: 1px solid var(--green-500);
            box-shadow: none;
            cursor: default;
        }}

        /* Toast notifications */
        .toast-container {{
            position: fixed;
            top: 1.5rem;
            right: 1.5rem;
            z-index: 2000;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }}

        .toast {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            padding: 0.85rem 1.25rem;
            box-shadow: 0 8px 32px rgba(26, 21, 48, 0.15);
            font-size: 0.85rem;
            font-weight: 500;
            color: var(--text-primary);
            animation: slideIn 0.35s cubic-bezier(0.4, 0, 0.2, 1);
            max-width: 420px;
        }}

        .toast.success {{ border-left: 4px solid var(--green-500); }}
        .toast.error {{ border-left: 4px solid var(--red-500); }}
        .toast.info {{ border-left: 4px solid var(--blue-500); }}

        .toast-icon {{ font-size: 1.2rem; flex-shrink: 0; }}

        .toast.fade-out {{
            animation: slideOut 0.3s ease forwards;
        }}

        @keyframes slideIn {{
            from {{ opacity: 0; transform: translateX(100px); }}
            to {{ opacity: 1; transform: translateX(0); }}
        }}

        @keyframes slideOut {{
            from {{ opacity: 1; transform: translateX(0); }}
            to {{ opacity: 0; transform: translateX(100px); }}
        }}

        /* Add Community button in topbar */
        .btn-import {{
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            background: linear-gradient(135deg, var(--green-500), #16a34a);
            color: white;
            border: none;
            border-radius: var(--radius-sm);
            padding: 0.6rem 1.2rem;
            font-size: 0.85rem;
            font-weight: 600;
            font-family: inherit;
            cursor: pointer;
            transition: var(--transition);
            box-shadow: 0 2px 8px rgba(34, 197, 94, 0.3);
        }}

        .btn-import:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 16px rgba(34, 197, 94, 0.4);
        }}

        /* Community list inside modal */
        .community-list {{
            list-style: none;
            padding: 0;
            margin: 1rem 0 0 0;
            display: flex;
            flex-direction: column;
            gap: 0.4rem;
            max-height: 320px;
            overflow-y: auto;
        }}

        .community-list-item {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.6rem 0.85rem;
            background: var(--bg-input);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            font-size: 0.85rem;
            font-weight: 500;
            color: var(--text-primary);
            transition: var(--transition);
        }}

        .community-list-item:hover {{
            border-color: var(--purple-400);
        }}

        .community-list-item .cl-name {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .community-list-item .cl-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--green-500);
            flex-shrink: 0;
        }}

        .btn-remove-community {{
            background: none;
            border: 1px solid transparent;
            border-radius: var(--radius-sm);
            color: var(--text-light);
            font-size: 0.78rem;
            cursor: pointer;
            padding: 0.25rem 0.6rem;
            transition: var(--transition);
            font-family: inherit;
        }}

        .btn-remove-community:hover {{
            background: rgba(239, 68, 68, 0.1);
            color: var(--red-500);
            border-color: var(--red-500);
        }}

        .btn-remove-community:disabled {{
            opacity: 0.4;
            cursor: not-allowed;
        }}

        .modal-section-label {{
            font-size: 0.78rem;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-top: 1.25rem;
            margin-bottom: 0.5rem;
        }}

        .community-count-badge {{
            font-size: 0.7rem;
            background: var(--purple-100);
            color: var(--purple-600);
            padding: 0.15rem 0.5rem;
            border-radius: 12px;
            font-weight: 600;
        }}

        /* ===== ANIMATIONS ===== */
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}

        @keyframes slideUp {{
            from {{ opacity: 0; transform: translateY(16px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        /* ===== RESPONSIVE ===== */

        /* --- Tablet (até 1024px) --- */
        @media (max-width: 1024px) {{
            .main {{ padding: 1.5rem; max-width: 100%; }}
            .stats-row {{ grid-template-columns: repeat(2, 1fr); }}
            .charts-grid, .settings-grid {{ grid-template-columns: 1fr; }}
            .topbar-right {{ gap: 0.5rem; }}
            .topbar-right .btn-outline,
            .topbar-right .btn-primary {{ font-size: 0.78rem; padding: 0.5rem 0.8rem; }}
        }}

        /* --- Mobile (até 768px) --- */
        @media (max-width: 768px) {{
            /* Sidebar vira barra inferior */
            .sidebar {{
                position: fixed;
                bottom: 0;
                left: 0;
                top: auto;
                width: 100%;
                height: 60px;
                flex-direction: row;
                justify-content: space-around;
                padding: 0.4rem 0;
                gap: 0;
                border-right: none;
                border-top: 1px solid var(--border);
                z-index: 100;
                background: var(--bg-sidebar);
            }}
            .sidebar-logo {{ display: none; }}
            .sidebar-spacer {{ display: none; }}
            .sidebar-icon {{
                width: 44px;
                height: 44px;
                font-size: 1.2rem;
            }}

            .main {{
                margin-left: 0;
                padding: 1rem;
                padding-bottom: 80px; /* espaço para navbar inferior */
            }}

            /* Topbar empilha verticalmente */
            .topbar {{
                flex-direction: column;
                align-items: stretch;
                gap: 0.75rem;
                margin-bottom: 1.25rem;
            }}
            .topbar-left {{
                justify-content: space-between;
                width: 100%;
            }}
            .topbar-left h1 {{ font-size: 1.3rem; }}
            .topbar-right {{
                width: 100%;
                flex-wrap: wrap;
                gap: 0.5rem;
            }}
            .search-box {{
                flex: 1 1 100%;
                min-width: unset;
                order: -1;
            }}
            .topbar-right .btn-import,
            .topbar-right .btn-outline,
            .topbar-right .btn-primary {{
                flex: 1;
                justify-content: center;
                font-size: 0.78rem;
                padding: 0.55rem 0.6rem;
            }}

            /* Tabs scrollam horizontalmente */
            /* Community Cards */
            .tabs-row {{
                grid-template-columns: repeat(3, 1fr);
                gap: 0.5rem;
            }}
            .tab-card {{ padding: 0.6rem 0.7rem; }}
            .tab-card-avatar {{ width: 28px; height: 28px; }}
            .tab-card-name {{ font-size: 0.75rem; }}

            /* Controls */
            .controls-row {{
                flex-direction: column;
                align-items: stretch;
                gap: 0.5rem;
            }}
            .mode-toggle {{ width: 100%; }}
            .mode-btn {{ flex: 1; text-align: center; font-size: 0.78rem; }}

            /* Cards de stats */
            .stats-row {{ grid-template-columns: repeat(2, 1fr); gap: 0.6rem; }}
            .stat-card {{ padding: 0.9rem; }}
            .stat-card .value {{ font-size: 1.3rem; }}

            /* Post cards */
            .post-top {{ flex-direction: column; gap: 0.5rem; }}
            .post-footer {{ flex-direction: column; align-items: flex-start; gap: 0.5rem; }}
            .post-pills {{ flex-wrap: wrap; }}

            /* Modal */
            .modal-box {{
                width: 100%;
                max-width: 100vw;
                max-height: 95vh;
                border-radius: var(--radius-lg) var(--radius-lg) 0 0;
                margin-top: auto;
            }}
            .modal-overlay {{
                align-items: flex-end;
            }}
            .modal-header {{ padding: 1rem; }}
            .modal-body {{ padding: 1rem; }}
            .input-row {{ flex-direction: column; }}
            .btn-fetch {{ width: 100%; justify-content: center; }}

            /* Charts */
            .charts-grid {{ grid-template-columns: 1fr; }}
            .chart-card {{ padding: 1rem; }}
        }}

        /* --- Mobile pequeno (até 480px) --- */
        @media (max-width: 480px) {{
            .main {{ padding: 0.75rem; padding-bottom: 75px; }}
            .topbar-left h1 {{ font-size: 1.1rem; }}
            .stats-row {{ grid-template-columns: 1fr; }}
            .stat-card .value {{ font-size: 1.15rem; }}
            .post-pills {{ gap: 0.25rem; }}
            .pill {{ font-size: 0.68rem; padding: 0.2rem 0.45rem; }}
            .post-title {{ font-size: 0.88rem; }}
            .rank-badge {{ width: 28px; height: 28px; font-size: 0.75rem; }}
            .tabs-row {{ grid-template-columns: repeat(2, 1fr); gap: 0.4rem; }}
            .tab-card-name {{ font-size: 0.72rem; }}
            .tab-card-avatar {{ width: 24px; height: 24px; }}
            .status-badge {{ font-size: 0.65rem; padding: 0.2rem 0.5rem; }}

            /* Botões de ação viram full-width */
            .topbar-right .btn-import,
            .topbar-right .btn-outline,
            .topbar-right .btn-primary {{
                font-size: 0.72rem;
            }}

            /* Toast no mobile */
            .toast-container {{
                left: 0.5rem;
                right: 0.5rem;
                top: auto;
                bottom: 70px;
            }}
            .toast {{ font-size: 0.8rem; }}

            /* Settings grid */
            .settings-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="layout">
        <!-- Sidebar -->
        <aside class="sidebar">
            <div class="sidebar-logo">📊</div>
            <div class="sidebar-icon active" data-page="dashboard" onclick="navigateTo('dashboard')" title="Dashboard">📈</div>
            <div class="sidebar-icon" data-page="posts" onclick="navigateTo('posts')" title="Posts">📝</div>
            <div class="sidebar-icon" data-page="trends" onclick="navigateTo('trends')" title="Trends">📡</div>
            <div class="sidebar-icon" data-page="articles" onclick="navigateTo('articles')" title="Artigos Markdown">📄</div>
            <div class="sidebar-icon" data-page="settings" onclick="navigateTo('settings')" title="Configurações">⚙️</div>
            <div class="sidebar-spacer"></div>
            <div class="sidebar-icon" data-page="logs" onclick="navigateTo('logs')" title="Logs">📋</div>
        </aside>

        <!-- Main Content -->
        <main class="main">
            <!-- Top Bar -->
            <div class="topbar">
                <div class="topbar-left">
                    <h1 id="pageTitle">Dashboard</h1>
                    <span class="status-badge" id="statusBadge" title="Verificando...">
                        <span class="status-dot"></span>
                        <span id="statusText">...</span>
                    </span>
                </div>
                <div class="topbar-right">
                    <div class="search-box">
                        <span class="search-icon">🔍</span>
                        <input type="text" id="searchInput" placeholder="Buscar posts..."
                               oninput="handleSearch()" />
                        <button class="search-clear" id="searchClear" onclick="clearSearch()">✕</button>
                    </div>
                    <button class="btn-import" onclick="openCommunityModal()">➕ Adicionar Comunidade</button>
                    <button class="btn-outline" onclick="location.reload()">🔄 Atualizar</button>
                    <button class="btn-primary" id="downloadBtn">📥 Exportar dados</button>
                </div>
            </div>

            <!-- PAGE: Dashboard -->
            <div class="page active" id="page-dashboard">
                <div class="tabs-row" id="tabsRow"></div>
                <div class="controls-row">
                    <span class="mode-label">Filtro:</span>
                    <div class="filter-group" id="filterGroup">
                        <button class="filter-btn active" data-filter="best" onclick="switchFilter('best')" title="Top Relevantes (Engajamento)">🔥 Melhores</button>
                        <button class="filter-btn" data-filter="hot" onclick="switchFilter('hot')" title="Posts em Destaque">🚀 Destaque</button>
                        <button class="filter-btn" data-filter="new" onclick="switchFilter('new')" title="Mais Novos">✨ Novos</button>
                        <button class="filter-btn" data-filter="top" onclick="switchFilter('top')" title="Mais Votados">🏆 Top</button>
                        <button class="filter-btn" data-filter="rising" onclick="switchFilter('rising')" title="Em Ascensão">📈 Ascensão</button>
                    </div>
                    <div class="time-filters" id="timeFilters">
                        <span class="mode-label" style="margin-right:0.25rem">Período:</span>
                        <button class="time-btn" data-period="1" onclick="switchTimePeriod(1)">24h</button>
                        <button class="time-btn active" data-period="7" onclick="switchTimePeriod(7)">Semana</button>
                        <button class="time-btn" data-period="30" onclick="switchTimePeriod(30)">Mês</button>
                    </div>
                </div>
                <div class="stats-row" id="statsRow"></div>
                <div class="section-header">
                    <span class="section-title" id="sectionTitle">Top Posts da Semana</span>
                    <span class="view-all" id="viewAllLabel">5 posts</span>
                </div>
                <div class="posts-list" id="postsList"></div>
            </div>

            <!-- PAGE: Posts (table) -->
            <div class="page" id="page-posts"></div>

            <!-- PAGE: Trends -->
            <div class="page" id="page-trends"></div>

            <!-- PAGE: Settings -->
            <div class="page" id="page-settings"></div>

            <!-- PAGE: Articles -->
            <div class="page" id="page-articles"></div>

            <!-- PAGE: Logs -->
            <div class="page" id="page-logs"></div>
        </main>
    </div>

    <!-- Community Management Modal -->
    <div class="modal-overlay" id="importModal" onclick="if(event.target===this)closeCommunityModal()">
        <div class="modal-box">
            <div class="modal-header">
                <h2>🌐 Gerenciar Comunidades</h2>
                <button class="modal-close" onclick="closeCommunityModal()" title="Fechar">✕</button>
            </div>
            <div class="modal-body">
                <p style="font-size:0.85rem;color:var(--text-secondary);margin-bottom:1rem">
                    Adicione comunidades do Reddit (subreddits) para monitorar os Top 10 posts em alta.
                </p>
                <div class="input-row">
                    <input class="input-field" id="communityInput" type="text"
                           placeholder="Ex: python, javascript, devops..."
                           onkeydown="if(event.key==='Enter')addCommunityFromInput()" />
                    <button class="btn-fetch" id="addCommunityBtn" onclick="addCommunityFromInput()">➕ Adicionar</button>
                </div>
                <div class="fetch-status" id="communityStatus"></div>
                <div class="modal-section-label">Comunidades monitoradas <span class="community-count-badge" id="communityCountBadge">0</span></div>
                <ul class="community-list" id="communityListArea"></ul>
                <p style="font-size:0.75rem;color:var(--text-light);margin-top:1rem">
                    ⚠️ Após adicionar ou remover comunidades, execute o pipeline para atualizar os posts.
                </p>
            </div>
        </div>
    </div>

    <!-- Toast Container -->
    <div class="toast-container" id="toastContainer"></div>

    <script>
        function decode(str) {{
            return JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(str), c => c.charCodeAt(0))));
        }}
        const topPosts = decode("{posts_json}");
        const allPostsData = decode("{all_posts_json}");
        const appConfig = decode("{config_json}");
        const appLogs = decode("{logs_json}");
        const envCommunities = decode("{env_communities_json}");

        /* Compat: allPosts usado pelo restante (articles, table, trends) */
        const allPosts = allPostsData;

        const grouped = {{}};
        topPosts.forEach(p => {{
            if (!grouped[p.subreddit]) grouped[p.subreddit] = [];
            grouped[p.subreddit].push(p);
        }});

        /* Agrupar TODOS os posts por subreddit (para modo recentes) */
        const groupedAll = {{}};
        allPostsData.forEach(p => {{
            if (!groupedAll[p.subreddit]) groupedAll[p.subreddit] = [];
            groupedAll[p.subreddit].push(p);
        }});

        /* Mesclar comunidades do .env com as extraídas dos posts.
           Isso garante que comunidades recém-adicionadas (sem posts ainda)
           apareçam nas tabs e na lista do modal. */
        const postSubs = Object.keys(grouped);
        const subs = [...new Set([...envCommunities, ...postSubs])];
        /* Inicializar grouped/groupedAll para comunidades sem posts */
        subs.forEach(s => {{
            if (!grouped[s]) grouped[s] = [];
            if (!groupedAll[s]) groupedAll[s] = [];
        }});
        let currentTab = subs[0] || '';
        let currentPage = 'dashboard';
        let currentFilter = 'best'; /* 'best' | 'hot' | 'new' | 'top' | 'rising' */
        let currentTimePeriod = 7;      /* 1 (dia), 7 (semana), 30 (mês) */

        /* ===== HELPERS ===== */
        function esc(s) {{ return (s||'').replace(/`/g,"'"); }}
        function getMaxEngagement(posts) {{ return Math.max(...(posts||allPosts).map(p => p.engagement_score || 0), 1); }}
        function getRatioClass(r) {{ if (r >= 0.9) return 'ratio-high'; if (r >= 0.7) return 'ratio-mid'; return 'ratio-low'; }}
        function getInitials(n) {{ return (n||'U').substring(0,2).toUpperCase(); }}
        function formatDate(iso) {{
            if (!iso) return '';
            const d = new Date(iso), now = new Date(), h = Math.floor((now-d)/36e5);
            if (h<1) return 'agora'; if (h<24) return h+'h atrás';
            const dd = Math.floor(h/24);
            if (dd===1) return 'ontem'; if (dd<7) return dd+' dias atrás';
            return d.toLocaleDateString('pt-BR');
        }}
        function fmtDt(iso) {{ if(!iso) return '—'; return new Date(iso).toLocaleString('pt-BR'); }}
        function fmtTime(iso) {{ if(!iso) return ''; return new Date(iso).toLocaleTimeString('pt-BR'); }}

        function getTimePeriodLabel(days) {{
            if (days <= 1) return 'últimas 24h';
            if (days <= 7) return 'última semana';
            return 'último mês';
        }}

        /* Filtrar posts por período de tempo e retornar os 10 mais recentes */
        function getRecentPosts(sub, periodDays) {{
            const all = groupedAll[sub] || [];
            if (all.length === 0) return [];
            const now = Date.now() / 1000;
            const cutoff = now - (periodDays * 86400);
            const filtered = all.filter(p => {{
                const ts = p.created_utc || (p.created_at ? new Date(p.created_at).getTime()/1000 : 0);
                return ts >= cutoff;
            }});
            /* Ordenar por data mais recente */
            filtered.sort((a, b) => {{
                const tsA = a.created_utc || (a.created_at ? new Date(a.created_at).getTime()/1000 : 0);
                const tsB = b.created_utc || (b.created_at ? new Date(b.created_at).getTime()/1000 : 0);
                return tsB - tsA;
            }});
            return filtered.slice(0, 10);
        }}

        /* ===== NAVIGATION ===== */
        const pageTitles = {{ dashboard: 'Dashboard', posts: 'Todos os Posts', trends: 'Trends & Análises', articles: 'Artigos Markdown', settings: 'Configurações', logs: 'Logs de Execução' }};

        function navigateTo(page) {{
            currentPage = page;
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            document.getElementById('page-' + page).classList.add('active');
            document.querySelectorAll('.sidebar-icon').forEach(i => {{
                i.classList.toggle('active', i.dataset.page === page);
            }});
            document.getElementById('pageTitle').textContent = pageTitles[page] || 'Dashboard';

            if (page === 'posts') renderPostsTable();
            if (page === 'trends') renderTrends();
            if (page === 'articles') renderArticles();
            if (page === 'settings') renderSettings();
            if (page === 'logs') renderLogs();
        }}

        /* ===== MODE TOGGLE ===== */
        function switchMode(mode) {{
            currentMode = mode;
            document.querySelectorAll('.mode-btn').forEach(b => {{
                b.classList.toggle('active', b.dataset.mode === mode);
            }});
            const tf = document.getElementById('timeFilters');
            if (mode === 'recent') {{
                tf.classList.add('visible');
            }} else {{
                tf.classList.remove('visible');
            }}
            renderDashboard();
        }}

        function switchTimePeriod(days) {{
            currentTimePeriod = days;
            document.querySelectorAll('.time-btn').forEach(b => {{
                b.classList.toggle('active', parseInt(b.dataset.period) === days);
            }});
            renderDashboard();
        }}

        /* Mapa de ícones fallback por comunidade */
        const communityIcons = {{
            'n8n': '⚡', 'automation': '🤖', 'Python': '🐍', 'python': '🐍',
            'LangChain': '🔗', 'langchain': '🔗', 'agno': '🧠',
            'huggingface': '🤗', 'ClaudeAI': '🟠', 'claudeai': '🟠',
            'ChatGPT': '💬', 'chatgpt': '💬', 'grok': '🚀',
            'Chatbots': '🗨️', 'chatbots': '🗨️', 'Rag': '📚', 'rag': '📚',
            'javascript': '🟨', 'react': '⚛️', 'typescript': '🔷',
            'devops': '🔧', 'docker': '🐳', 'kubernetes': '☸️',
            'machinelearning': '🧬', 'datascience': '📊', 'artificial': '🤖',
            'openai': '🟢', 'programming': '💻', 'webdev': '🌐',
            'linux': '🐧', 'golang': '🐹', 'rust': '🦀',
        }};

        function getSubredditAvatar(name) {{
            return `https://www.reddit.com/r/${{name}}/about.json`;
        }}

        /* Cache de avatares */
        const avatarCache = {{}};

        async function loadAvatar(sub) {{
            if (avatarCache[sub]) return avatarCache[sub];
            try {{
                const resp = await fetch(`https://www.reddit.com/r/${{sub}}/about.json`, {{ signal: AbortSignal.timeout(3000) }});
                const data = await resp.json();
                const icon = data?.data?.community_icon?.split('?')[0] || data?.data?.icon_img || '';
                if (icon) {{
                    avatarCache[sub] = icon;
                    return icon;
                }}
            }} catch(e) {{ /* fallback */ }}
            return '';
        }}

        function renderTabs() {{
            const container = document.getElementById('tabsRow');
            container.innerHTML = subs.map(s => {{
                const active = s === currentTab ? 'active' : '';
                /* Contagem baseada no filtro simples de quantidade total no sub */
                const count = (groupedAll[s]||[]).length; 
                const icon = communityIcons[s] || communityIcons[s.toLowerCase()] || '📌';
                return `<div class="tab-card ${{active}}" data-tab="${{s}}" onclick="switchTab('${{s}}')">
                    <img class="tab-card-avatar" id="avatar-${{s}}" src="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32'><rect width='32' height='32' rx='16' fill='%23f3f0ff'/><text x='50%25' y='55%25' text-anchor='middle' dominant-baseline='middle' font-size='16'>${{encodeURIComponent(icon)}}</text></svg>" alt="r/${{s}}" />
                    <div class="tab-card-info">
                        <div class="tab-card-name">r/${{s}}</div>
                        <span class="tab-card-count">${{count}} posts</span>
                    </div>
                </div>`;
            }}).join('');

            /* Carregar avatares reais do Reddit */
            subs.forEach(async s => {{
                const url = await loadAvatar(s);
                if (url) {{
                    const img = document.getElementById('avatar-' + s);
                    if (img) {{
                        img.src = url;
                        img.onerror = function() {{ /* mantém o SVG fallback */ }};
                    }}
                }}
            }});
        }}

        function renderStats(posts) {{
            const tE = posts.reduce((a,p) => a+(p.engagement_score||0), 0);
            const tS = posts.reduce((a,p) => a+(p.score||0), 0);
            const tC = posts.reduce((a,p) => a+(p.num_comments||0), 0);
            const aR = posts.length ? posts.reduce((a,p) => a+(p.upvote_ratio||0), 0)/posts.length : 0;
            document.getElementById('statsRow').innerHTML = `
                <div class="stat-card purple"><div class="label">🔥 Engajamento Total</div><div class="value">${{Math.round(tE).toLocaleString('pt-BR')}}</div><div class="sub">${{posts.length}} posts</div></div>
                <div class="stat-card gold"><div class="label">⬆️ Score Total</div><div class="value">${{tS.toLocaleString('pt-BR')}}</div><div class="sub">upvotes</div></div>
                <div class="stat-card blue"><div class="label">💬 Comentários</div><div class="value">${{tC.toLocaleString('pt-BR')}}</div><div class="sub">discussões</div></div>
                <div class="stat-card green"><div class="label">📊 Aprovação</div><div class="value">${{Math.round(aR*100)}}%</div><div class="sub">ratio médio</div></div>`;
        }}

        /* Obter posts filtrados e ordenados */
        function getActivePosts() {{
            let posts = groupedAll[currentTab] || [];
            if (posts.length === 0) return [];

            /* 1. Filtro de Tempo */
            const now = Date.now() / 1000;
            const cutoff = now - (currentTimePeriod * 86400); 
            
            posts = posts.filter(p => {{
                const ts = p.created_utc || (p.created_at ? new Date(p.created_at).getTime()/1000 : 0);
                return ts >= cutoff;
            }});

            /* 2. Filtro de Categoria (Ordenação) */
            /* clonar array para sort */
            let sorted = [...posts];

            switch(currentFilter) {{
                case 'hot': 
                    /* Hot: Score alto (geralmente recente) */
                    sorted.sort((a,b) => (b.score||0) - (a.score||0));
                    break;
                case 'new': 
                    /* New: Recentes */
                    sorted.sort((a,b) => ((b.created_utc||0) - (a.created_utc||0)));
                    break;
                case 'top': 
                    /* Top: Score alto (semelhante a Hot, mas estritamente votos) */
                    sorted.sort((a,b) => (b.score||0) - (a.score||0));
                    break;
                case 'rising': 
                    /* Rising: Ratio alto e recentes (< 24h na janela filtrada) */
                    /* Heurística: Score * Ratio */
                    sorted.sort((a,b) => ((b.score||0)*(b.upvote_ratio||0)) - ((a.score||0)*(a.upvote_ratio||0)));
                    break;
                case 'best': 
                default:
                    /* Best: Engajamento (nosso algoritmo) */
                    sorted.sort((a,b) => (b.engagement_score||0) - (a.engagement_score||0));
                    break;
            }}

            /* Retornar top 10 (ou mais dependendo da configuração, mas pedido foi "coloca os 10 mais") */
            return sorted.slice(0, 10);
        }}

        function renderDashboard() {{
            const posts = getActivePosts();
            renderTabs();
            renderStats(posts);
            renderDashboardPosts(posts);
        }}

        function renderDashboardPosts(posts) {{
            const maxE = getMaxEngagement(posts);
            const list = document.getElementById('postsList');

            const labels = {{
                best: '🔥 Melhores (Engajamento)',
                hot: '🚀 Destaque',
                new: '✨ Mais Novos',
                top: '🏆 Mais Votados',
                rising: '📈 Em Ascensão'
            }};
            const label = labels[currentFilter] || 'Posts';

            document.getElementById('sectionTitle').textContent = `${{label}} — r/${{currentTab}}`;
            document.getElementById('viewAllLabel').textContent = `${{posts.length}} posts`;

            if (posts.length === 0) {{
                list.innerHTML = `<div style="text-align:center;padding:3rem 1rem;color:var(--text-muted)">
                    <div style="font-size:2.5rem;margin-bottom:0.75rem">📭</div>
                    <p style="font-size:0.9rem">Nenhum post encontrado para o filtro <strong>${{labels[currentFilter]}}</strong> em r/${{currentTab}}.</p>
                    <p style="font-size:0.8rem;margin-top:0.5rem;color:var(--text-light)">Tente ampliar o período de tempo.</p>
                </div>`;
                return;
            }}

            list.innerHTML = posts.map((p,i) => {{
                const rank = (i+1);
                const rC=getRatioClass(p.upvote_ratio||0), rP=Math.round((p.upvote_ratio||0)*100);
                const eP=Math.min(((p.engagement_score||0)/maxE)*100,100);
                const ex=esc((p.selftext||'').replace(/\\n/g,' ').substring(0,180));
                const fl=p.flair?`<div class="post-flair">${{esc(p.flair)}}</div>`:'';
                const postIdx = allPosts.findIndex(ap => ap.permalink === p.permalink);
                const rankClass = rank <= 5 ? 'r' + rank : 'r5';
                return `<div class="post-card"><div class="post-top"><div class="rank-badge ${{rankClass}}">${{rank}}</div><div class="post-content">
                    <div class="post-title"><a href="${{p.permalink}}" target="_blank">${{esc(p.title)}}</a></div>
                    ${{ex?`<p class="post-excerpt">${{ex}}</p>`:''}}
                    ${{fl}}
                    <div class="post-stats">
                        <span class="pill engagement"><span class="pill-icon">🔥</span> ${{Math.round(p.engagement_score||0)}}</span>
                        <span class="pill score"><span class="pill-icon">⬆️</span> ${{(p.score||0).toLocaleString('pt-BR')}}</span>
                        <span class="pill comments"><span class="pill-icon">💬</span> ${{(p.num_comments||0).toLocaleString('pt-BR')}}</span>
                        <span class="pill ${{rC}}"><span class="pill-icon">📊</span> ${{rP}}%</span>
                    </div>
                    <div class="engagement-bar"><div class="engagement-fill" style="width:0%" data-width="${{eP}}%"></div></div>
                    <div class="post-footer">
                        <div class="post-author"><div class="author-avatar">${{getInitials(p.author)}}</div><span class="author-name">u/${{p.author}}</span></div>
                        <span class="post-date">${{formatDate(p.created_at)}}</span>
                        <button class="btn-convert" data-pidx="${{postIdx >= 0 ? postIdx : 0}}" data-rank="${{rank}}" onclick="event.stopPropagation();convertByIdx(this)">📄 Gerar Markdown</button>
                        <a class="post-link" href="${{p.permalink}}" target="_blank">Abrir no Reddit →</a>
                    </div></div></div></div>`;
            }}).join('');
            requestAnimationFrame(()=>{{ setTimeout(()=>{{ document.querySelectorAll('.engagement-fill').forEach(b=>{{b.style.width=b.dataset.width;}}); }},150); }});
        }}

        function switchFilter(filter) {{
            currentFilter = filter;
            document.querySelectorAll('.filter-btn').forEach(b => {{
                b.classList.toggle('active', b.dataset.filter === filter);
            }});
            renderDashboard();
        }}

        function switchTab(sub) {{ currentTab=sub; renderDashboard(); }}

        /* ===== MARKDOWN GENERATOR ===== */
        const savedArticles = [];


        function fmtDateBr(iso) {{
            if (!iso) return 'Data não disponível';
            const d = new Date(iso);
            const m = ['','janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro'];
            return `${{d.getDate()}} de ${{m[d.getMonth()+1]}} de ${{d.getFullYear()}}`;
        }}

        function engBar(score, max) {{
            const r = Math.min(score/max, 1);
            const f = Math.round(r * 10);
            return '█'.repeat(f) + '░'.repeat(10-f);
        }}

        function generateMarkdown(p, rank) {{
            const maxE = getMaxEngagement();
            const fl = p.flair ? `\\nflair: "${{p.flair}}"` : '';
            const dateBr = fmtDateBr(p.created_at);
            const summary = (p.selftext || '').trim() ? (p.selftext||'').split(/\\n/).filter(l=>l.trim()).slice(0,3).join(' ').substring(0,300) + '...' : '_Post sem conteúdo de texto (pode ser um link, imagem ou vídeo)._';
            const content = (p.selftext || '').trim() || '_Este post não contém texto. Acesse o link original para ver o conteúdo completo._';
            const now = new Date().toLocaleString('pt-BR', {{timeZone:'UTC'}});
            const bar = engBar(p.engagement_score||0, maxE);

            return `---\ntitle: "${{(p.title||'').replace(/"/g, '\\\\"')}}"
subreddit: r/${{p.subreddit}}
author: u/${{p.author}}
date: "${{p.created_at}}"
score: ${{p.score||0}}
comments: ${{p.num_comments||0}}
upvote_ratio: ${{p.upvote_ratio||0}}
engagement_score: ${{Math.round(p.engagement_score||0)}}
rank: ${{rank}}
source: Reddit
permalink: "${{p.permalink}}"${{fl}}
---

# ${{p.title}}

> **Ranking #${{rank}}** no r/${{p.subreddit}} • Publicado em ${{dateBr}}

---

## 📋 Resumo

${{summary}}

---

## 📖 Conteúdo Completo

${{content}}

---

## 📊 Métricas de Engajamento

| Métrica | Valor |
|---------|-------|
| 🔥 **Engajamento** | ${{Math.round(p.engagement_score||0)}} pontos |
| ⬆️ **Upvotes (Score)** | ${{p.score||0}} |
| 💬 **Comentários** | ${{p.num_comments||0}} |
| 📊 **Taxa de Aprovação** | ${{Math.round((p.upvote_ratio||0)*100)}}% |
| 🏷️ **Flair** | ${{p.flair || '—'}} |

**Nível de Engajamento:** ` + '`' + `${{bar}}` + '`' + ` ${{Math.round(p.engagement_score||0)}}/${{Math.round(maxE)}}

---

## 📌 Fonte & Créditos

> 🔴 **Este artigo é baseado em uma publicação do [Reddit](https://reddit.com).**
>
> Todo o conteúdo original pertence ao autor **u/${{p.author}}** e à comunidade **r/${{p.subreddit}}**.
> Este documento foi gerado automaticamente para fins de análise e referência.
>
> 🔗 **Post original:** [${{p.title}}](${{p.permalink}})
>
> 📅 **Data da publicação:** ${{dateBr}}
>
> ⚠️ _Respeite os direitos autorais. Para interagir com o conteúdo, visite o post original no Reddit._

---

<sub>📄 Artigo gerado automaticamente em ${{now}} pelo pipeline de automação Reddit Top Posts.</sub>
`;
        }}

        function convertByIdx(btn) {{
            const idx = parseInt(btn.dataset.pidx);
            const rank = parseInt(btn.dataset.rank);
            const p = allPosts[idx];
            if (!p) return;
            const md = generateMarkdown(p, rank);
            const slug = slugify(p.title);
            const exists = savedArticles.find(a => a.slug === slug);
            if (!exists) {{
                savedArticles.push({{ slug, title: p.title, subreddit: p.subreddit, rank, markdown: md, createdAt: new Date().toISOString() }});
            }}
            btn.innerHTML = '✅ Convertido';
            btn.classList.add('done');
            btn.disabled = true;
        }}

        function convertAll() {{
            allPosts.forEach(p => {{
                const rank = p.rank || 1;
                const slug = slugify(p.title);
                if (!savedArticles.find(a => a.slug === slug)) {{
                    const md = generateMarkdown(p, rank);
                    savedArticles.push({{ slug, title: p.title, subreddit: p.subreddit, rank, markdown: md, createdAt: new Date().toISOString() }});
                }}
            }});
            renderArticles();
            // Update convert buttons in dashboard
            document.querySelectorAll('.btn-convert:not(.done)').forEach(btn => {{ btn.innerHTML = '✅ Convertido'; btn.classList.add('done'); btn.disabled = true; }});
        }}

        function downloadMd(idx) {{
            const a = savedArticles[idx];
            const blob = new Blob([a.markdown], {{ type: 'text/markdown;charset=utf-8' }});
            const url = URL.createObjectURL(blob);
            const el = document.createElement('a');
            el.href = url; el.download = a.slug + '.md'; el.click();
            URL.revokeObjectURL(url);
        }}

        function downloadAllMd() {{
            savedArticles.forEach((a, i) => downloadMd(i));
        }}

        function togglePreview(idx) {{
            const el = document.getElementById('art-preview-' + idx);
            el.classList.toggle('open');
        }}

        /* ===== PAGE: ARTICLES ===== */
        function renderArticles() {{
            const el = document.getElementById('page-articles');
            if (savedArticles.length === 0) {{
                el.innerHTML = `
                    <div class="empty-articles">
                        <div class="empty-icon">📄</div>
                        <p>Nenhum artigo convertido ainda.<br>Vá ao Dashboard e clique em <strong>"📄 Gerar Markdown"</strong> em qualquer post,<br>ou converta todos de uma vez:</p>
                        <button class="btn-primary" onclick="convertAll();navigateTo('articles')">📄 Converter Todos os Posts</button>
                    </div>`;
                return;
            }}

            const bySub = {{}};
            savedArticles.forEach(a => {{ if (!bySub[a.subreddit]) bySub[a.subreddit] = 0; bySub[a.subreddit]++; }});

            el.innerHTML = `
                <div class="convert-all-bar">
                    <div class="info">📄 <strong>${{savedArticles.length}}</strong> artigos convertidos ${{savedArticles.length < allPosts.length ? `de ${{allPosts.length}} posts` : '— todos convertidos ✅'}}</div>
                    <div style="display:flex;gap:0.5rem">
                        ${{savedArticles.length < allPosts.length ? '<button class="btn-outline" onclick="convertAll();renderArticles()">📄 Converter restantes</button>' : ''}}
                        <button class="btn-primary" onclick="downloadAllMd()">💾 Salvar Todos (.md)</button>
                    </div>
                </div>

                <div class="articles-stats">
                    <div class="stat-card purple"><div class="label">📄 Total de Artigos</div><div class="value">${{savedArticles.length}}</div><div class="sub">convertidos para Markdown</div></div>
                    ${{Object.entries(bySub).map(([s,c]) => `<div class="stat-card blue"><div class="label">📂 r/${{s}}</div><div class="value">${{c}}</div><div class="sub">artigos</div></div>`).join('')}}
                </div>

                ${{savedArticles.map((a, i) => `
                    <div class="article-card" style="animation-delay:${{i*0.04}}s">
                        <div class="article-header" onclick="togglePreview(${{i}})">
                            <div class="article-info">
                                <span class="article-sub">r/${{a.subreddit}}</span>
                                <span class="article-name">#${{a.rank}} — ${{a.title}}</span>
                            </div>
                            <div class="article-actions">
                                <button class="btn-preview" onclick="event.stopPropagation();togglePreview(${{i}})">👁️ Preview</button>
                                <button class="btn-save" onclick="event.stopPropagation();downloadMd(${{i}})">💾 Salvar .md</button>
                            </div>
                        </div>
                        <div class="article-preview" id="art-preview-${{i}}">
                            <pre>${{a.markdown.replace(/</g,'&lt;').replace(/>/g,'&gt;')}}</pre>
                        </div>
                    </div>
                `).join('')}}
            `;
        }}

        /* ===== PAGE: POSTS TABLE ===== */
        function renderPostsTable() {{
            const sorted = [...allPosts].sort((a,b) => (b.engagement_score||0)-(a.engagement_score||0));
            document.getElementById('page-posts').innerHTML = `
                <div class="section-header" style="margin-bottom:1rem"><span class="section-title">Todos os Posts — Ranking Geral</span><span class="view-all">${{sorted.length}} posts</span></div>
                <div class="table-card"><table class="posts-table">
                    <thead><tr><th>#</th><th>Sub</th><th>Título</th><th>🔥 Eng.</th><th>⬆️ Score</th><th>💬 Com.</th><th>📊 Ratio</th><th>Autor</th><th>Data</th></tr></thead>
                    <tbody>${{sorted.map((p,i) => `<tr>
                        <td class="mono">${{i+1}}</td>
                        <td><span class="pill engagement" style="font-size:0.7rem">r/${{p.subreddit}}</span></td>
                        <td class="td-title"><a href="${{p.permalink}}" target="_blank">${{esc(p.title)}}</a></td>
                        <td class="mono" style="color:var(--gold-500)">${{Math.round(p.engagement_score||0)}}</td>
                        <td class="mono" style="color:var(--green-500)">${{p.score||0}}</td>
                        <td class="mono" style="color:var(--blue-500)">${{p.num_comments||0}}</td>
                        <td class="mono">${{Math.round((p.upvote_ratio||0)*100)}}%</td>
                        <td>u/${{p.author}}</td>
                        <td style="color:var(--text-light);font-size:0.75rem">${{formatDate(p.created_at)}}</td>
                    </tr>`).join('')}}</tbody>
                </table></div>`;
        }}

        /* ===== PAGE: TRENDS ===== */
        function renderTrends() {{
            const maxE = getMaxEngagement();
            // Engagement by sub
            let subBars = subs.map(s => {{
                const total = grouped[s].reduce((a,p) => a+(p.engagement_score||0), 0);
                return {{label: 'r/'+s, value: Math.round(total)}};
            }});
            const maxSub = Math.max(...subBars.map(b=>b.value),1);

            // Top posts bar chart
            const top10 = [...allPosts].sort((a,b)=>(b.engagement_score||0)-(a.engagement_score||0));
            let postBars = top10.map(p => ({{label: esc(p.title.substring(0,40))+(p.title.length>40?'...':''), value: Math.round(p.engagement_score||0), sub: p.subreddit}}));

            // Comments chart
            let commentBars = top10.map(p => ({{label: esc(p.title.substring(0,40))+(p.title.length>40?'...':''), value: p.num_comments||0}}));
            const maxC = Math.max(...commentBars.map(b=>b.value),1);

            // Score chart
            let scoreBars = top10.map(p => ({{label: esc(p.title.substring(0,40))+(p.title.length>40?'...':''), value: p.score||0}}));
            const maxS = Math.max(...scoreBars.map(b=>b.value),1);

            document.getElementById('page-trends').innerHTML = `
                <div class="section-header" style="margin-bottom:1.5rem"><span class="section-title">Análises & Comparações</span></div>

                <div class="chart-card" style="margin-bottom:1.5rem">
                    <h3>🔥 Engajamento Total por Subreddit</h3>
                    <div class="bar-chart">${{subBars.map(b => `<div class="bar-row">
                        <span class="bar-label">${{b.label}}</span>
                        <div class="bar-track"><div class="bar-fill purple" style="width:${{(b.value/maxSub*100)}}%">${{b.value}}</div></div>
                    </div>`).join('')}}</div>
                </div>

                <div class="chart-card" style="margin-bottom:1.5rem">
                    <h3>🏆 Ranking de Engajamento por Post</h3>
                    <div class="bar-chart">${{postBars.map((b,i) => `<div class="bar-row">
                        <span class="bar-label">${{b.label}}</span>
                        <div class="bar-track"><div class="bar-fill ${{i%2===0?'purple':'gold'}}" style="width:${{(b.value/maxE*100)}}%">${{b.value}}</div></div>
                    </div>`).join('')}}</div>
                </div>

                <div class="charts-grid">
                    <div class="chart-card">
                        <h3>💬 Comentários por Post</h3>
                        <div class="bar-chart">${{commentBars.map(b => `<div class="bar-row">
                            <span class="bar-label">${{b.label}}</span>
                            <div class="bar-track"><div class="bar-fill blue" style="width:${{(b.value/maxC*100)}}%">${{b.value}}</div></div>
                        </div>`).join('')}}</div>
                    </div>
                    <div class="chart-card">
                        <h3>⬆️ Score por Post</h3>
                        <div class="bar-chart">${{scoreBars.map(b => `<div class="bar-row">
                            <span class="bar-label">${{b.label}}</span>
                            <div class="bar-track"><div class="bar-fill green" style="width:${{(b.value/maxS*100)}}%">${{b.value}}</div></div>
                        </div>`).join('')}}</div>
                    </div>
                </div>`;
        }}

        /* ===== PAGE: SETTINGS ===== */
        function renderSettings() {{
            const descs = {{
                TARGET_SUBREDDITS: 'Subreddits monitorados',
                FETCH_LIMIT: 'Posts recentes por subreddit',
                TOP_N: 'Top posts selecionados por sub',
                PERIOD_DAYS: 'Janela de tempo (dias)',
                WEIGHT_SCORE: 'Peso dos upvotes',
                WEIGHT_COMMENTS: 'Peso dos comentários',
                WEIGHT_RATIO: 'Peso do upvote ratio',
                TMP_DIR: 'Diretório temporário'
            }};
            document.getElementById('page-settings').innerHTML = `
                <div class="section-header" style="margin-bottom:1.5rem"><span class="section-title">Parâmetros do Sistema</span></div>
                <div class="formula-card">
                    <h3>📐 Fórmula de Engajamento</h3>
                    <div class="formula-code">engagement = (score × ${{appConfig.WEIGHT_SCORE}}) + (comentários × ${{appConfig.WEIGHT_COMMENTS}}) + (upvote_ratio × ${{appConfig.WEIGHT_RATIO}})</div>
                </div>
                <div class="settings-grid">
                    ${{Object.entries(appConfig).map(([k,v]) => `<div class="setting-item">
                        <div class="s-label">${{k}}</div>
                        <div class="s-value">${{v}}</div>
                        <div class="s-desc">${{descs[k]||''}}</div>
                    </div>`).join('')}}
                </div>`;
        }}

        /* ===== PAGE: LOGS ===== */
        function renderLogs() {{
            const logs = [...appLogs].reverse();
            const suc = logs.filter(l=>l.status==='success').length;
            const err = logs.filter(l=>l.status==='error').length;
            document.getElementById('page-logs').innerHTML = `
                <div class="section-header" style="margin-bottom:1rem"><span class="section-title">Histórico de Execuções</span><span class="view-all">${{logs.length}} registros · ${{suc}} ✅ ${{err}} ❌</span></div>
                ${{logs.length===0 ? '<div class="chart-card"><p style="color:var(--text-muted);text-align:center;padding:2rem">Nenhum log registrado.</p></div>' :
                logs.map((l,i) => {{
                    const metrics = l.metrics && Object.keys(l.metrics).length ? `<div class="log-metrics">${{Object.entries(l.metrics).map(([k,v])=>`<div class="log-mpill"><span class="k">${{k}}: </span><span class="v">${{v}}</span></div>`).join('')}}</div>` : '';
                    const entries = l.log_entries && l.log_entries.length ? `<div class="log-entries-list">${{l.log_entries.map(e=>`<div><span class="le-time">${{fmtTime(e.time)}}</span> <span class="le-lvl ${{e.level}}">${{e.level}}</span> ${{e.message}}</div>`).join('')}}</div>` : '';
                    return `<div class="log-card" onclick="this.querySelector('.log-details').classList.toggle('open')">
                        <div class="log-top">
                            <div style="display:flex;align-items:center;gap:0.75rem">
                                <span class="log-badge ${{l.status}}">● ${{l.status}}</span>
                                <span class="log-script">${{l.script}}</span>
                            </div>
                            <div class="log-meta"><span>📅 ${{fmtDt(l.started_at)}}</span><span>⏱ ${{l.duration_seconds}}s</span></div>
                        </div>
                        <div class="log-details">${{l.error?`<div style="color:var(--red-500);margin-bottom:0.5rem">❌ ${{l.error}}</div>`:''}}
                            ${{metrics}}${{entries}}
                        </div>
                    </div>`;
                }}).join('')}}`;
        }}

        /* ===== DOWNLOAD ===== */
        document.getElementById('downloadBtn').addEventListener('click', () => {{
            const blob = new Blob([JSON.stringify(allPosts, null, 2)], {{ type: 'application/json' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a'); a.href = url; a.download = 'top_reddit_posts.json'; a.click();
            URL.revokeObjectURL(url);
        }});

        /* ===== API CONFIG ===== */
        const isServerMode = true;
        const API_BASE = window.location.protocol.startsWith('http')
            ? window.location.origin
            : 'http://localhost:5050';

        /* ===== SEARCH POSTS ===== */
        let searchTimeout = null;

        function handleSearch() {{
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(searchPosts, 250);
            const val = document.getElementById('searchInput').value;
            document.getElementById('searchClear').classList.toggle('visible', val.length > 0);
        }}

        function clearSearch() {{
            document.getElementById('searchInput').value = '';
            document.getElementById('searchClear').classList.remove('visible');
            renderDashboard();
        }}

        function searchPosts() {{
            const query = document.getElementById('searchInput').value.trim().toLowerCase();
            if (!query) {{
                renderDashboard();
                return;
            }}

            /* Buscar em TODOS os posts de TODAS as comunidades */
            const results = allPosts.filter(p => {{
                const title = (p.title || '').toLowerCase();
                const author = (p.author || '').toLowerCase();
                const sub = (p.subreddit || '').toLowerCase();
                const flair = (p.flair || p.link_flair_text || '').toLowerCase();
                const text = (p.selftext || '').toLowerCase();
                return title.includes(query) || author.includes(query) ||
                       sub.includes(query) || flair.includes(query) || text.includes(query);
            }});

            /* Renderizar resultados da busca */
            document.getElementById('sectionTitle').textContent = `🔍 Resultados para "${{query}}"`;
            document.getElementById('viewAllLabel').textContent = `${{results.length}} posts encontrados`;

            renderStats(results);

            const maxE = getMaxEngagement(results);
            const list = document.getElementById('postsList');

            if (results.length === 0) {{
                list.innerHTML = `<div style="text-align:center;padding:3rem 1rem;color:var(--text-muted)">
                    <div style="font-size:2.5rem;margin-bottom:0.75rem">🔍</div>
                    <p style="font-size:0.9rem">Nenhum post encontrado para "<strong>${{query}}</strong>".</p>
                    <p style="font-size:0.8rem;margin-top:0.5rem;color:var(--text-light)">Tente outro termo de busca.</p>
                </div>`;
                return;
            }}

            list.innerHTML = results.map((p,i) => {{
                const rank = i + 1;
                const rC=getRatioClass(p.upvote_ratio||0), rP=Math.round((p.upvote_ratio||0)*100);
                const eP=Math.min(((p.engagement_score||0)/maxE)*100,100);
                const ex=esc((p.selftext||'').replace(/\\\\n/g,' ').substring(0,180));
                const fl=p.flair?`<div class="post-flair">${{esc(p.flair)}}</div>`:'';
                const rankClass = rank <= 5 ? `r${{rank}}` : 'r5';
                return `<div class="post-card"><div class="post-top"><div class="rank-badge ${{rankClass}}">${{rank}}</div><div class="post-content">
                    <div class="post-title"><a href="${{p.permalink}}" target="_blank">${{esc(p.title)}}</a></div>
                    ${{ex?`<p class="post-excerpt">${{ex}}</p>`:''}}
                    ${{fl}}
                    <div class="post-pills">
                        <span class="pill engagement"><span class="pill-icon">🔥</span> ${{Math.round(p.engagement_score||0)}}</span>
                        <span class="pill score"><span class="pill-icon">⬆️</span> ${{(p.score||0).toLocaleString('pt-BR')}}</span>
                        <span class="pill comments"><span class="pill-icon">💬</span> ${{(p.num_comments||0).toLocaleString('pt-BR')}}</span>
                        <span class="pill ${{rC}}"><span class="pill-icon">📊</span> ${{rP}}%</span>
                        <span class="pill" style="background:var(--purple-50);color:var(--purple-600)"><span class="pill-icon">📂</span> r/${{p.subreddit||''}}</span>
                    </div></div></div>
                    <div class="engagement-bar"><div class="engagement-fill" style="width:${{eP.toFixed(1)}}%"></div></div>
                </div>`;
            }}).join('');
        }}

        /* ===== COMMUNITY MANAGEMENT ===== */

        function openCommunityModal() {{
            document.getElementById('importModal').classList.add('open');
            setTimeout(() => document.getElementById('communityInput').focus(), 200);
            renderCommunityList();
        }}

        function closeCommunityModal() {{
            document.getElementById('importModal').classList.remove('open');
            document.getElementById('communityInput').value = '';
            document.getElementById('communityStatus').textContent = '';
            document.getElementById('communityStatus').className = 'fetch-status';
        }}

        function renderCommunityList() {{
            const list = document.getElementById('communityListArea');
            const badge = document.getElementById('communityCountBadge');
            badge.textContent = subs.length;

            if (subs.length === 0) {{
                list.innerHTML = '<li style="text-align:center;padding:1.5rem;color:var(--text-light);font-size:0.85rem">Nenhuma comunidade cadastrada.</li>';
                return;
            }}

            list.innerHTML = subs.map(s => {{
                const count = (grouped[s] || []).length;
                return `<li class="community-list-item">
                    <span class="cl-name"><span class="cl-dot"></span> r/${{s}} <span style="color:var(--text-light);font-size:0.75rem">(${{count}} posts)</span></span>
                    <button class="btn-remove-community" onclick="removeCommunity('${{s}}')" title="Remover r/${{s}}"
                            ${{!isServerMode ? 'disabled' : ''}}>🗑️ Remover</button>
                </li>`;
            }}).join('');
        }}

        async function addCommunityFromInput() {{
            const input = document.getElementById('communityInput');
            const status = document.getElementById('communityStatus');
            const btn = document.getElementById('addCommunityBtn');
            let name = input.value.trim();

            /* Limpar prefixos como r/ ou /r/ */
            name = name.replace(/^\/?(r\/)/i, '');
            /* Remover URL completa se colada */
            const urlMatch = name.match(/reddit\.com\/r\/(\w+)/i);
            if (urlMatch) name = urlMatch[1];

            if (!name) {{
                status.textContent = '❌ Digite o nome da comunidade (ex: python).';
                status.className = 'fetch-status error';
                return;
            }}

            /* Validar: só letras, números e underscore */
            if (!/^\w+$/.test(name)) {{
                status.textContent = '❌ Nome inválido. Use apenas letras, números e _.';
                status.className = 'fetch-status error';
                return;
            }}

            /* Verificar duplicidade local */
            if (subs.map(s => s.toLowerCase()).includes(name.toLowerCase())) {{
                status.textContent = `ℹ️ r/${{name}} já está na lista.`;
                status.className = 'fetch-status';
                input.value = '';
                return;
            }}

            if (!isServerMode) {{
                status.textContent = '⚠️ Inicie o servidor para adicionar: python execution/server.py';
                status.className = 'fetch-status error';
                return;
            }}

            btn.disabled = true;
            btn.innerHTML = '⏳ Adicionando...';
            status.textContent = 'Adicionando comunidade...';
            status.className = 'fetch-status';

            try {{
                const resp = await fetch(`${{API_BASE}}/api/add-community`, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ name: name }}),
                }});
                const result = await resp.json();

                if (result.success) {{
                    status.textContent = `✅ r/${{name}} adicionada! Buscando posts...`;
                    status.className = 'fetch-status';
                    showToast(`r/${{name}} adicionada! Buscando posts automaticamente...`, 'success');

                    /* Atualizar comunidades visíveis */
                    if (!grouped[name]) {{
                        grouped[name] = [];
                        if (!groupedAll[name]) groupedAll[name] = [];
                        if (!subs.includes(name)) subs.push(name);
                        renderTabs();
                    }}
                    input.value = '';
                    renderCommunityList();

                    /* Executar pipeline automaticamente */
                    btn.innerHTML = '⏳ Buscando posts...';
                    try {{
                        const pipeResp = await fetch(`${{API_BASE}}/api/run-pipeline`, {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                        }});
                        const pipeResult = await pipeResp.json();
                        if (pipeResult.success) {{
                            status.textContent = `✅ Posts de r/${{name}} carregados! Recarregando...`;
                            showToast('Pipeline concluído! Recarregando dashboard...', 'success');
                            setTimeout(() => location.reload(), 1500);
                            return;
                        }} else {{
                            status.textContent = `⚠️ Comunidade salva, mas erro ao buscar posts.`;
                            showToast(pipeResult.error || 'Erro no pipeline.', 'error');
                        }}
                    }} catch (pipeErr) {{
                        status.textContent = `⚠️ Comunidade salva, mas não foi possível buscar posts.`;
                        showToast(`Erro de conexão ao pipeline: ${{pipeErr.message}}`, 'error');
                    }}
                }} else if (result.exists) {{
                    status.textContent = `ℹ️ r/${{name}} já está registrada.`;
                    status.className = 'fetch-status';
                    input.value = '';
                }} else {{
                    status.textContent = '❌ ' + (result.error || 'Erro ao adicionar.');
                    status.className = 'fetch-status error';
                }}
            }} catch (err) {{
                status.textContent = `❌ Erro de conexão: ${{err.message}}`;
                status.className = 'fetch-status error';
            }}

            btn.disabled = false;
            btn.innerHTML = '➕ Adicionar';
        }}

        async function removeCommunity(name) {{
            if (!isServerMode) {{
                showToast('Inicie o servidor para remover comunidades.', 'error');
                return;
            }}

            if (!confirm(`Remover r/${{name}} da lista de monitoramento?`)) return;

            try {{
                const resp = await fetch(`${{API_BASE}}/api/remove-community`, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ name: name }}),
                }});
                const result = await resp.json();

                if (result.success) {{
                    showToast(`r/${{name}} removida do sistema.`, 'success');

                    /* Atualizar estado local */
                    const idx = subs.findIndex(s => s.toLowerCase() === name.toLowerCase());
                    if (idx >= 0) subs.splice(idx, 1);
                    delete grouped[name];
                    delete groupedAll[name];

                    /* Se era a aba ativa, mudar para a primeira */
                    if (currentTab.toLowerCase() === name.toLowerCase()) {{
                        currentTab = subs[0] || '';
                    }}

                    renderDashboard();
                    renderCommunityList();
                }} else {{
                    showToast(result.error || 'Erro ao remover.', 'error');
                }}
            }} catch (err) {{
                showToast(`Erro de conexão: ${{err.message}}`, 'error');
            }}
        }}

        /* ===== TOAST NOTIFICATIONS ===== */
        function showToast(message, type = 'info') {{
            const container = document.getElementById('toastContainer');
            const icons = {{ success: '✅', error: '❌', info: 'ℹ️' }};
            const toast = document.createElement('div');
            toast.className = `toast ${{type}}`;
            toast.innerHTML = `<span class="toast-icon">${{icons[type] || 'ℹ️'}}</span><span>${{message}}</span>`;
            container.appendChild(toast);
            setTimeout(() => {{
                toast.classList.add('fade-out');
                setTimeout(() => toast.remove(), 300);
            }}, 4500);
        }}

        /* ===== INIT ===== */
        try {{
            renderDashboard();
        }} catch(e) {{
            console.error('❌ renderDashboard error:', e);
            document.getElementById('postsList').innerHTML = '<div style=\"padding:2rem;color:red;font-size:1rem\"><h3>Erro ao renderizar dashboard:</h3><pre>' + e.message + '\\n' + e.stack + '</pre></div>';
        }}

        /* ===== SERVER STATUS CHECK ===== */
        async function checkServerStatus() {{
            const badge = document.getElementById('statusBadge');
            const text = document.getElementById('statusText');
            try {{
                const resp = await fetch(`${{API_BASE}}/api/communities`, {{ signal: AbortSignal.timeout(4000) }});
                if (resp.ok) {{
                    badge.className = 'status-badge online';
                    badge.title = 'Servidor ativo em ' + API_BASE;
                    text.textContent = 'Online';
                }} else {{
                    throw new Error('not ok');
                }}
            }} catch(e) {{
                badge.className = 'status-badge offline';
                badge.title = 'Servidor indisponível. Inicie: python execution/server.py';
                text.textContent = 'Offline';
            }}
        }}
        checkServerStatus();
        setInterval(checkServerStatus, 30000);
    </script>
</body>
</html>"""

    return html


def main():
    posts = load_data()
    all_posts_data = load_all_data()
    html = generate_html(posts, all_posts_data)

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    abs_path = OUTPUT_HTML.resolve()
    print(f"✅ App gerado: {abs_path}")
    print(f"📊 {len(posts)} posts renderizados")

    # Auto-start server.py in background so community management works
    import subprocess
    script_dir = os.path.dirname(os.path.abspath(__file__))
    server_script = os.path.join(script_dir, "server.py")
    project_dir = os.path.dirname(script_dir)
    try:
        subprocess.Popen(
            [sys.executable, server_script],
            cwd=project_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("🚀 Servidor iniciado em http://localhost:5050")
        import time
        time.sleep(1)  # aguardar servidor subir
        webbrowser.open("http://localhost:5050")
        print("🌐 Dashboard aberto no navegador!")
    except Exception as e:
        print(f"⚠️ Não foi possível iniciar o servidor: {e}")
        try:
            webbrowser.open(f"file://{abs_path}")
            print("🌐 Abrindo versão local no navegador...")
        except Exception:
            print(f"   Abra manualmente: file://{abs_path}")


if __name__ == "__main__":
    main()
