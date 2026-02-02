# Quick Start: Fixing Context Window Errors

This guide helps you fix the `cannot truncate prompt with n_keep > n_ctx` error and handle large PCAP files.

## Problem You're Seeing

```
error code: 400 - {'error': 'cannot truncate prompt with n_keep (482463 > n_ctx(4096)'}
```

This means your PCAP data (482,463 tokens) exceeds your model's context window (4,096 tokens).

## Solution #1: Summary Mode (Recommended - Works Now!)

This is **already configured** in your `.env` file and will work immediately.

### What It Does
- Generates a ~2KB statistical summary instead of loading all packets
- Shows: protocol distribution, top IPs, conversations, ports
- Fits in any context window

### Steps

1. **Check your [.env](.env) file** (already set):
```bash
PCAP_LOAD_MODE=summary
MAX_CONTEXT_LENGTH=4096
```

2. **In LM Studio**, increase context length:
   - Go to Server Settings
   - Set "Context Length" to **8192** or **16384**
   - Update your `.env`:
   ```bash
   MAX_CONTEXT_LENGTH=8192
   ```

3. **Start LPW and upload your PCAP**:
```bash
lpw start
```

4. **You'll see**:
```
📊 Using summary mode - statistical overview loaded
```

5. **Ask questions**:
```
- "What protocols are in this capture?"
- "What are the top source IPs?"
- "Show me the conversation summary"
```

**Result:** Works with ANY PCAP size, fits in 4K context! ✅

---

## Solution #2: RAG Mode (Best for Detailed Analysis)

For when you need detailed packet-level answers (e.g., "Show me the HTTP POST requests").

### Prerequisites
- ✅ ChromaDB already installed (you have it!)
- ✅ Enough RAM (2-3x PCAP size)

### Steps

1. **Enable RAG in [.env](.env)**:
```bash
# Change this line
USE_RAG=true

# Keep these
PCAP_LOAD_MODE=summary
MAX_CONTEXT_LENGTH=8192
RAG_GROUP_SIZE=10
RAG_RETRIEVE_K=5
```

2. **Start LPW**:
```bash
lpw stop  # Stop if running
lpw start
```

3. **Upload PCAP** (will take longer for indexing):
```
Uploading capture.pcap (300MB)...
📊 Generating summary... ✓ (30s)
🔍 Indexing packets for RAG... ✓ (90s)
✅ Indexed 12,500 packet groups
```

4. **Ask detailed questions**:
```
- "Show me all HTTP requests to example.com"
- "What DNS queries were made for google.com?"
- "Show TLS handshake details"
```

**Result:** Accurate answers from relevant packets only! ✅

---

## Quick Comparison

| Mode | PCAP Size | Setup Time | Best For | Context Used |
|------|-----------|------------|----------|--------------|
| **Summary** | Any | 30s | Overview, stats | ~2KB |
| **RAG** | 100MB+ | 90s | Detailed queries | ~10-20KB |
| Full | <50MB | 10s | Small files | 100% |

---

## Testing Your Setup

### Test 1: Summary Mode (Should Work Now)

```bash
# 1. Check .env
cat .env | grep PCAP_LOAD_MODE
# Should show: PCAP_LOAD_MODE=summary

# 2. Start LPW
lpw start

# 3. Upload any PCAP
# 4. Ask: "What protocols are in this capture?"
# 5. Should get summary-based answer ✓
```

### Test 2: RAG Mode (If You Want Detailed Analysis)

```bash
# 1. Edit .env
echo "USE_RAG=true" >> .env

# 2. Restart
lpw stop && lpw start

# 3. Upload PCAP (wait for indexing)
# 4. Ask: "Show me HTTP traffic to 192.168.1.1"
# 5. Should retrieve and analyze relevant packets ✓
```

---

## Troubleshooting

### Still getting context error?

**Check LM Studio context length:**
1. Open LM Studio
2. Go to server tab
3. Check "Context Length" setting
4. Should be ≥ 8192

**Update .env to match:**
```bash
MAX_CONTEXT_LENGTH=8192  # or whatever LM Studio shows
```

### Summary mode doesn't show packet details?

This is expected! Summary mode shows statistics only.

**For packet details, use RAG:**
```bash
USE_RAG=true
```

### RAG indexing too slow?

**Limit packets indexed:**
```bash
RAG_MAX_INDEX=50000  # Index only first 50K packets
```

**Or increase group size:**
```bash
RAG_GROUP_SIZE=20  # 20 packets per group instead of 10
```

### Out of memory during RAG indexing?

**Your PCAP is very large. Options:**

1. **Limit indexing:**
```bash
RAG_MAX_INDEX=25000
```

2. **Use quick mode instead:**
```bash
PCAP_LOAD_MODE=quick
USE_RAG=false
```

---

## What Mode Should I Use?

### Use **Summary Mode** if:
- ✅ You want quick overview/statistics
- ✅ PCAP is 50MB+
- ✅ You don't need packet-level details
- ✅ You want it to work RIGHT NOW

### Use **RAG Mode** if:
- ✅ You need detailed packet analysis
- ✅ PCAP is 100MB+
- ✅ You have 8GB+ RAM
- ✅ You're willing to wait 1-2 min for indexing

### Use **Full Mode** if:
- ✅ PCAP is <50MB
- ✅ You want complete packet data in context

---

## Current Configuration (Your Setup)

Based on your `.env` file:

```bash
LLM_SERVER=100.64.0.1
LLM_SERVER_PORT=1234
MAX_CONTEXT_LENGTH=4096
PCAP_LOAD_MODE=summary   ← Currently using this
USE_RAG=false             ← RAG disabled
```

**Recommendation for you:**
1. Increase `MAX_CONTEXT_LENGTH=8192` in LM Studio
2. Update `.env`: `MAX_CONTEXT_LENGTH=8192`
3. Keep `PCAP_LOAD_MODE=summary`
4. Enable `USE_RAG=true` if you need detailed packet analysis

---

## Next Steps

**Right Now (Summary Mode):**
```bash
# Already configured! Just use it:
lpw start
# Upload PCAP
# Ask questions about statistics/overview
```

**For Better Results (RAG Mode):**
```bash
# 1. Edit .env
nano .env
# Add: USE_RAG=true

# 2. Restart
lpw stop && lpw start

# 3. Upload and wait for indexing
# 4. Ask detailed questions
```

**Questions?** Check the detailed guides:
- [PCAP_LOADING_MODES.md](PCAP_LOADING_MODES.md) - All modes explained
- [SIMPLE_RAG_GUIDE.md](SIMPLE_RAG_GUIDE.md) - RAG deep dive
- [RAG_IMPLEMENTATION.md](RAG_IMPLEMENTATION.md) - Technical details
