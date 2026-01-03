import streamlit as st
import requests
import time
from datetime import datetime

# 1. Page Configuration
st.set_page_config(
    page_title="FreshQuery | Live RAG",
    page_icon="🌐",
    layout="wide" # Switched to wide for better partitioning
)

# 2. Custom CSS for better UI partitioning
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .answer-container {
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        background-color: #0000000a;
        margin-bottom: 20px;
    }
    .source-card {
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #007bff;
        background-color: #0000000f;
        margin-bottom: 10px;
        font-size: 0.9rem;
    }
    .status-online { color: #28a745; font-weight: bold; }
    .status-offline { color: #dc3545; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 3. Helper Functions for Real-Time Status
def check_service(url):
    try:
        response = requests.get(url, timeout=2)
        return True if response.status_code < 500 else False
    except:
        return False

# 4. Sidebar: Accurate System Status
with st.sidebar:
    st.title("⚙️ System Monitor")
    st.info(f"Current Time: {datetime.now().strftime('%H:%M:%S')}")
    
    # Real-time health checks
    whoogle_status = check_service("http://localhost:5000")
    backend_status = check_service("http://localhost:8000")
    
    st.write("---")
    col1, col2 = st.columns(2)
    with col1:
        st.write("Whoogle Search")
        st.write("Backend API")
    with col2:
        st.markdown(f"<span class='{'status-online' if whoogle_status else 'status-offline'}'>{'● Online' if whoogle_status else '● Offline'}</span>", unsafe_allow_html=True)
        st.markdown(f"<span class='{'status-online' if backend_status else 'status-offline'}'>{'● Online' if backend_status else '● Offline'}</span>", unsafe_allow_html=True)
    
    st.write("---")
    st.subheader("Model Configuration")
    st.code("Model: Mistral-7B\nEnv: Ephemeral RAM\nPolicy: Majority Consensus")
    
    if st.button("🔄 Refresh Status"):
        st.rerun()

# 5. Main UI Layout
st.title("🌐 FreshQuery")
st.markdown("##### *Live Web-Grounded Question Answering Engine*")

# Partitioning the search area
search_col, _ = st.columns([2, 1])
with search_col:
    query = st.text_input("What would you like to know?", placeholder="Enter a time-sensitive or factual query...")

if st.button("Execute Live Search"):
    if not query:
        st.warning("Please enter a query first.")
    elif not backend_status:
        st.error("Cannot proceed: Backend API is offline. Please run `app.py`.")
    else:
        # 6. Execution Phase
        with st.status("🚀 Processing Query...", expanded=True) as status:
            start_time = time.time()
            
            try:
                # API Call
                response = requests.get(f"http://localhost:8000/ask?query={query}", timeout=300)
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "")
                    sources = data.get("sources", [])
                    elapsed = round(time.time() - start_time, 1)
                    
                    status.update(label=f"Query Resolved in {elapsed}s", state="complete", expanded=False)
                    
                    # 7. Partitioned Display of Results
                    st.divider()
                    
                    # Layout: Left column for Answer, Right column for metadata/sources
                    res_col1, res_col2 = st.columns([3, 2])
                    
                    with res_col1:
                        st.subheader("📝 Generated Answer")
                        st.markdown(f"<div class='answer-container'>{answer}</div>", unsafe_allow_html=True)
                        
                        st.caption(f"FreshQuery identified {len(sources)} distinct perspectives to reach this conclusion.")

                    with res_col2:
                        st.subheader("🔗 Grounding Sources")
                        if sources:
                            for idx, url in enumerate(sources):
                                st.markdown(f"""
                                    <div class='source-card'>
                                        <strong>Source #{idx+1}</strong><br>
                                        <a href='{url}' target='_blank'>{url[:50]}...</a>
                                    </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.warning("No citations were extracted for this answer.")
                            
                        # Performance metrics card
                        st.metric("Response Latency", f"{elapsed} seconds")
                
                else:
                    status.update(label="Logic Error", state="error")
                    st.error(f"The engine encountered an error: {response.text}")

            except requests.exceptions.Timeout:
                status.update(label="Timeout Error", state="error")
                st.error("The request timed out. Live crawling multiple sites can take over 2 minutes.")
            except Exception as e:
                status.update(label="System Failure", state="error")
                st.error(f"Unexpected error: {str(e)}")

# 8. Footer
st.divider()
st.markdown(
    "<center><small>FreshQuery v2.0 | Ephemeral RAG | Local-First Architecture</small></center>", 
    unsafe_allow_html=True
)