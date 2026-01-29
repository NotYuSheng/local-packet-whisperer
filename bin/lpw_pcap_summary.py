import subprocess
import streamlit as st
import os
import re

def generate_pcap_summary(input_file: str, filter: str = "") -> str:
    """
    Generate PCAP summary using native tshark/capinfos commands.
    Much faster than iterating through packets - uses built-in statistics.

    Returns a formatted summary string (~1-2KB) instead of full packet dump.
    """
    try:
        summary_parts = []

        # 1. Get basic file info with capinfos (VERY fast - milliseconds)
        capinfos_cmd = ['capinfos', input_file]
        capinfos_output = subprocess.check_output(capinfos_cmd, stderr=subprocess.DEVNULL).decode('utf-8')

        # Parse capinfos output
        packet_count = re.search(r'Number of packets:\s+(\d+)', capinfos_output)
        file_size = re.search(r'File size:\s+(\d+)', capinfos_output)
        duration = re.search(r'Capture duration:\s+([\d.]+)', capinfos_output)
        start_time = re.search(r'First packet time:\s+(.+)', capinfos_output)
        end_time = re.search(r'Last packet time:\s+(.+)', capinfos_output)
        avg_pkt_size = re.search(r'Average packet size:\s+([\d.]+)', capinfos_output)

        summary_parts.append("=== PCAP SUMMARY ===")
        summary_parts.append(f"File: {os.path.basename(input_file)}")
        if packet_count:
            summary_parts.append(f"Total Packets: {int(packet_count.group(1)):,}")
        if file_size:
            size_bytes = int(file_size.group(1))
            summary_parts.append(f"Total Size: {size_bytes:,} bytes ({size_bytes/1024/1024:.2f} MB)")
        if duration:
            summary_parts.append(f"Duration: {float(duration.group(1)):.2f} seconds")
        if avg_pkt_size:
            summary_parts.append(f"Average Packet Size: {float(avg_pkt_size.group(1)):.0f} bytes")

        # 2. Get protocol hierarchy with tshark (fast - few seconds)
        summary_parts.append("\n--- PROTOCOL HIERARCHY ---")
        phs_cmd = ['tshark', '-r', input_file, '-q', '-z', 'io,phs']
        if filter:
            phs_cmd.extend(['-Y', filter])
        phs_output = subprocess.check_output(phs_cmd, stderr=subprocess.DEVNULL, timeout=60).decode('utf-8')

        # Extract protocol hierarchy lines
        phs_lines = [line for line in phs_output.split('\n') if line.strip() and not line.startswith('=')]
        if len(phs_lines) > 2:  # Skip header lines
            for line in phs_lines[2:22]:  # Top 20 protocols
                if line.strip():
                    summary_parts.append(f"  {line.strip()}")

        # 3. Get conversation statistics (IP pairs)
        summary_parts.append("\n--- TOP CONVERSATIONS ---")
        conv_cmd = ['tshark', '-r', input_file, '-q', '-z', 'conv,ip']
        if filter:
            conv_cmd.extend(['-Y', filter])
        try:
            conv_output = subprocess.check_output(conv_cmd, stderr=subprocess.DEVNULL, timeout=60).decode('utf-8')
            conv_lines = [line for line in conv_output.split('\n') if '<->' in line]
            for line in conv_lines[:10]:  # Top 10 conversations
                summary_parts.append(f"  {line.strip()}")
        except subprocess.TimeoutExpired:
            summary_parts.append("  (Conversation analysis timed out - file too large)")

        # 4. Get endpoint statistics (IPs)
        summary_parts.append("\n--- TOP ENDPOINTS ---")
        endpoints_cmd = ['tshark', '-r', input_file, '-q', '-z', 'endpoints,ip']
        if filter:
            endpoints_cmd.extend(['-Y', filter])
        try:
            endpoints_output = subprocess.check_output(endpoints_cmd, stderr=subprocess.DEVNULL, timeout=60).decode('utf-8')
            endpoint_lines = [line for line in endpoints_output.split('\n') if line.strip() and not line.startswith('=')]
            if len(endpoint_lines) > 2:
                for line in endpoint_lines[2:12]:  # Top 10 endpoints
                    if line.strip():
                        summary_parts.append(f"  {line.strip()}")
        except subprocess.TimeoutExpired:
            summary_parts.append("  (Endpoint analysis timed out - file too large)")

        # 5. Timeline info
        summary_parts.append("\n--- TIMELINE ---")
        if start_time:
            summary_parts.append(f"Start Time: {start_time.group(1)}")
        if end_time:
            summary_parts.append(f"End Time: {end_time.group(1)}")

        summary_parts.append("\n=== END SUMMARY ===")
        summary_parts.append("\nNote: This is a statistical summary. For detailed packet analysis, ask specific questions.")

        return "\n".join(summary_parts)

    except FileNotFoundError:
        st.error(body='TShark/Wireshark is not installed.', icon='🚨')
        st.stop()
        return ""
    except Exception as e:
        st.error(f'Error generating PCAP summary: {e}', icon='🚨')
        return f"Error: Could not generate summary - {str(e)}"


def get_quick_stats(input_file: str, filter: str = "") -> str:
    """
    Ultra-fast summary using capinfos only.
    Use this for very large files when you just need basic stats.
    """
    try:
        capinfos_cmd = ['capinfos', input_file]
        capinfos_output = subprocess.check_output(capinfos_cmd, stderr=subprocess.DEVNULL).decode('utf-8')

        # Parse key fields
        packet_count = re.search(r'Number of packets:\s+(\d+)', capinfos_output)
        file_size = re.search(r'File size:\s+(\d+)', capinfos_output)
        duration = re.search(r'Capture duration:\s+([\d.]+)', capinfos_output)

        return f"""
=== QUICK PCAP STATS ===
File: {os.path.basename(input_file)}
Total Packets: {int(packet_count.group(1)):,} packets
File Size: {int(file_size.group(1))/1024/1024:.2f} MB
Duration: {float(duration.group(1)):.2f} seconds

Note: This is a quick summary. Use Summary mode for detailed statistics.
"""
    except Exception as e:
        return f"Error: {str(e)}"
