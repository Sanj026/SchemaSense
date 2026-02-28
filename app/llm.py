#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 12 20:29:25 2026

@author: sanjana
"""

# -*- coding: utf-8 -*-
"""
Created on Wed Sep 10 21:38:24 2025

@author: Sanjana
"""

"""
LLM Integration Module
Supports OpenRouter (primary) and Prem-1B-SQL (fallback)
"""

import requests
import os
from dotenv import load_dotenv
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch
import re

# Load environment variables
load_dotenv()

# Configuration
AI_ENGINE = os.getenv("AI_ENGINE", "openrouter")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

print(f"🤖 AI Engine configured: {AI_ENGINE}")

# ================== PREM-1B-SQL ENGINE ==================

prem_pipeline = None
prem_tokenizer = None

def setup_prem_engine():
    """Initialize Prem-1B-SQL model (lazy loading)"""
    global prem_pipeline, prem_tokenizer

    if prem_pipeline is not None:
        return prem_pipeline, prem_tokenizer

    try:
        print("🚀 Loading Prem-1B-SQL model...")
        model_name = "PremalMatalia/Prem-1B-SQL"

        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            low_cpu_mem_usage=True
        )

        pipeline_obj = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer
        )

        prem_pipeline = pipeline_obj
        prem_tokenizer = tokenizer

        print("✅ Prem-1B-SQL model loaded successfully!")
        return prem_pipeline, prem_tokenizer

    except Exception as e:
        raise Exception(f"Failed to load Prem model: {e}")


from tenacity import retry, stop_after_attempt, wait_exponential

# ================== SHARED PROMPT ==================

def build_sql_prompt(question: str, schema: str, db_type: str = "postgresql") -> str:
    """
    Single shared prompt for BOTH OpenRouter and Prem
    """
    if db_type == "mysql":
        quote_char = "`"
        example_correct1 = "SELECT artists.`Name`, albums.`Title`"
        example_incorrect1 = "SELECT artists.name, albums.title"
        example_incorrect2 = "SELECT artists.Name, albums.Title"
        example_correct2 = "JOIN albums ON artists.`ArtistId` = albums.`ArtistId`"
        example_incorrect3 = "JOIN albums ON artists.artist_id = albums.artist_id"
        few_shot1_q = "Show me all users."
        few_shot1_sql = "SELECT * FROM users LIMIT 10;"
        few_shot2_q = "How many employees are in the IT department?"
        few_shot2_sql = "SELECT COUNT(employees.`EmployeeId`) FROM employees JOIN departments ON employees.`DepartmentId` = departments.`DepartmentId` WHERE departments.`Name` ILIKE 'IT';"
        few_shot3_q = "Find the top 5 highest paid employees."
        few_shot3_sql = "SELECT employees.`Name`, employees.`Salary` FROM employees ORDER BY employees.`Salary` DESC LIMIT 5;"
    else:
        quote_char = '"'
        example_correct1 = 'SELECT artists."Name", albums."Title"'
        example_incorrect1 = "SELECT artists.name, albums.title"
        example_incorrect2 = "SELECT artists.Name, albums.Title"
        example_correct2 = 'JOIN albums ON artists."ArtistId" = albums."ArtistId"'
        example_incorrect3 = "JOIN albums ON artists.artist_id = albums.artist_id"
        few_shot1_q = "Show me all users."
        few_shot1_sql = "SELECT * FROM users LIMIT 10;"
        few_shot2_q = "How many employees are in the IT department?"
        few_shot2_sql = 'SELECT COUNT(employees."EmployeeId") FROM employees JOIN departments ON employees."DepartmentId" = departments."DepartmentId" WHERE departments."Name" ILIKE \'IT\';'
        few_shot3_q = "Find the top 5 highest paid employees."
        few_shot3_sql = 'SELECT employees."Name", employees."Salary" FROM employees ORDER BY employees."Salary" DESC LIMIT 5;'

    return f"""
You are a senior {db_type.upper()} SQL engineer.

DATABASE SCHEMA:
{schema}

USER INPUT:
{question}

CRITICAL BEHAVIOR RULES:
- If the user input is NOT a valid English question about data (examples: "hi", "hello", "hhv", "abc", "ok", random letters, greetings, or non-technical noise),
  then return this EXACT SQL:
  SELECT 1 WHERE 1=0;
