# -*- coding: utf-8 -*-
"""
Created on Tue Aug 26 15:48:34 2025

@author: Sanjana
"""
# test_schemasense.py
import requests
import time

# Base URL of your running API
BASE_URL = "http://127.0.0.1:8000/generate"

# Test cases with expected keywords to check
test_cases = [
    ("Show all artists", ["SELECT", "artists"]),
    ("List all albums", ["SELECT", "albums"]),
    ("Show artists and their albums", ["JOIN", "artists", "albums"]),
    ("Display albums with artist names", ["JOIN", "albums", "artists"]),
    ("Find albums by Radiohead", ["WHERE", "Radiohead", "JOIN"]),
    ("Show albums by The Beatles", ["WHERE", "Beatles", "JOIN"]),
    ("Find artist named Taylor Swift", ["WHERE", "Taylor Swift"]),
    ("Show only artist names", ["SELECT", "name", "FROM", "artists"]),
    ("Display album titles only", ["SELECT", "title", "FROM", "albums"]),
    ("How many albums does each artist have?", ["COUNT", "GROUP BY", "JOIN"]),
    ("Count total number of artists", ["COUNT", "artists"]),
    ("Show me data", ["SELECT"]),  # Vague query - just check it returns something valid
    ("Find songs by Radiohead", ["SELECT"])  # Should handle gracefully (no songs table)
]

def run_tests():
    print("🧪 Starting SchemaSense Test Suite...\n")
    print(f"Testing against: {BASE_URL}")
    print("=" * 60)
    
    for i, (question, expected_keywords) in enumerate(test_cases, 1):
        print(f"TEST {i:2d}: {question}")
        print("-" * 40)
        
        try:
            # Make the request
            response = requests.get(BASE_URL, params={"question": question}, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                # Check for errors
                if "error" in result:
                    print(f"❌ ERROR: {result['error']}")
                    continue
                
                # Extract the SQL query
                sql_query = result.get('generated_sql', '').upper()
                engine = result.get('engine', 'unknown')
                
                print(f"✅ Status: {response.status_code}")
                print(f"🤖 Engine: {engine}")
                print(f"📝 SQL: {sql_query}")
                
                # Check if expected keywords are present
                missing_keywords = []
                for keyword in expected_keywords:
                    if keyword.upper() not in sql_query:
                        missing_keywords.append(keyword)
                
                if missing_keywords:
                    print(f"⚠️  Missing keywords: {missing_keywords}")
                else:
                    print("🎯 All expected keywords found!")
                
                # Special checks
                if "LIMIT" not in sql_query and any(word in question.lower() for word in ["show", "list", "display"]):
                    print("💡 Suggestion: Consider adding LIMIT 10 for safety")
                    
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        
        print()  # Empty line between tests
        time.sleep(1)  # Brief pause to avoid overwhelming the server

if __name__ == "__main__":
    run_tests()