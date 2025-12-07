# chroma_test.py
import chromadb
from sentence_transformers import SentenceTransformer
import math

def merge_results(raw_results, source_name):
    """
    - finance_documents
    - sec_filings_qqq_10k
    - sec_filings_qqq_10q_2025
    """
    merged = []

    if raw_results and raw_results.get("documents"):
        for i in range(len(raw_results["documents"][0])):
            doc = raw_results["documents"][0][i]
            meta = raw_results["metadatas"][0][i]
            distance = raw_results["distances"][0][i]
            score = (1 - distance) * 100

            merged.append({
                "source": source_name,
                "text": doc,
                "metadata": meta,
                "score": score
            })

    return merged


def run_query():
    print("=" * 60)
    print("CHROMA SEARCH TOOL (Weighted Multi-DB)")
    print("=" * 60)

    # ============================
    # 1. Initialize
    # ============================
    print("\n Loading model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    print("📁 Connecting to database...")
    client = chromadb.PersistentClient(path="./chroma_db")

    collection = client.get_collection("finance_documents")           # Yahoo + Reddit
    sec_collection = client.get_collection("sec_filings_qqq_10k")    # SEC 10-K
    sec_10q_col = client.get_collection("sec_filings_qqq_10q_2025")  # SEC 10-Q

    print(f"✓ Yahoo/Reddit Docs: {collection.count()}")
    print(f"✓ SEC 10-K Docs: {sec_collection.count()}")
    print(f"✓ SEC 10-Q Docs: {sec_10q_col.count()}")

    # ============================
    # 2. Query
    # ============================
    query_text = "Tell me about OpenAI and Google"
    print(f"\n Searching for: '{query_text}'")

    query_embedding = model.encode(query_text).tolist()

    # ============================
    # 3. Weight Setting (70% News, 15% 10-K, 15% 10-Q)
    # ============================
    TOTAL_RESULTS = 10
    NEWS_RATIO = 0.7
    SEC_RATIO = 0.15
    SEC_Q_RATIO = 0.15

    news_k = math.ceil(TOTAL_RESULTS * NEWS_RATIO)
    sec_k = math.floor(TOTAL_RESULTS * SEC_RATIO)
    sec_q_k = math.floor(TOTAL_RESULTS * SEC_Q_RATIO)

    print(f"📊 Retrieval Plan → News: {news_k}, SEC-10K: {sec_k}, SEC-10Q: {sec_q_k}")

    # ============================
    # 4. Query Each Collection
    # ============================
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=news_k,
        include=["documents", "metadatas", "distances"]
    )

    sec_results = sec_collection.query(
        query_embeddings=[query_embedding],
        n_results=sec_k,
        include=["documents", "metadatas", "distances"]
    )

    sec_q_results = sec_10q_col.query(
        query_embeddings=[query_embedding],
        n_results=sec_q_k,
        include=["documents", "metadatas", "distances"]
    )

    # ============================
    # 5. Merge Results 
    # ============================
    merged_results = []

    merged_results.extend(merge_results(results, "NEWS"))
    merged_results.extend(merge_results(sec_results, "SEC-10K"))
    merged_results.extend(merge_results(sec_q_results, "SEC-10Q"))

    # ============================
    # 6. Global Sort
    # ============================
    merged_results.sort(key=lambda x: x["score"], reverse=True)

    # ============================
    # 7. Display Results
    # ============================
    print("\n" + "=" * 70)
    print("MERGED SEARCH RESULTS (70% News + 15% 10-K + 15% 10-Q)")
    print("=" * 70)

    if not merged_results:
        print("No results found.")
        return

    for i, item in enumerate(merged_results, 1):
        meta = item["metadata"]

        print(f"\n--- Result {i} | Source: {item['source']} | Relevance: {item['score']:.2f}% ---")

        # SEC
        if item["source"].startswith("SEC"):
            print(
                f"Ticker: {meta.get('ticker')}, "
                f"Year: {meta.get('year')}, "
                f"Form: {meta.get('form')}, "
                f"Filing Date: {meta.get('filing_date')}"
            )
        # Yahoo / Reddit
        else:
            print(
                f"Subreddit: {meta.get('subreddit', 'N/A')}, "
                f"Date: {meta.get('date', 'N/A')}, "
                f"Source: {meta.get('source', 'unknown')}"
            )

        print(f"Text Preview:\n{item['text'][:400]}...")
        print("-" * 70)


if __name__ == "__main__":
    run_query()
