# Dockerfile is used to build a Docker image containing all code, dependencies, and the Ollama service.
# File Name: Dockerfile

# Use the official Ollama base image
FROM ollama/ollama

# Install Python and necessary system tools, including python3-venv for virtual environments
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv git build-essential --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# --- Fix for 'externally-managed-environment' (PEP 668) ---
# Create a virtual environment for isolated Python package installation
RUN python3 -m venv /opt/venv

# Make the virtual environment's bin directory accessible system-wide
ENV PATH="/opt/venv/bin:$PATH"
# -----------------------------------------------------------

# Set the working directory
WORKDIR /app

# Copy dependency file and install Python dependencies into the venv
COPY requirements.txt .

# Now 'pip' refers to the pip inside the venv, which avoids the system conflict
RUN pip install --no-cache-dir -r requirements.txt --timeout 600

# Copy the entire project (including main.py, app.py, README.md, and the chroma_db folder)
COPY . /app

# Set permissions for the entrypoint.sh script
RUN chmod +x entrypoint.sh

# Expose FastAPI (8000) and Streamlit (8501) ports
EXPOSE 8000
EXPOSE 8501

# Run entrypoint.sh when the container starts
ENTRYPOINT ["./entrypoint.sh"]
