# -*- coding: utf-8 -*-
"""
Created on Tue Sep 16 14:25:54 2025

@author: Sanjana
"""

# backend.py
import os
import psycopg2
import pandas as pd
import re
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI
from supabase import create_client, Client
from dotenv import load_dotenv
from services.chart_relevance_service import analyze_chart_relevance
from services.chart_explanation_service import generate_chart_explanation
from services.analysis_capability_service import infer_analysis_capabilities

app = FastAPI()

# --- DEMO DB CREDENTIALS ---
# Replace with your Supabase/Postgres connection details
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASS", "postgres"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
}



# Load env
load_dotenv()
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# NEW: Database URL (for direct SQL connection)
DATABASE_URL = os.getenv("DATABASE_URL")





def connect_demo_db():
    """Try connecting to demo database via psycopg2 using DATABASE_URL"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
        tables = cur.fetchall()
        conn.close()
        return {"success": True, "tables": [t[0] for t in tables]}
    except Exception as e:
        return {"success": False, "error": str(e)}



def get_schema(conn):
    """Fetch tables, columns, and types from DB schema."""
    query = """
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position;
    """
    schema = {}
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
            for table, col, dtype in rows:
                if table not in schema:
                    schema[table] = []
                schema[table].append({"column": col, "type": dtype})
    except Exception as e:
        print(f"Schema fetch failed: {e}")
    return schema


def get_sample_data(conn, table_name, limit=5):
    """Fetch sample rows from a given table."""
    try:
        query = f"SELECT * FROM {table_name} LIMIT {limit};"
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        print(f"Sample data fetch failed: {e}")
        return pd.DataFrame()
    
    
# # ------------------------------------------------------------------
# # EXECUTE SQL (SAFE + READ-ONLY)
# # ------------------------------------------------------------------
# @app.post("/execute")
# def execute_sql(payload: dict):
#     sql_query = payload.get("sql", "").strip()
#     question = payload.get("question", "")

#     #Safety: allow only SELECT / WITH queries
#     if not sql_query.lower().startswith(("select", "with")):
#         return {
#             "success": False,
#             "error": "Only SELECT queries are allowed on demo database"
#         }

#     try:
#         conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
#         cur = conn.cursor()
#         # --- Schema validation ---
#         # --- SCHEMA VALIDATION AFTER SQL GENERATION ---

#         schema = get_schema(conn)
#         conn.close()
        
#         existing_tables = set(schema.keys())
#         used_tables = extract_tables_from_sql(sql_query)  # reuse helper from before
        
#         invalid_tables = used_tables - existing_tables
        
#         if invalid_tables:
#             return {
#                 "type": "invalid_schema",
#                 "error": f"Generated SQL references tables that do not exist: {', '.join(invalid_tables)}",
#                 "available_tables": list(existing_tables),
#                 "sql": sql_query  # optionally still send it for reference
#             }
        
#         cur.execute(sql_query)
#         rows = cur.fetchall()
#         conn.close()

#         data = [dict(row) for row in rows]

#         # 🔍 NEW: chart relevance analysis
#         chart_info = analyze_chart_relevance(
#             sql=sql_query,
#             rows=data
#         )
#         # 🧠 NEW: chart explanation (only if chart is relevant)
#         if chart_info.get("is_relevant"):
#             chart_info["insight"] = generate_chart_explanation(
#                 sql=sql_query,
#                 chart_type=chart_info.get("chart_type", "auto"),
#                 columns=chart_info.get("columns", []),
#                 row_count=len(data)
#             )
#         else:
#             chart_info["insight"] = ""

#         return {
#             "success": True,
#             "data": data,
#             "chart": chart_info
#         }

#     except Exception as e:
#         return {
#             "success": False,
#             "error": str(e)
#         }    


@app.get("/analysis-capabilities")
def get_analysis_capabilities():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        schema = get_schema(conn)
        conn.close()

        capabilities = infer_analysis_capabilities(schema)

        return {
            "success": True,
            "capabilities": capabilities
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }