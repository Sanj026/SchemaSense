# -*- coding: utf-8 -*-
"""
Created on Sun Aug 24 23:10:59 2025

@author: Sanjana
"""

# test_schemasense.py
import requests
import time

# Base URL of your running FastAPI server
BASE_URL = "http://127.0.0.1:8000"

# Test cases: (question, expected_keywords)
test_cases = [
    ("Show all artists", ["SELECT", "artists"]),
    ("Show artists and their albums", ["JOIN", "artists", "albums"]),
    ("Find albums by Radiohead", ["WHERE", "Radiohead", "JOIN"]),
    ("Show only artist names", ["SELECT", "name", "FROM", "artists"]),
    ("List all albums", ["SELECT", "albums"]),
    ("Find albums by The Beatles", ["WHERE", "Beatles", "JOIN"]),
    ("How many albums does each artist have?", ["COUNT", "GROUP BY", "JOIN"]),
]

def test_schemasense():
    print("🧪 Starting SchemaSense Test Suite...\n")
    
    for i, (question, expected_keywords) in enumerate(test_cases, 1):
        print(f"=== TEST {i}: '{question}' ===")
        
        try:
            # Make API request
            response = requests.get(
                f"{BASE_URL}/generate?question={question}",
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_sql = result.get('generated_sql', '').upper()
                print(f"✅ Success: {result['question']}")
                print(f"   Generated SQL: {generated_sql}")
                
                # Check if expected keywords are in the SQL
                missing_keywords = []
                for keyword in expected_keywords:
                    if keyword.upper() not in generated_sql:
                        missing_keywords.append(keyword)
                
                if missing_keywords:
                    print(f"   ⚠️  Missing: {missing_keywords}")
                else:
                    print(f"   🎯 All expected keywords found!")
                    
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        
        print()  # Empty line between tests
        time.sleep(2)  # Wait 2 seconds between tests to avoid overwhelming the server

if __name__ == "__main__":
    test_schemasense()