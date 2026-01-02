***

# FreshQuery: Live Web-Grounded QA Engine

FreshQuery is a "Live RAG" (Retrieval-Augmented Generation) system that provides accurate, up-to-date answers by searching and crawling the live web in real-time. 

Unlike traditional RAG systems, FreshQuery **does not use a database or persistent vector store**. It builds a temporary, in-memory index for every single query, ensuring total data freshness and user privacy.

## Key Features
- **Zero Persistence:** No SQL/NoSQL databases or persistent vector stores. Data exists only in RAM during the request cycle.
- **Real-Time Freshness:** Uses **Whoogle Search** and **Crawl4AI** to get data from the live web "right now."
- **Authoritative Sources:** Explicitly restricts retrieval to the top 4–5 most relevant web results.
- **Grounded Answers:** Powered by **Mistral-7B-Instruct** via Ollama, with strict instructions to only answer using provided context.
- **Minimalist Design:** Entire backend logic contained in a clean, high-performance FastAPI/Python structure.

---

## Technology Stack
| Layer | Technology |
| :--- | :--- |
| **LLM** | Mistral-7B-Instruct (via Ollama) |
| **Search Engine** | Whoogle Search (Self-hosted/Docker) |
| **Crawling** | Crawl4AI (Asynchronous Web Crawler) |
| **Embeddings** | Sentence-Transformers (all-MiniLM-L6-v2) |
| **Vector Search** | FAISS (In-memory CPU) |
| **API Backend** | FastAPI |
| **Frontend UI** | Streamlit |

---

## Prerequisites
Before you begin, ensure you have the following installed:
- **Python 3.10+**
- **Docker** (to run Whoogle)
- **Ollama** (to run Mistral)
- **RAM:** 8GB minimum (16GB+ recommended for running Mistral locally)

---

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/freshquery.git
cd freshquery
```

### 2. Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate venv (Windows)
venv\Scripts\activate
# Activate venv (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup browser engines for Crawl4AI
playwright install chromium
```

### 3. Start Infrastructure (Docker & Ollama)
**Run Whoogle Search:**
```bash
docker run -d -p 5000:5000 --name whoogle-search benbusby/whoogle-search:latest
```

**Run Mistral via Ollama:**
1. Install Ollama from [ollama.com](https://ollama.com).
2. Open your terminal and run:
```bash
ollama pull mistral:7b-instruct
```

---

## How to Run

To run FreshQuery, you need to open **two separate terminals** (keep your virtual environment active in both).

### Step 1: Start the FastAPI Backend
```bash
python app.py
```
The backend will start at `http://localhost:8000`.

### Step 2: Start the Streamlit Frontend
```bash
streamlit run ui.py
```
The UI will automatically open in your browser at `http://localhost:8501`.

---

## System Architecture
1. **User Query:** User enters a question in the Streamlit UI.
2. **Web Discovery:** FastAPI calls the Whoogle API to find the 5 most relevant URLs.
3. **Live Crawling:** Crawl4AI extracts clean markdown/text content from those 5 URLs simultaneously.
4. **Ephemeral Indexing:** Text is split into chunks, embedded, and stored in a temporary **FAISS** index in RAM.
5. **Context Retrieval:** The system retrieves the top 4 text chunks matching the query.
6. **Generation:** **Mistral-7B** generates a concise answer grounded *strictly* in the retrieved web context.
7. **Cleanup:** The FAISS index and text chunks are discarded immediately after the response is sent.

   <img width="2032" height="805" alt="image" src="https://github.com/user-attachments/assets/21b8b5d0-4252-4eea-83e8-2644ffa7252d" />


---

## Limitations
- **No Memory:** The system is stateless; it does not remember previous questions in a conversation.
- **Latency:** Speed depends on web search response times and your local hardware's ability to run Mistral.
- **Web Dependency:** If Whoogle or a specific website is down, results may vary.

---
