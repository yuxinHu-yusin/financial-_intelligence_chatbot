# load_to_chroma.py
import chromadb
from sentence_transformers import SentenceTransformer
import json
from tqdm import tqdm
import time

def load_jsonl_to_chroma(jsonl_file, chroma_path='./chroma_db'):
    """
    Load your Reddit JSONL data into Chroma vector database
    
    Args:
        jsonl_file: Your collected data file (reddit_data.jsonl)
        chroma_path: Where to save Chroma database (./chroma_db)
    """
    
    print("=" * 60)
    print("LOADING DATA INTO CHROMA VECTOR DATABASE")
    print("=" * 60)
    print()
    
    # ============================================
    # STEP 1: Initialize Embedding Model
    # ============================================
    print("📊 Loading embedding model (this may take a minute)...")
    print("   Model: all-MiniLM-L6-v2 (384 dimensions)")
    
    # This model converts text to vectors (embeddings)
    # IMPORTANT: Use the same model for both loading and querying!
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    print("✓ Embedding model loaded!\n")
    
    # ============================================
    # STEP 2: Initialize Chroma with Persistent Storage
    # ============================================
    print(f"📁 Setting up Chroma database at: {chroma_path}")
    
    # PersistentClient saves everything to disk
    chroma_client = chromadb.PersistentClient(path=chroma_path)
    
    # Create or get collection
    # If collection exists, it will be retrieved; if not, created
    collection = chroma_client.get_or_create_collection(
        name="finance_documents",
        metadata={"description": "Financial data from Reddit and other sources"}
    )
    
    # Check if data already exists
    existing_count = collection.count()
    print(f"   Existing documents in database: {existing_count}")
    
    if existing_count > 0:
        print(f"\n⚠️  WARNING: Database already has {existing_count} documents")
        response = input("   Do you want to ADD more data? (yes/no): ")
        if response.lower() != 'yes':
            print("   Exiting without changes.")
            return
    
    print()
    
    # ============================================
    # STEP 3: Read JSONL File
    # ============================================
    print(f"📖 Reading data from: {jsonl_file}")
    
    texts = []
    metadatas = []
    ids = []
    
    try:
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    entry = json.loads(line)
                    
                    # Extract required fields
                    texts.append(entry['text'])
                    metadatas.append(entry['metadata'])
                    ids.append(entry['id'])
                    
                except json.JSONDecodeError as e:
                    print(f"   ⚠️  Skipping line {line_num}: Invalid JSON")
                    continue
                except KeyError as e:
                    print(f"   ⚠️  Skipping line {line_num}: Missing field {e}")
                    continue
        
        print(f"✓ Successfully read {len(texts)} entries from file\n")
        
    except FileNotFoundError:
        print(f"❌ ERROR: File '{jsonl_file}' not found!")
        print("   Make sure you ran the Reddit collection script first.")
        return
    
    if len(texts) == 0:
        print("❌ ERROR: No valid entries found in file!")
        return
    
    # ============================================
    # STEP 4: Generate Embeddings and Load to Chroma
    # ============================================
    print("🔄 Generating embeddings and loading into Chroma...")
    print(f"   This will take ~{len(texts) * 0.1:.0f} seconds")
    print()
    
    # Process in batches for memory efficiency
    batch_size = 100
    total_added = 0
    
    for i in tqdm(range(0, len(texts), batch_size), desc="Processing batches"):
        # Get batch
        batch_texts = texts[i:i+batch_size]
        batch_metadatas = metadatas[i:i+batch_size]
        batch_ids = ids[i:i+batch_size]
        
        try:
            # Generate embeddings for this batch
            # This is where the "magic" happens - text becomes vectors!
            batch_embeddings = model.encode(
                batch_texts,
                show_progress_bar=False,
                convert_to_numpy=True
            ).tolist()
            
            # Add to Chroma (automatically saves to disk!)
            collection.add(
                documents=batch_texts,        # Original text
                embeddings=batch_embeddings,  # Vector representations
                metadatas=batch_metadatas,    # Metadata (source, date, etc.)
                ids=batch_ids                 # Unique IDs
            )
            
            total_added += len(batch_texts)
            
        except Exception as e:
            print(f"\n⚠️  Error processing batch {i//batch_size + 1}: {e}")
            continue
    
    print()
    
    # ============================================
    # STEP 5: Verify Results
    # ============================================
    print("=" * 60)
    print("✅ LOADING COMPLETE!")
    print("=" * 60)
    
    final_count = collection.count()
    
    print(f"\n📊 Database Statistics:")
    print(f"   Total documents: {final_count}")
    print(f"   Newly added: {total_added}")
    print(f"   Database location: {chroma_path}/")
    
    # Show breakdown by source
    print(f"\n📈 Breakdown by source:")
    source_counts = {}
    for metadata in metadatas:
        source = metadata.get('source', 'Unknown')
        source_counts[source] = source_counts.get(source, 0) + 1
    
    for source, count in sorted(source_counts.items()):
        print(f"   {source}: {count} documents")
    
    # Show breakdown by subreddit (if applicable)
    if metadatas and 'subreddit' in metadatas[0]:
        print(f"\n📈 Breakdown by subreddit:")
        sub_counts = {}
        for metadata in metadatas:
            sub = metadata.get('subreddit', 'Unknown')
            sub_counts[sub] = sub_counts.get(sub, 0) + 1
        
        for sub, count in sorted(sub_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   r/{sub}: {count} documents")
    
    print(f"\n💾 Your Chroma database is ready to use!")
    print(f"   Location: {chroma_path}/")
    print(f"   You can now use this with your RAG system.")
    print("=" * 60)

# ============================================
# Test Query Function (Optional)
# ============================================

def test_chroma_database(chroma_path='./chroma_db'):
    """
    Test that the database works by running a sample query
    """
    print("\n" + "=" * 60)
    print("TESTING CHROMA DATABASE")
    print("=" * 60)
    print()
    
    # Load model and database
    print("📊 Loading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    print("📁 Connecting to Chroma database...")
    chroma_client = chromadb.PersistentClient(path=chroma_path)
    collection = chroma_client.get_collection("finance_documents")
    
    print(f"✓ Database loaded: {collection.count()} documents\n")
    
    # Test queries
    test_queries = [
        "What are the latest AI developments?",
        "Tell me about OpenAI and Google",
        "IBM CEO thoughts on AI spending"
    ]
    
    for query in test_queries:
        print(f"🔍 Query: \"{query}\"")
        
        # Generate embedding for query
        query_embedding = model.encode(query).tolist()
        
        # Search Chroma
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=2,  # Top 2 results
            include=["documents", "metadatas", "distances"]
        )
        
        print(f"   Top results:")
        for i in range(len(results['documents'][0])):
            doc = results['documents'][0][i]
            metadata = results['metadatas'][0][i]
            distance = results['distances'][0][i]
            
            print(f"\n   Result {i+1}:")
            print(f"   - Relevance: {(1-distance)*100:.1f}%")
            print(f"   - Source: r/{metadata.get('subreddit', 'category')}")
            print(f"   - Text: {doc[:100]}...")
        
        print()
    
    print("=" * 60)
    print("✅ Database is working correctly!")
    print("=" * 60)

# ============================================
# Main Function
# ============================================

def main():
    """
    Main function - loads data and optionally tests it
    """
    # Load your Reddit data into Chroma
    load_jsonl_to_chroma(
        jsonl_file='yahoo_finance_data.jsonl',  # Your collected data
        chroma_path='./chroma_db'        # Where to save database
    )
    
    # Optional: Test the database
    print()
    response = input("Would you like to test the database with sample queries? (yes/no): ")
    if response.lower() == 'yes':
        test_chroma_database('./chroma_db')

if __name__ == "__main__":
    main()