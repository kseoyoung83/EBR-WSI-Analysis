#!/bin/bash

# WSI files to normalize (using CMU as target)
SOURCE_FILES=("TEST_sample1" "TEST_sample2")

echo "========================================"
echo "Stain Normalization Pipeline"
echo "Target: CMU-1-Small-Region"
echo "========================================"

for SOURCE in "${SOURCE_FILES[@]}"; do
    echo ""
    echo "Processing: $SOURCE.svs"
    echo "----------------------------------------"
    
    docker run --rm \
      -v "$(pwd)/data:/data" \
      -v "$(pwd)/results:/results" \
      -v "$(pwd)/myscripts:/workspace" \
      ghcr.io/tissueimageanalytics/tiatoolbox:1.6.0-py3.11-ubuntu \
      python3 /workspace/stain_normalization.py "$SOURCE"
    
    # Create subdirectory for this source
    mkdir -p "results/${SOURCE}"
    mv results/normalization_comparison.png "results/${SOURCE}/"
    mv results/normalized_*.png "results/${SOURCE}/" 2>/dev/null || true
    
    echo "✓ Results saved to: results/${SOURCE}/"
done

echo ""
echo "========================================"
echo "All normalizations complete!"
echo "========================================"