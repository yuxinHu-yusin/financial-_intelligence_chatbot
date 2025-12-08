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
            # Access /health route
            response = requests.get(f"{API_URL}/health", timeout=2)
            if response.status_code == 200:
                data = response.json()
                doc_count = data.get('total_documents', 'N/A')
                # Success message now shows document count
                st.success(f"✅ Backend Online! (Docs: {doc_count})")
            else:
                # Prompt user to check the FastAPI /health route
                st.error(f"❌ Error: {response.status_code}. Check if the FastAPI /health route has been added.")
        except requests.exceptions.ConnectionError:
            st.error("❌ Connection Failed. Confirm `python main.py` is running in the backend terminal.")

    st.markdown("---")
    st.markdown("**Model:** Llama 3.2 (3B)")
    st.markdown("**Database:** ChromaDB")
    
    # Button to clear chat history
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# --- 3. Main Interface ---
st.title("📈 Financial Intelligence Chatbot")
st.caption("Powered by RAG (Llama 3.2 + ChromaDB)")


# === 💡 Sample Questions ===

# List of sample questions
sample_questions = [
    "What do investors think about the current crypto market conditions?",
    "What are people saying about the S&P 500 performance lately?",
    "What are investors saying about the current state of the real estate market?",
    "Has JPMorgan Chase made any major announcements in recent weeks?",
]

# Function to handle sample question click: store the question for processing
def set_sample_prompt(question):
    st.session_state["prompt_to_process"] = question
    
st.subheader("💡 Sample Questions (Click to Ask)")

# Display buttons in columns
cols = st.columns(4) 
for col, question in zip(cols, sample_questions):
    with col:
        # Use on_click to update the session state
        st.button(
            question, 
            on_click=set_sample_prompt, 
            args=(question,), 
            key=f"sample_btn_{question[:10]}", # Ensure key is unique
            use_container_width=True
        )

st.markdown("---") 


# === Chat Logic ===

# Initialize chat history and prompt processor state
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I am your AI Financial Analyst. Ask me anything about stocks, crypto, or market news!"}]
if "prompt_to_process" not in st.session_state:
    st.session_state["prompt_to_process"] = None


# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 1. Check for user input from the chat box
# If user types in the chat input, set the prompt_to_process
if chat_input_value := st.chat_input("Ask a financial question about markets, stocks, or crypto...", key="chat_input"):
    st.session_state["prompt_to_process"] = chat_input_value

# 2. Get the prompt to process (either from chat input or sample button)
prompt = st.session_state.pop("prompt_to_process", None)

# 3. Execute the RAG logic if a prompt is available
if prompt:
# <<< MODIFICATION END: Unified Input Handling Logic >>>
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    # API Request Body
    request_body = {
        "question": prompt,
        "n_results": 5,
        "model": "llama3.2:3b"
    }

    # API Call and Response Handling
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            with st.spinner("🔍 Searching documents and analyzing..."):
                # Send request to FastAPI backend
                response = requests.post(f"{API_URL}/query", json=request_body, timeout=60) 
                
            if response.status_code == 200:
                data = response.json()
                answer = data.get('answer', 'No answer received.')
                sources = data.get('sources', [])
                
                # Simulate streaming response
                for chunk in answer.split():
                    full_response += chunk + " "
                    time.sleep(0.02)
                    message_placeholder.markdown(full_response + "▌")
                
                # Final display of the complete answer
                message_placeholder.markdown(full_response)
                
                # Display Source Documents in an expandable section
                if sources:
                    with st.expander("📚 View Source Documents"):
                        for idx, source in enumerate(sources):
                            score = source.get('relevance_score', 0.0)
                            text = source.get('text', 'Content missing')
                            metadata = source.get('metadata', {})

                            st.markdown(f"**Source Document {idx+1}** (Relevance: {score:.1f}%)")
                            # Truncate text to first 300 characters
                            st.info(text[:300] + "...") 
                            st.caption(f"Metadata: {metadata}")
                            st.markdown("---")
                            
                # Save AI response to session history
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
            else:
                st.error(f"Backend Error: {response.text}")
                
        except requests.exceptions.ConnectionError:
            st.error("❌ Could not connect to backend. Please ensure python main.py is running in another terminal.")
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")