# -*- coding: utf-8 -*-
"""
Created on Sat Aug 23 17:25:13 2025

@author: Sanjana
"""

# llm.py
import os
from dotenv import load_dotenv
import requests  # We'll use this later for the real API

# Load secrets (for when we use a real API key)
load_dotenv()

# 1. MOCK FUNCTION FOR NOW - For testing our architecture
def generate_sql_mock(question: str, schema: str) -> str:
    """
    A simple mock function that returns a hardcoded SQL query based on a keyword in the question.
    This lets us test our API flow without needing a real AI model yet.
    """
    question_lower = question.lower()
    
    if "artist" in question_lower and "album" in question_lower:
        return "SELECT artists.name, albums.title FROM artists JOIN albums ON artists.id = albums.artist_id;"
    elif "artist" in question_lower:
        return "SELECT * FROM artists;"
    elif "album" in question_lower:
        return "SELECT * FROM albums;"
    else:
        # A default query if no keywords match
        return "SELECT * FROM artists;"

# 2. REAL FUNCTION (STUB) - This is where we'll add the real Llama 3 integration next
def generate_sql_llama3(question: str, schema: str) -> str:
    """
    TODO: This function will send the question and schema to the Llama 3 API
    and return the generated SQL query.
    """
    # We will implement this in the next step
    pass

# 3. MAIN FUNCTION - This is the one we'll call from our API
# For now, it just uses the mock function.
def generate_sql(question: str, schema: str) -> str:
    return generate_sql_mock(question, schema)