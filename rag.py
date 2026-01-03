import httpx
import asyncio
from datetime import datetime
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import ollama

# Pre-load embedding model
embed_model = SentenceTransformer('all-MiniLM-L6-v2')

class FreshQueryRAG:
    def __init__(self):
        self.whoogle_url = "http://localhost:5000/search"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    async def search_web(self, query):
        """Phase 6.1: Search with Natural Ranking Priority"""
        params = {'q': query, 'format': 'json'}
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=20.0) as client:
                response = await client.get(self.whoogle_url, params=params)
                
                urls = []
                if response.status_code == 200 and "application/json" in response.headers.get("Content-Type", ""):
                    data = response.json()
                    results = data.get('results', data if isinstance(data, list) else [])
                    # Whoogle usually returns results in order of relevance/recency
                    urls = [r.get('url') or r.get('href') for r in results if r.get('url') or r.get('href')]
                else:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    for a in soup.find_all('a', href=True):
                        u = a['href']
                        if u.startswith('http') and 'google' not in u and 'whoogle' not in u:
                            urls.append(u)

                # Remove duplicates while preserving the search engine's original order
                seen = set()
                ordered_urls = [x for x in urls if not (x in seen or seen.add(x))]
                
                # We take the top 5, assuming the search engine has already 
                # prioritized the most recent/relevant ones.
                return [u for u in ordered_urls if u.startswith('http')][:5]
        except Exception as e:
            print(f"Search Error: {e}")
            return []

    async def crawl_pages(self, urls):
        """Phase 6.2: Parallel Live Crawling"""
        config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
        async with AsyncWebCrawler() as crawler:
            results = await crawler.arun_many(urls=urls, config=config)
            # Store data with their rank (original search position) to help LLM weigh priority
            return [{"url": r.url, "content": r.markdown.raw_markdown, "rank": i+1} 
                    for i, r in enumerate(results) if r.success and r.markdown]

    def process_and_index(self, web_data):
        """Phase 6.3 & 6.4: Indexing with Rank and Source Metadata"""
        chunks, metadata = [], []
        for entry in web_data:
            content, url, rank = entry['content'], entry['url'], entry['rank']
            for i in range(0, len(content), 450): 
                chunk = content[i:i+500].strip()
                if len(chunk) > 100:
                    # Explicitly tag each chunk with Search Rank and Source
                    # This allows the LLM to judge "Prominence" by search position
                    tagged_chunk = f"[Search Rank: #{rank} | Source: {url}]\n{chunk}"
                    chunks.append(tagged_chunk)
                    metadata.append({"url": url, "rank": rank})

        if not chunks: return None, None, []

        embeddings = embed_model.encode(chunks)
        index = faiss.IndexFlatL2(embeddings.shape[1])
        index.add(np.array(embeddings).astype('float32'))
        return index, chunks, metadata

    async def generate_answer(self, query, index, chunks, metadata):
        """Phase 6.5: Temporal Audit and Majority Consensus Generation"""
        now = datetime.now()
        current_time_str = now.strftime("%A, %B %d, %Y")

        query_vec = embed_model.encode([query])
        # Retrieve top 7 chunks to give the LLM enough broad data for consensus checking
        D, I = index.search(np.array(query_vec).astype('float32'), k=5)
        
        context_parts = [chunks[i] for i in I[0] if i != -1]
        context_text = "\n\n---\n\n".join(context_parts)
        unique_sources = list(set([metadata[i]['url'] for i in I[0] if i != -1]))

        # ENHANCED CONSENSUS & TEMPORAL PROMPT
        prompt = f"""[INST] You are FreshQuery, a real-time factual verification assistant.
        
CURRENT SYSTEM DATE: {current_time_str}

YOUR TASK:
Answer the user's question by synthesizing the provided web snippets. You must handle conflicting information using the protocol below.

CONSENSUS & RECENCY PROTOCOL:
1. TEMPORAL AUDIT: Scan snippets for publication dates or relative time markers (e.g., "2 hours ago"). Information explicitly timestamped closer to {current_time_str} takes absolute precedence.
2. SEARCH RANK PRIORITY: If no dates are found, snippets with a lower 'Search Rank' (e.g., Rank #1, #2) are considered more prominent/recent as per search engine sorting.
3. MAJORITY VOTE: If snippets provide conflicting facts (like numbers, names, or events), the version supported by the majority of unique sources is the one you must report.
4. TRANSPARENCY: If a conflict is significant and cannot be resolved (e.g., 2 sources say 'X' and 2 sources say 'Y'), briefly mention the discrepancy.

WEB SNIPPETS:
{context_text}

USER QUESTION: {query}
[/INST]"""
        
        try:
            client = ollama.AsyncClient()
            response = await client.generate(
                model='mistral:7b-instruct', 
                prompt=prompt,
                options={
                    "temperature": 0.0, # Setting to 0 for maximum factual strictness
                    "num_ctx": 2048     # Ensure enough room for all snippets
                }
            )
            return response['response'], unique_sources
        except Exception as e:
            return f"LLM Generation Error: {e}", unique_sources

async def run_rag_pipeline(query):
    """Orchestrator for the RAG Flow"""
    rag = FreshQueryRAG()
    
    # 1. Search (Ordered by Search Engine prominence/recency)
    urls = await rag.search_web(query)
    if not urls: return "I couldn't find any relevant web links.", []
    
    # 2. Crawl
    web_data = await rag.crawl_pages(urls)
    if not web_data: return "I found links but was unable to read their current content.", []

    # 3. Index with Metadata
    index, chunks, metadata = rag.process_and_index(web_data)
    if not index: return "No usable text was extracted from the live results.", []
    
    # 4. Generate with Consensus Protocol
    return await rag.generate_answer(query, index, chunks, metadata)