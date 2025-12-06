#!/bin/bash

# --- 1. Start Ollama Server ---
# Run the Ollama service in the background
echo "Starting Ollama server..."
ollama serve &

# Wait for Ollama to fully start
sleep 10
echo "Ollama server started."

# --- 2. Pull the required model (llama3.2:3b) ---
MODEL_NAME="llama3.2:3b"
echo "Pulling Ollama model: $MODEL_NAME..."
ollama pull $MODEL_NAME
echo "Model pull complete."

# --- 3. Start FastAPI Backend ---
echo "Starting FastAPI backend on port 8000..."
# Use the & symbol to run in the background
python main.py &

# Wait for FastAPI to start
sleep 5

# --- 4. Start Streamlit Frontend ---
echo "Starting Streamlit frontend on port 8501..."
# Must use 0.0.0.0 to be accessible from outside the VM/container
streamlit run app.py --server.port 8501 --server.enableCORS true --server.enableXsrfProtection false --server.address 0.0.0.0

# Streamlit runs in the foreground, keeping the container alive


