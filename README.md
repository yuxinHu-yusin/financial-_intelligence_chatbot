# 📈 Financial Intelligence Chatbot (RAG System)

A full-stack financial AI assistant that retrieves real-time market data (Stocks, Crypto, ETFs) from a local vector database and generates professional insights using a local LLM.

**Architecture:** Streamlit (Frontend) → FastAPI (Backend) → ChromaDB (Vector Store) + Ollama (LLM)

---

## 🚀 Features

- **Interactive UI:** Specific chat interface built with Streamlit.
- **RAG Technology:** Retrieval-Augmented Generation using `all-MiniLM-L6-v2`.
- **Local LLM:** Runs offline using **Llama 3.2** (optimized for speed and low memory).
- **FastAPI Backend:** Robust API handling retrieval and generation logic.
- **Source Citations:** AI answers include specific references to source documents with relevance scores.

---

## 🛠️ Prerequisites

1.  **Python 3.8+**
2.  **Ollama**:
    - Download: [ollama.com](https://ollama.com)
    - **Important:** Pull the lightweight model to prevent crashes:
      ```bash
      ollama pull llama3.2:3b
      ```

---

## 📦 Installation

1.  **Clone the repository** (or navigate to your project folder).

2.  **Install Dependencies:**

    ```bash
    pip install fastapi uvicorn chromadb sentence-transformers ollama pydantic streamlit requests
    ```

3.  **Check Directory Structure:**
    Ensure your project folder looks like this:
    ```text
    project_root/
    ├── chroma_db/           # 📂 Folder containing .sqlite3 and .bin files
    ├── main.py              # ⚙️ Backend (FastAPI)
    ├── app.py               # 🎨 Frontend (Streamlit)
    └── README.md
    ```

---

## 🏃‍♂️ How to Run (Step-by-Step)

You need 3 terminal windows to run the full system.

### Step 1: Start AI Engine (Terminal 1)

Ensure Ollama is running in the background.

```bash
ollama serve

Step 2: Start Backend API (Terminal 2)
This handles the logic and database connection.

Bash

python main.py
Wait until you see: "Uvicorn running on http://0.0.0.0:8000"

Step 3: Start Frontend UI (Terminal 3)
This launches the chat interface in your browser.

Bash

streamlit run app.py
The browser should open automatically at: http://localhost:8501

🧪 API Usage (Optional)
You can also test the backend without the UI using Swagger docs:

URL: http://localhost:8000/docs

Endpoint: POST /query

Sample Payload:

JSON

{
  "question": "What is the news about Apple?",
  "n_results": 4,
  "model": "llama3.2:3b"
}
```
