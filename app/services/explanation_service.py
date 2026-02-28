#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 16 16:10:23 2025

@author: sanjana
"""

# services/explanation_service.py
import os
from app.llm import generate_with_openrouter
import json

def generate_sql_explanation(sql_query: str, question: str = "", results_metadata: dict = None) -> str:
    """
    Use AI to explain SQL queries in plain English
    """
    prompt = f"""
You are a data analyst explaining SQL queries to business users.

ORIGINAL QUESTION: "{question}"
SQL QUERY: {sql_query}

TASK: Explain what this SQL query does in simple, business-friendly English.

GUIDELINES:
- Focus on what business insight the query provides
- Explain the logic in 1-2 sentences max
- Use non-technical language that a manager would understand
- Highlight what data is being retrieved and why it matters
- If there are filters/conditions, explain what they mean
- Do NOT explain SQL syntax or technical details

EXAMPLE:
- SQL: SELECT COUNT(*) FROM users WHERE signup_date > '2024-01-01'
- Explanation: "This shows how many new users signed up since the beginning of 2024"

Your explanation (1-2 sentences):
"""
    
    try:
        explanation = generate_with_openrouter(prompt, "")
        
        # Clean up the response
        explanation = explanation.strip()
        if explanation.startswith('"') and explanation.endswith('"'):
            explanation = explanation[1:-1]
            
        return explanation if explanation else "Unable to generate explanation"
        
    except Exception as e:
        print(f"Explanation generation failed: {e}")
        return "Explanation unavailable"