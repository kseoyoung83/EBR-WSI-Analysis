#!/bin/bash

WSI_FILES=("CMU-1-Small-Region" "TEST_sample1" "TEST_sample2")

echo "========================================"
echo "Feature Extraction & Analysis Pipeline"
echo "========================================"

for WSI in "${WSI_FILES[@]}"; do
    echo ""
    echo "Processing: $WSI.svs"
    echo "----------------------------------------"
    
    # Step 1: Extract features
    echo "[1/2] Extracting features..."
    docker run --rm \
      -v "$(pwd)/data:/data" \
      -v "$(pwd)/results:/results" \
      -v "$(pwd)/myscripts:/workspace" \
      ghcr.io/tissueimageanalytics/tiatoolbox:1.6.0-py3.11-ubuntu \
      python3 /workspace/extract_features.py "$WSI"
    
    # Step 2: Analyze features
    echo "[2/2] Analyzing features..."
    docker run --rm \
      -v "$(pwd)/data:/data" \
      -v "$(pwd)/results:/results" \
      -v "$(pwd)/myscripts:/workspace" \
      ghcr.io/tissueimageanalytics/tiatoolbox:1.6.0-py3.11-ubuntu \
      python3 /workspace/analyze_graph_features.py "$WSI"
    
    echo "✓ Completed: $WSI"
done

echo ""
echo "========================================"
echo "All processing complete!"
echo "========================================"