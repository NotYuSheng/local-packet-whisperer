# Docker Deployment Guide

This guide explains how to run Local Packet Whisperer using Docker.

## Prerequisites

- Docker installed ([Install Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed ([Install Docker Compose](https://docs.docker.com/compose/install/))

## Quick Start

### Option 1: Using Docker Compose (Recommended)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/NotYuSheng/local-packet-whisperer.git
   cd local-packet-whisperer
   ```

2. **Set environment variables** (optional):
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your-api-key-here
   LLM_SERVER=ollama
   LLM_SERVER_PORT=11434
   PCAP_DIR=./pcaps
   ```

3. **Start the services**:
   ```bash
   docker-compose up -d
   ```

   This will start:
   - Local Packet Whisperer on `http://localhost:8501`
   - Ollama (optional LLM server) on `http://localhost:11434`

4. **Access the application**:
   Open your browser and navigate to `http://localhost:8501`

5. **Stop the services**:
   ```bash
   docker-compose down
   ```

### Option 2: Using Docker Only

1. **Build the image**:
   ```bash
   docker build -t local-packet-whisperer .
   ```

2. **Run the container**:
   ```bash
   docker run -d \
     --name lpw \
     -p 8501:8501 \
     -e OPENAI_API_KEY=not-needed \
     local-packet-whisperer
   ```

3. **Access the application**:
   Open your browser and navigate to `http://localhost:8501`

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | API key for OpenAI-compatible endpoints | `not-needed` |
| `LLM_SERVER` | LLM server hostname | `127.0.0.1` |
| `LLM_SERVER_PORT` | LLM server port | `11434` |
| `PCAP_DIR` | Directory containing PCAP files | `./pcaps` |

### Using with Ollama

The docker-compose file includes an optional Ollama service for running local LLMs:

1. **Pull a model** (after starting services):
   ```bash
   docker exec -it ollama ollama pull llama3.1
   ```

2. **Configure LPW to use Ollama**:
   - In the LPW Settings page, set:
     - LLM Server Host: `ollama`
     - LLM Server Port: `11434`

### Using with External LLM Services

To use OpenAI, Azure OpenAI, or other compatible services:

1. **Set your API key**:
   ```bash
   export OPENAI_API_KEY=your-actual-api-key
   ```

2. **Update docker-compose.yml** to point to the correct endpoint in LPW Settings UI

### GPU Support (Ollama)

To enable GPU support for Ollama:

1. Install [nvidia-docker](https://github.com/NVIDIA/nvidia-docker)

2. Uncomment the GPU configuration in `docker-compose.yml`:
   ```yaml
   deploy:
     resources:
       reservations:
         devices:
           - driver: nvidia
             count: 1
             capabilities: [gpu]
   ```

## Volume Management

### Persistent Data

The docker-compose setup creates two volumes:
- `lpw-data`: Application data and settings
- `ollama-data`: Ollama models and configuration

To reset all data:
```bash
docker-compose down -v
```

### Mounting PCAP Files

Mount your PCAP files directory:

1. Create a `pcaps` directory:
   ```bash
   mkdir -p ./pcaps
   ```

2. Copy your PCAP files:
   ```bash
   cp /path/to/your/*.pcap ./pcaps/
   ```

3. Files will be available at `/pcaps` inside the container

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs lpw

# Or for standalone container
docker logs lpw
```

### Connection issues with Ollama
- Make sure both services are on the same network
- Use service name `ollama` as hostname (not `localhost`)
- Verify Ollama is running: `docker-compose ps`

### Permission issues with PCAP files
```bash
# Fix permissions on PCAP directory
chmod -R 755 ./pcaps
```

## Development

To run in development mode with live code reload:

```bash
docker-compose -f docker-compose.dev.yml up
```

## Security Notes

- Never commit `.env` files with real API keys
- Use Docker secrets for production deployments
- Limit container network access in production
- Keep base images updated regularly

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Streamlit Docker Deployment](https://docs.streamlit.io/knowledge-base/tutorials/deploy/docker)
- [Ollama Documentation](https://github.com/ollama/ollama)
