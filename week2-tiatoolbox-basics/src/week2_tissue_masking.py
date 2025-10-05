"""
Week 2: Tissue Masking
조직/배경 자동 구분 및 마스크 생성
"""

from tiatoolbox.wsicore.wsireader import WSIReader
import matplotlib.pyplot as plt
from pathlib import Path

wsi_path = "data/CMU-1-Small-Region.svs"
reader = WSIReader.open(wsi_path)
output_dir = Path("results/week2")
output_dir.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("Tissue Masking 실습")
print("=" * 60)

# 1. 기본 Tissue Mask 생성
print("\n[Step 1] 기본 Tissue Mask 생성")
mask_reader = reader.tissue_mask(
    method="morphological",
    resolution=4,
    units="mpp"
)
print(f"✓ Mask reader 생성 완료")
print(f"  - 원본 WSI 크기: {reader.info.level_dimensions[0]}")
print(f"  - Mask 이미지 크기: {mask_reader.info.level_dimensions[0]}")

# 2. Mask 썸네일 생성
print("\n[Step 2] Mask 썸네일 생성")
mask_thumbnail = mask_reader.slide_thumbnail(resolution=1.25, units="power")
print(f"✓ Mask 썸네일 크기: {mask_thumbnail.shape}")

# 원본과 mask 비교
original_thumbnail = reader.slide_thumbnail(resolution=1.25, units="power")

fig, axes = plt.subplots(1, 2, figsize=(12, 6))
axes[0].imshow(original_thumbnail)
axes[0].set_title("Original WSI", fontsize=12, pad=15)
axes[0].axis('off')
axes[1].imshow(mask_thumbnail, cmap='gray')
axes[1].set_title("Tissue Mask", fontsize=12, pad=15)
axes[1].axis('off')

plt.tight_layout(pad=2.0)
plt.savefig(output_dir / "tissue_mask_overview.png", dpi=150, bbox_inches='tight')
print(f"✓ 저장: tissue_mask_overview.png")

# 3. 특정 영역의 원본과 마스크 비교
print("\n[Step 3] 특정 영역 - 원본 vs Mask")
location = (1500, 1500)
size = (500, 500)

tissue_region = reader.read_rect(
    location=location,
    size=size,
    resolution=0.5,
    units="mpp"
)

mask_region = mask_reader.read_rect(
    location=location,  # 동일한 좌표 사용 가능!
    size=size,
    resolution=0.5,
    units="mpp"
)

print(f"✓ 원본 영역 크기: {tissue_region.shape}")
print(f"✓ Mask 영역 크기: {mask_region.shape}")

fig, axes = plt.subplots(1, 2, figsize=(12, 6))
axes[0].imshow(tissue_region)
axes[0].set_title(f"Tissue Region at {location}", fontsize=12, pad=15)
axes[0].axis('off')
axes[1].imshow(mask_region, vmin=0, vmax=1, cmap='gray')
axes[1].set_title(f"Mask Region at {location}", fontsize=12, pad=15)
axes[1].axis('off')

plt.tight_layout(pad=2.0)
plt.savefig(output_dir / "tissue_mask_region.png", dpi=150, bbox_inches='tight')
print(f"✓ 저장: tissue_mask_region.png")

# 4. 여러 위치에서 원본과 마스크 비교
print("\n[Step 4] 여러 위치 비교")
locations = [
    (500, 500),
    (1200, 1200),
    (2000, 1500),
]

fig, axes = plt.subplots(2, 3, figsize=(15, 10))

for idx, loc in enumerate(locations):
    # 원본
    tissue = reader.read_rect(loc, (256, 256), resolution=0.5, units="mpp")
    axes[0, idx].imshow(tissue)
    axes[0, idx].set_title(f"Tissue at {loc}", fontsize=10, pad=10)
    axes[0, idx].axis('off')
    
    # 마스크
    mask = mask_reader.read_rect(loc, (256, 256), resolution=0.5, units="mpp")
    axes[1, idx].imshow(mask, vmin=0, vmax=1, cmap='gray')
    axes[1, idx].set_title(f"Mask at {loc}", fontsize=10, pad=10)
    axes[1, idx].axis('off')

plt.tight_layout(pad=2.0)
plt.savefig(output_dir / "tissue_mask_multiple_locations.png", dpi=150, bbox_inches='tight')
print(f"✓ 저장: tissue_mask_multiple_locations.png")

# 5. 마스크 통계
print("\n[Step 5] Mask 통계")
# 전체 마스크 이미지 가져오기
full_mask = mask_reader.slide_thumbnail(resolution=5.0, units="power")
total_pixels = full_mask.size
tissue_pixels = (full_mask > 0).sum()
tissue_ratio = tissue_pixels / total_pixels * 100

print(f"✓ 전체 픽셀: {total_pixels:,}")
print(f"✓ 조직 픽셀: {tissue_pixels:,}")
print(f"✓ 조직 비율: {tissue_ratio:.2f}%")

print("\n" + "=" * 60)
print("Tissue Masking 실습 완료!")
print("=" * 60)