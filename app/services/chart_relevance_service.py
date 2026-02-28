#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 27 19:24:50 2026

@author: sanjana
"""

# services/chart_relevance_service.py

from typing import List, Dict, Any
import pandas as pd
import re

ID_LIKE_COLUMNS = {"id", "uuid", "hash", "key"}

def is_id_like(col_name: str) -> bool:
    col = col_name.lower()
    return any(token in col for token in ID_LIKE_COLUMNS)

def analyze_chart_relevance(sql: str, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Decide whether a chart should be shown for the query result
    """

    if not rows:
        return {"is_chart_relevant": False, "reason": "No data returned"}

    df = pd.DataFrame(rows)

    # Column count check
    if df.shape[1] < 2 or df.shape[1] > 4:
        return {
            "is_chart_relevant": False,
            "reason": "Too few or too many columns"
        }

    # Identify numeric & categorical columns
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = df.select_dtypes(include="object").columns.tolist()

    # Remove ID-like columns
    numeric_cols = [c for c in numeric_cols if not is_id_like(c)]
    categorical_cols = [c for c in categorical_cols if not is_id_like(c)]

    if not numeric_cols:
        return {
            "is_chart_relevant": False,
            "reason": "No meaningful numeric columns"
        }

    if df.shape[0] > 50:
        return {
            "is_chart_relevant": False,
            "reason": "Too many rows for automatic visualization"
        }

    # Detect aggregation from SQL
    is_aggregated = bool(re.search(r"\b(count|sum|avg|min|max)\b", sql.lower()))

    # Decide chart type
    if is_aggregated and categorical_cols:
        return {
            "is_chart_relevant": True,
            "chart_type": "bar",
            "x": categorical_cols[0],
            "y": numeric_cols[0]
        }

    if len(numeric_cols) == 1 and df.shape[0] > 2:
        return {
            "is_chart_relevant": True,
            "chart_type": "line",
            "x": df.index.name or "index",
            "y": numeric_cols[0]
        }

    return {
        "is_chart_relevant": False,
        "reason": "Data not suitable for visualization"
    }