import streamlit as st
import requests
import json
import time

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="Financial AI Analyst",
    page_icon="📈",
    layout="wide"
)

# Backend API URL (Ensure FastAPI is running on this port)
API_URL = "http://localhost:8000"

# --- 2. Sidebar Configuration ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/bullish.png", width=80)
    st.title("⚙️ System Status")
    
    # Button to check backend health
    if st.button("Check Backend Connection"):
        try:
            response = requests.get(f"{API_URL}/health", timeout=2)
            if response.status_code == 200:
                data = response.json()
                doc_count = data.get('total_documents', 'N/A')
                st.success(f"✅ Online! (Docs: {doc_count})")
            else:
                st.error(f"❌ Error: {response.status_code}")
        except requests.exceptions.ConnectionError:
            st.error("❌ Connection Failed. Is 'main.py' running?")

    st.markdown("---")
    st.markdown("**Model:** Llama 3.2 (3B)")
    st.markdown("**Database:** ChromaDB")
    
    # Button to clear chat history
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# --- 3. Initialize Chat History ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am your AI Financial Analyst. Ask me anything about stocks, crypto, or market news! 📈"}
    ]

# --- 4. Display Chat History ---
st.title("📈 Financial Intelligence Chatbot")
st.caption("Powered by RAG (Llama 3.2 + ChromaDB)")

# Render previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. Handle User Input ---
if prompt := st.chat_input("Ask a question (e.g., 'What is the news on Apple?')..."):
    
    # Display user message immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display AI response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        with st.spinner("🔍 Searching documents & Analyzing..."):
            try:
                # Send request to FastAPI backend
                payload = {"question": prompt, "n_results": 4}
                response = requests.post(f"{API_URL}/query", json=payload, timeout=60)
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data["answer"]
                    sources = data["sources"]
                    
                    # Streaming effect for the answer
                    for chunk in answer.split():
                        full_response += chunk + " "
                        time.sleep(0.02)
                        message_placeholder.markdown(full_response + "▌")
                    
                    # Final update without cursor
                    message_placeholder.markdown(full_response)
                    
                    # Display Source Documents in an expandable section
                    with st.expander("📚 View Source Documents"):
                        for idx, source in enumerate(sources):
                            st.markdown(f"**Source {idx+1}** (Relevance: {source['relevance_score']:.1f}%)")
                            # Truncate text to first 300 characters
                            st.info(source['text'][:300] + "...") 
                            st.caption(f"Metadata: {source['metadata']}")
                            st.markdown("---")
                            
                    # Save AI response to session history
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                    
                else:
                    st.error(f"Backend Error: {response.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Could not connect to backend. Please ensure `python main.py` is running in another terminal.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")