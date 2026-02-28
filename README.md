# SchemaSense: Natural Language to SQL Analytics Platform

SchemaSense is a production-ready **Natural Language to SQL (NL2SQL)** platform that empowers users to query databases using plain English. It bridges the gap between complex database schemas and business insights by automatically generating, validating, and visualizing SQL queries.

## 🚀 Features

- **English → SQL**: Simply type your question (e.g., "Who are the top 5 artists by sales?") and get valid SQL.
- **Multi-Dialect Support**: Full support for **PostgreSQL**, **MySQL** (with proper backtick quoting), and **SQLite**.
- **Dual-LLM Architecture**: High availability using **OpenRouter (Claude)** as primary and a local **Prem-SQL** model as fallback.
- **Smart Validation**: 3-layer pipeline that rejects nonsense input, validates against your schema, and verifies SQL syntax.
- **Auto-Visualization**: Automatically detects the best chart type (Bar, Line, Pie, Scatter) and renders insights using Plotly.
- **Business Explanations**: Generates plain-English summaries of what the data actually means.
- **Export Ready**: Download your results instantly as CSV.

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Streamlit
- **Database**: Supabase (PostgreSQL) / SQLAlchemy for multi-dialect
- **AI/LLM**: OpenRouter API & Transformers (Local Fallback)
- **Visuals**: Plotly & Altair

## 📋 Project Structure

```text
├── app/
│   ├── main.py             # FastAPI Backend
│   ├── frontend.py         # Streamlit UI
│   ├── llm.py              # AI/LLM Integration Logic
│   ├── services/           # Business Logic (Charts, Schema, Suggestions)
│   └── validators/         # Input & SQL Validation
├── supabase_restore.sql    # Database restoration script
└── requirements.txt        # Project dependencies
```

## ⚙️ Setup Instructions

### 1. Prerequisites
- Python 3.12 (Recommended)
- Supabase Account (for the demo database)

### 2. Environment Configuration
Create a `.env` file in the root directory and add your credentials:
```env
SUPABASE_URL="your_supabase_url"
SUPABASE_KEY="your_anon_public_key"
DATABASE_URL="postgresql://postgres:password@db.xxxx.supabase.co:5432/postgres"
OPENROUTER_API_KEY="your_openrouter_key"
AI_ENGINE="openrouter"
```

### 3. Installation
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Database Setup
1. Create a new Supabase project.
2. Run the provided `supabase_restore.sql` script in the Supabase SQL Editor to seed the Chinook dataset.

### 5. Running the App
**Start the Backend:**
```bash
python -m uvicorn app.main:app --reload --port 8000
```

**Start the Frontend:**
```bash
streamlit run app/frontend.py
```

## 🛡️ License
This project is for demonstration and internal use. See `LICENSE` for details (if applicable).
