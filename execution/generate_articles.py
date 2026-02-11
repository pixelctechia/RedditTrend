"""
generate_articles.py — Gera um arquivo Markdown (.md) para cada post do Reddit.

Cada artigo contém:
  - Frontmatter YAML com metadados
  - Título formatado
  - Resumo (auto-gerado a partir do início do texto)
  - Conteúdo completo do post
  - Métricas de engajamento
  - Seção de créditos / fonte (Reddit)

Uso:
    python execution/generate_articles.py

Entradas:
    - .tmp/formatted_posts.json (gerado por format_posts.py)

Saídas:
    - .tmp/articles/{subreddit}/{slug}.md (1 arquivo por post)
    - .tmp/articles/index.md (índice geral)
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

# Tentar importar o logger (opcional)
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from logger import AutomationLogger
except ImportError:
    AutomationLogger = None

load_dotenv()
TMP_DIR = os.getenv("TMP_DIR", ".tmp")
DATA_FILE = Path(TMP_DIR) / "formatted_posts.json"
ARTICLES_DIR = Path(TMP_DIR) / "articles"


def load_posts() -> list[dict]:
    """Carrega posts formatados."""
    if not DATA_FILE.exists():
        print("❌ Dados não encontrados. Execute o pipeline primeiro:")
        print("   python execution/fetch_reddit_posts.py")
        print("   python execution/format_posts.py")
        sys.exit(1)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def slugify(text: str, max_len: int = 60) -> str:
    """Converte texto em slug para nome de arquivo."""
    text = text.lower().strip()
    # Remove caracteres especiais
    text = re.sub(r"[^\w\s-]", "", text)
    # Espaços → hífens
    text = re.sub(r"[\s_]+", "-", text)
    # Múltiplos hífens → um
    text = re.sub(r"-+", "-", text)
    # Remove hífens nas bordas
    text = text.strip("-")
    return text[:max_len]


def generate_summary(selftext: str, max_sentences: int = 3) -> str:
    """Gera um resumo a partir das primeiras frases do texto do post."""
    if not selftext or not selftext.strip():
        return "_Post sem conteúdo de texto (pode ser um link, imagem ou vídeo)._"

    # Limpa o texto
    clean = selftext.strip()

    # Divide em parágrafos, pega os primeiros
    paragraphs = [p.strip() for p in clean.split("\n") if p.strip()]

    if not paragraphs:
        return "_Post sem conteúdo de texto._"

    # Pega as primeiras frases até atingir max_sentences ou ~300 caracteres
    summary_parts = []
    char_count = 0
    for para in paragraphs:
        if char_count > 300 or len(summary_parts) >= max_sentences:
            break
        summary_parts.append(para)
        char_count += len(para)

    summary = " ".join(summary_parts)

    # Se o resumo é igual ao texto completo, não truncar
    if len(summary) >= len(clean):
        return summary

    # Adiciona reticências se truncou
    if not summary.endswith((".", "!", "?")):
        summary += "..."

    return summary


def format_date_br(iso_date: str) -> str:
    """Formata data ISO para formato legível em pt-BR."""
    try:
        dt = datetime.fromisoformat(iso_date)
        meses = [
            "", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
            "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
        ]
        return f"{dt.day} de {meses[dt.month]} de {dt.year}"
    except (ValueError, TypeError):
        return "Data não disponível"


def format_engagement_bar(score: float, max_score: float) -> str:
    """Cria uma barra visual de engajamento usando caracteres Unicode."""
    if max_score <= 0:
        return "░░░░░░░░░░"
    ratio = min(score / max_score, 1.0)
    filled = round(ratio * 10)
    return "█" * filled + "░" * (10 - filled)


def generate_article_md(post: dict, rank_in_sub: int, max_engagement: float) -> str:
    """Gera o conteúdo Markdown de um artigo individual."""

    title = post.get("title", "Sem título")
    subreddit = post.get("subreddit", "desconhecido")
    author = post.get("author", "[deletado]")
    selftext = post.get("selftext", "")
    score = post.get("score", 0)
    comments = post.get("num_comments", 0)
    ratio = post.get("upvote_ratio", 0)
    engagement = post.get("engagement_score", 0)
    flair = post.get("flair", "")
    permalink = post.get("permalink", post.get("url", ""))
    created_at = post.get("created_at", "")
    date_formatted = format_date_br(created_at)
    eng_bar = format_engagement_bar(engagement, max_engagement)

    # Resumo
    summary = generate_summary(selftext)

    # Conteúdo completo limpo
    full_content = selftext.strip() if selftext else "_Este post não contém texto. Pode ser um link, imagem ou enquete. Acesse o link original para ver o conteúdo completo._"

    # Frontmatter YAML
    flair_line = f'\nflair: "{flair}"' if flair else ""
    frontmatter = f"""---
title: "{title.replace('"', '\\"')}"
subreddit: r/{subreddit}
author: u/{author}
date: "{created_at}"
score: {score}
comments: {comments}
upvote_ratio: {ratio}
engagement_score: {round(engagement)}
rank: {rank_in_sub}
source: Reddit
permalink: "{permalink}"{flair_line}
---"""

    # Corpo do artigo
    article = f"""{frontmatter}

# {title}

> **Ranking #{rank_in_sub}** no r/{subreddit} • Publicado em {date_formatted}

---

## 📋 Resumo

{summary}

---

## 📖 Conteúdo Completo

{full_content}

---

## 📊 Métricas de Engajamento

