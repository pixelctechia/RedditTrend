# Diretiva: Buscar Top 10 Posts por Engajamento — Reddit

## Objetivo

Coletar os **100 posts mais recentes** dos subreddits configurados, filtrar os publicados na **última semana**, calcular um **score de engajamento** ponderado e selecionar os **10 posts com maior engajamento** de cada subreddit. O dashboard suporta **dois modos de visualização**: "Top Relevantes" (ranking por engajamento) e "Mais Recentes" (10 posts mais novos com filtros de tempo: dia/semana/mês). Gerar artigos Markdown individuais, dashboard web interativo e exportar para Google Sheets.

## Entradas

| Variável              | Fonte  | Descrição                                                |
|-----------------------|--------|----------------------------------------------------------|
| `TARGET_SUBREDDITS`   | `.env` | Subreddits alvo, separados por vírgula (`n8n,automation`) |
| `FETCH_LIMIT`         | `.env` | Nº de posts recentes a buscar por subreddit (default: 100)|
| `TOP_N`               | `.env` | Nº de top posts a selecionar por subreddit (default: 10)  |
| `PERIOD_DAYS`         | `.env` | Janela de tempo em dias (default: 7 = última semana)       |
| `WEIGHT_SCORE`        | `.env` | Peso dos upvotes no cálculo de engajamento (default: 1.0)  |
| `WEIGHT_COMMENTS`     | `.env` | Peso dos comentários (default: 2.0)                        |
| `WEIGHT_RATIO`        | `.env` | Peso do upvote_ratio (default: 50.0)                       |

## Score de engajamento

A fórmula para ranquear posts por relevância e engajamento é:

```
engagement = (score × WEIGHT_SCORE) + (num_comments × WEIGHT_COMMENTS) + (upvote_ratio × WEIGHT_RATIO)
```

**Racional dos pesos:**
- **Comentários (×2.0):** indicam discussão real — engagement mais profundo que um simples upvote
- **Score (×1.0):** base de popularidade (upvotes - downvotes)
- **Upvote ratio (×50.0):** premia posts com aprovação consistente da comunidade (ex: 0.95 = 95%)

## Ferramentas / Scripts

### Passo 1: Buscar e ranquear posts
**Script:** `execution/fetch_reddit_posts.py`

- Usa endpoints públicos do Reddit (sem autenticação)
- Para cada subreddit em `TARGET_SUBREDDITS`:
  1. Busca até `FETCH_LIMIT` posts do endpoint `/r/{sub}/new` (com paginação)
  2. Filtra apenas os criados nos últimos `PERIOD_DAYS` dias
  3. Calcula `engagement_score` e seleciona os N com maior score
- Salva:
  - `.tmp/raw_posts.json` — todos os posts brutos coletados
  - `.tmp/top_posts.json` — somente os top N selecionados

### Passo 2: Formatar dados
**Script:** `execution/format_posts.py`

- Lê `.tmp/top_posts.json` e `.tmp/raw_posts.json`
- Gera um JSON limpo com os campos:
  - `rank`, `subreddit`, `title`, `score`, `num_comments`, `upvote_ratio`, `engagement_score`, `author`, `url`, `permalink`, `selftext`, `flair`, `created_at`
- Salva em `.tmp/formatted_posts.json` (top N por engajamento)
- Salva em `.tmp/formatted_all_posts.json` (TODOS os posts — para modo "Mais Recentes")
- Gera resumo legível com tabela em `.tmp/summary.md`

### Passo 3: Gerar artigos Markdown
**Script:** `execution/generate_articles.py`

- Lê `.tmp/formatted_posts.json`
- Para cada post, gera um arquivo `.md` com:
  - Frontmatter YAML (metadados completos)
  - Título + ranking + data
  - Resumo automático (primeiras frases)
  - Conteúdo completo do post
  - Tabela de métricas de engajamento + barra visual
  - Seção de créditos atribuindo ao Reddit com link original
- Organiza em pastas por subreddit: `.tmp/articles/{sub}/{slug}.md`
- Gera índice geral: `.tmp/articles/index.md`

### Passo 4: Gerar dashboard web
**Script:** `execution/generate_app.py`

- Lê `.tmp/formatted_posts.json`, `.tmp/formatted_all_posts.json`, `.env` e logs
- Gera app HTML autocontido com:
  - Dashboard com tabs por subreddit e stat cards
  - **Modo "🏆 Top Relevantes"** — ranking por engajamento (padrão)
  - **Modo "🕐 Mais Recentes"** — 10 posts mais novos com filtros de tempo:
    - **24h** — últimas 24 horas
    - **Semana** — últimos 7 dias
    - **Mês** — últimos 30 dias
  - Página Posts (tabela comparativa geral)
  - Página Trends (gráficos de barras CSS)
  - Página Configurações (parâmetros do .env)
  - Página Logs (histórico de execuções)
  - **Botão "➕ Importar Post"** no topbar para buscar posts por URL e adicionar novas comunidades
- Sempre retorna exatamente **10 posts** por subreddit no modo ativo
- Salva em `.tmp/app.html`

### Passo 4b (Opcional): Servidor local
**Script:** `execution/server.py`

