#!/usr/bin/env python3
"""
Week 4: Patch Prediction using Pre-trained Model
"""

from tiatoolbox.models.engine.patch_predictor import (
    IOPatchPredictorConfig,
    PatchPredictor,
)
import torch
import os
from pathlib import Path
import json
import sys  # ← 추가

print("=" * 60)
print("WSI Patch Prediction")
print("=" * 60)

# Device 설정
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"\nUsing device: {DEVICE}")

# WSI 파일명을 명령줄 인자로 받기
if len(sys.argv) > 1:
    wsi_filename = sys.argv[1]  # ← 첫 번째 인자
else:
    wsi_filename = "CMU-1-Small-Region"  # 기본값

# WSI 파일 경로
wsi_path = f"/data/{wsi_filename}.svs"

# 파일 존재 확인
if not os.path.exists(wsi_path):
    print(f"Error: {wsi_path} not found!")
    exit(1)

print(f"Processing: {wsi_path}")
print(f"Filename: {wsi_filename}")

# 출력 디렉토리 경로만 지정
save_dir = Path(f"/results/wsi_predictions/{wsi_filename}")

# IOPatchPredictorConfig 설정
print("\n[Step 1] Configuring IOPatchPredictorConfig")
wsi_ioconfig = IOPatchPredictorConfig(
    input_resolutions=[{"units": "mpp", "resolution": 0.5}],
    patch_input_shape=[224, 224],
    stride_shape=[224, 224],
)
print("  - Resolution: 0.5 mpp")
print("  - Patch size: 224x224")
print("  - Stride: 224x224 (no overlap)")

# 사전훈련된 모델 로드
print("\n[Step 2] Loading pre-trained model")
predictor = PatchPredictor(
    pretrained_model="resnet18-kather100k",
    batch_size=32
)
print("  - Model: resnet18-kather100k")
print("  - Batch size: 32")

# 패치 예측 실행
print("\n[Step 3] Running patch prediction...")
print("  (This may take a few minutes)")

wsi_output = predictor.predict(
    imgs=[Path(wsi_path)],
    masks=None,
    mode="wsi",
    merge_predictions=False,
    ioconfig=wsi_ioconfig,
    return_probabilities=True,
    save_dir=save_dir,
    device=DEVICE
)

print("\n[Step 4] Prediction completed!")

# 결과 통계
result = wsi_output[0]
predictions = result["predictions"]
coordinates = result["coordinates"]

print(f"\n{'='*60}")
print("Prediction Statistics")
print(f"{'='*60}")
print(f"Total patches: {len(predictions)}")
print(f"Coordinate format: [x_min, y_min, x_max, y_max]")

# 클래스 분포
from collections import Counter
class_counts = Counter(predictions)

CLASS_NAMES = {
    0: "BACK (Background)",
    1: "NORM (Normal)",
    2: "DEB (Debris)",
    3: "TUM (Tumor)",
    4: "ADI (Adipose)",
    5: "MUC (Mucus)",
    6: "MUS (Muscle)",
    7: "STR (Stroma)",
    8: "LYM (Lymphocytes)",
}

print(f"\nClass Distribution:")
for class_id in sorted(class_counts.keys()):
    count = class_counts[class_id]
    percentage = count / len(predictions) * 100
    print(f"  {class_id}: {CLASS_NAMES.get(class_id, 'Unknown'):25s} - {count:3d} patches ({percentage:5.1f}%)")

# JSON 파일로 저장 (파일명 기반)
output_json = save_dir / "predictions.json"
with open(output_json, 'w') as f:
    json_data = {
        'wsi_filename': wsi_filename,  # ← 추가: 파일명 저장
        'wsi_path': wsi_path,  # ← 추가: 원본 경로 저장
        'predictions': predictions,
        'coordinates': coordinates,
        'pretrained_model': result['pretrained_model'],
        'resolution': result['resolution'],
        'units': result['units'],
    }
    json.dump(json_data, f, indent=2)

print(f"\nResults saved to: {output_json}")
print(f"{'='*60}")