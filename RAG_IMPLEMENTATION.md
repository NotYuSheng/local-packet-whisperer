# RAG Implementation for Large PCAP Files

This document explains how to implement RAG (Retrieval Augmented Generation) for handling 300MB+ PCAP files.

## Overview: Two-Stage Analysis + RAG

### Stage 1: Initial Load (Summary + Indexing)
When user uploads a PCAP file:
1. ✅ Generate statistical summary (IMPLEMENTED)
2. ⏳ Create embeddings and index packets (TO IMPLEMENT)
3. ✅ Show summary in system message (IMPLEMENTED)

### Stage 2: Query-Time Retrieval
When user asks a question:
1. Embed the user's question
2. Semantic search in vector DB
3. Retrieve top-k relevant packet groups
4. Load ONLY those packets from PCAP
5. Send to LLM with conversation context

## Benefits

| Approach | 300MB PCAP | Context Used | Query Speed | Accuracy |
|----------|------------|--------------|-------------|----------|
| Current (load all) | ❌ Fails | 100% (fails) | N/A | N/A |
| Truncation only | ⚠️ Partial | 100% | Fast | Low |
| **Summary + RAG** | ✅ Works | ~10-20% | Fast | High |

## Implementation Steps

### Step 1: Add Dependencies

Add to `requirements.txt`:
```txt
chromadb>=0.4.24
sentence-transformers>=2.2.0
```

Or use Ollama for embeddings (no extra dependencies).

### Step 2: Enable RAG Mode

Add to `.env`:
```bash
# Enable RAG for large files
USE_RAG=true

# RAG Configuration
RAG_GROUP_SIZE=10          # Packets per embedding
RAG_MAX_INDEX=100000       # Max packets to index (0 = unlimited)
RAG_RETRIEVE_K=5           # Top-K groups to retrieve per query
RAG_EMBEDDING_MODEL=ollama # or "sentence-transformers"
```

### Step 3: Modify Upload Flow

Update `lpw_home.py`:

```python
if packetFile:
    # ... existing code ...

    if returnValue('use_rag'):
        # Stage 1: Summary + Indexing
        with st.spinner('📊 Generating summary...'):
            summary = getPcapSummary(...)
            st.session_state['pcap_data'] = summary

        with st.spinner('🔍 Indexing packets for RAG...'):
            rag = get_rag_instance(packetFile.name, filters)
            stats = rag.index_packets(
                group_size=returnValue('rag_group_size'),
                max_packets=returnValue('rag_max_index')
            )
            st.success(f"✅ Indexed {stats['total_groups']} packet groups")
            st.session_state['rag_instance'] = rag
    else:
        # Traditional loading
        st.session_state['pcap_data'] = getPcapData(...)
```

### Step 4: Modify Query Flow

Update `chatWithModel` to use RAG:

```python
def chatWithModelRAG(prompt: str, model: str):
    """Enhanced chat that uses RAG for packet retrieval"""

    if 'rag_instance' in st.session_state:
        rag = st.session_state['rag_instance']

        # Retrieve relevant packets
        relevant_groups = rag.query(prompt, top_k=returnValue('rag_retrieve_k'))

        # Format retrieved packets
        retrieved_context = "\\n\\n=== RELEVANT PACKETS ===\\n"
        for group in relevant_groups:
            retrieved_context += f"\\n{group['text']}\\n"
        retrieved_context += "\\n=== END RELEVANT PACKETS ===\\n\\n"

        # Enhance prompt with retrieved context
        enhanced_prompt = f"{retrieved_context}\\n\\nUser Question: {prompt}"

        # Send to LLM
        return oClient.chat(prompt=enhanced_prompt, model=model, temp=0.4)
    else:
        # Fallback to traditional
        return oClient.chat(prompt=prompt, model=model, temp=0.4)
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    PCAP Upload                          │
│                   (300MB file)                          │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌───────────────┐        ┌────────────────┐
│   Summary     │        │  RAG Indexing  │
│  Generation   │        │                │
│   (~2KB)      │        │ Parse packets  │
│               │        │ Create groups  │
│ Stats, IPs,   │        │ Generate       │
│ protocols     │        │ embeddings     │
└───────┬───────┘        │ Store in DB    │
        │                └───────┬────────┘
        │                        │
        ▼                        ▼
┌──────────────────────────────────────────┐
│      System Message (Small)              │
│  - Summary only (~2KB)                   │
│  - Fits in any context window            │
└──────────────────┬───────────────────────┘
                   │
                   ▼
         ┌─────────────────┐
         │   User Query    │
         └────────┬────────┘
                  │
                  ▼
         ┌────────────────┐
         │ RAG Retrieval  │
         │                │
         │ 1. Embed query │
         │ 2. Search DB   │
         │ 3. Get top-K   │
         └────────┬───────┘
                  │
                  ▼
         ┌─────────────────────────┐
         │ Load Specific Packets   │
         │ (Only relevant ones)    │
         └────────┬────────────────┘
                  │
                  ▼
         ┌─────────────────────────┐
         │  Send to LLM            │
         │  - Summary (2KB)        │
         │  - Retrieved packets    │
         │    (~50 packets = 10KB) │
         │  - User query           │
         │  Total: ~15KB ✅        │
         └─────────────────────────┘
```

