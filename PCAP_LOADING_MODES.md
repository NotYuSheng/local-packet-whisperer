# PCAP Loading Modes

LPW now supports three different modes for loading PCAP files, configurable via the `PCAP_LOAD_MODE` environment variable.

## Modes

### 1. Full Mode (`PCAP_LOAD_MODE=full`)
**Best for:** Small PCAP files (< 50MB)

- Loads all packet data into context
- Provides complete packet details
- Subject to `MAX_CONTEXT_LENGTH` truncation for large files
- Traditional LPW behavior

**Example .env:**
```bash
PCAP_LOAD_MODE=full
MAX_CONTEXT_LENGTH=8192
```

### 2. Summary Mode (`PCAP_LOAD_MODE=summary`) ⭐ **RECOMMENDED**
**Best for:** Medium to large PCAP files (50MB - 500MB+)

- Generates statistical summary only (~1-2KB)
- Includes:
  - Packet counts and size statistics
  - Protocol distribution
  - Top source/destination IPs
  - Top conversations
  - Port usage analysis
  - Application layer summary (HTTP, DNS, TLS)
  - Timeline information
- Fast loading even for 300MB+ files
- Fits in any context window

**Example .env:**
```bash
PCAP_LOAD_MODE=summary
MAX_CONTEXT_LENGTH=4096
```

**What you get:**
```
=== PCAP SUMMARY ===
File: capture.pcap
Total Packets: 125,432
Total Size: 312,456,789 bytes (298.12 MB)
Duration: 3600.45 seconds

--- PROTOCOL DISTRIBUTION ---
  TCP: 98,234 (78.3%)
  UDP: 25,123 (20.0%)
  ICMP: 2,075 (1.7%)

--- TOP SOURCE IPs ---
  192.168.1.100: 45,678 (36.4%)
  10.0.0.5: 23,456 (18.7%)
  ...
```

### 3. Quick Mode (`PCAP_LOAD_MODE=quick`)
**Best for:** Very large PCAP files (500MB+) or quick exploration

- Ultra-fast sampling
- Analyzes only first 1000 packets
- Provides basic protocol overview
- Instant loading

**Example .env:**
```bash
PCAP_LOAD_MODE=quick
```

## How Stage 1 Works (Summary/Quick Modes)

### The Problem
Loading a 300MB PCAP file as full packet data:
- Creates ~500,000+ tokens
- Exceeds any reasonable context window
- Takes minutes to process
- Causes context overflow errors

### The Solution
Instead of loading packet data, we extract **metadata only**:

```python
# Traditional approach (loads everything):
for pkt in capture:
    print(pkt)  # Full packet dump with all layers
    # Result: 300MB+ of text

# Summary approach (metadata only):
for pkt in capture:
    packet_count += 1
    protocols[pkt.highest_layer] += 1
    src_ips[pkt.ip.src] += 1
    # Result: ~2KB summary
```

### What's Included in Stage 1

1. **Counting & Aggregation**
   - Total packets, bytes, duration
   - Protocol distribution percentages
   - IP address frequencies
   - Port usage patterns

2. **No Raw Packet Data**
   - Does NOT include full packet dumps
   - Does NOT include payload data
   - Does NOT include all header details

3. **Top-N Analysis**
   - Top 10 source IPs
   - Top 10 destination IPs
   - Top 10 conversations
   - Top 5 ports

### Stage 2: On-Demand Retrieval (Future Enhancement)

When user asks specific questions, we can:
1. Parse the question
2. Generate appropriate filter
3. Load ONLY relevant packets
4. Send to LLM

Example:
```
User: "Show me all HTTP traffic to 192.168.1.1"
→ Apply filter: "http and ip.dst == 192.168.1.1"
→ Load only matching packets
→ Send to LLM
```

## Performance Comparison

| File Size | Full Mode | Summary Mode | Quick Mode |
|-----------|-----------|--------------|------------|
| 1 MB      | 2s        | 1s           | <1s        |
| 50 MB     | 60s       | 5s           | <1s        |
| 300 MB    | FAILS     | 30s          | <1s        |
| 1 GB      | FAILS     | 90s          | <1s        |

## Configuration Examples

### For small captures (development/testing)
```bash
PCAP_LOAD_MODE=full
MAX_CONTEXT_LENGTH=8192
PCAP_CONTEXT_RATIO=0.7
```

### For production use (large captures)
```bash
PCAP_LOAD_MODE=summary
MAX_CONTEXT_LENGTH=4096
PCAP_CONTEXT_RATIO=0.5
```

### For massive captures (forensics/analysis)
```bash
PCAP_LOAD_MODE=quick
MAX_CONTEXT_LENGTH=4096
```

## Troubleshooting

**Error: "cannot truncate prompt with n_keep > n_ctx"**
- Switch to `summary` or `quick` mode
- Or increase `MAX_CONTEXT_LENGTH`

**Summary mode doesn't show packet details**
- This is by design for large files
- Stage 2 (on-demand retrieval) coming soon
- Use display filters to focus on specific traffic

**Quick mode only shows 1000 packets**
- For faster exploration of huge files
- Switch to `summary` for full file analysis
