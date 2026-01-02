from fastapi import FastAPI, Query
from rag import run_rag_pipeline
import uvicorn

app = FastAPI()

@app.get("/ask")
async def ask(query: str = Query(...)):
    answer, sources = await run_rag_pipeline(query)
    return {"answer": answer, "sources": sources}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)