- If the question is empty or purely nonsensical, do NOT hallucinate a query. Return the fallback SQL above.


INSTRUCTIONS (DO NOT VIOLATE ANY):
1. Use ONLY the table and column names from the provided schema
2. If a table or column does not exist in the schema, do not use it
3. ALWAYS wrap every column name in {quote_char} quotes exactly as shown in the schema!
   CORRECT:   {example_correct1}
   INCORRECT: {example_incorrect1}
   INCORRECT: {example_incorrect2}
4. Table names do NOT need quotes, only column names need them
5. Use proper JOIN syntax with quoted column names in the ON condition
   CORRECT:   {example_correct2}
   INCORRECT: {example_incorrect3}
6. Qualify every column with its table name when joining multiple tables
7. For aggregate queries (COUNT, SUM, AVG, MIN, MAX), include GROUP BY
8. Default to LIMIT 10 for list queries unless specified
9. Use ILIKE for case-insensitive text matching
10. Return ONLY the SQL query on a single line
11. Do NOT include explanations, comments, or markdown formatting

FEW-SHOT EXAMPLES:
Question: "{few_shot1_q}"
SQL: {few_shot1_sql}

Question: "{few_shot2_q}"
SQL: {few_shot2_sql}

Question: "{few_shot3_q}"
SQL: {few_shot3_sql}

OUTPUT:
Return ONLY valid {db_type.upper()} SQL.
"""


# ================== OPENROUTER ENGINE ==================

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate_with_openrouter(question: str, schema: str, db_type: str = "postgresql") -> str:
    """Generate SQL using OpenRouter with automatic retries on failure"""

    prompt = build_sql_prompt(question, schema, db_type)

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "anthropic/claude-3-haiku",
                "messages": [
                    {
                        "role": "system",
                        "content": f"You are a {db_type.upper()} SQL expert. Output ONLY SQL."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 300,
                "temperature": 0.1
            },
            timeout=30
        )

        response.raise_for_status()
        result = response.json()

        sql_query = result["choices"][0]["message"]["content"].strip()

        # Cleanup
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        sql_query = " ".join(sql_query.split())

        if not sql_query.endswith(";"):
            sql_query += ";"

        return sql_query

    except Exception as e:
        print(f"OpenRouter Attempt Failed: {e}")
        raise Exception(f"OpenRouter API failed: {e}")


# ================== PREM ENGINE ==================

@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=5))
def generate_with_prem(question: str, schema: str, db_type: str = "postgresql") -> str:
    """Generate SQL using Prem-1B-SQL with automatic retries on failure"""

    pipeline_obj, tokenizer = setup_prem_engine()
    prompt = build_sql_prompt(question, schema, db_type)

    try:
        response = pipeline_obj(
            prompt,
            max_new_tokens=150,
            temperature=0.1,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )

        generated_text = response[0]["generated_text"]
        sql_query = generated_text.split("OUTPUT:")[-1].strip()

        sql_query = re.split(r"[;\n]", sql_query)[0] + ";"
        sql_query = " ".join(sql_query.split())

        return sql_query

    except Exception as e:
        print(f"Prem Attempt Failed: {e}")
        raise Exception(f"Prem model failed: {e}")


# ================== MAIN FUNCTION ==================

def generate_sql_with_tracking(question: str, schema: str, db_type: str = "postgresql") -> tuple[str, str]:
    """
    Generate SQL with automatic fallback between engines
    Returns: (sql_query, engine_name)
    """

    try:
        sql = generate_with_openrouter(question, schema, db_type)
        if sql and len(sql) > 10:
            return sql, "openrouter"
        raise Exception("Empty SQL from OpenRouter")

    except Exception:
        pass

    try:
        sql = generate_with_prem(question, schema, db_type)
        if sql and len(sql) > 10:
            return sql, "prem"
        raise Exception("Empty SQL from Prem")

    except Exception:
        return "SELECT 1 WHERE 1=0;", "fallback"


# ================== LEGACY ==================

def generate_with_openrouter_legacy(question: str, schema: str) -> str:
    return generate_with_openrouter(question, schema)