#!/bin/bash

# Week 7: Graph Construction
# Reads Week 6 predictions.json and builds graph

WSI_FILES=("CMU-1-Small-Region" "TEST_sample1" "TEST_sample2")

echo "=========================================="
echo "Week 7: Slide Graph Construction"
echo "=========================================="
echo ""

for WSI in "${WSI_FILES[@]}"; do
    echo "Processing: $WSI"
    echo "------------------------------------------"
    
    docker run --rm \
      -v "$(pwd)/../week6-slide-graph/results:/data/week6_results" \
      -v "$(pwd)/results:/results" \
      -v "$(pwd)/myscripts:/workspace" \
      ghcr.io/tissueimageanalytics/tiatoolbox:1.6.0-py3.11-ubuntu \
      python3 /workspace/build_graph.py "$WSI"
    
    echo ""
    echo "✓ Completed: $WSI"
    echo ""
done

echo "=========================================="
echo "All graphs built!"
echo "=========================================="