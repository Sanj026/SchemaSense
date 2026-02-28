#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  3 14:00:19 2026

@author: sanjana
"""


from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine
from typing import Dict, Any, List, Optional
import os
import re
import uuid
import pandas as pd
import numpy as np
import base64
from io import StringIO

from app.llm import generate_sql_with_tracking
from app.services.explanation_service import generate_sql_explanation
from app.services.chart_relevance_service import analyze_chart_relevance
from app.services.chart_explanation_service import generate_chart_explanation
from app.services.schema_service import extract_schema

# ------------------------------------------------------------------
# INITIALIZATION
# ------------------------------------------------------------------
load_dotenv()
app = FastAPI(title="SchemaSense API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase connection
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None
    print("⚠️  WARNING: Supabase not configured. Demo features will use fallback data.")

# Active connections
ACTIVE_CONNECTIONS: Dict[str, Engine] = {}

# ------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------

def extract_tables_from_sql(sql: str) -> set:
    """Extract table names from SQL query - CASE INSENSITIVE"""
    # Match FROM and JOIN clauses, accounting for optional double quotes
    pattern = r'(?:from|join)\s+"?([a-zA-Z_][a-zA-Z0-9_]*)"?'
    tables = set(re.findall(pattern, sql, re.IGNORECASE))
    return {t.lower() for t in tables}  # Normalize to lowercase


def get_demo_schema_text(db_type: str = "postgresql") -> str:
    """Fetch schema from demo database"""
    quote_char = '`' if db_type == "mysql" else '"'
    if not supabase:
        # Fallback schema
        if db_type == "mysql":
             return "artists(`ArtistId` integer, `Name` character varying)\nalbums(`AlbumId` integer, `Title` character varying, `ArtistId` integer)\ntracks(`TrackId` integer, `Name` character varying, `AlbumId` integer, `Milliseconds` integer, `UnitPrice` numeric)"
        return 'artists("ArtistId" integer, "Name" character varying)\nalbums("AlbumId" integer, "Title" character varying, "ArtistId" integer)\ntracks("TrackId" integer, "Name" character varying, "AlbumId" integer, "Milliseconds" integer, "UnitPrice" numeric)'

    
    try:
        tables_query = "SELECT tablename FROM pg_tables WHERE schemaname='public'"
        tables_result = supabase.rpc("execute_readonly_query", {"query_text": tables_query}).execute()
        
        if not tables_result.data:
            return ""
        
        schema_lines = []
        
        for table_row in tables_result.data:
            table_name = table_row['tablename']
            
            columns_query = f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema='public' AND table_name='{table_name}'
                ORDER BY ordinal_position
            """
            
            columns_result = supabase.rpc("execute_readonly_query", {"query_text": columns_query}).execute()
            
            if columns_result.data:
                # Double-quote column names so LLM sees exact casing
                # e.g. "ArtistId" integer  -> LLM generates artists."ArtistId" (correct)
                # without quotes: ArtistId integer -> LLM generates artists.ArtistId (fails)
                columns_str = ", ".join(
                    f'{quote_char}{col["column_name"]}{quote_char} {col["data_type"]}'
                    for col in columns_result.data
                )
                schema_lines.append(f"{table_name}({columns_str})")
        
        return "\n".join(schema_lines)
    
    except Exception as e:
        print(f"Error fetching schema: {e}")
        return "artists(artist_id integer, name character varying)\nalbums(album_id integer, title character varying, artist_id integer)\ntracks(track_id integer, name character varying, album_id integer, milliseconds integer, unit_price numeric)"


