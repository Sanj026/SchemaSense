# -*- coding: utf-8 -*-
"""
Created on Wed Sep 10 23:06:02 2025
@author: Sanjana
"""

# -*- coding: utf-8 -*-
"""
SchemaSense Frontend - Production Version
Natural Language to SQL Analytics Platform
"""

import streamlit as st
import requests
import pandas as pd
import time
import plotly.express as px
import numpy as np
import base64
import os
from io import BytesIO

# Read backend URL from environment variable (set on Render), fallback to localhost for local dev
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(
    page_title="SchemaSense - Production NL2SQL",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Custom CSS for better UX + RESPONSIVE DESIGN
st.markdown("""
<style>
    /* Responsive font sizes */
    .main-header {
        font-size: clamp(1.5rem, 4vw, 2.5rem);  /* Scales with viewport */
        font-weight: 700;
        color: #1f77b4;
    }
    
    /* Streamlit title responsive */
    h1 {
        font-size: clamp(1.5rem, 3vw, 2rem) !important;
    }
    
    h2 {
        font-size: clamp(1.2rem, 2.5vw, 1.5rem) !important;
    }
    
    h3 {
        font-size: clamp(1rem, 2vw, 1.25rem) !important;
    }
    
    /* Responsive text */
    p, li, .stMarkdown {
        font-size: clamp(0.875rem, 1.5vw, 1rem) !important;
    }
    
    /* Button text responsive */
    .stButton button {
        font-size: clamp(0.75rem, 1.5vw, 0.875rem) !important;
    }
    
    /* Input text responsive */
    .stTextInput input {
        font-size: clamp(0.875rem, 1.5vw, 1rem) !important;
    }
    
    /* Confidence scores */
    .confidence-high { color: #2ecc71; font-weight: bold; }
    .confidence-medium { color: #f39c12; font-weight: bold; }
    .confidence-low { color: #e74c3c; font-weight: bold; }
    
    /* Responsive containers */
    @media (max-width: 768px) {
        .stColumn {
            min-width: 100% !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# ------------------- SESSION STATE INIT -------------------
session_defaults = {
    "page": "connect",
    "db_connected": False,
    "demo_connected": False,
    "user_db_connected": False,
    "connection_type": None,
    "connection_id": None,
    "db_type": None,
    "schema_struct": None,
    "schema_text": "",
    "schema_last_fetched": None,
    "generated_sql": "",
    "sql_confidence": None,
    "sql_suggestions": [],
    "generated_sql_result": None,
    "execution_result": None,
    "last_question": "",
    "engine_used": None,
    "data_summary": None,
    "query_history": [],
    "auto_generate": False
}

for key, default_value in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default_value


# ------------------- HELPER FUNCTIONS -------------------

def is_schema_fresh():
    """Check if schema is less than 5 minutes old"""
    if not st.session_state.get("schema_last_fetched"):
        return False
    return time.time() - st.session_state.schema_last_fetched < 300


def auto_generate_visualizations(df):
    """Generate appropriate visualizations based on data"""
    if df.empty or len(df) <= 1:
        return None
    
    visualizations = []
    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    category_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
    date_columns = [
        col for col in df.columns 
        if any(term in str(col).lower() for term in ['date', 'time', 'year', 'month', 'day'])
    ]
    
    # Time series chart
    if date_columns and numeric_columns and len(df) > 5:
        try:
            fig = px.line(
                df,
                x=date_columns[0],
                y=numeric_columns[0],
                title=f"{numeric_columns[0]} over Time"
            )
            visualizations.append(("Time Series", fig))
        except:
            pass
    
    # Bar chart
    if category_columns and numeric_columns and len(df) <= 20:
        try:
            fig = px.bar(
                df,
                x=category_columns[0],
                y=numeric_columns[0],
                title=f"{numeric_columns[0]} by {category_columns[0]}"
            )
            visualizations.append(("Bar Chart", fig))
        except:
            pass
    
    # Pie chart
    if category_columns and numeric_columns and len(df) <= 10:
        try:
            fig = px.pie(
                df,
                names=category_columns[0],
                values=numeric_columns[0],
                title=f"Distribution of {numeric_columns[0]}"
            )
            visualizations.append(("Pie Chart", fig))
        except:
            pass
    
    # Scatter plot
    if len(numeric_columns) >= 2 and len(df) > 5:
        try:
            fig = px.scatter(
                df,
                x=numeric_columns[0],
                y=numeric_columns[1],
                title=f"{numeric_columns[1]} vs {numeric_columns[0]}"
            )
            visualizations.append(("Scatter Plot", fig))
        except:
            pass
    
    return visualizations if visualizations else None


def download_csv(df, filename="query_results.csv"):
    """Generate CSV download link"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">📥 Download CSV</a>'
    return href


# ------------------- CONNECTION PAGE -------------------

def show_connection_page():
    """Landing page with dropdown DB selector + working demo preview"""
    
    st.title("SchemaSense — Connect a Database")
    st.markdown("Choose a demo database or connect your own database (Postgres, MySQL, SQLite).")
    st.write("**Demo DB**: pre-populated sample database to play with (SELECT queries only).")
    
    # Two-column layout
    col1, col2 = st.columns([1, 1])
    
    # LEFT COLUMN: Demo Database
    with col1:
        st.subheader("🎯 Demo Database")
        st.write("Explore with sample data")
        if st.button("Use Demo Database", use_container_width=True, type="primary"):
            with st.spinner("Connecting to demo database..."):
                try:
                    res = requests.post(
                        f"{API_BASE}/connect_db",
                        json={"demo": True},
                        timeout=20
                    )
                    data = res.json()
                    
                    if data.get("success"):
                        st.session_state.db_connected = True
                        st.session_state.demo_connected = True
                        st.session_state.connection_type = "demo"
                        st.session_state.connection_id = None
                        st.session_state.db_type = "postgresql"
                        st.session_state.schema_text = data.get("schema_text", "")
                        st.session_state.schema_struct = data.get("schema_struct", {})
                        st.session_state.schema_last_fetched = time.time()
                        st.session_state.page = "main"
                        st.success("✅ Connected to demo database!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(f"Connection failed: {data.get('error')}")
                
                except Exception as e:
                    st.error(f"Connection error: {e}")
    
    # RIGHT COLUMN: Custom Database
    with col2:
        st.subheader("🔌 Connect Your Database")
        
        # DROPDOWN to select connection method
        connection_method = st.selectbox(
            "Connection Method",
            ["Connection String", "PostgreSQL", "MySQL", "SQLite"],
            help="Choose how to connect to your database"
        )
        
        # CONNECTION STRING
        if connection_method == "Connection String":
            conn_str = st.text_input(
                "Connection String",
                placeholder="postgresql://user:pass@host:5432/dbname",
                type="default"
            )
            
            if st.button("Connect", use_container_width=True):
                if not conn_str:
                    st.warning("⚠️ Please enter a connection string")
                else:
                    with st.spinner("Connecting..."):
                        try:
                            res = requests.post(
                                f"{API_BASE}/connect_db",
                                json={"connection_string": conn_str},
                                timeout=20
                            )
                            data = res.json()
                            
                            if data.get("success"):
                                st.session_state.db_connected = True
                                st.session_state.user_db_connected = True
                                st.session_state.connection_type = "custom"
                                st.session_state.connection_id = data.get("connection_id")
                                st.session_state.db_type = data.get("db_type", "postgresql")
                                st.session_state.schema_text = data.get("schema_text", "")
                                st.session_state.schema_struct = data.get("schema_struct", {})
                                st.session_state.schema_last_fetched = time.time()
                                st.session_state.page = "main"
                                st.success(f"✅ Connected to {data.get('db_type', 'database')}!")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error(f"❌ {data.get('error')}")
                        
                        except Exception as e:
                            st.error(f"❌ Connection error: {e}")
        
        # POSTGRESQL FORM
        elif connection_method == "PostgreSQL":
            host = st.text_input("Host", value="localhost")
            port = st.text_input("Port", value="5432")
            database = st.text_input("Database Name")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if st.button("Connect", use_container_width=True):
                if all([host, port, database, username, password]):
                    conn_str = f"postgresql://{username}:{password}@{host}:{port}/{database}"
                    
                    with st.spinner("Connecting..."):
                        try:
                            res = requests.post(
                                f"{API_BASE}/connect_db",
                                json={"connection_string": conn_str},
                                timeout=20
                            )
                            data = res.json()
                            
                            if data.get("success"):
                                st.session_state.db_connected = True
                                st.session_state.user_db_connected = True
                                st.session_state.connection_type = "custom"
                                st.session_state.connection_id = data.get("connection_id")
                                st.session_state.db_type = "postgresql"
                                st.session_state.schema_text = data.get("schema_text", "")
                                st.session_state.schema_struct = data.get("schema_struct", {})
                                st.session_state.schema_last_fetched = time.time()
                                st.session_state.page = "main"
                                st.success("✅ Connected to PostgreSQL!")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error(f"❌ {data.get('error')}")
                        
                        except Exception as e:
                            st.error(f"❌ {e}")
                else:
                    st.warning("⚠️ Please fill in all fields")
        
        # MYSQL FORM
        elif connection_method == "MySQL":
            host = st.text_input("Host", value="localhost")
            port = st.text_input("Port", value="3306")
            database = st.text_input("Database Name")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if st.button("Connect", use_container_width=True):
                if all([host, port, database, username, password]):
                    conn_str = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
                    
                    with st.spinner("Connecting..."):
                        try:
                            res = requests.post(
                                f"{API_BASE}/connect_db",
                                json={"connection_string": conn_str},
                                timeout=20
                            )
                            data = res.json()
                            
                            if data.get("success"):
                                st.session_state.db_connected = True
                                st.session_state.user_db_connected = True
                                st.session_state.connection_type = "custom"
                                st.session_state.connection_id = data.get("connection_id")
                                st.session_state.db_type = "mysql"
                                st.session_state.schema_text = data.get("schema_text", "")
                                st.session_state.schema_struct = data.get("schema_struct", {})
                                st.session_state.schema_last_fetched = time.time()
                                st.session_state.page = "main"
                                st.success("✅ Connected to MySQL!")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error(f"❌ {data.get('error')}")
                        
                        except Exception as e:
                            st.error(f"❌ {e}")
                else:
                    st.warning("⚠️ Please fill in all fields")
        
        # SQLITE FORM
        elif connection_method == "SQLite":
            db_path = st.text_input("Database File Path", placeholder="/path/to/database.db")
            
            if st.button("Connect", use_container_width=True):
                if db_path:
                    conn_str = f"sqlite:///{db_path}"
                    
                    with st.spinner("Connecting..."):
                        try:
                            res = requests.post(
                                f"{API_BASE}/connect_db",
                                json={"connection_string": conn_str},
                                timeout=20
                            )
                            data = res.json()
                            
                            if data.get("success"):
                                st.session_state.db_connected = True
                                st.session_state.user_db_connected = True
                                st.session_state.connection_type = "custom"
                                st.session_state.connection_id = data.get("connection_id")
                                st.session_state.db_type = "sqlite"
                                st.session_state.schema_text = data.get("schema_text", "")
                                st.session_state.schema_struct = data.get("schema_struct", {})
                                st.session_state.schema_last_fetched = time.time()
                                st.session_state.page = "main"
                                st.success("✅ Connected to SQLite!")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error(f"❌ {data.get('error')}")
                        
                        except Exception as e:
                            st.error(f"❌ {e}")
                else:
                    st.warning("⚠️ Please enter database file path")
    
    # DEMO DATABASE PREVIEW (Working version)
    st.markdown("---")
    st.subheader("📊 Demo Database Preview")
    st.write("See what's in the demo database before connecting:")
    
    with st.spinner("Loading demo preview..."):
        try:
            demo_resp = requests.get(f"{API_BASE}/demo_preview", timeout=15)
            if demo_resp.status_code == 200:
                data = demo_resp.json()
                
                if data.get("success") and data.get("tables"):
                    # Show tables in columns
                    tables_list = list(data["tables"].items())
                    num_cols = min(len(tables_list), 3)
                    preview_cols = st.columns(num_cols)
                    
                    for idx, (table_name, table_info) in enumerate(tables_list[:3]):
                        with preview_cols[idx]:
                            st.markdown(f"**📊 {table_name}**")
                            st.caption(f"{len(table_info['columns'])} columns")
                            
                            if table_info.get('preview'):
                                preview_df = pd.DataFrame(table_info['preview'])
                                st.dataframe(
                                    preview_df.head(3),
                                    use_container_width=True,
                                    height=150
                                )
                            else:
                                st.info("_No data_")
                else:
                    st.warning("⚠️ Demo preview unavailable - check if backend is running")
            else:
                st.warning("⚠️ Could not load demo preview - is backend running?")
        
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to backend. Please start the backend server first!")
        except Exception as e:
            st.warning(f"⚠️ Demo preview unavailable: {str(e)}")


# ------------------- MAIN PAGE -------------------

def show_main_page():
    """Main query interface with full features"""
    
    st.title("📊 SchemaSense: Natural Language to SQL")
    st.markdown("**Ask questions → Generate SQL → Execute → Visualize**")
    
    # ============ SIDEBAR ============
    with st.sidebar:
        st.header("⚙️ Database Connection")
        
        # Connection status
        if st.session_state.demo_connected:
            st.success(f"🎯 Demo Database ({st.session_state.db_type})")
        elif st.session_state.user_db_connected:
            st.success(f"🔌 Custom Database ({st.session_state.db_type})")
        
        if st.button("🔄 Change Database"):
            # Clear all state except history
            for key in session_defaults:
                if key != "query_history":
                    st.session_state[key] = session_defaults[key]
            st.session_state.page = "connect"
            st.rerun()
        
        st.markdown("---")
        
        # Schema display
        if st.session_state.schema_text:
            with st.expander("📋 Database Schema", expanded=False):
                st.text(st.session_state.schema_text)
        
        st.markdown("---")
        
        # Query History
        st.subheader("📜 Query History")
        if st.session_state.query_history:
            history = st.session_state.query_history[::-1]  # Reverse chronological
            for i, q in enumerate(history[:10]):  # Show last 10
                with st.expander(f"Q{len(history)-i}: {q['question'][:40]}..."):
                    st.code(q["sql"], language="sql")
                    if q.get("result"):
                        st.caption(f"Rows: {len(q['result'])}")
                    if q.get("explanation"):
                        st.info(f"💡 {q['explanation']}")
                    if st.button("🔁 Re-run", key=f"rerun_{i}"):
                        st.session_state.last_question = q["question"]
                        st.session_state.generated_sql = q["sql"]
                        st.rerun()
        else:
            st.write("_No queries yet_")
        
        st.markdown("---")
        
        # Demo Database Preview (if demo)
        if st.session_state.demo_connected:
            st.subheader("📂 Demo Data Preview")
            try:
                demo_resp = requests.get(f"{API_BASE}/demo_preview", timeout=15).json()
                if demo_resp.get("success"):
                    for table, info in demo_resp["tables"].items():
                        with st.expander(f"📊 {table}", expanded=False):
                            st.caption(f"**Columns:** {', '.join(info['columns'])}")
                            if info['preview']:
                                st.dataframe(
                                    pd.DataFrame(info['preview']),
                                    use_container_width=True,
                                    height=150
                                )
                            else:
                                st.write("_Empty table_")
                else:
                    st.warning("Demo preview unavailable")
            except:
                pass
        
        st.markdown("---")
        
        # How to Use
        st.subheader("💡 How to Use")
        st.write("1️⃣ Ask in plain English")
        st.write("2️⃣ Generate SQL automatically")
        st.write("3️⃣ Review & execute")
        st.write("4️⃣ Export or refine")
        
        st.markdown("---")
        
        # Example Questions (NON-CLICKABLE - just for inspiration)
        st.subheader("🎯 Example Questions")
        if st.session_state.demo_connected:
            # Demo-specific examples based on actual schema
            st.write("_Try asking:_")
            st.write("• Show me all artists")
            st.write("• Count tracks by genre")
            st.write("• Find top 10 albums by track count")
            st.write("• Display all tracks with their albums")
            st.write("• What are the longest songs?")
        else:
            # Generic examples for custom DB
            st.write("_Examples to try:_")
            st.write("• Show me all records from [table]")
            st.write("• Count items by [category]")
            st.write("• Find top 10 [items] by [metric]")
            st.write("• Display [field] grouped by [field]")
            st.write("• What are the highest [values]?")

    
    # ============ MAIN CONTENT ============
    
    # Question input
    question = st.text_input(
        "💬 Ask anything about your data",
        value=st.session_state.last_question,
        placeholder="e.g., Show me top 10 artists by track count",
        help="Describe what you want in plain English"
    )
    
    # Suggested Queries (from backend - demo-specific)
    if st.session_state.demo_connected:
        try:
            suggest_resp = requests.get(f"{API_BASE}/suggest_queries", timeout=10).json()
            if suggest_resp.get("success") and suggest_resp.get("queries"):
                st.markdown("**💡 Suggested Queries (based on demo database):**")
                suggest_cols = st.columns(min(len(suggest_resp["queries"]), 5))
                for idx, q in enumerate(suggest_resp["queries"][:5]):
                    with suggest_cols[idx]:
                        if st.button(
                            q["question"][:30] + "..." if len(q["question"]) > 30 else q["question"],
                            key=f"suggest_{q['created_at']}",
                            help=q.get("description", ""),
                            use_container_width=True
                        ):
                            st.session_state.last_question = q["question"]
                            st.session_state.auto_generate = True
                            st.rerun()
        except:
            pass
    
    st.markdown("---")
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        generate_btn = st.button(
            "🚀 Generate SQL",
            type="primary",
            use_container_width=True
        )
    
    with col2:
        # Enable execute only if SQL is valid SELECT query
        is_valid_sql = False
        if st.session_state.generated_sql:
            sql = st.session_state.generated_sql
            if isinstance(sql, str) and sql.lower().strip().startswith(('select', 'with')):
                is_valid_sql = True
        
        execute_btn = st.button(
            "▶️ Execute Query",
            disabled=not is_valid_sql,
            use_container_width=True
        )
    
    with col3:
        # PHASE 2: Regenerate button
        regenerate_btn = st.button(
            "🔄 Regenerate SQL",
            disabled=not st.session_state.last_question,
            use_container_width=True,
            help="Try generating SQL again with different approach"
        )
    
    # ============ GENERATE SQL ============
    if generate_btn or st.session_state.get("auto_generate"):
        st.session_state.auto_generate = False
        
        if not question:
            st.warning("⚠️ Please enter a question first!")
        else:
            with st.spinner("🤖 Generating SQL..."):
                try:
                    payload = {
                        "question": question,
                        "schema": st.session_state.schema_text,
                        "db_type": st.session_state.db_type
                    }
                    
                    if st.session_state.connection_id:
                        payload["connection_id"] = st.session_state.connection_id
                    
                    response = requests.post(
                        f"{API_BASE}/generate",
                        json=payload,
                        timeout=30
                    )
                    result = response.json()
                    
                    if result.get("type") == "sql" and result.get("sql"):
                        st.session_state.generated_sql = result["sql"]
                        st.session_state.engine_used = result.get("engine", "AI")
                        st.session_state.last_question = question
                        # Clear previous results so old charts/data never show under a new query
                        st.session_state.execution_result = None
                        st.session_state.data_summary = None
                        st.success(f"✅ SQL generated (Engine: {result.get('engine', 'AI')})")
                        st.rerun()
                    
                    elif result.get("type") == "error":
                        st.error(f"❌ {result.get('error')}")
                        tips = result.get("suggestions", [])
                        if tips:
                            for tip in tips:
                                st.info(f"💡 {tip}")
                    
                    elif result.get("type") == "clarification":
                        st.info("🤔 Your question needs clarification")
                
                except Exception as e:
                    st.error(f"❌ Generation error: {e}")
    
    # ============ REGENERATE SQL (PHASE 2) ============
    if regenerate_btn:
        with st.spinner("🔄 Regenerating SQL with improved approach..."):
            try:
                payload = {
                    "question": st.session_state.last_question,
                    "schema": st.session_state.schema_text,
                    "previous_sql": st.session_state.generated_sql,
                    "db_type": st.session_state.db_type
                }
                
                response = requests.post(
                    f"{API_BASE}/regenerate_sql",
                    json=payload,
                    timeout=30
                )
                result = response.json()
                
                if result.get("sql"):
                    st.session_state.generated_sql = result["sql"]
                    st.session_state.engine_used = result.get("engine", "AI")
                    st.session_state.sql_confidence = result.get("confidence", 0.5)
                    st.session_state.sql_suggestions = result.get("suggestions", [])
                    st.success("✅ SQL regenerated!")
                    st.rerun()
            
            except Exception as e:
                st.error(f"❌ Regeneration error: {e}")
    
    # ============ EXECUTE QUERY ============
    if execute_btn and st.session_state.generated_sql:
        with st.spinner("⚡ Executing query..."):
            try:
                payload = {
                    "sql": st.session_state.generated_sql,
                    "question": st.session_state.last_question
                }
                
                if st.session_state.connection_id:
                    payload["connection_id"] = st.session_state.connection_id
                
                res = requests.post(
                    f"{API_BASE}/execute",
                    json=payload,
                    timeout=30
                )
                execute_result = res.json()
                
                if execute_result.get("success"):
                    st.session_state.execution_result = execute_result
                    
                    # Get data summary
                    try:
                        summary_resp = requests.post(
                            f"{API_BASE}/summarize_data",
                            json={"data": execute_result.get("data", [])},
                            timeout=10
                        ).json()
                        
                        if summary_resp.get("success"):
                            st.session_state.data_summary = summary_resp["summary"]
                    except:
                        st.session_state.data_summary = None
                    
                    # Add to history
                    st.session_state.query_history.append({
                        "question": st.session_state.last_question,
                        "sql": st.session_state.generated_sql,
                        "result": execute_result.get("data", []),
                        "explanation": execute_result.get("explanation", ""),
                        "timestamp": time.time()
                    })
                    
                    st.success("✅ Query executed successfully!")
                    st.rerun()
                
                else:
                    # Error handling
                    if execute_result.get("type") == "invalid_schema":
                        st.error("❌ Query references non-existent tables")
                        st.info(
                            f"**Available tables:** {', '.join(execute_result.get('available_tables', []))}"
                        )
                    else:
                        st.error(f"❌ Execution failed: {execute_result.get('error')}")
            
            except Exception as e:
                st.error(f"❌ Execution error: {e}")
    
    # ============ DISPLAY GENERATED SQL ============
    if st.session_state.generated_sql:
        st.markdown("---")
        st.subheader("📝 Generated SQL Query")
        
        # Show confidence score if available (PHASE 2)
        if st.session_state.sql_confidence is not None:
            confidence = st.session_state.sql_confidence
            if confidence >= 0.8:
                confidence_class = "confidence-high"
                confidence_text = "High"
            elif confidence >= 0.5:
                confidence_class = "confidence-medium"
                confidence_text = "Medium"
            else:
                confidence_class = "confidence-low"
                confidence_text = "Low"
            
            st.markdown(
                f"**Confidence Score:** <span class='{confidence_class}'>{confidence_text} ({confidence:.1%})</span>",
                unsafe_allow_html=True
            )
        
        st.code(st.session_state.generated_sql, language="sql")
        
        # Show suggestions if any (PHASE 2)
        if st.session_state.sql_suggestions:
            with st.expander("💡 Improvement Suggestions"):
                for suggestion in st.session_state.sql_suggestions:
                    st.write(f"• {suggestion}")
    
    # ============ DISPLAY RESULTS ============
    if st.session_state.execution_result:
        st.markdown("---")
        st.subheader("📊 Query Results")
        
        exec_data = st.session_state.execution_result
        
        # Query explanation
        if exec_data.get("explanation"):
            st.info(f"💡 **Insight:** {exec_data['explanation']}")
        
        # Data table
        df = pd.DataFrame(exec_data.get("data", []))
        
        if not df.empty:
            # Metrics row
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("📊 Rows", len(df))
            col2.metric("📋 Columns", len(df.columns))
            col3.metric("💾 Memory", f"{df.memory_usage(deep=True).sum() / 1024:.1f} KB")
            col4.metric("🤖 Engine", st.session_state.engine_used or "AI")
            
            # Data table
            st.dataframe(df, use_container_width=True, height=400)
            
            # PHASE 2: CSV Export
            st.markdown("---")
            col_export1, col_export2 = st.columns([1, 4])
            with col_export1:
                if st.button("📥 Export to CSV", use_container_width=True):
                    try:
                        export_resp = requests.post(
                            f"{API_BASE}/export_csv",
                            json={
                                "data": exec_data.get("data", []),
                                "filename": f"query_results_{int(time.time())}.csv"
                            },
                            timeout=10
                        ).json()
                        
                        if export_resp.get("success"):
                            csv_content = base64.b64decode(export_resp["csv_content"])
                            st.download_button(
                                label="💾 Download CSV File",
                                data=csv_content,
                                file_name=export_resp["filename"],
                                mime="text/csv",
                                use_container_width=True
                            )
                    except Exception as e:
                        st.error(f"Export failed: {e}")
            
            # Chart relevance
            chart_info = exec_data.get("chart", {})
            is_chart_relevant = chart_info.get("is_relevant", False)
            insight = chart_info.get("insight")
            reason = chart_info.get("reason")
            
            # Show chart insight
            if insight:
                st.success(f"📈 **Chart Insight:** {insight}")
            
            # Visualization decision
            show_charts = is_chart_relevant or st.checkbox(
                "📊 Show visualizations anyway",
                help="Override automatic chart relevance check"
            )
            
            if show_charts:
                st.markdown("---")
                st.subheader("📈 Automatic Visualizations")
                
                visualizations = auto_generate_visualizations(df)
                
                if visualizations:
                    tabs = st.tabs([viz[0] for viz in visualizations])
                    
                    for tab, (viz_type, fig) in zip(tabs, visualizations):
                        with tab:
                            st.plotly_chart(fig, use_container_width=True)
                            st.caption(f"Auto-generated {viz_type}")
                else:
                    st.info("No suitable visualizations generated")
            
            else:
                st.info(f"📉 **Charts hidden:** {reason or 'Results not suitable for visualization'}")
        
        else:
            st.warning("⚠️ Query returned no rows")
        
        # Data summary
        if st.session_state.data_summary:
            st.markdown("---")
            with st.expander("📊 Data Summary & Statistics", expanded=False):
                summary = st.session_state.data_summary
                
                st.write(f"**Total Rows:** {summary['row_count']}")
                st.write(f"**Total Columns:** {summary['column_count']}")
                
                st.markdown("### Column Details")
                for col, info in summary["columns"].items():
                    st.markdown(f"#### `{col}`")
                    st.write(f"**Type:** {info['dtype']}")
                    st.write(f"**Missing:** {info['missing']} values")
                    
                    if "mean" in info:
                        st.write(
                            f"**Stats:** Min={info['min']}, Max={info['max']}, Avg={round(info['mean'], 2)}"
                        )
                    
                    if "top_values" in info:
                        st.write("**Top Values:**")
                        st.json(info["top_values"])


# ================= ROUTING =================

if st.session_state.page == "connect":
    show_connection_page()
elif st.session_state.page == "main":
    show_main_page()