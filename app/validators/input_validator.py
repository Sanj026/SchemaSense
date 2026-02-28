#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb  4 16:47:03 2026

@author: sanjana
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Input Quality Validator
Validates user questions BEFORE calling LLM to prevent wasted API calls and errors
"""

import re
from typing import Dict, List

# Patterns for non-data questions (greetings, single words, noise)
INVALID_PATTERNS = [
    r'^(hi|hello|hey|yo|sup|ok|okay|show|test|yes|no|yep|nope|cool|nice|thanks|thank you)$',
    r'^\w+$',  # Single word only
]

# SQL-related keywords that indicate a valid question
SQL_KEYWORDS = [
    'show', 'display', 'get', 'fetch', 'retrieve', 'find', 'search',
    'list', 'count', 'sum', 'avg', 'average', 'min', 'max', 'total',
    'what', 'how many', 'how much', 'which', 'who', 'when', 'where',
    'top', 'bottom', 'first', 'last', 'latest', 'oldest', 'newest',
    'select', 'all', 'each', 'every', 'filter', 'sort', 'order'
]


def validate_input_quality(question: str) -> Dict:
    """
    Validate if input is meaningful enough for SQL generation
    
    This is the FIRST checkpoint before calling the LLM.
    Prevents wasted API calls and improves user experience.
    
    Args:
        question: User's natural language question
    
    Returns:
        Dictionary with:
            - is_valid (bool): Whether question is acceptable
            - reason (str): Explanation of validation result
            - confidence (float): Quality score 0.0-1.0
    """
    question = question.strip()
    
    # Rule 1: Minimum length check
    if len(question) < 5:
        return {
            "is_valid": False,
            "reason": "Question too short. Please be more specific.",
            "confidence": 0.0,
            "suggestion": "Try: 'Show me all customers' or 'Count total orders'"
        }
    
    # Rule 2: Must have at least 2 words
    words = question.split()
    if len(words) < 2:
        return {
            "is_valid": False,
            "reason": "Question needs more context.",
            "confidence": 0.0,
            "suggestion": "Example: 'List all products' or 'Find customer emails'"
        }
    
    # Rule 3: Check for invalid patterns (greetings, noise)
    question_lower = question.lower()
    for pattern in INVALID_PATTERNS:
        if re.match(pattern, question_lower):
            return {
                "is_valid": False,
                "reason": "This doesn't look like a data question.",
                "confidence": 0.0,
                "suggestion": "Ask about your database tables and data"
            }
    
    # Rule 4: Must contain at least one SQL-related keyword
    has_sql_keyword = any(
        keyword in question_lower 
        for keyword in SQL_KEYWORDS
    )
    
    if not has_sql_keyword:
        return {
            "is_valid": False,
            "reason": "Question unclear. Use action words like 'show', 'count', 'find'.",
            "confidence": 0.2,
            "suggestion": "Example: 'Show top 10 sales' or 'Count customers by region'"
        }
    
    # Rule 5: Question marks are good (indicates genuine question)
    has_question_mark = '?' in question
    confidence_boost = 0.1 if has_question_mark else 0.0
    
    # Rule 6: Calculate base confidence from length and complexity
    base_confidence = min(0.6 + (len(words) * 0.05) + confidence_boost, 0.9)
    
    # PASSED all checks
    return {
        "is_valid": True,
        "reason": "Question looks valid for SQL generation",
        "confidence": base_confidence,
        "suggestion": None
    }


def get_example_questions() -> List[str]:
    """
    Return example questions to show users
    """
    return [
        "Show me all customers",
        "Count total orders",
        "Find products with price > 100",
        "What is the average salary?",
        "List top 10 sales by revenue",
        "How many users signed up last month?",
        "Get customer emails from New York",
        "Find employees in the Engineering department"
    ]


def suggest_question_improvements(question: str) -> List[str]:
    """
    Suggest improvements to make a question better
    """
    suggestions = []
    
    words = question.split()
    
    # Too vague
    if len(words) <= 3:
        suggestions.append("💡 Add more details to be more specific")
    
    # No verbs
    action_words = ['show', 'get', 'find', 'list', 'count']
    if not any(word in question.lower() for word in action_words):
        suggestions.append("💡 Start with an action: 'Show...', 'Count...', 'Find...'")
    
    # No filters
    if 'where' not in question.lower() and 'with' not in question.lower():
        suggestions.append("💡 Consider adding filters: 'where status = active'")
    
    # No limits
    if 'top' not in question.lower() and 'limit' not in question.lower():
        suggestions.append("💡 Consider adding limits: 'top 10' or 'first 20'")
    
    return suggestions


# Quick test
if __name__ == "__main__":
    # Test cases
    test_cases = [
        ("hi", False),
        ("show", False),
        ("ok", False),
        ("Show me all customers", True),
        ("Count total orders", True),
        ("what is the price", True),
        ("lorem ipsum dolor", False),
        ("Find products with high ratings", True),
    ]
    
    print("Testing Input Validator:")
    print("=" * 50)
    
    for question, expected_valid in test_cases:
        result = validate_input_quality(question)
        status = "✅ PASS" if result["is_valid"] == expected_valid else "❌ FAIL"
        
        print(f"\nQuestion: '{question}'")
        print(f"Expected: {'Valid' if expected_valid else 'Invalid'}")
        print(f"Got: {'Valid' if result['is_valid'] else 'Invalid'}")
        print(f"Reason: {result['reason']}")
        print(f"Status: {status}")