"""
format_posts.py — Formata os top posts em JSON limpo e gera resumo Markdown.

Uso:
    python execution/format_posts.py

Entradas:
    - .tmp/top_posts.json (gerado por fetch_reddit_posts.py)
    - .tmp/raw_posts.json  (todos os posts brutos coletados)

Saídas:
    - .tmp/formatted_posts.json     (top N — dados limpos e estruturados)
    - .tmp/formatted_all_posts.json (TODOS os posts — para modo "Mais Recentes")
    - .tmp/summary.md               (resumo legível com tabela)
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

# Importar logger
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from logger import AutomationLogger

load_dotenv()
TMP_DIR = os.getenv("TMP_DIR", ".tmp")

# Pesos do score de engajamento (mesmos de fetch_reddit_posts.py)
W_SCORE = float(os.getenv("WEIGHT_SCORE", "1.0"))
W_COMMENTS = float(os.getenv("WEIGHT_COMMENTS", "2.0"))
W_RATIO = float(os.getenv("WEIGHT_RATIO", "50.0"))

log = AutomationLogger("format_posts")

# ---------------------------------------------------------------------------
# 1. Carregar top posts
# ---------------------------------------------------------------------------
top_path = Path(TMP_DIR) / "top_posts.json"

if not top_path.exists():
    log.error(f"Arquivo não encontrado: {top_path}. Execute fetch_reddit_posts.py primeiro.")
    sys.exit(1)

with open(top_path, "r", encoding="utf-8") as f:
    top_data: dict[str, list[dict]] = json.load(f)

print(f"📂 Carregados top posts de {len(top_data)} subreddit(s)")
log.info(f"Carregados top posts de {len(top_data)} subreddit(s)")

# ---------------------------------------------------------------------------
# 2. Formatar dados
# ---------------------------------------------------------------------------
formatted: list[dict] = []

for subreddit, posts in top_data.items():
    for i, post in enumerate(posts, start=1):
        # Converter timestamp Unix para ISO 8601
        created_utc = post.get("created_utc", 0)
        if created_utc:
            created_iso = datetime.fromtimestamp(created_utc, tz=timezone.utc).isoformat()
        else:
            created_iso = ""

        formatted.append({
            "rank": i,
            "subreddit": post.get("subreddit", subreddit),
            "title": post.get("title", "").strip(),
            "score": post.get("score", 0),
            "num_comments": post.get("num_comments", 0),
            "upvote_ratio": post.get("upvote_ratio", 0.0),
            "engagement_score": post.get("engagement_score", 0),
            "author": post.get("author", "[deleted]"),
            "url": post.get("url", ""),
            "permalink": post.get("permalink", ""),
            "selftext": post.get("selftext", ""),
            "flair": post.get("link_flair_text", ""),
            "created_at": created_iso,
        })

# ---------------------------------------------------------------------------
# 3. Salvar JSON formatado
# ---------------------------------------------------------------------------
formatted_path = Path(TMP_DIR) / "formatted_posts.json"
with open(formatted_path, "w", encoding="utf-8") as f:
    json.dump(formatted, f, ensure_ascii=False, indent=2)

print(f"✅ {len(formatted)} posts formatados salvos em {formatted_path}")
log.info(f"{len(formatted)} posts formatados salvos em {formatted_path}")
log.metric("posts_formatados", len(formatted))

# ---------------------------------------------------------------------------
# 3b. Formatar TODOS os posts brutos (para modo "Mais Recentes" no dashboard)
# ---------------------------------------------------------------------------
raw_path = Path(TMP_DIR) / "raw_posts.json"
formatted_all: list[dict] = []

if raw_path.exists():
    with open(raw_path, "r", encoding="utf-8") as f:
        raw_data: dict[str, list[dict]] = json.load(f)

    for subreddit, posts in raw_data.items():
        for post in posts:
            created_utc = post.get("created_utc", 0)
            if created_utc:
                created_iso = datetime.fromtimestamp(created_utc, tz=timezone.utc).isoformat()
            else:
                created_iso = ""

            # Calcular engagement com mesma fórmula
            engagement = (
                post.get("score", 0) * W_SCORE
                + post.get("num_comments", 0) * W_COMMENTS
                + post.get("upvote_ratio", 0.0) * W_RATIO
            )

            formatted_all.append({
                "subreddit": post.get("subreddit", subreddit),
                "title": post.get("title", "").strip(),
                "score": post.get("score", 0),
                "num_comments": post.get("num_comments", 0),
                "upvote_ratio": post.get("upvote_ratio", 0.0),
                "engagement_score": round(engagement, 2),
                "author": post.get("author", "[deleted]"),
                "url": post.get("url", ""),
                "permalink": post.get("permalink", ""),
                "selftext": post.get("selftext", ""),
                "flair": post.get("link_flair_text", ""),
                "created_at": created_iso,
                "created_utc": created_utc,
            })

    all_path = Path(TMP_DIR) / "formatted_all_posts.json"
    with open(all_path, "w", encoding="utf-8") as f:
        json.dump(formatted_all, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(formatted_all)} posts totais formatados salvos em {all_path}")
    log.info(f"{len(formatted_all)} posts totais formatados salvos em {all_path}")
    log.metric("posts_totais_formatados", len(formatted_all))
else:
    print("⚠️ raw_posts.json não encontrado — pulando formatted_all_posts.json")
    log.warn("raw_posts.json não encontrado. formatted_all_posts.json não gerado.")
# 4. Gerar resumo Markdown
# ---------------------------------------------------------------------------
summary_lines: list[str] = []
summary_lines.append("# 🏆 Top 5 Posts por Engajamento — Reddit\n")
summary_lines.append(f"**Gerado em:** {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n")
summary_lines.append("**Método:** 100 posts recentes → filtro última semana → ranking por engajamento\n")
summary_lines.append("**Fórmula:** `engagement = (score × 1.0) + (comentários × 2.0) + (upvote_ratio × 50)`\n")

# Agrupar por subreddit
subreddits_seen: dict[str, list[dict]] = {}
for post in formatted:
    sub = post["subreddit"]
    if sub not in subreddits_seen:
        subreddits_seen[sub] = []
    subreddits_seen[sub].append(post)

for sub, posts in subreddits_seen.items():
    summary_lines.append(f"\n---\n\n## r/{sub}\n")
    summary_lines.append("| # | Título | 🔥 Engajamento | ⬆️ Score | 💬 Comentários | 📊 Ratio | Autor |")
    summary_lines.append("|---|--------|----------------|---------|----------------|---------|-------|")
    for post in posts:
        title_short = post["title"][:70] + ("..." if len(post["title"]) > 70 else "")
        link = f"[{title_short}]({post['permalink']})"
        ratio_pct = f"{post['upvote_ratio'] * 100:.0f}%"
        summary_lines.append(
            f"| {post['rank']} | {link} | **{post['engagement_score']:,.0f}** | "
            f"{post['score']:,} | {post['num_comments']:,} | {ratio_pct} | u/{post['author']} |"
        )

# Adicionar seção de contexto
summary_lines.append("\n---\n")
summary_lines.append("### 📌 Como interpretar o score de engajamento\n")
summary_lines.append("- **Score alto + muitos comentários** = post viral com discussão ativa")
summary_lines.append("- **Score baixo + muitos comentários** = post polêmico ou que pede ajuda")
summary_lines.append("- **Ratio alto (>90%)** = post bem recebido pela comunidade")
summary_lines.append("- **Ratio baixo (<70%)** = post controverso\n")

summary_path = Path(TMP_DIR) / "summary.md"
with open(summary_path, "w", encoding="utf-8") as f:
    f.write("\n".join(summary_lines) + "\n")

print(f"📝 Resumo gerado em {summary_path}")
print("🏁 Formatação concluída!")
log.metric("arquivo_json", str(formatted_path))
log.metric("arquivo_summary", str(summary_path))
log.success(f"{len(formatted)} posts formatados, resumo gerado")
