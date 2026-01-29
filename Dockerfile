FROM python:3.11-slim

# Install system dependencies including tshark for packet capture
# Configure tshark to allow non-superuser packet capture
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    tshark \
    libpcap-dev \
    && rm -rf /var/lib/apt/lists/* \
    && chmod +x /usr/bin/dumpcap

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt VERSION.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy only application code (bin/ and config/)
COPY bin/ ./bin/
COPY config/ ./config/

# Create necessary directories
RUN mkdir -p /root/.lpw/temp /root/.lpw/config /app/.streamlit

# Create Streamlit config for file upload size
RUN printf "[server]\nmaxUploadSize = 500\n" > /app/.streamlit/config.toml

# Expose Streamlit default port
EXPOSE 8501

# Set environment variables
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
# Allow TShark to run as root (required in Docker)
ENV WIRESHARK_RUN_AS_USER=root

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run the application
CMD ["streamlit", "run", "bin/lpw_main.py"]
