import uvicorn
import chromadb
import ollama
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from sentence_transformers import SentenceTransformer

# --- 1. Initialization ---
app = FastAPI(title="Finance RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. Load Resources ---
print("--- [System] Starting Backend (Lightweight Mode) ---")

print("1. Loading Embedding Model...")
# Small model 90MB
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
print("   -> Embedding Model loaded.")

print("2. Connecting to ChromaDB...")
try:
    db_client = chromadb.PersistentClient(path="./chroma_db")
    collection = db_client.get_collection("finance_documents")
    print(f"   -> Connected. Documents: {collection.count()}")
except Exception as e:
    print(f"   -> Error: {e}")

# --- 3. Data Models ---
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

# --- 4. Logic ---
def retrieve_documents(question: str, n: int):
    query_vec = embedding_model.encode(question).tolist()
    results = collection.query(
        query_embeddings=[query_vec],
        n_results=n,
        include=["documents", "metadatas", "distances"]
    )
    return results

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

# --- 5. API ---
# Add /health check endpoint to resolve 404 error from frontend
@app.get("/health")
def health_check():
    """Returns the status and current document count of the vector store."""
    try:
        # Get the document count
        count = collection.count()
    except Exception:
        # If DB connection fails (unlikely if initialization worked), return 0
        count = 0 
        
    # The frontend expects a 200 OK status and the document count
    return {"status": "ok", "total_documents": count}

@app.post("/query", response_model=QueryResponse)
def query_rag(request: QueryRequest):
    print(f"\n[Query] {request.question}")
    
    # 1. Search
    results = retrieve_documents(request.question, request.n_results)
    
    sources = []
    context_text = ""
    if results['documents']:
        for i in range(len(results['documents'][0])):
            doc = results['documents'][0][i]
            meta = results['metadatas'][0][i]
            score = (1 - results['distances'][0][i]) * 100
            sources.append(SourceDocument(text=doc, metadata=meta, relevance_score=score))
            context_text += f"- {doc}\n"

    # 2. Generate 
    print(f"[LLM] Generating with {request.model}...")
    answer = generate_answer(request.question, context_text, request.model)
    
    return QueryResponse(answer=answer, sources=sources, used_model=request.model)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
