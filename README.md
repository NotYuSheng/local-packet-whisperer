![](gifs/lpw_logo_small.png)
# Local Packet Whisperer (LPW)

A privacy-focused PCAP analysis tool powered by local and cloud LLMs. Chat with your network captures using AI, with support for both Ollama (local) and OpenAI-compatible APIs.

![](gifs/lpw_latest_cover.png)

## Features

- **100% Local or Cloud** - Use Ollama for private local analysis or connect to OpenAI-compatible APIs
- **Docker Support** - One-command deployment with docker-compose
- **RAG for Large Files** - Handle 500MB+ PCAP files efficiently with session-based vector search
- **Streamlit UI** - Clean, intuitive web interface for packet analysis
- **Network-Ready** - Connect to LLM servers over your network
- **Multiple LLM Support** - Compatible with Ollama, OpenAI, and other OpenAI-compatible endpoints

## Quick Start

**Prerequisites:** [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)

```bash
git clone https://github.com/NotYuSheng/local-packet-whisperer.git
cd local-packet-whisperer
cp example.env .env  # Define llm enndpoint
docker compose up -d
```

Access the application at [http://localhost:8501](http://localhost:8501)

To stop:
```bash
docker compose down
```

## Contributions

Contributions are welcome! Feel free to:
- Report bugs via [Issues](https://github.com/NotYuSheng/local-packet-whisperer/issues)
- Submit pull requests with bug fixes or new features
- Suggest improvements or new features

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

This is fork with additions including Docker support, RAG implementation, and OpenAI API compatibility.

Original project: [local-packet-whisperer](https://github.com/kspviswa/local-packet-whisperer) by [kspviswa](https://github.com/kspviswa)
