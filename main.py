import uvicorn
import math
import re
import chromadb
import ollama
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from sentence_transformers import SentenceTransformer

# ================================
# 1. APP INIT
# ================================
app = FastAPI(title="Finance RAG API (Yahoo + Reddit + SEC)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================================
# 2. LOAD MODELS & DB
# ================================
print("\n--- [System] Starting Backend (Multi-DB RAG Mode) ---")

print("1. Loading Embedding Model...")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
print("   -> Embedding model loaded.")

print("2. Connecting to ChromaDB...")
db_client = chromadb.PersistentClient(path="./chroma_db")

# Yahoo + Reddit
finance_collection = db_client.get_collection("finance_documents")

# SEC
sec_collection = db_client.get_collection("sec_filings_qqq_10k")
sec_10q_collection = db_client.get_collection("sec_filings_qqq_10q_2025")

print(f"   -> finance_documents: {finance_collection.count()}")
print(f"   -> sec_filings_qqq_10k: {sec_collection.count()}")
print(f"   -> sec_filings_qqq_10q_2025: {sec_10q_collection.count()}")

# ================================
# 3. DATA MODELS
# ================================
class QueryRequest(BaseModel):
    question: str
    n_results: int = 5
    model: str = "llama3.2:3b"

class SourceDocument(BaseModel):
    text: str
    metadata: dict
    relevance_score: float

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceDocument]
    used_model: str

# ================================
# 4. RETRIEVAL LOGIC (MULTI DB)
# ================================
def detect_query_intent(question: str):
    q = question.lower()

    # Extract year if present
    year_match = re.search(r"(20\d{2})", q)
    year = int(year_match.group(1)) if year_match else None

    fin_keywords = [
        "10-k", "10k", "10-q", "10q", "annual report", "quarterly report",
        "balance sheet", "income statement", "cash flow",
        "revenue", "profit", "loss", "net income", "gross margin", "margin",
        "operating income", "ebit", "ebitda", "free cash flow", "fcf",
        "eps", "earnings", "guidance",
        "assets", "liabilities", "equity", "debt",
        "litigation", "regulatory",
        "expense", "cost", "capex", "r&d",
        "valuation", "market cap", "p/e",
        "dividend", "buyback"
    ]

    market_keywords = [
        "sentiment", "price", "trend", "rally", "crash", "volatility",
        "market", "nasdaq", "s&p", "dow", "qqq", "spy",
        "inflation", "interest rate", "fed", "gdp", "recession",
        "bitcoin", "btc", "eth", "crypto"
    ]

    for k in fin_keywords:
        if k in q:
            return {
                "type": "financial",
                "year": year
            }

    for k in market_keywords:
        if k in q:
            return {
                "type": "market",
                "year": year
            }

    return {
        "type": "general",
        "year": year
    }



def retrieve_from_collection(collection, query_vec, n):
    return collection.query(
        query_embeddings=[query_vec],
        n_results=n,
        include=["documents", "metadatas", "distances"]
    )

