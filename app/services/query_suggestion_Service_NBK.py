#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 28 11:57:54 2026

@author: sanjana
"""



# app/services/query_suggestion_service.py

from typing import List, Dict
from collections import deque
import difflib
import time

# Store last N queries per session/user (can later move to DB)
RECENT_QUERIES: Dict[str, deque] = {}  # {session_id: deque([{"question":..., "sql":..., "timestamp":...}])}
MAX_HISTORY = 20  # keep last 20 queries

def add_query_to_history(session_id: str, question: str, sql: str):
    """Add a query to session history."""
    if session_id not in RECENT_QUERIES:
        RECENT_QUERIES[session_id] = deque(maxlen=MAX_HISTORY)
    RECENT_QUERIES[session_id].append({
        "question": question,
        "sql": sql,
        "timestamp": time.time()
    })

def get_recent_queries(session_id: str) -> List[Dict]:
    """Return recent queries for a session."""
    return list(RECENT_QUERIES.get(session_id, []))

def suggest_queries(session_id: str, partial_question: str, max_suggestions: int = 5) -> List[Dict]:
    """Suggest queries based on partial question using similarity matching."""
    recent = RECENT_QUERIES.get(session_id, [])
    suggestions = []

    # Compare partial question to previous questions
    for q in recent:
        similarity = difflib.SequenceMatcher(None, partial_question.lower(), q["question"].lower()).ratio()
        if similarity > 0.3:  # adjustable threshold
            suggestions.append({**q, "similarity": similarity})

    # Sort by similarity descending
    suggestions = sorted(suggestions, key=lambda x: x["similarity"], reverse=True)

    return suggestions[:max_suggestions]