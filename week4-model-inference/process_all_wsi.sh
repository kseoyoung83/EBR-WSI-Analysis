#!/bin/bash

# 처리할 WSI 파일 목록
WSI_FILES=("CMU-1-Small-Region" "TEST_sample1" "TEST_sample2")

for WSI in "${WSI_FILES[@]}"; do
    echo "========================================"
    echo "Processing: $WSI.svs"
    echo "========================================"
    
    # 예측 실행 (파일명을 인자로 전달)
    echo "[Step 1] Running prediction..."
    docker run --rm \
      -v "$(pwd)/data:/data" \
      -v "$(pwd)/results:/results" \
      -v "$(pwd)/myscripts:/workspace" \
      ghcr.io/tissueimageanalytics/tiatoolbox:1.6.0-py3.11-ubuntu \
      python3 /workspace/patch_prediction.py "$WSI"
    
    # 시각화 실행 (파일명을 인자로 전달)
    echo "[Step 2] Running visualization..."
    docker run --rm \
      -v "$(pwd)/data:/data" \
      -v "$(pwd)/results:/results" \
      -v "$(pwd)/myscripts:/workspace" \
      ghcr.io/tissueimageanalytics/tiatoolbox:1.6.0-py3.11-ubuntu \
      python3 /workspace/visualize_wsi_prediction.py "$WSI"
    
    echo "[DONE] $WSI"
    echo ""
done

echo "========================================"
echo "All WSI files processed!"
echo "========================================"