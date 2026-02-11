"""
export_to_sheets.py — Exporta os posts formatados para uma Google Sheet.

Uso:
    python execution/export_to_sheets.py

Entradas:
    - .tmp/formatted_posts.json (gerado por format_posts.py)
    - .env: GOOGLE_SHEET_ID, GOOGLE_SHEET_NAME
    - credentials.json (OAuth2 do Google)
    - token.json (gerado após primeiro login)

Saídas:
    - Planilha Google Sheets atualizada com os top posts
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

TMP_DIR = os.getenv("TMP_DIR", ".tmp")
SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "Top5Reddit")

# ---------------------------------------------------------------------------
# 1. Validações
# ---------------------------------------------------------------------------
if not SHEET_ID:
    print("❌ GOOGLE_SHEET_ID não configurado no .env")
    print("   Este passo é opcional. Os dados já estão em .tmp/formatted_posts.json")
    sys.exit(1)

formatted_path = Path(TMP_DIR) / "formatted_posts.json"
if not formatted_path.exists():
    print(f"❌ Arquivo não encontrado: {formatted_path}")
    print("   Execute primeiro: python execution/format_posts.py")
    sys.exit(1)

# ---------------------------------------------------------------------------
# 2. Importar Google Sheets API (tardio para não quebrar se não for usar)
# ---------------------------------------------------------------------------
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
except ImportError:
    print("❌ Bibliotecas do Google não instaladas.")
    print("   Instale com: pip install google-auth google-auth-oauthlib google-api-python-client")
    sys.exit(1)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# ---------------------------------------------------------------------------
# 3. Autenticação Google
# ---------------------------------------------------------------------------
def get_google_creds():
    """Autentica com Google OAuth2, usando token.json se disponível."""
    creds = None
    token_path = Path("token.json")
    creds_path = Path("credentials.json")

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not creds_path.exists():
                print("❌ credentials.json não encontrado na raiz do projeto.")
                print("   Baixe em: https://console.cloud.google.com/apis/credentials")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as f:
            f.write(creds.to_json())

    return creds

# ---------------------------------------------------------------------------
# 4. Exportar para a planilha
# ---------------------------------------------------------------------------
def main():
    # Carregar dados
    with open(formatted_path, "r", encoding="utf-8") as f:
        posts: list[dict] = json.load(f)

    if not posts:
        print("⚠️ Nenhum post para exportar.")
        return

    print(f"📊 Exportando {len(posts)} posts para Google Sheets...")

    creds = get_google_creds()
    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()

    # Cabeçalho
    headers = ["#", "Subreddit", "Título", "🔥 Engajamento", "⬆️ Score", "💬 Comentários",
               "📊 Ratio", "Flair", "Autor", "URL", "Permalink", "Criado em"]
    rows = [headers]

    for post in posts:
        rows.append([
            post.get("rank", ""),
            post.get("subreddit", ""),
            post.get("title", ""),
            post.get("engagement_score", 0),
            post.get("score", 0),
            post.get("num_comments", 0),
            f"{post.get('upvote_ratio', 0) * 100:.0f}%",
            post.get("flair", ""),
            post.get("author", ""),
            post.get("url", ""),
            post.get("permalink", ""),
            post.get("created_at", ""),
        ])

    # Limpar aba e inserir dados
    range_name = f"{SHEET_NAME}!A1"

    # Limpar conteúdo existente
    sheet.values().clear(
        spreadsheetId=SHEET_ID,
        range=SHEET_NAME,
    ).execute()

    # Inserir novos dados
    sheet.values().update(
        spreadsheetId=SHEET_ID,
        range=range_name,
        valueInputOption="USER_ENTERED",
        body={"values": rows},
    ).execute()

    print(f"✅ Dados exportados para a planilha!")
    print(f"   📎 https://docs.google.com/spreadsheets/d/{SHEET_ID}")
    print("🏁 Exportação concluída!")


if __name__ == "__main__":
    main()
