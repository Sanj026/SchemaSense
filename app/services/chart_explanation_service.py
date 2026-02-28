#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 27 19:48:26 2026

@author: sanjana
"""

# services/chart_explanation_service.py

from typing import List
from app.llm import generate_with_openrouter

def generate_chart_explanation(
    sql: str,
    chart_type: str,
    columns: List[str],
    row_count: int
) -> str:
    """
    Generate a business-friendly explanation for a chart
    """

    prompt = f"""
You are a data analyst explaining a visualization to a business user.

SQL QUERY:
{sql}

CHART TYPE:
{chart_type}

COLUMNS USED:
{", ".join(columns)}

ROW COUNT:
{row_count}

TASK:
Explain what insight this chart provides in 1–2 simple sentences.
Do NOT mention SQL, databases, or technical terms.
Focus on trends, comparisons, or patterns.

Example:
"This bar chart compares total sales by category, showing that Electronics leads by a large margin."
"""

    try:
        response = generate_with_openrouter(prompt, "")
        return response.strip()
    except Exception:
        return ""