| Métrica | Valor |
|---------|-------|
| 🔥 **Engajamento** | {round(engagement)} pontos |
| ⬆️ **Upvotes (Score)** | {score} |
| 💬 **Comentários** | {comments} |
| 📊 **Taxa de Aprovação** | {round(ratio * 100)}% |
| 🏷️ **Flair** | {flair if flair else "—"} |

**Nível de Engajamento:** `{eng_bar}` {round(engagement)}/{round(max_engagement)}

---

## 📌 Fonte & Créditos

> 🔴 **Este artigo é baseado em uma publicação do [Reddit](https://reddit.com).**
>
> Todo o conteúdo original pertence ao autor **u/{author}** e à comunidade **r/{subreddit}**.
> Este documento foi gerado automaticamente para fins de análise e referência.
>
> 🔗 **Post original:** [{title}]({permalink})
>
> 📅 **Data da publicação:** {date_formatted}
>
> ⚠️ _Respeite os direitos autorais. Para interagir com o conteúdo, visite o post original no Reddit._

---

<sub>📄 Artigo gerado automaticamente em {datetime.now(tz=timezone.utc).strftime("%d/%m/%Y às %H:%M UTC")} pelo pipeline de automação Reddit Top Posts.</sub>
"""

    return article


def generate_index_md(posts_by_sub: dict[str, list[dict]], generated_files: list[dict]) -> str:
    """Gera o arquivo de índice com links para todos os artigos."""

    now = datetime.now(tz=timezone.utc).strftime("%d/%m/%Y às %H:%M UTC")
    total = sum(len(v) for v in posts_by_sub.values())

    sections = []
    for sub, posts in posts_by_sub.items():
        items = []
        for p in posts:
            rank = p.get("rank", 0)
            title = p.get("title", "Sem título")
            engagement = round(p.get("engagement_score", 0))
            slug = slugify(title)
            items.append(
                f"| {rank} | [{title}](./{sub}/{slug}.md) | "
                f"🔥 {engagement} | ⬆️ {p.get('score', 0)} | 💬 {p.get('num_comments', 0)} |"
            )

        section = f"""### 📂 r/{sub}

| # | Título | Engajamento | Score | Comentários |
|---|--------|-------------|-------|-------------|
{chr(10).join(items)}
"""
        sections.append(section)

    index = f"""---
title: "Índice — Top Posts do Reddit"
generated_at: "{now}"
total_posts: {total}
subreddits: {list(posts_by_sub.keys())}
---

# 📚 Índice de Artigos — Top Posts do Reddit

> 🗓️ Gerado em **{now}**
> 📊 **{total} artigos** de **{len(posts_by_sub)} subreddits**

---

{chr(10).join(sections)}

---

## ℹ️ Sobre

Estes artigos foram gerados automaticamente pelo pipeline **Reddit Top Posts**.
Cada arquivo `.md` contém o título, resumo, conteúdo completo, métricas de engajamento
e créditos com link para o post original no Reddit.

**Pipeline:** `fetch_reddit_posts.py` → `format_posts.py` → `generate_articles.py`

<sub>Gerado automaticamente. Todo conteúdo pertence aos respectivos autores no Reddit.</sub>
"""

    return index


def main():
    # Inicializar logger (se disponível)
    log = AutomationLogger("generate_articles") if AutomationLogger else None

    posts = load_posts()
    if log:
        log.info(f"Carregados {len(posts)} posts formatados")

    # Agrupar por subreddit
    posts_by_sub: dict[str, list[dict]] = {}
    for p in posts:
        sub = p["subreddit"]
        if sub not in posts_by_sub:
            posts_by_sub[sub] = []
        posts_by_sub[sub].append(p)

    # Calcular engajamento máximo para barras visuais
    max_engagement = max((p.get("engagement_score", 0) for p in posts), default=1)

    # Criar diretórios
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    generated_files = []
    total_generated = 0

    for sub, sub_posts in posts_by_sub.items():
        sub_dir = ARTICLES_DIR / sub
        sub_dir.mkdir(parents=True, exist_ok=True)

        for post in sub_posts:
            rank = post.get("rank", 0)
            title = post.get("title", "sem-titulo")
            slug = slugify(title)
            filename = f"{slug}.md"
            filepath = sub_dir / filename

            # Gerar conteúdo do artigo
            article_content = generate_article_md(post, rank, max_engagement)

            # Salvar arquivo
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(article_content)

            generated_files.append({
                "subreddit": sub,
                "rank": rank,
                "title": title,
                "file": str(filepath),
            })
            total_generated += 1

            print(f"  ✅ r/{sub} #{rank}: {filename}")
            if log:
                log.info(f"r/{sub} #{rank}: {filename}")

    # Gerar índice geral
    index_content = generate_index_md(posts_by_sub, generated_files)
    index_path = ARTICLES_DIR / "index.md"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_content)

    print(f"\n{'='*60}")
    print(f"📄 {total_generated} artigos Markdown gerados")
    print(f"📂 Diretório: {ARTICLES_DIR.resolve()}")
    print(f"📚 Índice: {index_path.resolve()}")
    for sub in posts_by_sub:
        count = len(posts_by_sub[sub])
        print(f"   📁 {sub}/ → {count} artigos")
    print(f"{'='*60}")

    if log:
        log.metric("total_artigos", total_generated)
        log.metric("subreddits", len(posts_by_sub))
        log.metric("diretorio", str(ARTICLES_DIR.resolve()))
        log.metric("arquivos", [f["file"] for f in generated_files])
        log.success(f"{total_generated} artigos Markdown gerados em {ARTICLES_DIR}")


if __name__ == "__main__":
    main()
