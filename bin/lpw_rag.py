"""
RAG (Retrieval Augmented Generation) for PCAP Analysis

This module provides semantic search capabilities for large PCAP files.
Instead of loading all packets into context, we:
1. Create embeddings for packet groups
2. Store in vector database
3. Retrieve only relevant packets based on user queries

Requires: chromadb, sentence-transformers (or use Ollama embeddings)
"""

import pyshark as ps
import streamlit as st
from typing import List, Dict, Tuple
import os
import asyncio
from lpw_init import getLpwPath

# TODO: Add these dependencies to requirements.txt
# - chromadb>=0.4.0
# - sentence-transformers>=2.2.0

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    st.warning("ChromaDB not installed. Install with: pip install chromadb", icon="⚠️")


class PcapRAG:
    """
    RAG system for PCAP analysis.

    Usage:
        rag = PcapRAG(pcap_file="capture.pcap")
        rag.index_packets()  # One-time indexing
        results = rag.query("Show me HTTP traffic")  # Retrieve relevant packets
    """

    def __init__(self, pcap_file: str, filter: str = ""):
        self.pcap_file = pcap_file
        self.filter = filter
        self.collection_name = "current_pcap_session"  # Simple session name

        # Initialize ChromaDB in-memory (session only, no persistence)
        if CHROMADB_AVAILABLE:
            # Use EphemeralClient for in-memory storage (auto-cleanup on restart)
            self.client = chromadb.EphemeralClient()

            # Delete old collection if exists (fresh start each upload)
            try:
                self.client.delete_collection(name=self.collection_name)
            except:
                pass  # Collection doesn't exist yet

            # Create new collection for this session
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"pcap_file": pcap_file, "session": "current"}
            )

    def index_packets(self, group_size: int = 10, max_packets: int = None) -> Dict:
        """
        Index packets into vector database.

        Args:
            group_size: Number of packets to group together (reduces DB size)
            max_packets: Maximum packets to index (None = all)

        Returns:
            Statistics about indexing
        """
        if not CHROMADB_AVAILABLE:
            st.error("ChromaDB not available. Cannot index packets.")
            return {}

        try:
            if os.name == 'nt':
                eventloop = asyncio.ProactorEventLoop()
                asyncio.set_event_loop(eventloop)

            cap = ps.FileCapture(input_file=self.pcap_file, display_filter=self.filter)

            packet_groups = []
            current_group = []
            group_id = 0
            packet_count = 0

            for pkt in cap:
                packet_count += 1

                # Create packet description
                pkt_desc = self._create_packet_description(pkt)
                current_group.append({
                    'packet_num': packet_count,
                    'description': pkt_desc,
                    'raw': str(pkt)
                })

                # Group packets
                if len(current_group) >= group_size:
                    packet_groups.append({
                        'id': f"group_{group_id}",
                        'packets': current_group,
                        'text': self._create_group_text(current_group)
                    })
                    current_group = []
                    group_id += 1

                if max_packets and packet_count >= max_packets:
                    break

            # Add remaining packets
            if current_group:
                packet_groups.append({
                    'id': f"group_{group_id}",
                    'packets': current_group,
                    'text': self._create_group_text(current_group)
                })

            cap.close()

            # Index in ChromaDB
            documents = [g['text'] for g in packet_groups]
            ids = [g['id'] for g in packet_groups]
            metadatas = [{
                'packet_count': len(g['packets']),
                'first_packet': g['packets'][0]['packet_num'],
                'last_packet': g['packets'][-1]['packet_num']
            } for g in packet_groups]

            self.collection.add(
                documents=documents,
                ids=ids,
                metadatas=metadatas
            )

            return {
                'total_packets': packet_count,
                'total_groups': len(packet_groups),
                'group_size': group_size
            }

        except Exception as e:
            st.error(f"Error indexing packets: {e}")
            return {}

    def query(self, query_text: str, top_k: int = 5) -> List[Dict]:
        """
        Query for relevant packets using semantic search.

        Args:
            query_text: User's question or search query
            top_k: Number of packet groups to retrieve

        Returns:
            List of relevant packet groups with their packets
        """
        if not CHROMADB_AVAILABLE:
            return []

        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=top_k
            )

            # Extract packet details
            relevant_groups = []
            for i, group_id in enumerate(results['ids'][0]):
                relevant_groups.append({
                    'group_id': group_id,
                    'distance': results['distances'][0][i],
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i]
                })

            return relevant_groups

        except Exception as e:
            st.error(f"Error querying packets: {e}")
            return []

    def get_packets_for_groups(self, group_ids: List[str]) -> str:
        """
        Retrieve full packet details for specific groups.

        This would load the actual packets from the PCAP file
        based on the packet numbers in the groups.
        """
        # TODO: Implement efficient packet extraction by number
        pass

    def _create_packet_description(self, pkt) -> str:
        """Create a human-readable description of a packet for embedding"""
        desc_parts = []

        # Protocol
        if hasattr(pkt, 'highest_layer'):
            desc_parts.append(f"Protocol: {pkt.highest_layer}")

        # IP layer
        if hasattr(pkt, 'ip'):
            desc_parts.append(f"From {pkt.ip.src} to {pkt.ip.dst}")

        # Transport layer
        if hasattr(pkt, 'tcp'):
            desc_parts.append(f"TCP port {pkt.tcp.srcport} to {pkt.tcp.dstport}")
        elif hasattr(pkt, 'udp'):
            desc_parts.append(f"UDP port {pkt.udp.srcport} to {pkt.udp.dstport}")

        # Application layer hints
        if hasattr(pkt, 'http'):
            if hasattr(pkt.http, 'request_method'):
                desc_parts.append(f"HTTP {pkt.http.request_method} request")
            if hasattr(pkt.http, 'host'):
                desc_parts.append(f"to {pkt.http.host}")
        elif hasattr(pkt, 'dns'):
            if hasattr(pkt.dns, 'qry_name'):
                desc_parts.append(f"DNS query for {pkt.dns.qry_name}")
        elif hasattr(pkt, 'tls'):
            desc_parts.append("TLS/SSL encrypted traffic")

        return ", ".join(desc_parts)

    def _create_group_text(self, packet_group: List[Dict]) -> str:
        """Create searchable text for a packet group"""
        texts = [p['description'] for p in packet_group]
        return " | ".join(texts)

    def cleanup(self):
        """
        Cleanup session data. Called when:
        - User uploads new PCAP
        - App restarts
        - User explicitly requests cleanup

        With EphemeralClient, data is already in-memory only,
        but this provides explicit cleanup if needed.
        """
        if CHROMADB_AVAILABLE:
            try:
                self.client.delete_collection(name=self.collection_name)
            except Exception as e:
                # Collection might not exist, that's fine
                pass

    def delete_index(self):
        """Alias for cleanup() - kept for backwards compatibility"""
        self.cleanup()


# Helper function for integration
@st.cache_resource
def get_rag_instance(pcap_file: str, filter: str = "") -> PcapRAG:
    """Get or create RAG instance for a PCAP file (cached)"""
    return PcapRAG(pcap_file, filter)
