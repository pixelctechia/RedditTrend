"""
fetch_reddit_posts.py — Busca os 100 posts mais recentes de cada subreddit
usando a API pública do Reddit (sem autenticação), filtra pela última semana,
calcula score de engajamento e seleciona os top 5.

Uso:
    python execution/fetch_reddit_posts.py

SEM CHAVES DE API — usa endpoints públicos: reddit.com/r/{sub}/new.json

Entradas (.env):
    - TARGET_SUBREDDITS  (ex: "n8n,automation")
    - FETCH_LIMIT        (ex: 100)
    - TOP_N              (ex: 5)
    - PERIOD_DAYS        (ex: 7)
    - WEIGHT_SCORE, WEIGHT_COMMENTS, WEIGHT_RATIO
    - TMP_DIR

Saídas:
    - .tmp/raw_posts.json       → todos os posts recentes coletados
    - .tmp/top_posts.json       → top N por engajamento de cada subreddit
"""

import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

# Adicionar diretório execution ao path para importar logger
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from logger import AutomationLogger

# ---------------------------------------------------------------------------
# 1. Carregar variáveis de ambiente
# ---------------------------------------------------------------------------
load_dotenv()

TARGET_SUBREDDITS = os.getenv("TARGET_SUBREDDITS", "n8n,automation")
FETCH_LIMIT = int(os.getenv("FETCH_LIMIT", "100"))
TOP_N = int(os.getenv("TOP_N", "10"))
PERIOD_DAYS = int(os.getenv("PERIOD_DAYS", "7"))
TMP_DIR = os.getenv("TMP_DIR", ".tmp")

# Pesos do score de engajamento
W_SCORE = float(os.getenv("WEIGHT_SCORE", "1.0"))
W_COMMENTS = float(os.getenv("WEIGHT_COMMENTS", "2.0"))
W_RATIO = float(os.getenv("WEIGHT_RATIO", "50.0"))

# User-Agent descritivo para não ser bloqueado pelo Reddit
USER_AGENT = "Mozilla/5.0 (compatible; top5bot/1.0; Python script for educational purposes)"

# ---------------------------------------------------------------------------
# 2. Garantir diretório temporário
# ---------------------------------------------------------------------------
Path(TMP_DIR).mkdir(parents=True, exist_ok=True)


def fetch_posts_from_endpoint(subreddit: str, category: str, limit: int) -> list[dict]:
    """
    Busca posts de uma categoria específica (new, hot, top, rising).
    """
    base_url = f"https://www.reddit.com/r/{subreddit}/{category}.json"
    headers = {"User-Agent": USER_AGENT}
    all_posts = []
    
    params = {"limit": min(100, limit), "raw_json": 1}
    if category == "top":
        params["t"] = "week"  # Top da semana

    try:
        resp = requests.get(base_url, headers=headers, params=params, timeout=15)
    except Exception as e:
        print(f"   ❌ Erro conex ({category}): {e}")
        return []

    if resp.status_code != 200:
        print(f"   ⚠️ Erro {resp.status_code} em r/{subreddit}/{category}")
        return []

    data = resp.json().get("data", {})
    children = data.get("children", [])

    for child in children:
        d = child.get("data", {})
        all_posts.append({
            "id": d.get("id", ""),
            "subreddit": d.get("subreddit", subreddit),
            "title": d.get("title", ""),
            "score": d.get("score", 0),
            "num_comments": d.get("num_comments", 0),
            "upvote_ratio": d.get("upvote_ratio", 0.0),
            "author": d.get("author", "[deleted]"),
            "url": d.get("url", ""),
            "created_utc": d.get("created_utc", 0),
            "permalink": f"https://reddit.com{d.get('permalink', '')}",
            "selftext": d.get("selftext", "")[:500],
            "link_flair_text": d.get("link_flair_text", ""),
            "category_source": category # Marcamos a origem
        })
    
    print(f"   📄 {category}: +{len(all_posts)} posts")
    time.sleep(1) # Respectful delay
    return all_posts

def fetch_all_categories(subreddit: str, total_limit: int) -> list[dict]:
    """Busca posts de todas as categorias e deduplica."""
    categories = ["new", "hot", "top", "rising"]
    # Divide o limite entre as categorias, mas garante um mínimo
    limit_per_cat = max(25, total_limit // len(categories))
    
    deduplicated = {}
    
    print(f"📡 Buscando posts de r/{subreddit} (new, hot, top, rising)...")
    
    for cat in categories:
        posts = fetch_posts_from_endpoint(subreddit, cat, limit_per_cat)
        for p in posts:
            if p["id"] not in deduplicated:
                deduplicated[p["id"]] = p
            else:
                # Se já existe, podemos atualizar o score se for mais recente (opcional)
                pass
                
    results = list(deduplicated.values())
    print(f"   ✅ Total único: {len(results)} posts coletados de r/{subreddit}")
    return results


# ---------------------------------------------------------------------------
# 4. Filtrar posts pela janela de tempo
# ---------------------------------------------------------------------------
def filter_by_period(posts: list[dict], period_days: int) -> list[dict]:
    """Filtra posts criados dentro dos últimos `period_days` dias."""
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=period_days)
    cutoff_ts = cutoff.timestamp()
    return [p for p in posts if p.get("created_utc", 0) >= cutoff_ts]


