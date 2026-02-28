#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 15 13:04:25 2025

@author: sanjana
"""

# test_everything.py
import requests
import json
import pandas as pd
import time

API_BASE = "http://localhost:8000"

class CompleteTester:
    def __init__(self):
        self.results = {}
        self.schema_text = None
    
    def test_backend_connection(self):
        """Test if backend server is running"""
        print("🔌 Testing Backend Connection...")
        try:
            response = requests.get(f"{API_BASE}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print("✓ Backend server running")
                print(f"  Message: {data.get('message')}")
                return True
            else:
                print(f"✗ Backend returned status: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Backend connection failed: {e}")
            return False
    
    def test_database_connection(self):
        """Test database connection"""
        print("\n🗄️ Testing Database Connection...")
        try:
            response = requests.post(f"{API_BASE}/connect_db", json={"demo": True}, timeout=15)
            data = response.json()
            
            if data.get("success"):
                self.schema_text = data.get("schema_text", "")
                print("✓ Database connection successful")
                print(f"  Schema loaded: {len(self.schema_text)} characters")
                return True
            else:
                print(f"✗ Database connection failed: {data.get('error')}")
                return False
        except Exception as e:
            print(f"✗ Database test failed: {e}")
            return False
    
    def test_sql_generation(self, question, expected_type="sql"):
        """Test SQL generation for a specific question"""
        print(f"\n🤖 Testing: '{question}'")
        
        try:
            payload = {
                "question": question,
                "schema": self.schema_text
            }
            
            response = requests.post(f"{API_BASE}/generate", json=payload, timeout=30)
            data = response.json()
            
            if "error" in data:
                print(f"✗ Generation error: {data['error']}")
                return False, None
            
            if "sql" in data:
                sql = data["sql"]
                engine = data.get("engine", "unknown")
                print(f"✓ SQL generated successfully")
                print(f"  Engine: {engine}")
                print(f"  SQL: {sql}")
                return True, sql
            
            if "type" in data and data["type"] == "clarification":
                print("? Question needs clarification")
                options = data.get("options", [])
                for opt in options:
                    print(f"  - {opt.get('interpretation')}")
                return "clarification", None
            
            print("✗ Unexpected response format")
            return False, None
            
        except Exception as e:
            print(f"✗ Generation failed: {e}")
            return False, None
    
    def test_sql_execution(self, sql, question):
        """Test if generated SQL executes successfully"""
        if not sql:
            return False
        
        print(f"⚡ Testing SQL execution...")
        
        try:
            payload = {
                "sql": sql,
                "question": question
            }
            
            response = requests.post(f"{API_BASE}/execute", json=payload, timeout=30)
            data = response.json()
            
            if data.get("success"):
                rows = len(data.get("data", []))
                print(f"✓ Execution successful - {rows} rows returned")
                if data.get("fixed"):
                    print("  🔧 Query was auto-corrected!")
                return True
            else:
                print(f"✗ Execution failed: {data.get('error')}")
                return False
                
        except Exception as e:
            print(f"✗ Execution error: {e}")
            return False
    
    def test_frontend_flow(self):
        """Test complete frontend-to-backend flow"""
        print("\n🌐 Testing Complete Flow...")
        
        test_cases = [
            {
                "question": "show all artists",
                "description": "Simple SELECT query"
            },
            {
                "question": "count all albums", 
                "description": "Aggregate function"
            },
            {
                "question": "show artists with their albums",
                "description": "JOIN query"
            },
            {
                "question": "find albums by artist id 1",
                "description": "WHERE clause"
            },
            {
                "question": "show me everything",
                "description": "Ambiguous query (should clarify)"
            }
        ]
        
        results = []
        for test in test_cases:
            print(f"\n📋 {test['description']}")
            print(f"   Question: '{test['question']}'")
            
            # Generate SQL
            success, sql = self.test_sql_generation(test["question"])
            
            if success == True and sql:
                # Test execution
                exec_success = self.test_sql_execution(sql, test["question"])
                results.append({
                    "question": test["question"],
                    "sql_generation": "✓",
                    "sql_execution": "✓" if exec_success else "✗",
                    "type": "sql"
                })
            elif success == "clarification":
                results.append({
                    "question": test["question"], 
                    "sql_generation": "?",
                    "sql_execution": "N/A",
                    "type": "clarification"
                })
            else:
                results.append({
                    "question": test["question"],
                    "sql_generation": "✗", 
                    "sql_execution": "N/A",
                    "type": "failed"
                })
        
        return results
    
    def run_complete_test(self):
        """Run all tests"""
        print("🚀 SCHEMASENSE COMPLETE SYSTEM TEST")
        print("=" * 60)
        
        # Test backend
        backend_ok = self.test_backend_connection()
        if not backend_ok:
            print("❌ Backend failed - stopping tests")
            return False
        
        # Test database
        db_ok = self.test_database_connection()
        if not db_ok:
            print("❌ Database failed - stopping tests")  
            return False
        
        # Test complete flow
        flow_results = self.test_frontend_flow()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        for result in flow_results:
            status = "✅" if result["sql_generation"] == "✓" and result["sql_execution"] in ["✓", "N/A"] else "❌"
            print(f"{status} {result['question']}")
            print(f"   Generation: {result['sql_generation']} | Execution: {result['sql_execution']} | Type: {result['type']}")
        
        # Calculate success rate
        successful = sum(1 for r in flow_results if r["sql_generation"] == "✓")
        total = len(flow_results)
        
        print(f"\n🎯 Success Rate: {successful}/{total} ({successful/total*100:.1f}%)")
        
        if successful == total:
            print("🎉 ALL SYSTEMS GO! Your SchemaSense is working perfectly!")
        elif successful >= total * 0.7:
            print("⚠️  Mostly working - some minor issues to fix")
        else:
            print("❌ Significant issues found - needs debugging")
        
        return successful > 0

def main():
    """Run the complete test suite"""
    print("Make sure your backend is running: uvicorn main:app --reload --port 8000")
    print("This test will check everything from database connection to SQL generation and execution.\n")
    
    tester = CompleteTester()
    success = tester.run_complete_test()
    
    if success:
        print("\n✅ Ready for Phase 1 completion!")
    else:
        print("\n🔧 Let's fix the issues before moving forward")

if __name__ == "__main__":
    main()