import pyshark as ps
import streamlit as st
from collections import defaultdict, Counter
from datetime import datetime
import os
import asyncio

def generate_pcap_summary(input_file: str, filter: str = "") -> str:
    """
    Generate a lightweight summary of a PCAP file without loading all packet data.
    This creates a compact representation suitable for LLM context.

    Returns a formatted summary string (~1-2KB) instead of full packet dump (could be 300MB+)
    """
    try:
        if os.name == 'nt':
            eventloop = asyncio.ProactorEventLoop()
            asyncio.set_event_loop(eventloop)

        cap = ps.FileCapture(input_file=input_file, display_filter=filter)

        # Statistics collectors
        packet_count = 0
        protocols = Counter()
        src_ips = Counter()
        dst_ips = Counter()
        src_ports = Counter()
        dst_ports = Counter()
        conversations = Counter()  # (src_ip, dst_ip) pairs
        packet_sizes = []
        timestamps = []

        # Protocol-specific counters
        http_requests = 0
        dns_queries = 0
        tls_handshakes = 0

        # Iterate through packets ONCE, extracting only metadata
        for pkt in cap:
            packet_count += 1

            # Get timestamp
            if hasattr(pkt, 'sniff_timestamp'):
                timestamps.append(float(pkt.sniff_timestamp))

            # Get packet length
            if hasattr(pkt, 'length'):
                packet_sizes.append(int(pkt.length))

            # Protocol analysis
            if hasattr(pkt, 'highest_layer'):
                protocols[pkt.highest_layer] += 1

            # IP layer analysis
            if hasattr(pkt, 'ip'):
                src_ips[pkt.ip.src] += 1
                dst_ips[pkt.ip.dst] += 1
                conversations[(pkt.ip.src, pkt.ip.dst)] += 1

            # Transport layer analysis
            if hasattr(pkt, 'tcp'):
                src_ports[f"TCP/{pkt.tcp.srcport}"] += 1
                dst_ports[f"TCP/{pkt.tcp.dstport}"] += 1
            elif hasattr(pkt, 'udp'):
                src_ports[f"UDP/{pkt.udp.srcport}"] += 1
                dst_ports[f"UDP/{pkt.udp.dstport}"] += 1

            # Application layer detection
            if hasattr(pkt, 'http'):
                http_requests += 1
            if hasattr(pkt, 'dns'):
                dns_queries += 1
            if hasattr(pkt, 'tls') or hasattr(pkt, 'ssl'):
                tls_handshakes += 1

            # Limit iteration for very large files (optional safety)
            # Can remove this to analyze entire file
            # if packet_count >= 100000:  # Stop after 100k packets for summary
            #     break

        cap.close()

        # Calculate statistics
        duration = max(timestamps) - min(timestamps) if timestamps else 0
        avg_packet_size = sum(packet_sizes) / len(packet_sizes) if packet_sizes else 0
        total_bytes = sum(packet_sizes)

        # Build compact summary
        summary = f"""
=== PCAP SUMMARY ===
File: {os.path.basename(input_file)}
Total Packets: {packet_count:,}
Total Size: {total_bytes:,} bytes ({total_bytes/1024/1024:.2f} MB)
Duration: {duration:.2f} seconds
Average Packet Size: {avg_packet_size:.0f} bytes

--- PROTOCOL DISTRIBUTION ---
{format_counter(protocols, top_n=10)}

--- TOP SOURCE IPs (Top 10) ---
{format_counter(src_ips, top_n=10)}

--- TOP DESTINATION IPs (Top 10) ---
{format_counter(dst_ips, top_n=10)}

--- TOP CONVERSATIONS (Top 10) ---
{format_conversations(conversations, top_n=10)}

--- TOP PORTS ---
Source Ports: {format_counter(src_ports, top_n=5)}
Destination Ports: {format_counter(dst_ports, top_n=5)}

--- APPLICATION LAYER SUMMARY ---
HTTP Requests: {http_requests}
DNS Queries: {dns_queries}
TLS/SSL Handshakes: {tls_handshakes}

--- TIMELINE ---
Start Time: {datetime.fromtimestamp(min(timestamps)).strftime('%Y-%m-%d %H:%M:%S') if timestamps else 'N/A'}
End Time: {datetime.fromtimestamp(max(timestamps)).strftime('%Y-%m-%d %H:%M:%S') if timestamps else 'N/A'}

=== END SUMMARY ===

Note: This is a statistical summary. For detailed packet analysis, ask specific questions
and relevant packets will be retrieved on-demand.
"""
        return summary.strip()

    except ps.tshark.tshark.TSharkNotFoundException:
        st.error(body='TShark/Wireshark is not installed.', icon='🚨')
        st.stop()
        return ""
    except Exception as e:
        st.error(f'Error generating PCAP summary: {e}', icon='🚨')
        return f"Error: Could not generate summary - {str(e)}"


def format_counter(counter: Counter, top_n: int = 10) -> str:
    """Format a Counter object as a readable string"""
    if not counter:
        return "  No data"

    lines = []
    for item, count in counter.most_common(top_n):
        percentage = (count / sum(counter.values())) * 100
        lines.append(f"  {item}: {count:,} ({percentage:.1f}%)")
    return "\n".join(lines)


def format_conversations(conversations: Counter, top_n: int = 10) -> str:
    """Format conversation pairs as readable strings"""
    if not conversations:
        return "  No data"

    lines = []
    for (src, dst), count in conversations.most_common(top_n):
        lines.append(f"  {src} → {dst}: {count:,} packets")
    return "\n".join(lines)


# Quick stats function for even faster analysis (counts only, no detailed parsing)
def get_quick_stats(input_file: str, filter: str = "") -> str:
    """
    Ultra-fast summary - just counts, no detailed analysis.
    Use this for very large files (300MB+) where even summary generation is slow.
    """
    try:
        if os.name == 'nt':
            eventloop = asyncio.ProactorEventLoop()
            asyncio.set_event_loop(eventloop)

        cap = ps.FileCapture(input_file=input_file, display_filter=filter)

        packet_count = 0
        protocols = set()

        for pkt in cap:
            packet_count += 1
            if hasattr(pkt, 'highest_layer'):
                protocols.add(pkt.highest_layer)

            # Stop after sampling
            if packet_count >= 1000:
                break

        cap.close()

        return f"""
=== QUICK PCAP STATS ===
File: {os.path.basename(input_file)}
Sample Size: {packet_count:,} packets (first 1000)
Protocols Found: {', '.join(sorted(protocols))}

Note: This is a quick sample. Ask questions to analyze specific traffic.
"""
    except Exception as e:
        return f"Error: {str(e)}"
