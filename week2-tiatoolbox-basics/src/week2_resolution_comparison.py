"""
Week 2: Resolution & Level Comparison
다양한 해상도와 단위로 WSI 읽기
"""

from tiatoolbox.wsicore.wsireader import WSIReader
import matplotlib.pyplot as plt
from pathlib import Path

wsi_path = "data/CMU-1-Small-Region.svs"
reader = WSIReader.open(wsi_path)
output_dir = Path("results/week2")

print("=" * 60)
print("해상도 및 레벨 비교 실습")
print("=" * 60)

# 1. 썸네일 - 다양한 해상도로 생성
print("\n[실습 1] 썸네일 해상도 비교")
resolutions = [0.5, 1.25, 2.5, 5.0]

fig, axes = plt.subplots(2, 2, figsize=(12, 10))
axes = axes.flatten()

for idx, res in enumerate(resolutions):
    thumbnail = reader.slide_thumbnail(resolution=res, units="power")
    axes[idx].imshow(thumbnail)
    axes[idx].set_title(f"Resolution: {res}x (size: {thumbnail.shape[:2]})")
    axes[idx].axis('off')
    print(f"✓ {res}x 썸네일 크기: {thumbnail.shape}")

plt.tight_layout()
plt.savefig(output_dir / "thumbnail_resolution_comparison.png", dpi=150)
print(f"✓ 저장: thumbnail_resolution_comparison.png")

# 2. 같은 위치, 다른 해상도로 패치 읽기
print("\n[실습 2] 같은 위치, 다른 MPP (Microns Per Pixel)")
location = (1200, 1200)
size = (512, 512)
mpp_values = [0.25, 0.5, 1.0, 2.0]

fig, axes = plt.subplots(2, 2, figsize=(12, 12))
axes = axes.flatten()

for idx, mpp in enumerate(mpp_values):
    patch = reader.read_rect(location, size, resolution=mpp, units='mpp')
    axes[idx].imshow(patch)
    axes[idx].set_title(f"MPP: {mpp} (size: {patch.shape[:2]})")
    axes[idx].axis('off')
    print(f"✓ MPP {mpp}: 패치 크기 {patch.shape}")

plt.tight_layout()
plt.savefig(output_dir / "patch_mpp_comparison.png", dpi=150)
print(f"✓ 저장: patch_mpp_comparison.png")

# 3. WSI의 다양한 영역 탐색
print("\n[실습 3] WSI 다양한 영역 탐색")
# 전체 크기 확인
width, height = reader.info.level_dimensions[0]
print(f"전체 크기: {width} x {height}")

# 그리드 방식으로 여러 위치 샘플링
locations = [
    (width//4, height//4),
    (width//2, height//4),
    (3*width//4, height//4),
    (width//4, height//2),
    (width//2, height//2),
    (3*width//4, height//2),
]

fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes = axes.flatten()

for idx, loc in enumerate(locations):
    patch = reader.read_rect(loc, (256, 256), resolution=0.5, units='mpp')
    axes[idx].imshow(patch)
    axes[idx].set_title(f"Location: ({loc[0]}, {loc[1]})")
    axes[idx].axis('off')

plt.tight_layout()
plt.savefig(output_dir / "wsi_region_exploration.png", dpi=150)
print(f"✓ 저장: wsi_region_exploration.png")

print("\n" + "=" * 60)
print("모든 실습 완료!")
print("=" * 60)