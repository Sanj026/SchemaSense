# -*- coding: utf-8 -*-
"""
Created on Wed Sep 10 23:05:42 2025

@author: Sanjana
"""

schemasense/
├── main.py          # Your existing FastAPI backend
├── app_frontend.py  # NEW Streamlit frontend
├── .env             # Your environment variables
└── requirements.txt # Updated dependencies

Streamlit (app_frontend.py)
    ↓ calls API
FastAPI (main.py)
    ↓ delegates
llm.py   backend.py

schemasense/
├── services/
│   ├── __init__.py
│   └── explanation_service.py 

     # <-- New file
├── main.py
├── app_frontend.py
└── ... (other files)


schemasense/
├── services/               # NEW: Business logic layer
│   ├── __init__.py        # Makes this a Python package
│   └── explanation_service.py  # All explanation logic
├── main.py                # FastAPI routes (cleaner now!)
├── app_frontend.py        # Streamlit UI
├── llm.py                 # AI operations
├── backend.py             # Database operations
└── requirements.txt

main.py – FastAPI backend with endpoints for DB connection, SQL generation, execution, and demo preview. Handles both demo and user DBs, with retry/fallback logic for AI engines.

llm.py – SQL generation engines using OpenRouter and Prem-1B-SQL, with fallback, single-line SQL enforcement, and ambiguity handling.

frontend.py – Streamlit app with connection page, main page, SQL generation/execution, and automatic visualization logic. Handles session state, demo/custom DB connections, clarifications, and charts.

backend.py – Utility functions for connecting to demo DB via psycopg2, fetching schema, and sample data. Supports Supabase demo as well.

schema_service.py – Schema extraction via SQLAlchemy engine, returning tables, columns, PKs, FKs.

explanation_service.py – Generates natural-language explanations of SQL queries via OpenRouter.




frontend.py
 └── calls POST /execute
        ↓
backend.py
 └── /execute
        ├── run SQL
        ├── analyze_chart_relevance
        └── return { data, chart }