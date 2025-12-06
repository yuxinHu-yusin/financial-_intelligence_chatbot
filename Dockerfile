# Dockerfile is used to build a Docker image containing all code, dependencies, and the Ollama service.
# File Name: Dockerfile

# Use the official Ollama base image
FROM ollama/ollama

# Install Python and necessary system tools
RUN apt-get update && \
    apt-get install -y python3 python3-pip git && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy dependency file and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the entire project (including main.py, app.py, README.md, and the chroma_db folder)
COPY . /app

# Set permissions for the entrypoint.sh script
RUN chmod +x entrypoint.sh

# Expose FastAPI (8000) and Streamlit (8501) ports
EXPOSE 8000
EXPOSE 8501

# Run entrypoint.sh when the container starts
ENTRYPOINT ["./entrypoint.sh"]
