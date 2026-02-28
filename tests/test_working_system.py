#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 15 13:10:09 2025

@author: sanjana
"""

# test_working_system.py
import requests
import json
import time

API_BASE = "http://localhost:8000"

def test_complete_workflow():
    """Test the complete NL→SQL→Results workflow"""
    print("🚀 Testing Complete SchemaSense Workflow")
    print("=" * 50)
    
    # Step 1: Connect to demo database
    print("1. Connecting to demo database...")
    try:
        response = requests.post(f"{API_BASE}/connect_db", json={"demo": True}, timeout=15)
        data = response.json()
        
        if data.get("success"):
            schema_text = data.get("schema_text", "")
            print("✅ Database connected successfully!")
            print(f"   Schema loaded: {len(schema_text)} characters")
        else:
            print(f"❌ Database connection failed: {data.get('error')}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False
    
    # Step 2: Test SQL generation with various queries
    test_queries = [
        "show all artists",
        "count all albums",
        "show artists with their albums", 
        "find albums by artist id 1",
        "show top 5 artists"
    ]
    
    print("\n2. Testing SQL Generation:")
    print("-" * 30)
    
    for i, question in enumerate(test_queries, 1):
        print(f"\nQuery {i}: '{question}'")
        
        try:
            payload = {
                "question": question,
                "schema": schema_text
            }
            
            response = requests.post(f"{API_BASE}/generate", json=payload, timeout=30)
            data = response.json()
            
            if "error" in data:
                print(f"   ❌ Generation error: {data['error']}")
                continue
                
            if "sql" in data:
                sql = data["sql"]
                engine = data.get("engine", "unknown")
                print(f"   ✅ SQL generated ({engine})")
                print(f"   SQL: {sql}")
                
                # Step 3: Test execution
                exec_payload = {
                    "sql": sql,
                    "question": question
                }
                
                exec_response = requests.post(f"{API_BASE}/execute", json=exec_payload, timeout=30)
                exec_data = exec_response.json()
                
                if exec_data.get("success"):
                    rows = len(exec_data.get("data", []))
                    print(f"   ✅ Execution successful - {rows} rows")
                    if exec_data.get("fixed"):
                        print("   🔧 Query was auto-corrected!")
                else:
                    print(f"   ❌ Execution failed: {exec_data.get('error')}")
                    
            elif "type" in data and data["type"] == "clarification":
                print("   ❓ Needs clarification")
                options = data.get("options", [])
                for opt in options[:2]:  # Show first 2 options
                    print(f"     - {opt.get('interpretation')}")
            else:
                print(f"   ❓ Unexpected response: {data}")
                
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
    
    # Step 4: Test clarification system
    print("\n3. Testing Clarification System:")
    print("-" * 30)
    
    ambiguous_queries = [
        "show data",
        "get results",
        "show me everything"
    ]
    
    for query in ambiguous_queries:
        print(f"\nAmbiguous query: '{query}'")
        try:
            payload = {
                "question": query,
                "schema": schema_text
            }
            
            response = requests.post(f"{API_BASE}/generate", json=payload, timeout=30)
            data = response.json()
            
            if "type" in data and data["type"] == "clarification":
                print("   ✅ Correctly identified as ambiguous")
                options = data.get("options", [])
                print(f"   Options: {len(options)} interpretations")
            elif "sql" in data:
                print("   ⚠️  Generated SQL instead of clarification")
                print(f"   SQL: {data['sql'][:100]}...")
            else:
                print(f"   ❓ Unexpected: {data}")
                
        except Exception as e:
            print(f"   ❌ Clarification test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Test completed! Check results above.")
    return True

if __name__ == "__main__":
    test_complete_workflow()