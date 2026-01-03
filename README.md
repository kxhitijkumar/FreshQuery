# FreshQuery : Live Streaming & Grounded RAG Engine

**FreshQuery** is a high-performance, live-grounded Retrieval-Augmented Generation (RAG) system. Unlike traditional RAG pipelines that rely on stale, pre-indexed databases, FreshQuery performs **on-demand web discovery and crawling** to provide answers grounded in the "Right Now."

With the integration of **Real-time Streaming**, **Majority Consensus Logic**, and **Temporal Grounding**, FreshQuery ensures that the information you receive is not only fresh but also verified across multiple independent sources.

---

## Advanced Features

- **Real-time Token Streaming:** Experience immediate feedback with a typewriter-style response interface.
- **Majority Consensus Protocol:** Automatically cross-references multiple web sources to resolve conflicting information, prioritizing facts supported by the majority of links.
- **Temporal Awareness:** Injects the current system date and time into the reasoning engine, allowing the AI to accurately interpret "today," "yesterday," and recent news events.
- **Zero-Persistence Architecture:** Entirely ephemeral. Vectors and text chunks are generated in RAM per-query and discarded immediately after the response, ensuring 100% data privacy.
- **Rank-Based Prioritization:** Respects search engine prominence, giving higher weight to top-ranked search results.

---

## Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **LLM** | Mistral-7B-Instruct (via Ollama) | Streamed, grounded answer generation |
| **Search Engine** | Whoogle Search (Docker) | Privacy-focused web discovery |
| **Live Crawling** | Crawl4AI (Async) | On-the-fly markdown extraction |
| **Embeddings** | Sentence-Transformers | Semantic chunk representation |
| **Vector Search** | FAISS (In-Memory CPU) | Ephemeral similarity search |
| **Backend** | FastAPI (Async Streaming) | High-concurrency API layer |
| **Frontend** | Streamlit (Wide-Partitioned) | Modern, interactive user interface |

---

## Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/freshquery.git
cd freshquery
```

### 2. Configure Environment
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install browser binaries for the crawler
playwright install chromium
```

### 3. Initialize Infrastructure
**Start Whoogle Search (Docker):**
```bash
docker run -d -p 5000:5000 --name whoogle-search benbusby/whoogle-search:latest
```

**Prepare Mistral (Ollama):**
Ensure Ollama is running, then pull the model:
```bash
ollama pull mistral:7b-instruct
```

---

## Usage Instructions

To operate the system, run the backend and frontend in separate terminals:

### Terminal 1: Backend API
```bash
python app.py
```
*Starts the streaming-enabled FastAPI server at `http://localhost:8000`.*

### Terminal 2: Streamlit Interface
```bash
streamlit run ui.py
```
*Launches the partitioned UI at `http://localhost:8501`.*

---

## System Architecture & Logic

1.  **Temporal Injection:** The system captures the current date/time to ground the LLM's perception of "today."
2.  **Web Discovery:** Whoogle finds the top 5 relevant URLs based on the user's query.
3.  **Parallel Crawling:** Crawl4AI performs a live "headless" visit to all 5 sites simultaneously.
4.  **Source-Aware Indexing:** Content is chunked and tagged with its **Search Rank** and **Source URL**.
5.  **Fact-Checking Protocol:**
    *   **Recency:** Prioritizes info with newer timestamps.
    *   **Consensus:** Selects factual values (prices, dates, names) appearing in the majority of sources.
6.  **Streaming Generation:** Mistral-7B streams tokens directly to the UI, while the grounding sources populate in a separate panel for immediate verification.

   <img width="2032" height="805" alt="image" src="https://github.com/user-attachments/assets/663cc00f-0825-4b1f-8256-0ec7a121b3f8" />



---

## Important Considerations
- **Latency:** Because the system crawls the web at request-time, responses typically take 30-40 seconds depending on website speeds.
- **Hardware:** Running Mistral-7B locally requires a minimum of 8GB RAM (16GB+ recommended).
- **Rate Limits:** Frequent queries may lead to temporary IP blocks from search engines; use Whoogle responsibly.

---
