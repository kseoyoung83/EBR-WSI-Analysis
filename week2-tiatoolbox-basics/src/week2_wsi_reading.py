"""
Week 2: TIAToolbox WSI Reading
목표: WSI 파일 읽기, 정보 확인, 썸네일 생성, 특정 영역 읽기
"""

from tiatoolbox.wsicore.wsireader import WSIReader
import matplotlib.pyplot as plt
from pathlib import Path

# WSI 파일 경로
wsi_path = "data/CMU-1-Small-Region.svs"

print("=" * 50)
print("TIAToolbox WSI Reading 실습")
print("=" * 50)

# 1. WSI 파일 열기
print("\n[Step 1] WSI 파일 열기")
reader = WSIReader.open(wsi_path)
print(f"✓ 파일 열기 성공: {wsi_path}")

# 2. WSI 정보 확인
print("\n[Step 2] WSI 기본 정보")
print(f"- 파일 경로: {reader.input_path}")
print(f"- 전체 크기: {reader.info.level_dimensions[0]}")  # (width, height)
print(f"- 레벨 수: {reader.info.level_count}")
print(f"- 각 레벨 크기:")
for i, dim in enumerate(reader.info.level_dimensions):
    print(f"  Level {i}: {dim}")

# 3. 썸네일 생성
print("\n[Step 3] 썸네일 생성")
thumbnail = reader.slide_thumbnail(resolution=1.25, units="power")
print(f"✓ 썸네일 크기: {thumbnail.shape}")

# 저장
output_dir = Path("results/week2")
output_dir.mkdir(parents=True, exist_ok=True)
plt.imsave(output_dir / "thumbnail.png", thumbnail)
print(f"✓ 저장 완료: {output_dir / 'thumbnail.png'}")

# 4. 특정 좌표의 영역 읽기
print("\n[Step 4] 특정 영역 읽기")
location = (1200, 1200)  # (x, y) 좌표
size = (256, 256)        # 읽을 크기
patch = reader.read_rect(
    location,
    size,
    resolution=0.5,  # MPP (Microns Per Pixel)
    units='mpp'
)
print(f"✓ 패치 크기: {patch.shape}")
print(f"✓ 좌표: {location}, 크기: {size}")

# 저장
plt.imsave(output_dir / "patch_sample.png", patch)
print(f"✓ 저장 완료: {output_dir / 'patch_sample.png'}")

# 5. 여러 위치의 패치 비교
print("\n[Step 5] 여러 위치 패치 비교")
locations = [
    (500, 500),
    (1200, 1200),
    (2000, 1500),
]

fig, axes = plt.subplots(1, 3, figsize=(15, 6))
for idx, loc in enumerate(locations):
    patch = reader.read_rect(loc, (256, 256), resolution=0.5, units='mpp')
    axes[idx].imshow(patch)
    axes[idx].set_title(f"Location: {loc}")
    axes[idx].set_title(f"Location: {loc}", pad=15)  # pad 추가
    axes[idx].axis('off')

plt.subplots_adjust(top=0.9) 
plt.tight_layout(pad=2.0)
plt.savefig(output_dir / "patch_comparison.png", dpi=150, bbox_inches='tight') 

print(f"✓ 비교 이미지 저장: {output_dir / 'patch_comparison.png'}")

print("\n" + "=" * 50)
print("실습 완료!")
print(f"결과물 위치: {output_dir}")
print("=" * 50)