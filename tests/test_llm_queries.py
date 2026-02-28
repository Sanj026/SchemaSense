import requests
import json
import time

API_URL = "http://localhost:8000/regenerate_sql"

# --- MULTIPLE SCHEMAS TO PROVE NO HARDCODING ---

MUSIC_SCHEMA = """
albums(AlbumId integer, Title character varying, ArtistId integer)
artists(ArtistId integer, Name character varying)
tracks(TrackId integer, Name character varying, AlbumId integer, Composer character varying, Milliseconds integer, UnitPrice numeric)
"""

ECOMMERCE_SCHEMA = """
users(id integer, first_name character varying, last_name character varying, sign_up_date timestamp without time zone)
orders(id integer, user_id integer, order_date timestamp without time zone, total_amount numeric, status character varying)
products(id integer, name character varying, category character varying, price numeric, stock integer)
order_items(id integer, order_id integer, product_id integer, quantity integer, unit_price numeric)
"""

HEALTHCARE_SCHEMA = """
patients(patient_id integer, name character varying, dob date, gender character varying)
doctors(doctor_id integer, name character varying, specialty character varying, hospital_id integer)
appointments(appointment_id integer, patient_id integer, doctor_id integer, appointment_date timestamp without time zone, status character varying)
treatments(treatment_id integer, appointment_id integer, description character varying, cost numeric)
"""

TEST_CASES = [
    # General Logic / Noise
    {
        "name": "Noise / Irrelevant",
        "schema": MUSIC_SCHEMA,
        "question": "Hello what is the weather today?",
        "expected_low_confidence": True
    },
    
    # MUSIC DB TESTS
    {
        "name": "Simple Select (Music)",
        "schema": MUSIC_SCHEMA,
        "question": "Show me all the artists",
        "expected_low_confidence": False
    },
    {
        "name": "Case Insensitive Filtering (Music)",
        "schema": MUSIC_SCHEMA,
        "question": "Find tracks where the composer is Beethoven",
        "expected_low_confidence": False
    },
    
    # E-COMMERCE DB TESTS (Simulating MySQL)
    {
        "name": "Date Filtering (E-commerce - MySQL)",
        "schema": ECOMMERCE_SCHEMA,
        "question": "How many orders were placed in 2023?",
        "db_type": "mysql",
        "expected_low_confidence": False
    },
    {
        "name": "Complex 4-Table Join with Aggregation (E-commerce - MySQL)",
        "schema": ECOMMERCE_SCHEMA,
        "question": "List the top 3 users who bought the most products in the Electronics category",
        "db_type": "mysql",
        "expected_low_confidence": False
    },
    {
        "name": "Hallucinated Fields (E-commerce - MySQL)",
        "schema": ECOMMERCE_SCHEMA,
        "question": "Show me the credit card numbers of all users",
        "db_type": "mysql",
        "expected_low_confidence": True 
    },

    # HEALTHCARE DB TESTS
    {
        "name": "Conditional Logic & Join (Healthcare)",
        "schema": HEALTHCARE_SCHEMA,
        "question": "Find all cancelled appointments for Pediatricians",
        "expected_low_confidence": False
    },
    {
        "name": "Aggregate Sum & Grouping (Healthcare)",
        "schema": HEALTHCARE_SCHEMA,
        "question": "What is the total cost of treatments performed by each doctor?",
        "expected_low_confidence": False
    }
]


def run_tests():
    print("🚀 Starting RIGID LLM Query Generation Tests...")
    print("=" * 60)
    
    passed = 0
    total = len(TEST_CASES)
    
    for i, test in enumerate(TEST_CASES):
        print(f"\\nTest {i+1}: {test['name']}")
        print(f"Question: \\\"{test['question']}\\\"")
        
        payload = {
            "question": test["question"],
            "schema": test["schema"],
            "db_type": test.get("db_type", "postgresql")
        }
        
        try:
            start_time = time.time()
            response = requests.post(API_URL, json=payload, timeout=30)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                sql = data.get("sql", "")
                conf = data.get("confidence", 0.0)
                
                print(f"SQL Generated: {sql}")
                print(f"Confidence:    {conf:.2f}")
                print(f"Time Taken:    {elapsed:.2f}s")
                
                # Basic validation logic
                expected_low = test.get("expected_low_confidence", False)
                if expected_low and conf < 0.5:
                    print("✅ PASS: Correctly scored low confidence.")
                    passed += 1
                elif not expected_low and conf >= 0.5:
                    print("✅ PASS: Correctly generated high confidence SQL.")
                    passed += 1
                elif expected_low and conf >= 0.5:
                    print("❌ FAIL: Expected low confidence but got high confidence.")
                else:
                    print("❌ FAIL: Expected high confidence but got low confidence.")
                    
            else:
                print(f"❌ FAIL: API returned status code {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"❌ FAIL: Request failed - {e}")
            
        # Small delay to respect rate limits
        time.sleep(2)

    print("\\n" + "=" * 60)
    print(f"🏁 Rigid Test Suite Complete: {passed}/{total} Passed")

if __name__ == "__main__":
    run_tests()
