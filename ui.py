import streamlit as st
import requests
import time

# 1. Page Configuration
st.set_page_config(
    page_title="FreshQuery | Live RAG",
    page_icon="🌐",
    layout="centered"
)

# 2. Minimalist Styling
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stTextInput { border-radius: 10px; }
    .stButton button { width: 100%; border-radius: 10px; background-color: #007bff; color: white; }
    .source-tag { 
        font-size: 0.8rem; padding: 2px 8px; margin: 2px; 
        background: #e9ecef; border-radius: 5px; color: #495057;
        text-decoration: none; display: inline-block;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Header
st.title("🌐 FreshQuery")
st.caption("Live Web-Grounded Question Answering Engine (No Database)")
st.divider()

# 4. Input Area
query = st.text_input("Ask a question about current events:", placeholder="e.g. What is the current status of the Artemis mission?")

if st.button("Search & Generate"):
    if query:
        with st.status("🔍 Searching web, crawling content, and generating answer...", expanded=True) as status:
            try:
                # Step 1: Call the FastAPI Backend
                start_time = time.time()
                response = requests.get(f"http://localhost:8000/ask?query={query}", timeout=120)
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "No answer generated.")
                    sources = data.get("sources", [])
                    
                    status.update(label=f"Done! (Took {round(time.time() - start_time, 1)}s)", state="complete", expanded=False)
                    
                    # 5. Display Results
                    st.subheader("Answer")
                    st.markdown(answer)
                    
                    st.divider()
                    
                    # 6. Display Sources
                    if sources:
                        st.subheader("Sources Grounded")
                        for idx, url in enumerate(sources):
                            st.markdown(f"**[{idx+1}]** {url}")
                    else:
                        st.info("No external sources were needed for this response.")
                        
                else:
                    status.update(label="Error processing request", state="error")
                    st.error(f"Backend returned an error: {response.text}")
                    
            except requests.exceptions.ConnectionError:
                status.update(label="Backend Connection Failed", state="error")
                st.error("Make sure your FastAPI server (app.py) is running on http://localhost:8000")
    else:
        st.warning("Please enter a query.")

# 7. Sidebar / Footer
with st.sidebar:
    st.header("System Status")
    st.success("Whoogle: Online")
    st.success("Ollama (Qwen): Online")
    st.success("Memory: Volatile/Ephemeral")
    st.divider()
    st.info("This system does not store any data. Every query triggers a fresh web crawl.")