#!/bin/bash

# Week 7: Boundary Detection

WSI_FILES=("CMU-1-Small-Region" "TEST_sample1" "TEST_sample2")

echo "=========================================="
echo "Week 7: Boundary Detection"
echo "=========================================="
echo ""

for WSI in "${WSI_FILES[@]}"; do
    echo "Processing: $WSI"
    echo "------------------------------------------"
    
    docker run --rm \
      -v "$(pwd)/results:/results" \
      -v "$(pwd)/myscripts:/workspace" \
      ghcr.io/tissueimageanalytics/tiatoolbox:1.6.0-py3.11-ubuntu \
      python3 /workspace/analyze_boundaries.py "$WSI"
    
    echo ""
    echo "✓ Completed: $WSI"
    echo ""
done

echo "=========================================="
echo "All boundary analyses complete!"
echo "=========================================="