## Example Workflow

### Upload (One Time)
```
User uploads: capture.pcap (300MB, 125,000 packets)

Stage 1a - Summary (30 seconds):
├─ Parse all packets
├─ Generate statistics
└─ Result: 2KB summary

Stage 1b - RAG Index (60 seconds):
├─ Group packets (10 per group = 12,500 groups)
├─ Create embeddings
├─ Store in ChromaDB
└─ Result: Vector DB ready

Total: ~90 seconds, one-time cost
```

### Query (Each Time)
```
User: "Show me all HTTP traffic to example.com"

Step 1 - RAG Retrieval (< 1 second):
├─ Embed query
├─ Search 12,500 groups
├─ Return top 5 most relevant groups
└─ Result: 50 packets

Step 2 - LLM Context (< 1 second):
├─ Summary: 2KB
├─ Retrieved packets: 10KB
├─ Conversation history: 3KB
└─ Total: 15KB (fits in 4096 token context!)

Step 3 - LLM Response (5 seconds):
└─ Analyzes only relevant packets
└─ Accurate answer based on retrieved context

Total: ~6 seconds per query
```

## Embedding Options

### Option 1: Ollama Embeddings (Recommended)
```python
# Use existing Ollama server
from ollama import Client

client = Client(host='http://localhost:11434')
embedding = client.embeddings(model='nomic-embed-text', prompt=text)
```

**Pros:**
- No extra dependencies
- Uses existing infrastructure
- Works offline

**Cons:**
- Slightly slower than specialized models

### Option 2: Sentence Transformers
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embedding = model.encode(text)
```

**Pros:**
- Fast embedding
- Good quality

**Cons:**
- Extra dependency (~400MB model download)

## Performance Estimates

| PCAP Size | Packets | Index Time | DB Size | Query Time |
|-----------|---------|------------|---------|------------|
| 50 MB     | 25K     | 30s        | 50MB    | <1s        |
| 300 MB    | 125K    | 90s        | 250MB   | <1s        |
| 1 GB      | 500K    | 5min       | 800MB   | 1-2s       |

## Next Steps

1. **Install dependencies:**
   ```bash
   pip install chromadb sentence-transformers
   ```

2. **Update .env:**
   ```bash
   USE_RAG=true
   RAG_GROUP_SIZE=10
   RAG_RETRIEVE_K=5
   ```

3. **Test with large file:**
   - Upload 300MB PCAP
   - Wait for indexing
   - Ask questions
   - Verify accurate retrieval

## Future Enhancements

1. **Hybrid Search:** Combine semantic + keyword filtering
2. **Re-ranking:** Improve retrieval accuracy with re-ranker
3. **Streaming Indexing:** Index while uploading
4. **Persistent Cache:** Save indexes between sessions
5. **Query Expansion:** Auto-expand user queries for better retrieval
