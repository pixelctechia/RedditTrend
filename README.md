<p align="center">
  <img src="assets/banner.png" alt="RedditPulse Banner" width="100%">
</p>

<h1 align="center">🔥 RedditPulse</h1>

<p align="center">
  <strong>Top 10 trending Reddit posts per subreddit — ranked by engagement, not just upvotes.</strong>
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-demo">Demo</a> •
  <a href="#-requirements">Requirements</a> •
  <a href="#-installation">Installation</a> •
  <a href="#%EF%B8%8F-configuration">Configuration</a> •
  <a href="#-usage">Usage</a> •
  <a href="#-project-structure">Project Structure</a> •
  <a href="#-roadmap">Roadmap</a> •
  <a href="#-contributing">Contributing</a> •
  <a href="#-license">License</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8+-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Reddit-API-FF4500?logo=reddit&logoColor=white" alt="Reddit API">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/no_auth-public_endpoints-orange" alt="No Auth Required">
</p>

---

## 🌐 Language / Idioma

- **[English](#-english)**
- **[Português (Brasil)](#-português-brasil)**

---

# 🇺🇸 English

## ✨ Features

- 🔥 **Engagement-based ranking** — Custom scoring formula weighing upvotes, comments, and approval ratio
- 📊 **Interactive Dashboard** — Beautiful self-contained HTML dashboard with tabs per subreddit
- 🏆 **Dual view modes** — "Top Relevant" (by engagement) and "Most Recent" (with time filters: 24h / week / month)
- ➕ **Import Posts** — Fetch any Reddit post by URL directly from the dashboard
- 🌐 **Add Communities** — Add new subreddits via the dashboard UI (persisted to `.env`)
- 📈 **Trends & Charts** — CSS-based bar charts for visual comparison
- 📝 **Markdown Articles** — Auto-generated article per post with frontmatter and engagement metrics
- 📋 **Google Sheets Export** — Optional export to Google Sheets
- 🖥️ **Local Server** — Built-in Python server with REST API for community management
- 🔓 **No API keys needed** — Uses Reddit's public endpoints (no OAuth required)

## 🎬 Demo

<p align="center">
  <img src="assets/demo_dashboard.png" alt="Dashboard Demo" width="80%">
</p>

> *Screenshot: Dashboard showing Top 10 posts from multiple subreddits with engagement scores.*
>
> To see it live, run the pipeline and open the dashboard!

## 📋 Requirements

| Requirement | Version |
|---|---|
| Python | 3.8+ |
| pip | latest |
| Internet connection | required |

**Python packages** (installed via `requirements.txt`):

- `requests` ≥ 2.31.0 — HTTP requests to Reddit
- `python-dotenv` ≥ 1.0.0 — Environment variable management

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/pixelctechia/RedditTrend.git
cd RedditTrend
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your subreddits

Edit the `.env` file to add the subreddits you want to track:

```env
TARGET_SUBREDDITS=python,javascript,devops,linux,artificial
```

That's it! No API keys. No OAuth. No tokens. 🎉

## ⚙️ Configuration

All settings are managed via the `.env` file:

| Variable | Default | Description |
|---|---|---|
| `TARGET_SUBREDDITS` | `n8n,automation,Python` | Comma-separated subreddits to monitor |
| `FETCH_LIMIT` | `100` | Number of recent posts to fetch per subreddit |
| `TOP_N` | `10` | Number of top posts to select per subreddit |
| `PERIOD_DAYS` | `7` | Time window in days (7 = last week) |
| `WEIGHT_SCORE` | `1.0` | Weight for upvotes in engagement formula |
| `WEIGHT_COMMENTS` | `2.0` | Weight for comments (deeper engagement) |
| `WEIGHT_RATIO` | `50.0` | Weight for upvote ratio (community approval) |
| `TMP_DIR` | `.tmp` | Directory for intermediate and output files |

### 🧠 Engagement Score Formula

```
engagement = (score × WEIGHT_SCORE) + (num_comments × WEIGHT_COMMENTS) + (upvote_ratio × WEIGHT_RATIO)
```

> Comments are weighted 2× more than upvotes because they indicate deeper engagement.

## 🎯 Usage

### Quick Start — Full Pipeline

Run all steps in sequence:

```bash
# 1. Fetch posts from Reddit
python execution/fetch_reddit_posts.py

# 2. Format and rank data
python execution/format_posts.py

# 3. Generate Markdown articles
python execution/generate_articles.py

# 4. Generate interactive dashboard
python execution/generate_app.py
```

The dashboard will be saved at `.tmp/app.html` — open it directly in your browser!

### 🖥️ Local Server (recommended)

For the full experience with post importing and community management:

```bash
python execution/server.py
```

Then open **http://localhost:5050** in your browser.

**Server API endpoints:**

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the dashboard |
| `GET` | `/api/fetch-post?url=...` | Fetch a Reddit post by URL |
| `POST` | `/api/add-community` | Add a subreddit to `.env` |
| `GET` | `/api/communities` | List tracked subreddits |

### Adding a new subreddit

**Option A — Via `.env` file:**

```env
TARGET_SUBREDDITS=python,javascript,your_new_subreddit
```

Then re-run the pipeline.

**Option B — Via Dashboard UI:**

1. Click the **"➕ Import Post"** button in the top bar
2. Paste a Reddit post URL
3. The subreddit is added automatically

### Example subreddits to try

```
python, javascript, devops, linux, artificial, 
MachineLearning, ChatGPT, ClaudeAI, webdev, reactjs
```

## 📁 Project Structure

```
RedditPulse/
├── .env                          # Configuration (subreddits, weights, limits)
├── .gitignore                    # Git ignore rules
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── assets/
│   └── banner.png                # GitHub banner image
├── directives/
│   └── fetch_top_posts.md        # SOP — Standard Operating Procedure
├── execution/
│   ├── fetch_reddit_posts.py     # Step 1: Fetch + rank posts
│   ├── format_posts.py           # Step 2: Format data
│   ├── generate_articles.py      # Step 3: Generate Markdown articles
│   ├── generate_app.py           # Step 4: Generate HTML dashboard
│   ├── server.py                 # Step 4b: Local server with API
│   ├── export_to_sheets.py       # Step 5: Google Sheets export (optional)
│   ├── view_logs.py              # Utility: View execution logs
│   └── logger.py                 # Utility: Logging system
└── .tmp/                         # Generated output (gitignored)
    ├── raw_posts.json
    ├── top_posts.json
    ├── formatted_posts.json
    ├── formatted_all_posts.json
    ├── summary.md
    ├── app.html                  # ← The dashboard
    ├── articles/
    │   ├── index.md
    │   └── {subreddit}/{slug}.md
    └── logs/
        └── run_history.json
```

## 🗺️ Roadmap

- [x] Fetch top posts by engagement score
- [x] Interactive web dashboard
- [x] Dual mode: Top Relevant / Most Recent
- [x] Import posts by URL
- [x] Add communities via dashboard
- [x] Markdown article generation
- [x] Google Sheets export
- [ ] Email/Slack notifications for high-engagement posts
- [ ] Scheduled execution (cron/systemd)
- [ ] Multi-language dashboard UI
- [ ] Post sentiment analysis
- [ ] RSS feed output
- [ ] Docker support

## 🤝 Contributing

Contributions are welcome! Here's how:

1. **Fork** this repository
2. **Create** a feature branch: `git checkout -b feature/my-feature`
3. **Commit** your changes: `git commit -m "Add: my new feature"`
4. **Push** to the branch: `git push origin feature/my-feature`
5. **Open** a Pull Request

Please ensure your code follows the existing project structure (see `directives/` for the 3-layer architecture pattern).

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This project is **unofficial** and is not affiliated with, endorsed by, or associated with **Reddit, Inc.** in any way. Reddit™ is a registered trademark of Reddit, Inc. This tool uses Reddit's **public endpoints** for educational and personal use. Please respect Reddit's [Terms of Service](https://www.redditinc.com/policies/user-agreement) and [API Terms](https://www.reddit.com/wiki/api-terms/) when using this project. Use responsibly.

---

---

# 🇧🇷 Português (Brasil)

## ✨ Funcionalidades

- 🔥 **Ranking por engajamento** — Fórmula de score customizada pesando upvotes, comentários e taxa de aprovação
- 📊 **Dashboard interativo** — Dashboard HTML autocontido com abas por subreddit
- 🏆 **Dois modos de visualização** — "Top Relevantes" (por engajamento) e "Mais Recentes" (com filtros: 24h / semana / mês)
- ➕ **Importar Posts** — Busque qualquer post do Reddit por URL direto no dashboard
- 🌐 **Adicionar Comunidades** — Adicione novos subreddits pela interface (salvo no `.env`)
- 📈 **Tendências e Gráficos** — Gráficos de barras em CSS para comparação visual
- 📝 **Artigos Markdown** — Artigo gerado automaticamente por post com frontmatter e métricas
- 📋 **Exportação Google Sheets** — Exportação opcional para planilhas Google
- 🖥️ **Servidor Local** — Servidor Python embutido com API REST para gerenciar comunidades
- 🔓 **Sem chaves de API** — Usa endpoints públicos do Reddit (sem OAuth)

## 🎬 Demo

<p align="center">
  <img src="assets/demo_dashboard.png" alt="Demo do Dashboard" width="80%">
</p>

> *Captura de tela: Dashboard mostrando os Top 10 posts de múltiplos subreddits com scores de engajamento.*
>
> Para ver ao vivo, execute o pipeline e abra o dashboard!

## 📋 Requisitos

| Requisito | Versão |
|---|---|
| Python | 3.8+ |
| pip | mais recente |
| Conexão com internet | necessária |

**Pacotes Python** (instalados via `requirements.txt`):

- `requests` ≥ 2.31.0 — Requisições HTTP para o Reddit
- `python-dotenv` ≥ 1.0.0 — Gerenciamento de variáveis de ambiente

## 🚀 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/pixelctechia/RedditTrend.git
cd RedditTrend
```

### 2. Crie um ambiente virtual (recomendado)

```bash
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure seus subreddits

Edite o arquivo `.env` para adicionar os subreddits que deseja acompanhar:

```env
TARGET_SUBREDDITS=python,javascript,devops,linux,artificial
```

Pronto! Sem chaves de API. Sem OAuth. Sem tokens. 🎉

## ⚙️ Configuração

Todas as configurações são gerenciadas pelo arquivo `.env`:

| Variável | Padrão | Descrição |
|---|---|---|
| `TARGET_SUBREDDITS` | `n8n,automation,Python` | Subreddits monitorados, separados por vírgula |
| `FETCH_LIMIT` | `100` | Nº de posts recentes a buscar por subreddit |
| `TOP_N` | `10` | Nº de top posts a selecionar por subreddit |
| `PERIOD_DAYS` | `7` | Janela de tempo em dias (7 = última semana) |
| `WEIGHT_SCORE` | `1.0` | Peso dos upvotes na fórmula de engajamento |
| `WEIGHT_COMMENTS` | `2.0` | Peso dos comentários (engajamento mais profundo) |
| `WEIGHT_RATIO` | `50.0` | Peso do upvote ratio (aprovação da comunidade) |
| `TMP_DIR` | `.tmp` | Diretório para arquivos intermediários e saída |

### 🧠 Fórmula do Score de Engajamento

```
engajamento = (score × WEIGHT_SCORE) + (num_comments × WEIGHT_COMMENTS) + (upvote_ratio × WEIGHT_RATIO)
```

> Comentários têm peso 2× maior que upvotes porque indicam engajamento mais profundo.

## 🎯 Como Usar

### Início Rápido — Pipeline Completa

Execute todos os passos em sequência:

```bash
# 1. Buscar posts do Reddit
python execution/fetch_reddit_posts.py

# 2. Formatar e ranquear dados
python execution/format_posts.py

# 3. Gerar artigos Markdown
python execution/generate_articles.py

# 4. Gerar dashboard interativo
python execution/generate_app.py
```

O dashboard será salvo em `.tmp/app.html` — abra diretamente no navegador!

### 🖥️ Servidor Local (recomendado)

Para a experiência completa com importação de posts e gestão de comunidades:

```bash
python execution/server.py
```

Depois abra **http://localhost:5050** no navegador.

**Endpoints da API do servidor:**

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/` | Serve o dashboard |
| `GET` | `/api/fetch-post?url=...` | Busca um post do Reddit por URL |
| `POST` | `/api/add-community` | Adiciona subreddit ao `.env` |
| `GET` | `/api/communities` | Lista subreddits monitorados |

### Adicionando um novo subreddit

**Opção A — Via arquivo `.env`:**

```env
TARGET_SUBREDDITS=python,javascript,seu_novo_subreddit
```

Depois re-execute a pipeline.

**Opção B — Via interface do Dashboard:**

1. Clique no botão **"➕ Importar Post"** na barra superior
2. Cole a URL de um post do Reddit
3. O subreddit é adicionado automaticamente

### Subreddits de exemplo para testar

```
python, javascript, devops, linux, artificial, 
MachineLearning, ChatGPT, ClaudeAI, webdev, reactjs
```

## 📁 Estrutura do Projeto

```
RedditPulse/
├── .env                          # Configuração (subreddits, pesos, limites)
├── .gitignore                    # Regras de ignorar do Git
├── requirements.txt              # Dependências Python
├── README.md                     # Este arquivo
├── assets/
│   └── banner.png                # Imagem de capa do GitHub
├── directives/
│   └── fetch_top_posts.md        # SOP — Procedimento Operacional Padrão
├── execution/
│   ├── fetch_reddit_posts.py     # Passo 1: Buscar + ranquear posts
│   ├── format_posts.py           # Passo 2: Formatar dados
│   ├── generate_articles.py      # Passo 3: Gerar artigos Markdown
│   ├── generate_app.py           # Passo 4: Gerar dashboard HTML
│   ├── server.py                 # Passo 4b: Servidor local com API
│   ├── export_to_sheets.py       # Passo 5: Exportar Google Sheets (opcional)
│   ├── view_logs.py              # Utilitário: Ver logs de execução
│   └── logger.py                 # Utilitário: Sistema de logging
└── .tmp/                         # Saída gerada (ignorado pelo git)
    ├── raw_posts.json
    ├── top_posts.json
    ├── formatted_posts.json
    ├── formatted_all_posts.json
    ├── summary.md
    ├── app.html                  # ← O dashboard
    ├── articles/
    │   ├── index.md
    │   └── {subreddit}/{slug}.md
    └── logs/
        └── run_history.json
```

## 🗺️ Roadmap

- [x] Buscar top posts por score de engajamento
- [x] Dashboard web interativo
- [x] Modo duplo: Top Relevantes / Mais Recentes
- [x] Importar posts por URL
- [x] Adicionar comunidades via dashboard
- [x] Geração de artigos Markdown
- [x] Exportação para Google Sheets
- [ ] Notificações por email/Slack para posts de alto engajamento
- [ ] Execução agendada (cron/systemd)
- [ ] Interface do dashboard multi-idioma
- [ ] Análise de sentimento dos posts
- [ ] Saída em formato RSS Feed
- [ ] Suporte a Docker

## 🤝 Contribuindo

Contribuições são bem-vindas! Veja como:

1. **Faça um fork** deste repositório
2. **Crie** uma branch: `git checkout -b feature/minha-feature`
3. **Commit** suas alterações: `git commit -m "Add: minha nova feature"`
4. **Push** para a branch: `git push origin feature/minha-feature`
5. **Abra** um Pull Request

Garanta que seu código siga a estrutura existente do projeto (veja `directives/` para o padrão de arquitetura em 3 camadas).

## 📄 Licença

Este projeto é licenciado sob a **Licença MIT** — veja o arquivo [LICENSE](LICENSE) para detalhes.

## ⚠️ Aviso Legal

Este projeto é **não oficial** e não é afiliado, endossado ou associado ao **Reddit, Inc.** de nenhuma forma. Reddit™ é uma marca registrada da Reddit, Inc. Esta ferramenta utiliza **endpoints públicos** do Reddit para uso educacional e pessoal. Por favor, respeite os [Termos de Serviço](https://www.redditinc.com/policies/user-agreement) e os [Termos da API](https://www.reddit.com/wiki/api-terms/) do Reddit ao usar este projeto. Use com responsabilidade.

---

<p align="center">
  Feito com ❤️ por <a href="https://github.com/pixelctechia">pixelctechia</a>
</p>
