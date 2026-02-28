#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 27 20:06:43 2026

@author: sanjana
"""
# -*- coding: utf-8 -*-
"""
Analysis Capability Service
Infers possible analyses based on database schema
"""

from typing import Dict, List


def infer_analysis_capabilities(schema: Dict) -> List[Dict]:
    """
    Infers possible analyses based on schema structure
    
    Args:
        schema: Schema dictionary with format:
        {
            table_name: [
                {"column": "...", "type": "..."},
                ...
            ]
        }
    
    Returns:
        List of capability dictionaries:
        [
            {
                "table": str,
                "type": str,  # "time_series", "aggregation", "entity_summary"
                "description": str,
                "reason": str
            }
        ]
    """
    
    capabilities = []
    
    for table, columns in schema.items():
        # Build column type mapping
        column_types = {
            c["column"]: c["type"].lower() 
            for c in columns
        }
        
        # Identify column categories
        numeric_cols = [
            c for c, t in column_types.items()
            if t in ("integer", "numeric", "double precision", "real", "bigint", "int", "float")
        ]
        
        datetime_cols = [
            c for c, t in column_types.items()
            if "date" in t or "time" in t or "timestamp" in t
        ]
        
        categorical_cols = [
            c for c, t in column_types.items()
            if t in ("text", "varchar", "character varying", "char")
        ]
        
        # TIME-SERIES ANALYSIS
        if datetime_cols and numeric_cols:
            capabilities.append({
                "table": table,
                "type": "time_series",
                "description": "Trend analysis over time",
                "reason": f"Found datetime column(s) {datetime_cols} and numeric column(s) {numeric_cols}"
            })
        
        # AGGREGATION ANALYSIS
        if numeric_cols:
            capabilities.append({
                "table": table,
                "type": "aggregation",
                "description": "Statistical summaries on numeric metrics",
                "reason": f"Numeric columns detected: {numeric_cols}"
            })
        
        # ENTITY SUMMARY ANALYSIS
        if categorical_cols and numeric_cols:
            capabilities.append({
                "table": table,
                "type": "entity_summary",
                "description": "Grouped summaries by categorical fields",
                "reason": f"Categorical columns {categorical_cols} with numeric metrics {numeric_cols}"
            })
    
    return capabilities