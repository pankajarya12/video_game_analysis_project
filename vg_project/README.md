# 🎮 Video Game Sales & Engagement Analysis

Full Python project: **data cleaning → SQLite → Streamlit dashboard → Jupyter EDA**.

## Features

| Area | Details |
|------|---------|
| 🔐 **Authentication**  | Username/password login (bcrypt). Default: `admin/admin123`, `analyst/analyst123` |
| 🎨 **Theme & Layout**  | Dark theme, multi-page sidebar, polished CSS, custom metric cards |
| 📊 **Overview**         | KPIs, top-10 games, yearly trend, genre share |
| 🌍 **Regional Sales**   | NA / EU / JP / Other breakdowns + heatmaps |
| 🎮 **Drill-down**       | Platform → Genre → Publisher → Game detail |
| 🤖 **AI Insights**      | Statistical highlights + optional LLM narrative (Lovable AI / OpenAI) |
| 🧪 **Data-Quality**     | Validation score, null report, dtype check, duplicates, FK integrity |
| 📥 **Exports**          | Cleaned CSV, SQLite `.db`, multi-sheet Excel, one-page PDF |
| 🐳 **Docker**           | One-command run via `docker compose up` |
| 📓 **Jupyter notebook** | `notebooks/eda.ipynb` with 30 analytical questions |

## Quick start (local)

```bash
pip install -r requirements.txt

# (optional) drop your real CSVs into data/
#   data/games.csv
#   data/vgsales.csv

python utils/data_loader.py          # builds db/videogames.db
streamlit run app.py                 # opens at http://localhost:8501
```

If no CSVs are present, the loader falls back to a **synthetic sample** so the
app runs out of the box.

## Quick start (Docker)

```bash
docker compose up --build
# → http://localhost:8501
```

Mounted volumes:
- `./data` — drop `games.csv` and `vgsales.csv` here
- `./db`   — SQLite DB persisted on host
- `./config` — `users.yaml` persisted on host

## Optional: AI narrative

Set one of these env vars before launching to enable the LLM summary on the
**AI Insights** page:

```bash
export LOVABLE_API_KEY=...   # preferred
# or
export OPENAI_API_KEY=...
```

## Project structure

```
.
├── app.py                  # Streamlit entry (login + landing)
├── pages/                  # multi-page dashboard
├── utils/
│   ├── data_loader.py      # load → clean → SQLite
│   ├── validation.py       # data-quality report
│   ├── auth.py             # bcrypt login
│   ├── insights.py         # stat + LLM insights
│   └── reports.py          # PDF + Excel export
├── sql/schema.sql          # normalized schema
├── db/videogames.db        # generated SQLite database
├── notebooks/eda.ipynb     # 30-question Jupyter EDA
├── data/                   # drop CSVs here
├── config/users.yaml       # auto-seeded users
├── .streamlit/config.toml  # dark theme
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Code remarks

- **Auth**: `utils/auth.py` seeds `config/users.yaml` on first run with bcrypt-hashed passwords. Change defaults before deploying.
- **DB build**: `utils/data_loader.py` runs schema, deduplicates dimensions (platforms / genres / publishers), then inserts `games` and `sales` with FKs. A `(name, platform)` lookup links `sales.game_id → games.game_id`.
- **Validation**: `utils/validation.py` returns a 0-100 score plus per-column null/dtype reports — surfaced on the *Data Quality* page.
- **Insights**: `utils/insights.py` always provides statistical bullets; LLM narrative is opt-in and fails soft.
- **Exports**: PDF is generated with `fpdf2` (no headless browser needed → Docker-friendly); Excel uses `openpyxl` with multiple sheets.
- **Docker**: image is `python:3.11-slim`, builds the SQLite DB at image-build time so the container is ready to serve immediately.
