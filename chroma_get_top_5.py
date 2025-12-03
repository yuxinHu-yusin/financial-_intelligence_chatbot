# chroma_test.py
import chromadb
from sentence_transformers import SentenceTransformer

def run_query():
    print("=" * 60)
    print("CHROMA SEARCH TOOL")
    print("=" * 60)

    # 1. Initialize
    print("\n📊 Loading model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    print("📁 Connecting to database...")
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_collection("finance_documents")
    
    print(f"✓ Connected! Total documents: {collection.count()}")
    
    # 2. Define Query
    # You can change this text to search for anything
    query_text = "Tell me about OpenAI and Google"
    print(f"\n🔍 Searching for: '{query_text}'")
    
    # 3. Generate Embedding
    query_embedding = model.encode(query_text).tolist()
    
    # 4. Search (Get top 5)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=5,  # Requesting top 5 results
        include=["documents", "metadatas", "distances"]
    )
    
    # 5. Display Results
    print(f"\nFound {len(results['documents'][0])} relevant results:\n")
    
    for i in range(len(results['documents'][0])):
        doc = results['documents'][0][i]
        meta = results['metadatas'][0][i]
        distance = results['distances'][0][i]
        score = (1 - distance) * 100  # Convert distance to similarity score
        
        print(f"--- Result {i+1} (Relevance: {score:.1f}%) ---")
        print(f"Source: r/{meta.get('subreddit', 'unknown')}")
        print(f"Date: {meta.get('date', 'unknown')}")
        print(f"Text: {doc[:300]}...") # Show first 300 chars
        print()

if __name__ == "__main__":
    run_query()
