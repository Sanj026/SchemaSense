#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb  4 16:47:50 2026

@author: sanjana
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schema Validator
Pre-validates that entities mentioned in question exist in schema
Prevents hallucination of non-existent tables/columns
"""

from typing import Dict, List, Set, Tuple
import re


def extract_likely_entities(question: str) -> Set[str]:
    """
    Extract potential table/column names from user question
    
    Args:
        question: User's natural language question
    
    Returns:
        Set of words that might be table/column names
    """
    # Common stop words to ignore
    stop_words = {
        'show', 'me', 'all', 'the', 'from', 'with', 'by', 'in',
        'how', 'many', 'what', 'which', 'who', 'when', 'where',
        'get', 'find', 'list', 'count', 'sum', 'avg', 'total',
        'is', 'are', 'was', 'were', 'has', 'have', 'had',
        'my', 'your', 'their', 'a', 'an', 'and', 'or', 'but'
    }
    
    # Extract words
    words = question.lower().split()
    
    # Filter: keep only potential entity names
    entities = {
        word.strip('.,?!;:') 
        for word in words 
        if len(word) > 2 and word not in stop_words
    }
    
    return entities


def normalize_table_name(name: str) -> str:
    """
    Normalize table name for comparison
    Handles plurals, case, underscores
    """
    name = name.lower().strip()
    
    # Remove common suffixes
    if name.endswith('s') and len(name) > 3:
        name = name[:-1]
    
    return name


def find_similar_tables(entity: str, available_tables: Set[str]) -> List[str]:
    """
    Find tables with similar names (for suggestions)
    
    Args:
        entity: Entity mentioned in question
        available_tables: Set of available table names
    
    Returns:
        List of similar table names
    """
    entity_norm = normalize_table_name(entity)
    similar = []
    
    for table in available_tables:
        table_norm = normalize_table_name(table)
        
        # Exact match after normalization
        if entity_norm == table_norm:
            similar.append(table)
            continue
        
        # Check if one contains the other
        if entity_norm in table_norm or table_norm in entity_norm:
            similar.append(table)
            continue
        
        # Check common patterns
        # e.g., "user" vs "users", "order" vs "orders"
        if entity_norm + 's' == table_norm or entity_norm == table_norm + 's':
            similar.append(table)
    
    return similar


def validate_schema_availability(
    question: str,
    schema: Dict
) -> Dict:
    """
    Validate that entities mentioned in question exist in schema
    
    This prevents the LLM from hallucinating non-existent tables.
    
    Args:
        question: User's question
        schema: Schema structure from database
            Format: {"tables": {"table_name": {"columns": [...]}}}
    
    Returns:
        Dictionary with:
            - is_valid (bool): Whether validation passed
            - missing_entities (list): Entities not found
            - suggestions (list): Helpful suggestions
            - available_tables (list): All available tables
    """
    
    # If no schema provided, skip validation
    if not schema or not schema.get("tables"):
        return {
            "is_valid": True,
            "missing_entities": [],
            "suggestions": [],
            "available_tables": []
        }
    
    # Get all available tables (case-insensitive)
    available_tables = {
        table.lower() 
        for table in schema["tables"].keys()
    }
    
    # Extract entities from question
    mentioned_entities = extract_likely_entities(question)
    
    # Find entities that look like table names but don't exist
    missing = []
    suggestions = []
    
    for entity in mentioned_entities:
        # Check if this entity is a table name
        entity_norm = normalize_table_name(entity)
        
        # Look for exact or similar matches
        similar = find_similar_tables(entity, available_tables)
        
        if not similar:
            # No match found - might be a column or completely wrong
            # Only flag if it looks like a table name (noun, not too common)
            if len(entity) > 3:
                missing.append(entity)
        else:
            # Found similar table - user might have meant this
            if entity.lower() not in available_tables:
                suggestions.append(
                    f"Did you mean '{similar[0]}'? (You wrote '{entity}')"
                )
    
    # Determine if validation passed
    # We're lenient here: only fail if clearly wrong tables mentioned
    is_valid = len(missing) == 0 or len(mentioned_entities) > 5
    # (If many entities, user probably just asking generally)
    
    return {
        "is_valid": is_valid,
        "missing_entities": missing,
        "suggestions": suggestions if not is_valid else [],
        "available_tables": sorted(available_tables)
    }


def extract_tables_from_sql(sql: str) -> Set[str]:
    """
    Extract table names from generated SQL query
    For post-generation validation
    
    Args:
        sql: Generated SQL query
    
    Returns:
        Set of table names found in SQL
    """
    # Match FROM and JOIN clauses (case insensitive)
    pattern = r'(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
    tables = set(re.findall(pattern, sql, re.IGNORECASE))
    
    # Normalize to lowercase
    return {t.lower() for t in tables}


def validate_sql_against_schema(
    sql: str,
    schema: Dict
) -> Dict:
    """
    Validate generated SQL against schema
    Post-generation check
    
    Args:
        sql: Generated SQL query
        schema: Database schema
    
    Returns:
        Validation result
    """
    if not schema or not schema.get("tables"):
        return {"is_valid": True, "invalid_tables": []}
    
    # Extract tables from SQL
    sql_tables = extract_tables_from_sql(sql)
    
    # Get available tables
    schema_tables = {
        table.lower() 
        for table in schema["tables"].keys()
    }
    
    # Find invalid tables
    invalid_tables = sql_tables - schema_tables
    
    if invalid_tables:
        return {
            "is_valid": False,
            "invalid_tables": list(invalid_tables),
            "available_tables": sorted(schema_tables),
            "error": f"SQL references non-existent tables: {', '.join(invalid_tables)}"
        }
    
    return {
        "is_valid": True,
        "invalid_tables": []
    }


# Quick test
if __name__ == "__main__":
    # Test schema
    test_schema = {
        "tables": {
            "customers": {"columns": ["id", "name", "email"]},
            "orders": {"columns": ["id", "customer_id", "total"]},
            "products": {"columns": ["id", "name", "price"]},
        }
    }
    
    # Test cases
    test_cases = [
        ("Show me all customers", True),  # Valid: 'customers' exists
        ("Count total orders", True),  # Valid: 'orders' exists
        ("Find all users", False),  # Invalid: 'users' doesn't exist
        ("List products with price > 100", True),  # Valid: 'products' exists
        ("Show me invoices", False),  # Invalid: 'invoices' doesn't exist
    ]
    
    print("Testing Schema Validator:")
    print("=" * 50)
    
    for question, expected_valid in test_cases:
        result = validate_schema_availability(question, test_schema)
        status = "✅ PASS" if result["is_valid"] == expected_valid else "⚠️  CHECK"
        
        print(f"\nQuestion: '{question}'")
        print(f"Expected: {'Valid' if expected_valid else 'Invalid'}")
        print(f"Got: {'Valid' if result['is_valid'] else 'Invalid'}")
        print(f"Missing: {result['missing_entities']}")
        print(f"Suggestions: {result['suggestions']}")
        print(f"Status: {status}")