#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 25 22:56:41 2026

@author: sanjana
"""
# -*- coding: utf-8 -*-
"""
Query Suggestion Service
Suggests queries based on user history and similarity matching
"""

from typing import List, Dict
from collections import deque
import difflib
import time

# Store last N queries per session (in-memory for now)
RECENT_QUERIES: Dict[str, deque] = {}
MAX_HISTORY = 20


def add_query_to_history(session_id: str, question: str, sql: str):
    """
    Add a query to session history
    
    Args:
        session_id: Unique session identifier
        question: Natural language question
        sql: Generated SQL query
    """
    if session_id not in RECENT_QUERIES:
        RECENT_QUERIES[session_id] = deque(maxlen=MAX_HISTORY)
    
    RECENT_QUERIES[session_id].append({
        "question": question,
        "sql": sql,
        "timestamp": time.time()
    })


def get_recent_queries(session_id: str) -> List[Dict]:
    """
    Get recent queries for a session
    
    Args:
        session_id: Unique session identifier
    
    Returns:
        List of query dictionaries
    """
    return list(RECENT_QUERIES.get(session_id, []))


def suggest_queries(
    session_id: str,
    partial_question: str,
    max_suggestions: int = 5
) -> List[Dict]:
    """
    Suggest queries based on partial question using similarity matching
    
    Args:
        session_id: Unique session identifier
        partial_question: Partial user input
        max_suggestions: Maximum number of suggestions to return
    
    Returns:
        List of suggested queries sorted by similarity
    """
    recent = RECENT_QUERIES.get(session_id, [])
    suggestions = []
    
    partial_lower = partial_question.lower()
    
    # Calculate similarity for each recent query
    for query in recent:
        similarity = difflib.SequenceMatcher(
            None,
            partial_lower,
            query["question"].lower()
        ).ratio()
        
        # Only include if similarity is above threshold
        if similarity > 0.3:
            suggestions.append({
                **query,
                "similarity": similarity
            })
    
    # Sort by similarity (descending)
    suggestions.sort(key=lambda x: x["similarity"], reverse=True)
    
    return suggestions[:max_suggestions]


def clear_session_history(session_id: str):
    """Clear history for a specific session"""
    if session_id in RECENT_QUERIES:
        del RECENT_QUERIES[session_id]