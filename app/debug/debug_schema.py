#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 15 13:12:32 2025

@author: sanjana
"""

# debug_schema.py
import requests

API_BASE = "http://localhost:8000"

def check_schema_issue():
    print("🔍 Debugging Schema Issue")
    print("=" * 40)
    
    # Connect to demo database
    response = requests.post(f"{API_BASE}/connect_db", json={"demo": True}, timeout=15)
    data = response.json()
    
    if data.get("success"):
        schema_text = data.get("schema_text", "")
        schema_struct = data.get("schema", {})
        
        print(f"Schema text length: {len(schema_text)}")
        print(f"Schema text preview: {schema_text[:200]}...")
        print(f"Schema structure: {schema_struct}")
        
        # Check what tables are available
        if schema_struct:
            print(f"\nTables found: {list(schema_struct.keys())}")
            for table, info in schema_struct.items():
                print(f"  {table}: {len(info.get('columns', []))} columns")
        else:
            print("\n❌ No schema structure returned!")
            
    else:
        print(f"Connection failed: {data.get('error')}")

if __name__ == "__main__":
    check_schema_issue()