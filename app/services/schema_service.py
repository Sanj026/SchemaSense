#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 25 18:52:17 2026

@author: sanjana
"""

# app/services/schema_service.py

from sqlalchemy import inspect
from sqlalchemy.engine import Engine
from typing import Dict, Any


def extract_schema(engine: Engine) -> Dict[str, Any]:
    """
    Extract tables, columns, PKs, and FKs from the connected database.
    """
    inspector = inspect(engine)
    schema: Dict[str, Any] = {"tables": {}}

    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)
        pk = inspector.get_pk_constraint(table_name).get("constrained_columns", [])
        fks = inspector.get_foreign_keys(table_name)

        schema["tables"][table_name] = {
            "columns": [col["name"] for col in columns],
            "primary_key": pk,
            "foreign_keys": {
                fk["constrained_columns"][0]: (
                    fk["referred_table"],
                    fk["referred_columns"][0],
                )
                for fk in fks if fk.get("constrained_columns")
            },
        }

    return schema