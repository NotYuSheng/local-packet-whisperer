#!/usr/bin/env python3
"""
Test script to verify PCAP loading modes are working correctly.
Run this before starting LPW to ensure everything is configured properly.
"""

import os
import sys
from pathlib import Path

# Add bin directory to path
sys.path.insert(0, str(Path(__file__).parent / 'bin'))

def test_imports():
    """Test that all required imports work"""
    print("Testing imports...")

    try:
        import pyshark
        print("  ✓ pyshark")
    except ImportError as e:
        print(f"  ✗ pyshark - {e}")
        return False

    try:
        import streamlit
        print("  ✓ streamlit")
    except ImportError as e:
        print(f"  ✗ streamlit - {e}")
        return False

    try:
        import chromadb
        print("  ✓ chromadb (RAG available)")
    except ImportError:
        print("  ⚠ chromadb not installed (RAG not available)")
        print("    Install with: pip install chromadb")

    try:
        from lpw_init import returnValue, default_settings
        print("  ✓ lpw_init")
    except ImportError as e:
        print(f"  ✗ lpw_init - {e}")
        return False

    try:
        from lpw_packet import getPcapData, getPcapSummary, getQuickPcapStats
        print("  ✓ lpw_packet (all modes)")
    except ImportError as e:
        print(f"  ✗ lpw_packet - {e}")
        return False

    try:
        from lpw_pcap_summary import generate_pcap_summary, get_quick_stats
        print("  ✓ lpw_pcap_summary")
    except ImportError as e:
        print(f"  ✗ lpw_pcap_summary - {e}")
        return False

    try:
        from lpw_rag import PcapRAG
        print("  ✓ lpw_rag (RAG module)")
    except ImportError as e:
        print(f"  ⚠ lpw_rag - {e}")

    return True

def test_env_config():
    """Test .env configuration"""
    print("\nTesting .env configuration...")

    from dotenv import load_dotenv
    load_dotenv()

    # Check required settings
    max_context = os.getenv('MAX_CONTEXT_LENGTH', '4096')
    print(f"  MAX_CONTEXT_LENGTH: {max_context}")

    pcap_mode = os.getenv('PCAP_LOAD_MODE', 'summary')
    print(f"  PCAP_LOAD_MODE: {pcap_mode}")

    if pcap_mode not in ['full', 'summary', 'quick']:
        print(f"  ⚠ Invalid PCAP_LOAD_MODE: {pcap_mode}")
        print(f"    Should be: full, summary, or quick")

    context_ratio = os.getenv('PCAP_CONTEXT_RATIO', '0.5')
    print(f"  PCAP_CONTEXT_RATIO: {context_ratio}")

    use_rag = os.getenv('USE_RAG', 'false')
    print(f"  USE_RAG: {use_rag}")

    if use_rag.lower() == 'true':
        print("  RAG Configuration:")
        print(f"    RAG_GROUP_SIZE: {os.getenv('RAG_GROUP_SIZE', '10')}")
        print(f"    RAG_MAX_INDEX: {os.getenv('RAG_MAX_INDEX', '0')} (0 = unlimited)")
        print(f"    RAG_RETRIEVE_K: {os.getenv('RAG_RETRIEVE_K', '5')}")

    llm_server = os.getenv('LLM_SERVER', '127.0.0.1')
    llm_port = os.getenv('LLM_SERVER_PORT', '11434')
    print(f"\n  LLM Server: {llm_server}:{llm_port}")

    return True

def test_pcap_files():
    """Check if there are test PCAP files available"""
    print("\nLooking for test PCAP files...")

    pcap_files = []
    for ext in ['*.pcap', '*.pcapng']:
        pcap_files.extend(Path('.').glob(ext))

    if pcap_files:
        print(f"  Found {len(pcap_files)} PCAP file(s):")
        for f in pcap_files[:5]:  # Show first 5
            size_mb = f.stat().st_size / (1024 * 1024)
            print(f"    - {f.name} ({size_mb:.2f} MB)")
        if len(pcap_files) > 5:
            print(f"    ... and {len(pcap_files) - 5} more")
    else:
        print("  No PCAP files found in current directory")
        print("  You can upload PCAPs through the web interface")

    return True

def test_summary_mode():
    """Test if summary mode would work"""
    print("\nTesting summary mode capability...")

    try:
        from lpw_pcap_summary import generate_pcap_summary
        print("  ✓ Summary generation available")

        # Check if we have a test PCAP
        pcap_files = list(Path('.').glob('*.pcap')) + list(Path('.').glob('*.pcapng'))
        if pcap_files:
            test_file = pcap_files[0]
            print(f"  Testing with: {test_file.name}")
            print("  (This will take a few seconds...)")

            summary = generate_pcap_summary(str(test_file))
            summary_size = len(summary)
            print(f"  ✓ Generated summary: {summary_size} chars (~{summary_size//4} tokens)")

            if summary_size < 10000:
                print("  ✓ Summary fits easily in 4K context window")
            else:
                print(f"  ⚠ Summary is large ({summary_size} chars)")
        else:
            print("  ℹ No PCAP files to test with")
            print("  Summary mode will work when you upload a PCAP")

    except Exception as e:
        print(f"  ✗ Error testing summary mode: {e}")
        return False

    return True

def test_rag_availability():
    """Test if RAG is available and working"""
    print("\nTesting RAG availability...")

    try:
        import chromadb
        print("  ✓ ChromaDB installed")

        # Test ephemeral client creation
        client = chromadb.EphemeralClient()
        collection = client.create_collection(name="test_collection")
        print("  ✓ Can create in-memory collections")

        # Test adding and querying
        collection.add(
            documents=["This is a test packet"],
            ids=["test1"]
        )
        results = collection.query(
            query_texts=["test"],
            n_results=1
        )
        print("  ✓ Can add and query documents")

        # Cleanup
        client.delete_collection(name="test_collection")
        print("  ✓ Can cleanup collections")

        print("\n  RAG is ready to use!")
        print("  Set USE_RAG=true in .env to enable")

    except ImportError:
        print("  ✗ ChromaDB not installed")
        print("  RAG not available")
        print("  Install with: pip install chromadb")
        return False
    except Exception as e:
        print(f"  ✗ Error testing RAG: {e}")
        return False

    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("LPW PCAP Loading Modes Test")
    print("=" * 60)

    all_passed = True

    all_passed &= test_imports()
    all_passed &= test_env_config()
    all_passed &= test_pcap_files()

    # Optional tests
    print("\n" + "=" * 60)
    print("Optional Feature Tests")
    print("=" * 60)

    test_summary_mode()
    test_rag_availability()

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All core tests passed!")
        print("\nYou can now start LPW with: lpw start")
        print("\nRecommended configuration:")
        print("  PCAP_LOAD_MODE=summary  (for large files)")
        print("  USE_RAG=true            (for detailed queries)")
    else:
        print("✗ Some tests failed")
        print("Please fix the issues above before starting LPW")
    print("=" * 60)

if __name__ == "__main__":
    main()
