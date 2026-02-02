#!/bin/bash

echo "=========================================="
echo "Large PCAP Files for Testing (300MB+)"
echo "=========================================="
echo ""

echo "Option 1: MACCDC 2012 (Network Security Dataset)"
echo "Files: Multiple 50-300MB captures"
echo "Download:"
echo "  wget https://download.netresec.com/pcap/maccdc-2012/maccdc2012_00000.pcap.gz"
echo "  gunzip maccdc2012_00000.pcap.gz"
echo "  Size: ~280MB uncompressed"
echo ""

echo "Option 2: DEF CON CTF Captures"
echo "Files: 100-500MB captures"
echo "Download:"
echo "  wget https://download.netresec.com/pcap/defcon-18-2010/defcon18-forensics-puzzles-1.pcap"
echo "  Size: ~330MB"
echo ""

echo "Option 3: DARPA Intrusion Detection"
echo "Files: Large network captures"
echo "Download:"
echo "  wget https://www.ll.mit.edu/r-d/datasets/1998-darpa-intrusion-detection-evaluation-dataset"
echo "  Size: Various sizes up to 500MB+"
echo ""

echo "Option 4: Publicly Available PCAP Repository"
echo "Visit: https://www.netresec.com/index.ashx?page=PcapFiles"
echo ""

echo "=========================================="
echo "Quick Download (Recommended for Testing)"
echo "=========================================="
echo ""

# Try to download a large sample
if command -v wget &> /dev/null; then
    echo "Using wget to download MACCDC sample (280MB)..."
    wget -O maccdc2012_00000.pcap.gz https://download.netresec.com/pcap/maccdc-2012/maccdc2012_00000.pcap.gz
    
    if [ -f maccdc2012_00000.pcap.gz ]; then
        echo "Uncompressing..."
        gunzip maccdc2012_00000.pcap.gz
        echo "✓ Downloaded and extracted!"
        ls -lh maccdc2012_00000.pcap
    fi
elif command -v curl &> /dev/null; then
    echo "Using curl to download MACCDC sample (280MB)..."
    curl -L -o maccdc2012_00000.pcap.gz https://download.netresec.com/pcap/maccdc-2012/maccdc2012_00000.pcap.gz
    
    if [ -f maccdc2012_00000.pcap.gz ]; then
        echo "Uncompressing..."
        gunzip maccdc2012_00000.pcap.gz
        echo "✓ Downloaded and extracted!"
        ls -lh maccdc2012_00000.pcap
    fi
else
    echo "Neither wget nor curl found. Please install one to download."
fi

