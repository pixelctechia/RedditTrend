# 🚀 Comandos — RedditPulse

Guia rápido com os comandos para rodar o projeto localmente.

---

## 1. Ativar o ambiente virtual

```bash
cd ~/apps/N8N\ fluxos/top_5_post_reddit
source .venv/bin/activate
```

> Após ativar, você verá `(.venv)` no início do terminal.

---

## 2. Instalar dependências (apenas na primeira vez)

```bash
pip install -r requirements.txt
```

---

## 3. Rodar o pipeline completo (buscar posts + gerar dashboard)

```bash
python execution/fetch_reddit_posts.py
python execution/format_posts.py
python execution/generate_app.py
```

> O `generate_app.py` já **inicia o servidor automaticamente** e abre o dashboard em `http://localhost:5050`.

---

## 4. Rodar apenas o servidor (se o dashboard já foi gerado)

```bash
python execution/server.py
```

> Acesse: **http://localhost:5050**

---

## 5. Comando único (pipeline + servidor + dashboard)

```bash
source .venv/bin/activate && \
python execution/fetch_reddit_posts.py && \
python execution/format_posts.py && \
python execution/generate_app.py
```

Cole esse bloco inteiro no terminal para executar tudo de uma vez.

---

## 📋 Resumo rápido

| Ação                        | Comando                                  |
|-----------------------------|------------------------------------------|
| Ativar ambiente virtual     | `source .venv/bin/activate`              |
| Buscar posts do Reddit      | `python execution/fetch_reddit_posts.py` |
| Formatar dados              | `python execution/format_posts.py`       |
| Gerar dashboard + servidor  | `python execution/generate_app.py`       |
| Apenas o servidor           | `python execution/server.py`             |
| Abrir no navegador          | http://localhost:5050                     |
