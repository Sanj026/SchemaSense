# -*- coding: utf-8 -*-
"""
Created on Fri Sep 19 22:30:00 2025

@author: Sanjana
"""

# debug_clarification.py
import requests
import json

API_BASE = "http://localhost:8000"

def test_ambiguity_detection():
    """Test the ambiguity detection specifically"""
    print("Testing ambiguity detection...")
    
    test_questions = [
        "show artists",  # Should be clear
        "show data",     # Should be ambiguous
        "get results"    # Should be ambiguous
    ]
    
    for question in test_questions:
        print(f"\nTesting: '{question}'")
        
        # Test the ambiguity check directly
        ambiguity_prompt = f"""
        Is this question ambiguous or could it have multiple interpretations?
        Question: "{question}"
        
        Respond with ONLY JSON: {{"ambiguous": true|false}}
        """
        
        try:
            # Call your AI directly
            from llm import generate_sql
            result = generate_sql(ambiguity_prompt, "artists(id, name), albums(id, title, artist_id)")
            
            print(f"AI raw response: {result}")
            
            # Try to parse
            try:
                parsed = json.loads(result)
                print(f"Parsed JSON: {parsed}")
            except json.JSONDecodeError:
                print("Response is not valid JSON")
                print(f"Response type: {type(result)}")
                
        except Exception as e:
            print(f"Error in ambiguity check: {e}")

def test_clarification_generation():
    """Test the clarification generation specifically"""
    print("\n\nTesting clarification generation...")
    
    ambiguous_question = "show data"
    
    try:
        payload = {
            "question": ambiguous_question,
            "schema": "artists(id, name), albums(id, title, artist_id)"
        }
        
        response = requests.post(f"{API_BASE}/clarify", json=payload, timeout=30)
        data = response.json()
        
        print(f"Clarification endpoint response: {data}")
        
    except Exception as e:
        print(f"Error calling clarification endpoint: {e}")

if __name__ == "__main__":
    test_ambiguity_detection()
    test_clarification_generation()