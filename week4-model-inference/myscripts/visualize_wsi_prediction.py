#!/usr/bin/env python3
"""
Week 4: WSI Prediction Visualization
"""

from pathlib import Path
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import cm
from collections import Counter
import sys  # ← 추가

from tiatoolbox.wsicore.wsireader import WSIReader
from tiatoolbox.models.engine.patch_predictor import PatchPredictor
from tiatoolbox.utils.visualization import overlay_prediction_mask

print("=" * 60)
print("WSI Prediction Visualization")
print("=" * 60)

# WSI 파일명을 명령줄 인자로 받기
if len(sys.argv) > 1:
    wsi_filename = sys.argv[1]  # ← 첫 번째 인자
else:
    wsi_filename = "CMU-1-Small-Region"  # 기본값

# 파일 경로 자동 생성
wsi_path = f"/data/{wsi_filename}.svs"
predictions_json = f"/results/wsi_predictions/{wsi_filename}/predictions.json"
output_dir = Path(f"/results/visualizations/{wsi_filename}")
output_dir.mkdir(parents=True, exist_ok=True)

print(f"\nWSI: {wsi_path}")
print(f"Predictions: {predictions_json}")
print(f"Output: {output_dir}")

# 클래스 정의 (Kather 100K 데이터셋)
CLASS_NAMES = {
    0: "BACK",
    1: "NORM",
    2: "DEB",
    3: "TUM",
    4: "ADI",
    5: "MUC",
    6: "MUS",
    7: "STR",
    8: "LYM",
}

# 클래스 전체 영어 이름
CLASS_NAMES_FULL = {
    0: "Background",
    1: "Normal colon mucosa",
    2: "Debris",
    3: "Colorectal adenocarcinoma epithelium",
    4: "Adipose tissue",
    5: "Mucus",
    6: "Smooth muscle",
    7: "Cancer-associated stroma",
    8: "Lymphocytes",
}

# 클래스별 색상
label_color_dict = {}
label_color_dict[0] = ("empty", (0, 0, 0))
colors = cm.get_cmap("Set1").colors
for class_id, class_name in CLASS_NAMES.items():
    if class_id > 0:
        label_color_dict[class_id] = (class_name, 255 * np.array(colors[class_id - 1]))

# JSON에서 예측 결과 로드
print("\n[Step 1] Loading prediction results")
with open(predictions_json, 'r') as f:
    result = json.load(f)

predictions = result['predictions']
coordinates = result['coordinates']
print(f"  - Loaded {len(predictions)} patch predictions")
print(f"  - WSI filename from JSON: {result.get('wsi_filename', 'N/A')}")

# 클래스 분포 분석
print("\n[Step 2] Analyzing class distribution")
class_counts = Counter(predictions)

fig, ax = plt.subplots(1, 1, figsize=(12, 6))

classes = sorted(class_counts.keys())
counts = [class_counts[c] for c in classes]
labels = [CLASS_NAMES[c] for c in classes]

bar_colors = []
for c in classes:
    if c == 0:
        bar_colors.append('black')
    else:
        bar_colors.append(colors[c - 1])

ax.bar(range(len(classes)), counts, color=bar_colors, edgecolor='black', alpha=0.7)
ax.set_xticks(range(len(classes)))
ax.set_xticklabels([f"{c}\n{CLASS_NAMES[c]}" for c in classes], fontsize=9)
ax.set_xlabel('Class', fontsize=12)
ax.set_ylabel('Number of Patches', fontsize=12)
ax.set_title(f'Patch Prediction Distribution - {wsi_filename}', fontsize=14, fontweight='bold')
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig(output_dir / "class_distribution.png", dpi=150, bbox_inches='tight')
print(f"  - Saved: {output_dir / 'class_distribution.png'}")
plt.close()

# WSI 썸네일 생성
print("\n[Step 3] Loading WSI and generating thumbnail")
reader = WSIReader.open(wsi_path)
print(f"  - WSI size: {reader.info.level_dimensions[0]}")

overview_resolution = 4
overview_unit = "mpp"

wsi_thumbnail = reader.slide_thumbnail(
    resolution=overview_resolution, 
    units=overview_unit
)
print(f"  - Thumbnail size: {wsi_thumbnail.shape}")

# 예측 맵 생성
print("\n[Step 4] Merging predictions into prediction map")
print("  (This may take a moment)")

predictor = PatchPredictor(pretrained_model="resnet18-kather100k", batch_size=32)

wsi_output_dict = {
    'predictions': predictions,
    'coordinates': coordinates,
    'resolution': result['resolution'],
    'units': result['units'],
}

pred_map = predictor.merge_predictions(
    wsi_path,
    wsi_output_dict,
    resolution=overview_resolution,
    units=overview_unit,
)
print(f"  - Prediction map size: {pred_map.shape}")

# 오버레이 시각화
print("\n[Step 5] Creating overlay visualization")

overlay = overlay_prediction_mask(
    wsi_thumbnail,
    pred_map,
    alpha=0.5,
    label_info=label_color_dict,
    return_ax=True,
)

plt.savefig(output_dir / "wsi_prediction_overlay.png", dpi=150, bbox_inches='tight')
print(f"  - Saved: {output_dir / 'wsi_prediction_overlay.png'}")
plt.close()

# 원본 썸네일
print("\n[Step 6] Saving original thumbnail")
fig, ax = plt.subplots(figsize=(10, 10))
ax.imshow(wsi_thumbnail)
ax.set_title(f"Original WSI - {wsi_filename}", fontsize=14, fontweight='bold')
ax.axis('off')
plt.savefig(output_dir / "wsi_original_thumbnail.png", dpi=150, bbox_inches='tight')
print(f"  - Saved: {output_dir / 'wsi_original_thumbnail.png'}")
plt.close()

# 범례
print("\n[Step 7] Creating legend")
fig, ax = plt.subplots(figsize=(10, 6))
ax.axis('off')

legend_patches = []
for class_id in sorted(CLASS_NAMES.keys()):
    if class_id in class_counts:
        color = label_color_dict[class_id][1] / 255.0 if class_id > 0 else [0, 0, 0]
        count = class_counts[class_id]
        label = f"{CLASS_NAMES[class_id]}: {CLASS_NAMES_FULL[class_id]} ({count} patches)"
        legend_patches.append(mpatches.Patch(color=color, label=label))

ax.legend(
    handles=legend_patches, 
    loc='center',
    fontsize=12,
    frameon=True,
    title="Tissue Classes",
    title_fontsize=14
)

plt.savefig(output_dir / "legend.png", dpi=150, bbox_inches='tight')
print(f"  - Saved: {output_dir / 'legend.png'}")
plt.close()

print(f"\n{'='*60}")
print("Visualization Complete!")
print(f"{'='*60}")
print(f"Output directory: {output_dir}")
print(f"\nGenerated files:")
print(f"  1. class_distribution.png")
print(f"  2. wsi_original_thumbnail.png")
print(f"  3. wsi_prediction_overlay.png")
print(f"  4. legend.png")
print(f"{'='*60}")