# ---------------------------------------------------------------------------
# 5. Calcular score de engajamento e ranquear
# ---------------------------------------------------------------------------
def calculate_engagement(post: dict) -> float:
    """
    engagement = (score × W_SCORE) + (num_comments × W_COMMENTS) + (upvote_ratio × W_RATIO)
    """
    return (
        post.get("score", 0) * W_SCORE
        + post.get("num_comments", 0) * W_COMMENTS
        + post.get("upvote_ratio", 0.0) * W_RATIO
    )


def rank_top_posts(posts: list[dict], top_n: int) -> list[dict]:
    """Ranqueia posts por engajamento e retorna os top N."""
    for post in posts:
        post["engagement_score"] = round(calculate_engagement(post), 2)
    posts.sort(key=lambda x: x["engagement_score"], reverse=True)
    return posts[:top_n]


# ---------------------------------------------------------------------------
# 6. Main
# ---------------------------------------------------------------------------
def main():
    log = AutomationLogger("fetch_reddit_posts")

    subreddits = [s.strip() for s in TARGET_SUBREDDITS.split(",") if s.strip()]
    if not subreddits:
        log.error("Nenhum subreddit configurado em TARGET_SUBREDDITS.")
        sys.exit(1)

    log.info(f"Subreddits alvo: {', '.join(f'r/{s}' for s in subreddits)}")
    log.info(f"Config: fetch={FETCH_LIMIT}, top_n={TOP_N}, dias={PERIOD_DAYS}")
    log.info(f"Pesos: score={W_SCORE}, comments={W_COMMENTS}, ratio={W_RATIO}")

    print("=" * 60)
    print("🔍 Reddit Top Posts — Sem API Key (endpoint público)")
    print("=" * 60)
    print(f"🎯 Subreddits: {', '.join(f'r/{s}' for s in subreddits)}")
    print(f"📦 Posts a buscar por sub: {FETCH_LIMIT}")
    print(f"📅 Janela de tempo: últimos {PERIOD_DAYS} dias")
    print(f"🏆 Top N por sub: {TOP_N}")
    print(f"⚖️  Pesos: score={W_SCORE}, comments={W_COMMENTS}, ratio={W_RATIO}")
    print("=" * 60 + "\n")

    all_raw: dict[str, list[dict]] = {}
    all_top: dict[str, list[dict]] = {}

    try:
        for sub in subreddits:
            # Passo 1: Buscar posts recentes
            log.info(f"Buscando {FETCH_LIMIT} posts de r/{sub}...")
            raw_posts = fetch_all_categories(sub, total_limit=FETCH_LIMIT)
            all_raw[sub] = raw_posts

            if not raw_posts:
                log.warn(f"Nenhum post encontrado em r/{sub}")
                print(f"   ⚠️ Nenhum post encontrado em r/{sub}.\n")
                all_top[sub] = []
                continue

            log.info(f"r/{sub}: {len(raw_posts)} posts coletados")

            # Passo 2: Filtrar pela janela de tempo
            weekly_posts = filter_by_period(raw_posts, PERIOD_DAYS)
            log.info(f"r/{sub}: {len(weekly_posts)} posts na última semana")
            print(f"   📅 {len(weekly_posts)} posts na última semana (de {len(raw_posts)} coletados)")

            if not weekly_posts:
                log.warn(f"Nenhum post da última semana em r/{sub}")
                print(f"   ⚠️ Nenhum post da última semana em r/{sub}.\n")
                all_top[sub] = []
                continue

            # Passo 3: Ranquear por engajamento
            top_posts = rank_top_posts(weekly_posts, TOP_N)
            all_top[sub] = top_posts

            log.info(f"r/{sub}: Top {len(top_posts)} selecionados")
            for i, p in enumerate(top_posts, 1):
                log.info(f"  r/{sub} #{i}: [{p['engagement_score']:.0f}] {p['title'][:80]}")

            print(f"   🏆 Top {len(top_posts)} por engajamento:")
            for i, p in enumerate(top_posts, 1):
                print(f"      {i}. [{p['engagement_score']:.0f}] {p['title'][:70]}")
            print()

        # Salvar resultado bruto
        raw_path = Path(TMP_DIR) / "raw_posts.json"
        with open(raw_path, "w", encoding="utf-8") as f:
            json.dump(all_raw, f, ensure_ascii=False, indent=2)

        # Salvar top posts selecionados
        top_path = Path(TMP_DIR) / "top_posts.json"
        with open(top_path, "w", encoding="utf-8") as f:
            json.dump(all_top, f, ensure_ascii=False, indent=2)

        total_raw = sum(len(v) for v in all_raw.values())
        total_top = sum(len(v) for v in all_top.values())

        # Métricas finais
        log.metric("subreddits", len(subreddits))
        log.metric("posts_coletados", total_raw)
        log.metric("posts_na_semana", sum(len(filter_by_period(v, PERIOD_DAYS)) for v in all_raw.values()))
        log.metric("top_posts_selecionados", total_top)
        log.metric("subreddits_alvo", ", ".join(f"r/{s}" for s in subreddits))

        print("=" * 60)
        print(f"💾 {total_raw} posts brutos → {raw_path}")
        print(f"🏆 {total_top} top posts  → {top_path}")
        print("=" * 60)
        print("🏁 Concluído! Agora execute: python execution/format_posts.py")

        log.success(f"{total_raw} posts coletados, {total_top} top posts selecionados")

    except Exception as e:
        log.error(f"Erro inesperado: {str(e)}", exception=e)
        raise


if __name__ == "__main__":
    main()
