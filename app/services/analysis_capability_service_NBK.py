#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 28 11:56:30 2026

@author: sanjana
"""



# services/analysis_capability_service.py

from typing import Dict, List


def infer_analysis_capabilities(schema: Dict) -> List[Dict]:
    """
    Infers possible analyses based on schema structure.
    Schema format:
    {
        table_name: [
            {"column": "...", "type": "..."},
            ...
        ]
    }
    """

    capabilities = []

    for table, columns in schema.items():
        column_types = {c["column"]: c["type"].lower() for c in columns}

        numeric_cols = [
            c for c, t in column_types.items()
            if t in ("integer", "numeric", "double precision", "real", "bigint")
        ]

        datetime_cols = [
            c for c, t in column_types.items()
            if "date" in t or "time" in t
        ]

        categorical_cols = [
            c for c, t in column_types.items()
            if t in ("text", "varchar", "character varying")
        ]

        # 📈 Time-series analysis
        if datetime_cols and numeric_cols:
            capabilities.append({
                "table": table,
                "type": "time_series",
                "description": "Trend analysis over time",
                "reason": f"Found datetime column(s) {datetime_cols} and numeric column(s) {numeric_cols}"
            })

        # 📊 Aggregation analysis
        if numeric_cols:
            capabilities.append({
                "table": table,
                "type": "aggregation",
                "description": "Aggregations on numeric metrics",
                "reason": f"Numeric columns detected: {numeric_cols}"
            })

        # 🧑 Entity analysis
        if categorical_cols and numeric_cols:
            capabilities.append({
                "table": table,
                "type": "entity_summary",
                "description": "Grouped summaries by categorical fields",
                "reason": f"Categorical columns {categorical_cols} with numeric metrics {numeric_cols}"
            })

    return capabilities