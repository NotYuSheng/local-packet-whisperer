import pyshark as ps
import streamlit as st
import os
import re
import asyncio
from lpw_init import getLpwPath, returnValue
from lpw_pcap_summary import generate_pcap_summary, get_quick_stats

def remove_ansi_escape_sequences(input_string):
    # Define a regular expression pattern to match ANSI escape sequences
    ansi_escape_pattern = r'\x1B(?:[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]'
    
    # Use re.sub() to replace ANSI escape sequences with an empty string
    cleaned_string = re.sub(ansi_escape_pattern, '', input_string)
    
    return cleaned_string

@st.cache_data
def getPcapData(input_file:str = "", filter="", decode_info={}):
    try :
        if os.name == 'nt':
            eventloop = asyncio.ProactorEventLoop()
            asyncio.set_event_loop(eventloop)
        cap : ps.FileCapture = ps.FileCapture(input_file=input_file, display_filter=filter)
        outfile_path = os.path.join(getLpwPath('temp'), 'out.txt')
        with open(outfile_path, 'w') as f:
            for pkt in cap:
                print(pkt, file=f)
        out_string = open(outfile_path, 'r').read()

        # Apply context length limits to prevent exceeding model's context window
        # Calculate max characters: tokens * 4 (rough approximation) * context ratio
        max_context = returnValue('max_context_length')
        context_ratio = returnValue('pcap_context_ratio')
        max_chars = int(max_context * 4 * context_ratio)  # ~4 chars per token

        original_length = len(out_string)
        if original_length > max_chars:
            # Truncate and add informative message
            out_string = out_string[:max_chars]
            truncation_msg = f"\n\n{'='*50}\n[TRUNCATED]\nOriginal capture: {original_length:,} chars\nShowing: {max_chars:,} chars ({int(context_ratio*100)}% of {max_context} token context)\nTo see more data, increase MAX_CONTEXT_LENGTH in .env file\n{'='*50}\n"
            out_string = out_string + truncation_msg
            st.warning(f'⚠️ PCAP data truncated to fit context window. Showing {max_chars:,} of {original_length:,} chars. Increase MAX_CONTEXT_LENGTH in .env to see more.', icon='📏')

        #os.remove('out.txt')
    except ps.tshark.tshark.TSharkNotFoundException:
        st.error(body='TShark/Wireshark is not installed. \n Please install [wireshark](https://tshark.dev/setup/install/#install-wireshark-with-a-package-manager) first', icon='🚨')
        st.warning(body='LPW is now stopped', icon='🛑')
        st.stop()
    return remove_ansi_escape_sequences(out_string)

@st.cache_data
def getPcapSummary(input_file: str = "", filter: str = "") -> str:
    """
    Alternative to getPcapData that returns only a statistical summary.
    Use this for large PCAP files (300MB+) to avoid context window issues.

    Returns:
        A compact summary (~1-2KB) instead of full packet dump
    """
    return generate_pcap_summary(input_file, filter)

@st.cache_data
def getQuickPcapStats(input_file: str = "", filter: str = "") -> str:
    """
    Ultra-fast summary for very large files.
    Samples first 1000 packets only.
    """
    return get_quick_stats(input_file, filter)