def retrieve_documents(question: str, n: int):
    query_vec = embedding_model.encode(question).tolist()
    intent = detect_query_intent(question)
    query_type = intent["type"]
    query_year = intent["year"]

    # ============================
    # 70% / 30% Weight Setting
    # ============================
    NEWS_RATIO = 0.7
    SEC_RATIO = 0.15
    SEC_Q_RATIO = 0.15

    if query_type == "financial":
        NEWS_RATIO = 0.5
        SEC_RATIO  = 0.15
        SEC_Q_RATIO = 0.35
    
    elif query_type == "market":
        NEWS_RATIO = 0.75
        SEC_RATIO  = 0.1
        SEC_Q_RATIO = 0.15


    news_k = max(1, math.ceil(n * NEWS_RATIO))
    sec_k = max(1, math.floor(n * SEC_RATIO))
    sec_q_k = max(1, math.floor(n * SEC_Q_RATIO))

    print(f"[RETRIEVE] Yahoo/Reddit={news_k}, SEC-10K={sec_k}, SEC-10Q={sec_q_k}")

    # ============================
    # Retrieve from two Vector DBs separately
    # ============================
    yahoo_results = retrieve_from_collection(
        finance_collection, query_vec, news_k
    )

    sec_results = retrieve_from_collection(
        sec_collection, query_vec, sec_k
    )

    sec_q_results = retrieve_from_collection(
        sec_10q_collection, query_vec, sec_q_k
    )

    merged = []

    # ============================
    # Yahoo + Reddit
    # ============================
    if yahoo_results and yahoo_results.get("documents"):
        for i in range(len(yahoo_results["documents"][0])):
            merged.append({
                "text": yahoo_results["documents"][0][i],
                "metadata": yahoo_results["metadatas"][0][i],
                "score": (1 - yahoo_results["distances"][0][i]) * 100
            })

    # ============================
    # SEC
    # ============================
    if sec_results and sec_results.get("documents"):
        for i in range(len(sec_results["documents"][0])):
            merged.append({
                "text": sec_results["documents"][0][i],
                "metadata": sec_results["metadatas"][0][i],
                "score": (1 - sec_results["distances"][0][i]) * 100
            })

    if sec_q_results and sec_q_results.get("documents"):
        for i in range(len(sec_q_results["documents"][0])):
            merged.append({
                "text": sec_q_results["documents"][0][i],
                "metadata": sec_q_results["metadatas"][0][i],
                "score": (1 - sec_q_results["distances"][0][i]) * 100
            })

    # ============================
    # Global Sort by Similarity
    # ============================
    merged.sort(key=lambda x: x["score"], reverse=True)

    # ============================
    # Return final Top-N
    # ============================
    return merged[:n]

# ================================
# 5. PROMPT ENGINEERING 
# ================================
def generate_answer(question: str, context: str, model_name: str):
    prompt = f"""
# CONTEXT #
You are the generation component in a Retrieval-Augmented Generation (RAG) system.
The user's query has been matched with the most relevant information from a financial knowledge base.

# OBJECTIVE #
Answer the user's question accurately by synthesizing information from the retrieved content.
Present the answer as inherent knowledge and do NOT reveal or mention the retrieval process.

# STYLE #
Clear, structured explanatory prose.
Match the technical depth of the user's question.
Typically 2–4 concise paragraphs unless otherwise required.

# TONE #
Confident, authoritative, and helpful.
Avoid hedging language such as "might", "possibly", or "it seems" unless uncertainty is explicitly justified.

# AUDIENCE #
End users seeking seamless financial analysis without knowledge of the backend system.

# RESPONSE #
Context:
{context}

Query:
{question}

Rules:
- Never mention "documents", "sources", "context", "database", or any retrieval-related terms.
- Present all information as direct knowledge.
- Only use facts contained in the provided context.
- If relevant information is missing, respond exactly with:
  "I don't have specific information about this based on the available data."
- Synthesize across all content. Do NOT summarize document-by-document.

Answer:
"""

    try:
        response = ollama.chat(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
        )
        return response["message"]["content"]
    except Exception as e:
        return f"Error generating answer: {str(e)}"

# ================================
# 6. API
# ================================
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "finance_documents": finance_collection.count(),
        "sec_documents": sec_collection.count(),
        "sec_10q_documents": sec_10q_collection.count(),
        "total_documents": finance_collection.count() + sec_collection.count() + sec_10q_collection.count()
    }

@app.post("/query", response_model=QueryResponse)
def query_rag(request: QueryRequest):
    print(f"\n[QUERY] {request.question}")

    results = retrieve_documents(request.question, request.n_results)

    sources = []
    context_text = ""

    for item in results:
        sources.append(SourceDocument(
            text=item["text"],
            metadata=item["metadata"],
            relevance_score=item["score"]
        ))
        context_text += f"- {item['text']}\n"

    print(f"[LLM] Generating with {request.model} ...")
    answer = generate_answer(request.question, context_text, request.model)

    return QueryResponse(
        answer=answer,
        sources=sources,
        used_model=request.model
    )

# ================================
# 7. RUN
# ================================
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
