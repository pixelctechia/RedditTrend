"""
server.py — Servidor local para o dashboard Reddit Top Posts.

Serve o dashboard (app.html) e fornece API para importar posts do Reddit
e gerenciar comunidades sem intervenção manual no código.

Uso:
    python execution/server.py

Endpoints:
    GET  /                           → Serve app.html (dashboard)
    GET  /api/fetch-post?url=<url>   → Busca dados de um post do Reddit por URL
    POST /api/add-community          → Adiciona subreddit ao TARGET_SUBREDDITS no .env
    GET  /api/communities            → Lista comunidades registradas

Abre automaticamente http://localhost:5050 no navegador.
"""

import http.server
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------
load_dotenv()
TMP_DIR = os.getenv("TMP_DIR", ".tmp")
PORT = int(os.getenv("SERVER_PORT", "5050"))

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)

USER_AGENT = (
    "Mozilla/5.0 (compatible; top5bot/1.0; "
    "Python script for educational purposes)"
)

# ---------------------------------------------------------------------------
# Funções utilitárias
# ---------------------------------------------------------------------------

def parse_reddit_url(url: str) -> dict | None:
    """
    Extrai subreddit e post_id de uma URL do Reddit.

    Suporta:
      - https://www.reddit.com/r/{sub}/comments/{id}/{slug}/
      - https://old.reddit.com/r/{sub}/comments/{id}/{slug}/
      - https://reddit.com/r/{sub}/comments/{id}/
      - https://redd.it/{id}  (link curto — sem subreddit)
      - https://www.reddit.com/r/{sub}/s/{shareId}  (share link do app)
    """
    patterns = [
        # Post URL completa (com /comments/)
        (r"(?:https?://)?(?:www\.|old\.)?reddit\.com/r/(\w+)/comments/(\w+)", "post"),
        # Share link do app Reddit (/r/sub/s/shortId)
        (r"(?:https?://)?(?:www\.|old\.)?reddit\.com/r/(\w+)/s/(\w+)", "share"),
        # Link curto redd.it
        (r"(?:https?://)?redd\.it/(\w+)", "short"),
    ]
    for pattern, kind in patterns:
        m = re.search(pattern, url)
        if m:
            groups = m.groups()
            if kind == "post":
                return {"subreddit": groups[0], "post_id": groups[1], "type": "post"}
            elif kind == "share":
                return {"subreddit": groups[0], "share_id": groups[1], "type": "share"}
            elif kind == "short":
                return {"subreddit": None, "post_id": groups[0], "type": "short"}
    return None


def is_subreddit_only_url(url: str) -> bool:
    """Verifica se a URL é apenas de subreddit (sem post)."""
    return bool(re.search(
        r"(?:https?://)?(?:www\.|old\.)?reddit\.com/r/\w+/?$", url.strip()
    ))


