import httpx
import asyncio
from datetime import datetime
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import ollama

# Pre-load embedding model at module level for efficiency
embed_model = SentenceTransformer('all-MiniLM-L6-v2')

class FreshQueryRAG:
    def __init__(self):
        self.whoogle_url = "http://localhost:5000/search"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    async def search_web(self, query):
        """Phase 6.1: Async Web Discovery with HTML Fallback"""
        params = {'q': query, 'format': 'json'}
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=20.0) as client:
                response = await client.get(self.whoogle_url, params=params)
                
                # Check for JSON response
                if response.status_code == 200 and "application/json" in response.headers.get("Content-Type", ""):
                    data = response.json()
                    results = data.get('results', data if isinstance(data, list) else [])
                    urls = [r.get('url') or r.get('href') for r in results if r.get('url') or r.get('href')]
                    return [u for u in urls if u and u.startswith('http')][:5]
                
                # Fallback to HTML Parsing if JSON fails
                else:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    links = []
                    for a in soup.find_all('a', href=True):
                        url = a['href']
                        if url.startswith('http') and 'google' not in url and 'whoogle' not in url:
                            if url not in links: links.append(url)
                        if len(links) >= 5: break
                    return links
        except Exception as e:
            print(f"Search Error: {e}")
            return []

    async def crawl_pages(self, urls):
        """Phase 6.2: Parallel Live Crawling via Crawl4AI"""
        config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
        async with AsyncWebCrawler() as crawler:
            results = await crawler.arun_many(urls=urls, config=config)
            return [{"url": r.url, "content": r.markdown.raw_markdown} 
                    for r in results if r.success and r.markdown]

    def process_and_index(self, web_data):
        """Phase 6.3 & 6.4: Ephemeral In-Memory Indexing"""
        chunks, sources = [], []
        for entry in web_data:
            content, url = entry['content'], entry['url']
            # Chunking with 50-char overlap for context continuity
            for i in range(0, len(content), 450): 
                chunk = content[i:i+500].strip()
                if len(chunk) > 100:
                    chunks.append(chunk)
                    sources.append(url)

        if not chunks: return None, None, []

        embeddings = embed_model.encode(chunks)
        index = faiss.IndexFlatL2(embeddings.shape[1])
        index.add(np.array(embeddings).astype('float32'))
        return index, chunks, sources

    async def generate_answer(self, query, index, chunks, sources):
        """Phase 6.5: Temporal-Aware Grounded Generation via Mistral"""
        # Get current time and date for temporal grounding
        now = datetime.now()
        current_time_str = now.strftime("%A, %B %d, %Y | Time: %I:%M %p")

        # Retrieve top 4 relevant chunks
        query_vec = embed_model.encode([query])
        D, I = index.search(np.array(query_vec).astype('float32'), k=4)
        
        context_parts = []
        cited_urls = []
        for i in I[0]:
            if i != -1:
                context_parts.append(chunks[i])
                cited_urls.append(sources[i])

        context_text = "\n\n---\n\n".join(context_parts)
        unique_sources = list(set(cited_urls))

        # Mistral-specific instruction formatting with Temporal Reference
        prompt = f"""[INST] You are FreshQuery, a live-grounded AI assistant.
        
CURRENT SYSTEM TIME: {current_time_str}
Use this time as your "today" reference when interpreting news or dates in the context below.

CONTEXT FROM LIVE WEB CRAWL:
{context_text}

Based ONLY on the context provided, answer the user's question. If the context doesn't contain the answer, say that current web data doesn't provide enough information.

QUESTION: {query} [/INST]"""
        
        try:
            client = ollama.AsyncClient()
            response = await client.generate(model='mistral:7b-instruct', prompt=prompt)
            return response['response'], unique_sources
        except Exception as e:
            return f"LLM Generation Error: {e}", unique_sources

async def run_rag_pipeline(query):
    """Main Orchestrator"""
    rag = FreshQueryRAG()
    
    # 1. Search
    urls = await rag.search_web(query)
    if not urls: 
        return "I could not find any live web results for this query.", []
    
    # 2. Crawl
    web_data = await rag.crawl_pages(urls)
    if not web_data: 
        return "I found links but was unable to crawl their content (access might be restricted).", []

    # 3. Index
    index, chunks, sources = rag.process_and_index(web_data)
    if not index: 
        return "The crawled pages did not contain enough readable text to process.", []
    
    # 4. Generate
    return await rag.generate_answer(query, index, chunks, sources)