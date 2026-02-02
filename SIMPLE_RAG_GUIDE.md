# Simple Session-Based RAG for LPW

## Overview

This is a **simple, session-only** implementation of RAG (Retrieval Augmented Generation) for handling large PCAP files (300MB+).

### Key Features
- ✅ **In-memory only** - No persistent storage
- ✅ **Auto-cleanup** - Data expires when app restarts
- ✅ **No configuration needed** - Works out of the box
- ✅ **Simple** - Just install one package and go

## How It Works

### Session Lifecycle

```
1. User uploads PCAP
   └─> Create in-memory vector database
   └─> Index packets
   └─> Ready for queries

2. User asks questions
   └─> Search vector DB
   └─> Retrieve relevant packets
   └─> Send to LLM

3. User uploads NEW PCAP OR app restarts
   └─> Old data automatically deleted
   └─> Start fresh
```

### Data Storage

- **Where:** RAM only (using ChromaDB EphemeralClient)
- **Persistence:** None - data deleted on app restart
- **Size:** ~2-3x PCAP size (e.g., 300MB PCAP = ~600-900MB RAM)
- **Cleanup:** Automatic when:
  - App restarts
  - New PCAP uploaded
  - Streamlit session ends

## Installation

### Step 1: Install ChromaDB

```bash
pip install chromadb
```

That's it! No other dependencies needed if using Ollama for embeddings.

### Step 2: Enable RAG

Add to `.env`:
```bash
# Enable session-based RAG
USE_RAG=true

# How many packets per embedding group (default: 10)
RAG_GROUP_SIZE=10

# How many groups to retrieve per query (default: 5)
RAG_RETRIEVE_K=5
```

### Step 3: Use LPW Normally

Upload your PCAP and ask questions. RAG happens automatically!

## Example Session

```
# Terminal 1: Start LPW
$ lpw start

# Browser: Upload 300MB PCAP
Uploading capture.pcap (300MB)...
├─ Generating summary... ✓ (30s)
├─ Indexing packets... ✓ (60s)
└─ Ready! Indexed 12,500 packet groups

# Ask questions (RAG automatically retrieves relevant packets)
You: "Show me all HTTP traffic"
LPW: [Searches 12,500 groups, retrieves top 5 most relevant]
     [Sends only ~50 packets to LLM instead of all 125,000]
     [Provides accurate answer based on retrieved packets]

You: "What DNS queries were made?"
LPW: [Again searches and retrieves only relevant packets]
     [Fast and accurate]

# Upload new PCAP
Uploading new_capture.pcap...
├─ Old index automatically deleted ✓
└─ Creating new index... ✓

# Or restart app
$ lpw stop
$ lpw start
└─> All session data cleared automatically
```

## Memory Management

### Automatic Cleanup

ChromaDB's `EphemeralClient` stores everything in RAM:
- **Advantage:** Fast, no disk I/O
- **Automatic cleanup:** Data gone when Python process ends
- **No disk usage:** Zero persistent storage

### Manual Cleanup (Optional)

If you want to clear data without restarting:

```python
# In your code:
if 'rag_instance' in st.session_state:
    st.session_state['rag_instance'].cleanup()
    del st.session_state['rag_instance']
```

Or add a "Clear Index" button in the UI.

## Resource Usage

| PCAP Size | Packets | RAM Used | Index Time | Query Time |
|-----------|---------|----------|------------|------------|
| 50 MB     | 25K     | ~100MB   | 30s        | <1s        |
| 300 MB    | 125K    | ~600MB   | 90s        | <1s        |
| 1 GB      | 500K    | ~2GB     | 5min       | 1-2s       |

**Recommendation:** For very large files (1GB+), use a machine with at least 8GB RAM.

## FAQs

### Q: Will data persist between sessions?
**A:** No. All data is in-memory only and deleted when the app restarts.

### Q: What happens if I upload a new PCAP?
**A:** The old index is automatically deleted and a new one is created.

### Q: Can I use this on a server with multiple users?
**A:** Each Streamlit session gets its own in-memory database, so yes. But each user's data uses RAM.

### Q: What if my PCAP is too large for RAM?
**A:** Use `RAG_MAX_INDEX` to limit how many packets get indexed:
```bash
RAG_MAX_INDEX=50000  # Only index first 50K packets
```

### Q: How accurate is the retrieval?
**A:** Very good for semantic queries like "HTTP traffic" or "DNS queries". May miss exact match needs (use filters for those).

### Q: Can I save the index to disk?
**A:** Not in this simple implementation. If you need persistence, modify `lpw_rag.py` to use `PersistentClient` instead of `EphemeralClient`.

## Comparison with Other Approaches

| Approach | Pros | Cons | Best For |
|----------|------|------|----------|
| **Load All** | Simple, complete data | ❌ Fails for large files | <50MB files |
| **Truncate** | Fast, simple | ⚠️ Missing data | Small questions |
| **Summary Only** | Fast, always works | ⚠️ No details | Overview queries |
| **Session RAG** ✅ | Accurate, scalable, simple | Uses RAM | Large files |
| **Persistent RAG** | Reusable index | Complex, disk space | Repeated analysis |

## When to Use Session RAG

✅ **Use session-based RAG when:**
- PCAP files are 100MB+
- You need accurate answers to specific questions
- You're okay with indexing once per session
- You have enough RAM

❌ **Don't use RAG when:**
- PCAP files are <50MB (just use "full" mode)
- You only need high-level statistics (use "summary" mode)
- RAM is very limited (<4GB total)

## Troubleshooting

### "ChromaDB not installed"
```bash
pip install chromadb
```

### "Out of memory during indexing"
Reduce indexed packets:
```bash
RAG_MAX_INDEX=25000  # Index only first 25K packets
```

### "Indexing takes too long"
Increase group size to create fewer embeddings:
```bash
RAG_GROUP_SIZE=20  # 20 packets per group instead of 10
```

### "Retrieval not accurate"
Increase retrieved groups:
```bash
RAG_RETRIEVE_K=10  # Retrieve more groups per query
```

## Summary

Session-based RAG is the **simple, effective solution** for large PCAP files:
- ✅ No complex configuration
- ✅ No disk management
- ✅ Auto-cleanup
- ✅ Accurate retrieval
- ✅ Scales to 300MB+ files

Just install ChromaDB, set `USE_RAG=true`, and go!