def resolve_share_url(url: str) -> str | None:
    """Resolve um share link do Reddit seguindo o redirect."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    req.method = "HEAD"
    try:
        # Seguir redirects manualmente para pegar a URL final
        opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler)
        with opener.open(req, timeout=10) as resp:
            return resp.url
    except Exception:
        # Fallback: tentar com GET
        try:
            req2 = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req2, timeout=10) as resp:
                return resp.url
        except Exception:
            return None


def fetch_reddit_post(url: str) -> dict:
    """Busca dados de um post do Reddit pela URL pública."""

    # Verificar se é apenas URL de subreddit
    if is_subreddit_only_url(url):
        return {
            "error": "Esta é uma URL de subreddit, não de post. "
            "Cole a URL de um post específico (deve conter /comments/ ou /s/)."
        }

    parsed = parse_reddit_url(url)
    if not parsed:
        return {
            "error": "URL inválida. Formatos aceitos:\n"
            "• https://reddit.com/r/sub/comments/id/...\n"
            "• https://reddit.com/r/sub/s/shareId\n"
            "• https://redd.it/id"
        }

    # Se for share link, resolver o redirect primeiro
    if parsed.get("type") == "share":
        resolved = resolve_share_url(url.strip())
        if resolved:
            re_parsed = parse_reddit_url(resolved)
            if re_parsed and re_parsed.get("type") == "post":
                parsed = re_parsed
            else:
                # Tentar extrair direto da URL resolvida
                return fetch_reddit_post(resolved)
        else:
            return {"error": "Não foi possível resolver o share link. Tente a URL completa do post."}

    post_id = parsed.get("post_id")
    sub = parsed.get("subreddit")

    if not post_id:
        return {"error": "Não foi possível extrair o ID do post da URL."}

    if sub:
        api_url = f"https://www.reddit.com/r/{sub}/comments/{post_id}.json"
    else:
        api_url = f"https://www.reddit.com/comments/{post_id}.json"

    req = urllib.request.Request(
        api_url,
        headers={"User-Agent": USER_AGENT},
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
            data = json.loads(raw)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"error": "Post não encontrado (404)."}
        if e.code == 403:
            return {"error": "Post é privado ou restrito (403)."}
        return {"error": f"Erro HTTP {e.code} ao buscar post."}
    except urllib.error.URLError as e:
        return {"error": f"Erro de conexão: {e.reason}"}
    except Exception as e:
        return {"error": f"Erro inesperado: {str(e)}"}

    # Resposta do Reddit para post: [listing_post, listing_comments]
    if not isinstance(data, list) or len(data) == 0:
        return {"error": "Resposta inesperada do Reddit."}

    try:
        post_data = data[0]["data"]["children"][0]["data"]
    except (KeyError, IndexError):
        return {"error": "Formato de resposta inesperado."}

    subreddit_name = post_data.get("subreddit", sub or "")
    communities = get_communities()
    is_tracked = subreddit_name.lower() in [c.lower() for c in communities]

    return {
        "success": True,
        "post": {
            "subreddit": subreddit_name,
            "title": post_data.get("title", ""),
            "score": post_data.get("score", 0),
            "num_comments": post_data.get("num_comments", 0),
            "upvote_ratio": post_data.get("upvote_ratio", 0.0),
            "author": post_data.get("author", "[deleted]"),
            "selftext": (post_data.get("selftext", "") or "")[:500],
            "url": post_data.get("url", ""),
            "permalink": f"https://reddit.com{post_data.get('permalink', '')}",
            "created_utc": post_data.get("created_utc", 0),
            "link_flair_text": post_data.get("link_flair_text", ""),
            "subreddit_subscribers": post_data.get("subreddit_subscribers", 0),
        },
        "community": {
            "name": subreddit_name,
            "is_tracked": is_tracked,
            "subscribers": post_data.get("subreddit_subscribers", 0),
        },
    }


def get_communities() -> list[str]:
    """Lê comunidades atuais do arquivo .env."""
    # Re-ler .env a cada chamada para pegar atualizações
    load_dotenv(override=True)
    target = os.getenv("TARGET_SUBREDDITS", "")
    return [s.strip() for s in target.split(",") if s.strip()]


def add_community(name: str) -> dict:
    """Adiciona uma comunidade ao TARGET_SUBREDDITS no .env."""
    communities = get_communities()
    name_clean = name.strip()

    # Verificar se já existe (case-insensitive)
    if name_clean.lower() in [c.lower() for c in communities]:
        return {
            "error": f"r/{name_clean} já está registrada no sistema.",
            "exists": True,
            "communities": communities,
        }

    # Ler .env
    env_path = Path(PROJECT_DIR) / ".env"
    if not env_path.exists():
        return {"error": "Arquivo .env não encontrado."}

    content = env_path.read_text(encoding="utf-8")

    # Encontrar e atualizar linha TARGET_SUBREDDITS
    pattern = r"(TARGET_SUBREDDITS=)(.*)"
    match = re.search(pattern, content)
    if match:
        current_value = match.group(2).strip()
        new_value = f"{current_value},{name_clean}" if current_value else name_clean
        content = re.sub(pattern, f"TARGET_SUBREDDITS={new_value}", content)
    else:
        # Linha não existe — adicionar
        all_subs = ",".join(communities + [name_clean])
        content += f"\nTARGET_SUBREDDITS={all_subs}\n"

    env_path.write_text(content, encoding="utf-8")

    # Atualizar env em memória
    os.environ["TARGET_SUBREDDITS"] = ",".join(
        get_communities()  # re-ler para confirmar
    )
    # Re-read para retornar a lista atualizada
    updated = get_communities()
    if name_clean.lower() not in [c.lower() for c in updated]:
        # Fallback: re-ler forçando
        load_dotenv(override=True)
        updated = get_communities()

    return {
        "success": True,
        "message": f"✅ r/{name_clean} adicionada ao sistema!",
        "communities": updated,
    }


# ---------------------------------------------------------------------------
# HTTP Handler
# ---------------------------------------------------------------------------

class DashboardHandler(http.server.BaseHTTPRequestHandler):
    """Handler HTTP para o dashboard com API."""

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Servir dashboard
        if path in ("/", "/index.html"):
            app_path = Path(PROJECT_DIR) / TMP_DIR / "app.html"
            if app_path.exists():
                self._send_html(app_path.read_text(encoding="utf-8"))
            else:
                self._send_json(
                    {"error": "app.html não encontrado. Execute o pipeline primeiro."},
                    status=404,
                )
            return

        # API: Buscar post
        if path == "/api/fetch-post":
            url = query.get("url", [""])[0]
            if not url:
                self._send_json({"error": "Parâmetro 'url' é obrigatório."})
            else:
                result = fetch_reddit_post(url)
                self._send_json(result)
            return

        # API: Listar comunidades
        if path == "/api/communities":
            self._send_json({"communities": get_communities()})
            return

        self._send_json({"error": "Rota não encontrada."}, status=404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/add-community":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self._send_json({"error": "JSON inválido."})
                return

            name = data.get("name", "").strip()
            if not name:
                self._send_json({"error": "Nome da comunidade é obrigatório."})
                return

            # Validar: só letras, números e underscore
            if not re.match(r"^\w+$", name):
                self._send_json(
                    {"error": "Nome inválido. Use apenas letras, números e _."}
                )
                return

            result = add_community(name)
            self._send_json(result)
            return

        self._send_json({"error": "Rota não encontrada."}, status=404)

    def do_OPTIONS(self):
        """Suporte a CORS preflight."""
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    # --- Helpers ---

    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str):
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, format, *args):
        print(f"  🌐 {self.address_string()} — {format % args}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    from http.server import ThreadingHTTPServer

    server = ThreadingHTTPServer(("", PORT), DashboardHandler)

    print("=" * 60)
    print(f"🚀 Dashboard Server — http://localhost:{PORT}")
    print(f"📊 Servindo: {Path(PROJECT_DIR) / TMP_DIR / 'app.html'}")
    print("=" * 60)
    print()
    print("  Endpoints:")
    print(f"    📊 Dashboard .............. http://localhost:{PORT}/")
    print(f"    🔍 Buscar post ............ GET  /api/fetch-post?url=...")
    print(f"    ➕ Adicionar comunidade .... POST /api/add-community")
    print(f"    📋 Listar comunidades ...... GET  /api/communities")
    print()
    print("  Ctrl+C para parar\n")

    try:
        webbrowser.open(f"http://localhost:{PORT}")
    except Exception:
        pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Servidor encerrado.")
        server.server_close()


if __name__ == "__main__":
    main()