def get_demo_schema_struct() -> Dict:
    """Fetch demo schema as structured dict"""
    if not supabase:
        return {
            "artists": [{"column": "artist_id", "type": "integer"}, {"column": "name", "type": "character varying"}],
            "albums": [{"column": "album_id", "type": "integer"}, {"column": "title", "type": "character varying"}, {"column": "artist_id", "type": "integer"}],
            "tracks": [{"column": "track_id", "type": "integer"}, {"column": "name", "type": "character varying"}, {"column": "album_id", "type": "integer"}]
        }
    
    try:
        tables_query = "SELECT tablename FROM pg_tables WHERE schemaname='public'"
        tables_result = supabase.rpc("execute_readonly_query", {"query_text": tables_query}).execute()
        
        schema = {}
        
        for table_row in tables_result.data:
            table_name = table_row['tablename']
            
            columns_query = f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema='public' AND table_name='{table_name}'
                ORDER BY ordinal_position
            """
            
            columns_result = supabase.rpc("execute_readonly_query", {"query_text": columns_query}).execute()
            
            schema[table_name] = [
                {"column": col['column_name'], "type": col['data_type']}
                for col in columns_result.data
            ]
        
        return schema
    
    except Exception as e:
        print(f"Error: {e}")
        return {}


def detect_db_type(connection_string: str) -> str:
    """Detect database type from connection string"""
    conn_lower = connection_string.lower()
    
    if conn_lower.startswith("postgresql://") or conn_lower.startswith("postgres://"):
        return "postgresql"
    elif conn_lower.startswith("mysql://") or conn_lower.startswith("mysql+"):
        return "mysql"
    elif conn_lower.startswith("sqlite://") or conn_lower.endswith(".db") or conn_lower.endswith(".sqlite"):
        return "sqlite"
    else:
        return "postgresql"


# ------------------------------------------------------------------
# ENDPOINTS
# ------------------------------------------------------------------

@app.get("/")
def root():
    """Health check"""
    return {
        "status": "online",
        "service": "SchemaSense API",
        "version": "1.0.0"
    }


@app.post("/connect_db")
async def connect_db(payload: dict):
    """Connect to database - SUPPORTS PostgreSQL, MySQL, SQLite"""
    try:
        # DEMO DATABASE
        if payload.get("demo"):
            schema_text = get_demo_schema_text()
            schema_struct = get_demo_schema_struct()
            
            return {
                "success": True,
                "schema_text": schema_text,
                "schema_struct": schema_struct,
                "connection_id": None,
                "db_type": "postgresql"
            }
        
        # CUSTOM DATABASE
        connection_string = payload.get("connection_string", "").strip()
        if not connection_string:
            return {"success": False, "error": "Connection string is required"}
        
        db_type = detect_db_type(connection_string)
        
        # Create engine
        if db_type == "sqlite":
            engine = create_engine(connection_string)
        else:
            engine = create_engine(connection_string, connect_args={"connect_timeout": 10})
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        connection_id = str(uuid.uuid4())
        ACTIVE_CONNECTIONS[connection_id] = engine
        
        # Extract schema
        schema_struct = extract_schema(engine)
        
        schema_lines = []
        for table_name, table_info in schema_struct.get("tables", {}).items():
            columns = table_info.get("columns", [])
            columns_str = ", ".join(columns)
            schema_lines.append(f"{table_name}({columns_str})")
        
        schema_text = "\n".join(schema_lines)
        
        return {
            "success": True,
            "connection_id": connection_id,
            "schema_text": schema_text,
            "schema_struct": schema_struct,
            "db_type": db_type
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/generate")
async def generate_query(payload: dict):
    """Generate SQL from natural language"""
    question = payload.get("question", "").strip()
    connection_id = payload.get("connection_id")
    
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")
    
    # Intialize database dialect detection
    db_type = "postgresql"
    
    # Get schema
    schema_text = payload.get("schema", "")
    if not schema_text:
        if connection_id and connection_id in ACTIVE_CONNECTIONS:
            engine = ACTIVE_CONNECTIONS[connection_id]
            # Infer dialect internally via engine
            if engine.dialect.name == "mysql":
                db_type = "mysql"
            elif engine.dialect.name == "sqlite":
                db_type = "sqlite"

            schema_struct = extract_schema(engine)
            schema_lines = []
            for table_name, table_info in schema_struct.get("tables", {}).items():
                columns = table_info.get("columns", [])
                columns_str = ", ".join(columns)
                schema_lines.append(f"{table_name}({columns_str})")
            schema_text = "\n".join(schema_lines)
        else:
            schema_text = get_demo_schema_text(db_type)
            db_type = payload.get("db_type", "postgresql")
    else:
        # Fallback to payload extraction if provided for regenerating
        db_type = payload.get("db_type", "postgresql")
    
    # VALIDATE QUESTION QUALITY FIRST
    question_quality = validate_question_quality(question)
    if not question_quality["is_valid"]:
        return {
            "type": "error",
            "error": question_quality["reason"],
            "suggestions": ["Please provide a more complete question or use one of our suggestions below."]
        }

    # Set quote character for schema embedding based on db_type
    quote_char = '`' if db_type == "mysql" else '"'

    # Ensure schema uses correct quotes for this specific request if it's fallback text
    if "postgres" in db_type and "`" in schema_text:
         schema_text = schema_text.replace("`", '"')
    elif "mysql" in db_type and '"' in schema_text:
         schema_text = schema_text.replace('"', "`")

    # Generate SQL
    try:
        sql, engine_used = generate_sql_with_tracking(question, schema_text, db_type)
        
        return {
            "type": "sql",
            "sql": sql,
            "engine": engine_used
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SQL generation failed: {str(e)}")


@app.post("/execute")
async def execute_query(payload: dict):
    """
    Execute SQL query - FIXED SCHEMA VALIDATION
    """
    sql = payload.get("sql", "").strip()
    question = payload.get("question", "")
    connection_id = payload.get("connection_id")
    
    if not sql:
        return {"success": False, "error": "SQL query is required"}
    
    # Safety: only SELECT queries
    if not sql.lower().strip().startswith(("select", "with")):
        return {"success": False, "error": "Only SELECT queries are allowed for safety"}
    
    try:
        # DEMO DATABASE
        if not connection_id:
            # FIXED SCHEMA VALIDATION - Case insensitive comparison
            schema_text = get_demo_schema_text()
            existing_tables = {
                line.split("(")[0].strip().lower()  # FIXED: Added .strip().lower()
                for line in schema_text.split("\n") 
                if line.strip() and "(" in line
            }
            
            used_tables = extract_tables_from_sql(sql)  # Already returns lowercase
            invalid_tables = used_tables - existing_tables
            
            if invalid_tables:
                return {
                    "success": False,
                    "type": "invalid_schema",
                    "error": f"Tables do not exist: {', '.join(invalid_tables)}",
                    "available_tables": sorted(list(existing_tables))
                }
            
            # Execute via local SQLite demo database directly
            demo_engine = create_engine("sqlite:///app/demo.db")
            with demo_engine.connect() as conn:
                result = conn.execute(text(sql))
                columns = result.keys()
                rows = result.fetchall()
                data = [dict(zip(columns, row)) for row in rows]
        
        # CUSTOM DATABASE
        else:
            if connection_id not in ACTIVE_CONNECTIONS:
                return {"success": False, "error": "Invalid or expired connection ID"}
            
            engine = ACTIVE_CONNECTIONS[connection_id]
            
            with engine.connect() as conn:
                result = conn.execute(text(sql))
                columns = result.keys()
                rows = result.fetchall()
                data = [dict(zip(columns, row)) for row in rows]
        
        # Generate explanation
        explanation = generate_sql_explanation(sql, question)
        
        # Analyze chart relevance
        chart_info = analyze_chart_relevance(sql, data)
        
        # Generate chart explanation if relevant
        if chart_info.get("is_relevant"):
            chart_info["insight"] = generate_chart_explanation(
                sql=sql,
                chart_type=chart_info.get("chart_type", "auto"),
                columns=chart_info.get("columns", []),
                row_count=len(data)
            )
        
        return {
            "success": True,
            "data": data,
            "explanation": explanation,
            "chart": chart_info
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/summarize_data")
async def summarize_data(payload: dict):
    """PHASE 2: Generate statistical summary"""
    try:
        data = payload.get("data", [])
        
        if not data:
            return {"success": False, "error": "No data provided"}
        
        df = pd.DataFrame(data)
        
        summary = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": {}
        }
        
        for col in df.columns:
            col_info = {
                "dtype": str(df[col].dtype),
                "missing": int(df[col].isna().sum())
            }
            
            # Numeric columns
            if df[col].dtype in ['int64', 'float64']:
                col_info.update({
                    "min": float(df[col].min()) if not pd.isna(df[col].min()) else None,
                    "max": float(df[col].max()) if not pd.isna(df[col].max()) else None,
                    "mean": float(df[col].mean()) if not pd.isna(df[col].mean()) else None,
                })
            
            # Categorical columns
            else:
                value_counts = df[col].value_counts().head(5).to_dict()
                col_info["top_values"] = {
                    str(k): int(v) for k, v in value_counts.items()
                }
            
            summary["columns"][col] = col_info
        
        return {"success": True, "summary": summary}
    
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/demo_preview")
async def demo_preview():
    """
    Demo database preview - ALWAYS WORKS (fallback data)
    """
    # Fallback data (always works)
    fallback_data = {
        "success": True,
        "tables": {
            "artists": {
                "columns": ["artist_id", "name"],
                "preview": [
                    {"artist_id": 1, "name": "The 1975"},
                    {"artist_id": 2, "name": "Ricky Montgomery"},
                    {"artist_id": 3, "name": "Ravyn Lenae"},
                    {"artist_id": 4, "name": "Alanis Morissette"},
                    {"artist_id": 5, "name": "Alice In Chains"}
                ]
            },
            "albums": {
                "columns": ["album_id", "title", "artist_id"],
                "preview": [
                    {"album_id": 1, "title":"Being Funny in a Foreign Language (2022)","": 1},
                    {"album_id": 2, "title": "Montgomery Ricky (2016)", "artist_id": 2},
                    {"album_id": 3, "title": "Hypnos", "artist_id": 2},
                    {"album_id": 4, "title": "Let There Be Rock", "artist_id": 1},
                    {"album_id": 5, "title": "Big Ones", "artist_id": 3}
                ]
            },
            "tracks": {
                "columns": ["track_id", "name", "album_id", "milliseconds", "unit_price"],
                "preview": [
                    {"track_id": 1, "name": "About You", "album_id": 1, "milliseconds": 343719},
                    {"track_id": 2, "name": "Line Without a Hook", "album_id": 2, "milliseconds": 342562},
                    {"track_id": 3, "name": "Love Me Not", "album_id": 3, "milliseconds": 230619},
                    {"track_id": 4, "name": "Restless and Wild", "album_id": 3, "milliseconds": 252051, "unit_price": 0.99},
                    {"track_id": 5, "name": "Princess of the Dawn", "album_id": 3, "milliseconds": 375418, "unit_price": 0.99}
                ]
            }
        }
    }
    
    # Try real data from Supabase
    if supabase:
        try:
            schema = get_demo_schema_struct()
            
            if schema:
                tables_info = {}
                
                for table_name, columns in list(schema.items())[:3]:
                    col_names = [col["column"] for col in columns]
                    
                    query = f"SELECT * FROM {table_name} LIMIT 5"
                    result = supabase.rpc("execute_readonly_query", {"query_text": query}).execute()
                    
                    tables_info[table_name] = {
                        "columns": col_names,
                        "preview": result.data if result.data else []
                    }
                
                return {"success": True, "tables": tables_info}
        except:
            pass
    
    # Return fallback
    return fallback_data


@app.get("/suggest_queries")
async def suggest_queries():
    """PHASE 2: Smart query suggestions"""
    try:
        schema = get_demo_schema_struct()
        suggestions = []
        
        for table_name, columns in list(schema.items())[:3]:
            suggestions.append({
                "question": f"Show me all {table_name}",
                "description": f"View all records from {table_name} table",
                "created_at": f"suggestion_{table_name}_all"
            })
            
            suggestions.append({
                "question": f"How many {table_name} are there?",
                "description": f"Count total records in {table_name}",
                "created_at": f"suggestion_{table_name}_count"
            })
        
        return {"success": True, "queries": suggestions[:5]}
    
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/export_csv")
async def export_csv(payload: dict):
    """PHASE 2: Export query results to CSV"""
    try:
        data = payload.get("data", [])
        if not data:
            return {"success": False, "error": "No data to export"}
        
        df = pd.DataFrame(data)
        
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue()
        
        csv_base64 = base64.b64encode(csv_content.encode()).decode()
        
        return {
            "success": True,
            "csv_content": csv_base64,
            "filename": payload.get("filename", "query_results.csv")
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}



@app.post("/regenerate_sql")
async def regenerate_sql(payload: dict):
    """PHASE 2: Regenerate SQL with IMPROVED confidence scoring"""
    question = payload.get("question", "").strip()
    schema = payload.get("schema", "")
    previous_sql = payload.get("previous_sql", "")
    
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")
    
    # VALIDATE QUESTION QUALITY FIRST
    question_quality = validate_question_quality(question)
    
    if not question_quality["is_valid"]:
        return {
            "type": "error",
            "error": question_quality["reason"],
            "suggestions": ["Please provide a more complete question"]
        }
    
    # Get db_type
    db_type = payload.get("db_type", "postgresql")
    
    # Generate new SQL
    sql, engine_used = generate_sql_with_tracking(question, schema, db_type)
    
    # Calculate REALISTIC confidence
    confidence = calculate_realistic_confidence(sql, question, schema)
    
    # Generate suggestions
    suggestions = generate_improvement_suggestions(sql, question, confidence)
    
    return {
        "type": "sql",
        "sql": sql,
        "engine": engine_used,
        "confidence": confidence,
        "suggestions": suggestions
    }


def validate_question_quality(question: str) -> dict:
    """
    Validate if question is meaningful enough to generate SQL
    """
    # Too short
    if len(question) < 3:
        return {
            "is_valid": False,
            "reason": "Question too short. Please be more specific."
        }
    
    # Only one word and too short
    words = question.split()
    if len(words) < 1:
        return {
            "is_valid": False,
            "reason": "Empty question provided."
        }
    
    # Nonsense detection (e.g. "hhv", "abc")
    if len(words) == 1 and len(words[0]) < 4 and not words[0].lower() in ["map", "list", "all"]:
         return {
            "is_valid": False,
            "reason": "Input seems to be nonsense. Please ask a data-related question."
         }
    if len(words) < 2:
        return {
            "is_valid": False,
            "reason": "Question needs more context. Example: 'Show me all artists'"
        }
    
    # No verbs or keywords
    sql_keywords = ['show', 'get', 'find', 'list', 'count', 'sum', 'avg', 'what', 'how', 'which']
    has_keyword = any(kw in question.lower() for kw in sql_keywords)
    
    if not has_keyword:
        return {
            "is_valid": False,
            "reason": "Question unclear. Try: 'Show...', 'Find...', 'Count...', 'What...'"
        }
    
    return {"is_valid": True}


def calculate_realistic_confidence(sql: str, question: str, schema: str) -> float:
    """
    Calculate REALISTIC confidence score (not inflated)
    """
    if sql.lower().strip() == "select 1 where 1=0;":
        return 0.0

    score = 0.0 
    
    sql_lower = sql.lower()
    
    # 1. Basic Structure (Max 30%)
    if sql_lower.startswith('select'):
        score += 0.15
        if 'from' in sql_lower:
            score += 0.15

    # 2. Schema Validation (Max 30%)
    if schema:
        schema_tables = {
            line.split("(")[0].strip().lower()
            for line in schema.split("\n")
            if line.strip() and "(" in line
        }
        used_tables = extract_tables_from_sql(sql)
        
        # Valid table check
        if used_tables and used_tables.issubset(schema_tables):
            score += 0.30
        else:
            score -= 0.30  # Heavy penalty for hallucinated tables
            
        # JOIN Check
        if len(used_tables) > 1:
            if 'join' in sql_lower and 'on' in sql_lower:
                score += 0.10
            else:
                score -= 0.20  # Missing JOIN for multiple tables

    # 3. Question Alignment & Specificity (Max 30%)
    if 'where' in sql_lower or 'group by' in sql_lower:
        score += 0.15
        
    if 'limit' in sql_lower:
        score += 0.10
        
    # Check if words from question appear in SQL (rough alignment)
    question_words = set(re.findall(r'\b\w+\b', question.lower()))
    sql_words = set(re.findall(r'\b\w+\b', sql_lower))
    
    # Ignore common stop words for overlap
    stop_words = {'show', 'me', 'the', 'what', 'is', 'how', 'many', 'list', 'all'}
    meaningful_q_words = question_words - stop_words
    
    if meaningful_q_words:
        overlap = meaningful_q_words.intersection(sql_words)
        if overlap:
            score += 0.05
            
    # 4. Complexity & formatting penalties
    if sql_lower.count('join') > 3:
        score -= 0.15  # Extremely complex joins usually mean trouble in 1B params
    if "select *" in sql_lower:
        score -= 0.10  # Penalize lazy selecting

    return max(0.0, min(score, 1.0))


def generate_improvement_suggestions(sql: str, question: str, confidence: float) -> list:
    """
    Generate HELPFUL improvement suggestions
    """
    suggestions = []
    
    # Low confidence
    if confidence < 0.5:
        suggestions.append("⚠️ Low confidence - Review SQL carefully before executing")
    elif confidence < 0.7:
        suggestions.append("💡 Medium confidence - Double-check the SQL matches your intent")
    
    # Missing best practices
    if "limit" not in sql.lower():
        suggestions.append("📊 Add LIMIT clause to prevent large result sets")
    
    if "select *" in sql.lower():
        suggestions.append("🎯 Consider selecting specific columns instead of SELECT *")
    
    if "where" not in sql.lower() and "group by" not in sql.lower():
        suggestions.append("🔍 Consider adding WHERE clause to filter results")
    
    # Vague question
    if len(question.split()) < 4:
        suggestions.append("💬 Try being more specific in your question for better results")
    
    return suggestions


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting SchemaSense API")
    print("📍 URL: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)