- Serve o dashboard em `http://localhost:5050`
- Fornece API para:
  - `GET /api/fetch-post?url=...` — busca dados de um post do Reddit por URL
  - `POST /api/add-community` — adiciona subreddit ao `TARGET_SUBREDDITS` no `.env`
  - `GET /api/communities` — lista comunidades registradas
- Permite importar posts e adicionar comunidades **diretamente pelo dashboard**
- Usa `ThreadingHTTPServer` para requests concorrentes

### Passo 5 (Opcional): Exportar para Google Sheets
**Script:** `execution/export_to_sheets.py`

- Lê `.tmp/formatted_posts.json`
- Insere os dados na planilha configurada em `GOOGLE_SHEET_ID`
- Requer `credentials.json` e `token.json` válidos

## Saídas

| Arquivo                             | Tipo           | Descrição                                    |
|-------------------------------------|----------------|----------------------------------------------|
| `.tmp/raw_posts.json`               | Intermediário  | Todos os posts recentes coletados            |
| `.tmp/top_posts.json`               | Intermediário  | Top N posts por engajamento                  |
| `.tmp/formatted_posts.json`         | Intermediário  | Top N formatados e limpos                    |
| `.tmp/formatted_all_posts.json`     | Intermediário  | TODOS os posts formatados (modo Recentes)    |
| `.tmp/summary.md`                   | Intermediário  | Resumo legível com tabela                    |
| `.tmp/articles/{sub}/{slug}.md`     | Entregável     | Artigo Markdown por post                     |
| `.tmp/articles/index.md`            | Entregável     | Índice geral de artigos                      |
| `.tmp/app.html`                     | Entregável     | Dashboard web interativo                     |
| `.tmp/logs/dashboard.html`          | Entregável     | Dashboard de logs de execução                |
| Google Sheets                       | Entregável     | Planilha atualizada com top posts            |

## Casos de borda

- **Subreddit inexistente/privado:** API retorna 404/403 → logar aviso e pular
- **Menos de 5 posts na janela de tempo:** retornar o que houver, sem erro
- **Rate limit da API:** Reddit ≈60 req/min → respeitar header `X-Ratelimit-Remaining` + delay de 0.5s entre páginas
- **Credenciais inválidas:** mensagem clara e exit
- **Sem internet:** capturar ConnectionError e retornar posts coletados até o momento
- **Posts duplicados entre páginas:** o endpoint `/new` pagina com cursor `after`, sem duplicatas

## Aprendizados

_(Atualizar conforme novos comportamentos forem descobertos)_

- Endpoints públicos do Reddit (`/r/{sub}/new.json`) funcionam sem autenticação OAuth2
- O endpoint `/r/{sub}/new` retorna max 100 posts por request; usar `after` para paginar
- O endpoint `/r/{sub}/top` não serve para o caso de uso — ele ranqueia por score, não por engajamento customizado
- `upvote_ratio` é um float entre 0 e 1 (0.95 = 95% de upvotes)
- User-Agent personalizado evita bloqueios por rate limiting
- `link_flair_text` pode ser útil para categorizar posts (ex: "Question", "Show off", "Help")
- Posts sem `selftext` (links/imagens) recebem aviso no artigo Markdown
- Slugs dos arquivos truncados a 60 chars para evitar problemas no filesystem
- O pipeline completo gera ~20 artigos em menos de 1 segundo
- O modo "Mais Recentes" filtra client-side a partir de `formatted_all_posts.json`, sem necessidade de re-fetch do Reddit
- `formatted_all_posts.json` inclui campo `created_utc` (timestamp Unix) para filtragem precisa por tempo
- O toggle de modo e os filtros de tempo são animados com transições CSS para UX fluida
- Sempre retorna exatamente 10 posts independente do modo selecionado (ou menos se não houver dados suficientes)
- O servidor local (`server.py`) permite buscar posts por URL e adicionar comunidades sem editar código
- Comunidades adicionadas via dashboard são persistidas no `.env` automaticamente
- Ao adicionar comunidade, os posts só aparecem após re-executar o pipeline
- Quando aberto como `file://`, o dashboard consegue buscar posts (CORS), mas precisa do servidor para adicionar comunidades e resolver share links
- URLs do Reddit têm vários formatos: `/r/sub/comments/id/slug/` (post), `/r/sub/s/shortId` (share do app), `redd.it/id` (curto), `/r/sub/` (subreddit — não é post)
- Share links (`/r/sub/s/id`) são redirects que precisam ser resolvidos pelo servidor (seguir redirect) antes de extrair o post
- **CUIDADO COM F-STRINGS PYTHON + JAVASCRIPT:** `\n` em f-strings Python é interpretado como newline literal. Para gerar regex `/\n/g` no JS, usar `\\\\n` (4 backslashes). Para `new RegExp('\\w')`, cada `\` extra precisa de `\\` no f-string. Sempre verificar o HTML de saída com `cat -A` para confirmar contagem de backslashes

## Pipeline Completo

```bash
# 1. Buscar posts do Reddit
python execution/fetch_reddit_posts.py

# 2. Formatar dados
python execution/format_posts.py

# 3. Gerar artigos Markdown
python execution/generate_articles.py

# 4. Gerar dashboard web
python execution/generate_app.py

# 5. (Opcional) Servir via servidor local (habilita import de posts)
python execution/server.py

# 6. (Opcional) Ver logs
python execution/view_logs.py
```
