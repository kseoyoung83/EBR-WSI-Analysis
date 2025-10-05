<artifact identifier="week2-report-markdown" type="text/markdown" title="2주차 TIAToolbox 실습 레포트">
# Evolution of Biomedical Research

의과대학 의예과 2024191115 김서영

## ▼ 2주차 실습

## 실습 개요

### 1. 실습 목표
- TIAToolbox를 이용한 WSI(Whole Slide Image) 읽기 및 정보 확인
- 다양한 해상도(resolution) 및 단위(units) 이해
- 썸네일 생성 및 특정 영역 추출
- Tissue Masking을 통한 조직/배경 자동 분리
- 1주차 OpenSlide와 TIAToolbox의 차이점 학습

### 2. 실습 환경
- **운영체제**: macOS (Apple M1 Pro)
- **개발 도구**: VS Code
- **패키지 관리자**: UV
- **Python 버전**: 3.11.13 (3.13에서 다운그레이드)
- **주요 라이브러리**:
  - tiatoolbox 1.3.0
  - shapely >= 2.0.0
  - matplotlib 3.9.3
  - numpy 2.1.3
  - openslide-python 1.4.2

### 3. 데이터
- **파일명**: CMU-1-Small-Region.svs (1주차와 동일)
- **크기**: 1.8MB
- **전체 해상도**: 2220 x 2967 픽셀
- **레벨 수**: 1
- **출처**: TIAToolbox 샘플 데이터

### 4. 학습 배경
- **1주차**: 로컬 환경에서 OpenSlide를 이용한 패치 추출
- **2주차 목표**: TIAToolbox의 고급 기능 학습 (원래는 Google Colab 예정)
- **변경 사유**: 
  - Colab에서 import 오류 발생
  - VS Code 환경이 이미 구축되어 있어 로컬에서 진행하는 것이 더 효율적
  - GPU 사용을 필요로 할 만큼의 큰 데이터 미사용
  - 세션 제한 없이 이용하고자 함
  - 패키지 의존성을 기존 로컬 환경에 맞춘 채로 예제 연습하고자 함

---

## 실습 과정

### 1. 환경 재구축

#### a. 문제 발견: Python 버전 충돌

**상황**:
1주차에서 Python 3.11로 가상환경을 구축했다고 생각했으나, 실제로는 Python 3.13.5가 사용되고 있었음.

```bash
cd ~/Desktop/wsi_processing
source .venv/bin/activate
python --version
# 출력: Python 3.13.5
```

**TIAToolbox 설치 시도**:

```bash
uv add tiatoolbox
```

**에러 발생**:

```
× Failed to build `shapely==1.8.5.post1`
├─▶ The build backend returned an error
╰─▶ Call to `setuptools.build_meta:__legacy__.build_wheel` failed (exit status: 1)

[stderr]
...
File "/Users/ksy/.cache/uv/builds-v0/.tmpHWTjvc/lib/python3.13/site-packages/
pkg_resources/__init__.py", line 2191, in <module>
    register_finder(pkgutil.ImpImporter, find_on_path)
                    ^^^^^^^^^^^^^^^^^^^
AttributeError: module 'pkgutil' has no attribute 'ImpImporter'. 
Did you mean: 'zipimporter'?
```

**원인 분석**:
- Python 3.13에서 `pkgutil.ImpImporter` 가 제거됨
- shapely 1.8.5 (TIAToolbox의 의존성)가 Python 3.13과 호환되지 않음
- UV 빌드 캐시에 Python 3.13 환경이 남아있음

#### b. 해결 과정

**Step 1: 가상환경 완전 재구축**

```bash
cd ~/Desktop/wsi_processing

# 1. 가상환경 비활성화
deactivate

# 2. 기존 가상환경 삭제
rm -rf .venv

# 3. UV 캐시 삭제 (중요!)
rm -rf ~/.cache/uv

# 4. Python 3.11 확인
python3.11 --version
# 출력: Python 3.11.13
```

**Step 2: Python 3.11로 가상환경 생성**

```bash
# 5. 가상환경 생성
uv venv --python python3.11

# 6. 가상환경 파일 확인
ls -la .venv/bin/python*
# 출력: python, python3, python3.11 등

# 7. 활성화
source .venv/bin/activate

# 8. Python 경로 확인 (중요!)
which python
# 출력: /Users/ksy/Desktop/wsi_processing/.venv/bin/python
```

**처음에는 실패**:

```bash
which python
# 출력: /Users/ksy/.pyenv/shims/python # 잘못된 경로!
```

pyenv가 우선순위를 가져가서 실패. 터미널 재시작으로 해결:

```bash
exec zsh # 터미널 재시작
cd ~/Desktop/wsi_processing
source .venv/bin/activate
which python
# 출력: /Users/ksy/Desktop/wsi_processing/.venv/bin/python # 성공!
```

**Step 3: 패키지 재설치**

```bash
# 9. 기존 패키지 동기화
uv sync

# 10. shapely를 최신 버전으로 먼저 설치 (핵심!)
uv add "shapely>=2.0.0"

# 11. TIAToolbox 설치
uv add tiatoolbox
```

**성공 확인**:

```bash
python -c "import tiatoolbox; print('TIAToolbox version:', tiatoolbox.__version__)"
# 출력: 
# /Users/ksy/Desktop/wsi_processing/.venv/lib/python3.13/site-packages/tiatoolbox/
# __init__.py:8: UserWarning: pkg_resources is deprecated as an API.
# TIAToolbox version: 1.3.0
```

경고 메시지는 정상 (setuptools deprecation 경고, 무시 가능)

#### c. 학습 내용

**Python 의존성 지옥 (Dependency Hell) 경험**:

1. **패키지 간 의존성 체인**:
   ```
   TIAToolbox → shapely 1.8.5 → setuptools → pkg_resources
   Python 3.13에서 pkgutil.ImpImporter 제거
   하나의 호환성 문제가 전체 설치 실패로 이어짐
   ```

2. **해결 전략**:
   - shapely를 2.0.0 이상으로 선행 설치
   - 최신 버전은 Python 3.13 호환 문제 해결됨
   - 의존성 순서 조정으로 문제 회피

3. **캐시의 중요성**:
   - UV는 빌드 캐시를 `~/.cache/uv`에 저장
   - 가상환경만 재생성해도 캐시가 남아 있으면 동일한 에러 발생
   - `rm -rf ~/.cache/uv` 필수

4. **가상환경 활성화 확인**:
   - `which python`으로 실제 사용 중인 Python 경로 확인 필수
   - pyenv, conda 등 다른 Python 관리자와 충돌 가능

---

### 2. TIAToolbox 기본 실습

#### a. 코드 작성: week2_wsi_reading.py

```python
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
print(f"- 전체 크기: {reader.info.level_dimensions[0]}")
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
location = (1200, 1200)
size = (256, 256)
patch = reader.read_rect(
    location,
    size,
    resolution=0.5,
    units='mpp'
)
print(f"✓ 패치 크기: {patch.shape}")
print(f"✓ 좌표: {location}, 크기: {size}")
plt.imsave(output_dir / "patch_sample.png", patch)
print(f"✓ 저장 완료: {output_dir / 'patch_sample.png'}")

# 5. 여러 위치의 패치 비교
print("\n[Step 5] 여러 위치 패치 비교")
locations = [
    (500, 500),
    (1200, 1200),
    (2000, 1500),
]

fig, axes = plt.subplots(1, 3, figsize=(15, 6)) # height 증가로 제목 잘림 방지
for idx, loc in enumerate(locations):
    patch = reader.read_rect(loc, (256, 256), resolution=0.5, units='mpp')
    axes[idx].imshow(patch)
    axes[idx].set_title(f"Location: {loc}", fontsize=12, pad=15)
    axes[idx].axis('off')

plt.tight_layout(pad=2.0)
plt.savefig(output_dir / "patch_comparison.png", dpi=150, bbox_inches='tight')
print(f"✓ 비교 이미지 저장: {output_dir / 'patch_comparison.png'}")

print("\n" + "=" * 50)
print("실습 완료!")
print(f"결과물 위치: {output_dir}")
print("=" * 50)
```

#### b. 실행 결과

```bash
python src/week2_wsi_reading.py
```

**출력**:

```
==================================================
TIAToolbox WSI Reading 실습
==================================================

[Step 1] WSI 파일 열기
✓ 파일 열기 성공: data/CMU-1-Small-Region.svs

[Step 2] WSI 기본 정보
- 파일 경로: data/CMU-1-Small-Region.svs
- 전체 크기: (2220, 2967)
- 레벨 수: 1
- 각 레벨 크기:
  Level 0: (2220, 2967)

[Step 3] 썸네일 생성
✓ 썸네일 크기: (185, 139, 3)
✓ 저장 완료: results/week2/thumbnail.png

[Step 4] 특정 영역 읽기
✓ 패치 크기: (256, 256, 3)
✓ 좌표: (1200, 1200), 크기: (256, 256)
✓ 저장 완료: results/week2/patch_sample.png

[Step 5] 여러 위치 패치 비교
✓ 비교 이미지 저장: results/week2/patch_comparison.png

==================================================
실습 완료!
결과물 위치: results/week2
==================================================
```

**결과 확인**:

```bash
ls results/patches/ | wc -l
# 출력: 88

ls results/patches/ | head -5
# 출력:
# patch_x0_y0.png
# patch_x0_y1024.png
# patch_x0_y1280.png
# patch_x0_y1536.png
# patch_x0_y1792.png

open results/patches/patch_x0_y0.png
# 시각적 확인
```

#### c. 시행착오: matplotlib 제목 잘림

**문제**: `patch_comparison.png`에서 상단의 "Location" 제목이 잘려서 보임.

**원인**:
- `figsize=(15, 5)`로 높이가 부족
- `tight_layout()`이 제목 공간을 충분히 확보하지 못함

**해결**:

```python
fig, axes = plt.subplots(1, 3, figsize=(15, 6)) # 5 → 6으로 증가
for idx, loc in enumerate(locations):
    patch = reader.read_rect(loc, (256, 256), resolution=0.5, units='mpp')
    axes[idx].imshow(patch)
    axes[idx].set_title(f"Location: {loc}", fontsize=12, pad=15) # pad 추가
    axes[idx].axis('off')

plt.tight_layout(pad=2.0) # 전체 여백 증가
plt.savefig(output_dir / "patch_comparison.png", dpi=150, bbox_inches='tight')
```

**학습**:
- matplotlib에서 복잡한 레이아웃은 수동 조정 필요
- `pad` 파라미터로 요소 간 간격 조정
- `bbox_inches='tight'`로 불필요한 여백 제거

---

### 3. 해상도 비교 실습

#### a. 코드 작성: week2_resolution_comparison.py

```python
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
width, height = reader.info.level_dimensions[0]
print(f"전체 크기: {width} x {height}")

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
```

#### b. 실행 결과

```bash
python src/week2_resolution_comparison.py
```

**출력**:

```
============================================================
해상도 및 레벨 비교 실습
============================================================

[실습 1] 썸네일 해상도 비교
✓ 0.5x 썸네일 크기: (370, 278, 3)
✓ 1.25x 썸네일 크기: (185, 139, 3)
✓ 2.5x 썸네일 크기: (93, 70, 3)
✓ 5.0x 썸네일 크기: (47, 35, 3)
✓ 저장: thumbnail_resolution_comparison.png

[실습 2] 같은 위치, 다른 MPP (Microns Per Pixel)
✓ MPP 0.25: 패치 크기 (512, 512, 3)
✓ MPP 0.5: 패치 크기 (512, 512, 3)
✓ MPP 1.0: 패치 크기 (512, 512, 3)
✓ MPP 2.0: 패치 크기 (512, 512, 3)
✓ 저장: patch_mpp_comparison.png

[실습 3] WSI 다양한 영역 탐색
전체 크기: 2220 x 2967
✓ 저장: wsi_region_exploration.png

============================================================
모든 실습 완료!
============================================================
```

#### c. 해상도 개념 학습

**1. units="power" vs units="mpp"**

| units | 의미 | 값이 작을수록 | 값이 클수록 |
|-------|------|--------------|------------|
| power (resolution 단위) | 배율 (0.5x=절반 크기) | 덜 축소된 이미지 | 더 작은 이미지 |
| mpp | microns per pixel | 더 확대된 이미지 | 더 축소된 이미지 |

**2. 실험 결과 해석**:
- **Resolution 0.5x**: 370 × 278 픽셀 (가장 큼, 가장 상세)
- **Resolution 5.0x**: 47 × 35 픽셀 (가장 작음, 전체 개요)
- **MPP 0.25**: 조직 구조가 매우 확대되어 세밀한 부분 관찰 가능
- **MPP 2.0**: 조직 구조가 축소되어 넓은 영역 관찰 가능

---

### 4. Tissue Masking 실습

#### a. 코드 작성: week2_tissue_masking.py

```python
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
    location=location,
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
    tissue = reader.read_rect(loc, (256, 256), resolution=0.5, units="mpp")
    axes[0, idx].imshow(tissue)
    axes[0, idx].set_title(f"Tissue at {loc}", fontsize=10, pad=10)
    axes[0, idx].axis('off')
    
    mask = mask_reader.read_rect(loc, (256, 256), resolution=0.5, units="mpp")
    axes[1, idx].imshow(mask, vmin=0, vmax=1, cmap='gray')
    axes[1, idx].set_title(f"Mask at {loc}", fontsize=10, pad=10)
    axes[1, idx].axis('off')

plt.tight_layout(pad=2.0)
plt.savefig(output_dir / "tissue_mask_multiple_locations.png", dpi=150, bbox_inches='tight')
print(f"✓ 저장: tissue_mask_multiple_locations.png")

# 5. 마스크 통계
print("\n[Step 5] Mask 통계")
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
```

#### b. 실행 결과

```bash
python src/week2_tissue_masking.py
```

**출력**:

```
============================================================
Tissue Masking 실습
============================================================

[Step 1] 기본 Tissue Mask 생성
✓ Mask reader 생성 완료
  - 원본 WSI 크기: (2220, 2967)
  - Mask 이미지 크기: (2220, 2967)

[Step 2] Mask 썸네일 생성
✓ Mask 썸네일 크기: (185, 139)
✓ 저장: tissue_mask_overview.png

[Step 3] 특정 영역 - 원본 vs Mask
✓ 원본 영역 크기: (500, 500, 3)
✓ Mask 영역 크기: (500, 500)
✓ 저장: tissue_mask_region.png

[Step 4] 여러 위치 비교
✓ 저장: tissue_mask_multiple_locations.png

[Step 5] Mask 통계
✓ 전체 픽셀: 411,810
✓ 조직 픽셀: 177,310
✓ 조직 비율: 43.06%

============================================================
Tissue Masking 실습 완료!
============================================================
```

**결과 확인**:

```bash
ls results/patches/all | wc -l
# 출력: 88

ls results/patches/tissue_only | wc -l
# 출력: 39

open results/patches/tissue_only/
# 조직 사진만 담은 폴더 열기
```

#### c. Tissue Mask 해석

**Mask 색상 의미**:
- **흰색 (값 1)**: 조직(tissue)
- **검은색 (값 0)**: 배경(glass/no tissue)

**Location (1200, 1200) 분석**:
- Tissue 이미지: 분홍-보라색 H&E 염색 조직으로 가득 참
- Mask 이미지: 전부 흰색 → 조직으로 가득 차 있음을 의미 (정상)
- 검증: 해당 위치의 mask 값이 거의 100% 조직임을 확인

**Location (500, 500) 및 (2000, 1500)**:
- Tissue 이미지: 대부분 배경(흰색)
- Mask 이미지: 검은색 → 배경으로 올바르게 감지

**통계 결과**:
- 전체 슬라이드의 43.06%가 조직
- 1주차의 `tissue_threshold=0.3` (30%) 설정과 비교
- TIAToolbox는 Otsu method + morphological operations 사용 (더 정교)

**1주차 방법 (단순 임계값)**:
- 밝기 < 200인 픽셀을 조직으로 간주
- 고정된 기준이라 모든 WSI에 적용하기 어려움
- 노이즈(얼룩, 먼지)도 조직으로 인식될 수 있음

**2주차 방법 (Otsu + Morphological)**:
- **Otsu Method**: 이미지마다 최적의 임계값을 자동 계산
- **Morphological Operations**:
  - Erosion 침식: 작은 노이즈 제거
  - Dilation 팽창: 조직 영역 복원 및 약간 확장
- **결과**: 더 깨끗하고 안정적인 마스크

#### d. tissue_mask()의 기능

```python
# 동일한 좌표로 원본과 마스크를 읽을 수 있음
tissue_region = reader.read_rect(location, size, resolution, units)
mask_region = mask_reader.read_rect(location, size, resolution, units) # 같은 좌표!
```

**`tissue_mask()` 메서드**: VirtualWSIReader 객체를 반환합니다 (`mask_reader`라는 변수로 받음)

**VirtualWSIReader의 핵심 장점**:
- 실제로는 낮은 해상도의 마스크 이미지
- 하지만 원본 WSI와 동일한 좌표계 사용 가능
- 좌표 변환을 자동으로 처리

---

## 최종 결과물

### 1. 정량적 결과

| 항목 | 값 |
|------|-----|
| 실습 파일 수 | 3개 (wsi_reading, resolution_comparison, tissue_masking) |
| 생성된 이미지 수 | 9개 |
| WSI 크기 | 2220 × 2967 픽셀 |
| 조직 비율 | 43.06% |

### 2. 생성된 파일 목록

```
results/week2/
├── thumbnail.png
├── patch_sample.png
├── patch_comparison.png
├── thumbnail_resolution_comparison.png
├── patch_mpp_comparison.png
├── wsi_region_exploration.png
├── tissue_mask_overview.png
├── tissue_mask_region.png
└── tissue_mask_multiple_locations.png
```

### 3. 정성적 결과

#### a. WSI 읽기:
- WSIReader를 통한 간편한 WSI 접근
- 여러 해상도와 단위 지원
- 메타데이터 자동 추출

#### b. 해상도 비교:
- units="power": 배율 기반 (0.5x ~ 5.0x)
- units="mpp": 물리적 단위 (Microns Per Pixel)
- 용도에 따라 적절한 해상도 선택 가능

#### c. Tissue Masking:
- Otsu method를 이용한 자동 임계값 설정
- Morphological operations로 노이즈 제거
- VirtualWSIReader로 원본과 동일한 좌표계 사용

---

## 핵심 학습 내용

### 1. 환경 관리

#### a. Python 버전 호환성의 중요성

**문제**: Python 3.13의 `pkgutil.ImpImporter` 제거

**영향**: shapely 1.8.5 빌드 실패 → TIAToolbox 설치 불가

**해결**: Python 3.11 + shapely >= 2.0.0

#### b. 의존성 관리 전략

**전략 1: 최신 버전 우선 설치**
- shapely >= 2.0.0 먼저 설치
- 최신 버전은 호환성 문제가 해결된 경우 많음

**전략 2: 캐시 관리**
- `~/.cache/uv` 정기적으로 삭제
- 빌드 오류 시 캐시 영향 고려

**전략 3: 가상환경 검증**
- `which python`으로 실제 사용 중인 Python 경로 확인 필수
- pyenv, conda 등 다른 Python 관리자와 충돌 가능

#### c. 1주차 vs 2주차 환경 비교

| 항목 | 1주차 | 2주차 |
|------|-------|-------|
| Python | 3.11.13 | 3.11.13 |
| 주요 문제 | OpenSlide 라이브러리 연동 | shapely 빌드 실패 |
| 해결 방법 | DYLD_LIBRARY_PATH | shapely 선행 설치 |
| 학습 | 시스템 라이브러리 | 의존성 체인 |

### 2. TIAToolbox vs OpenSlide

#### a. API 비교

```python
# OpenSlide (1주차)
slide = openslide.OpenSlide(path)
patch = slide.read_region((x, y), level, (w, h))
patch = patch.convert("RGB")

# TIAToolbox (2주차)
reader = WSIReader.open(path)
patch = reader.read_rect((x, y), (w, h), resolution, units)
# RGB 변환 자동, 더 직관적인 API
```

#### b. 기능 비교

| 기능 | OpenSlide | TIAToolbox |
|------|-----------|-----------|
| WSI reading | ✓ | ✓ |
| diverse format | ✓ | ✓ |
| thumbnail formation | 수동 | slide_thumbnail() |
| resolution units | level | power, mpp, level |
| tissue masking | 수동 구현 | tissue_mask() |
| 좌표계 | 수동 변환 | VirtualWSIReader |

#### c. 사용 시나리오

**OpenSlide**: 기본적인 WSI 읽기, 저수준 제어 필요 시

**TIAToolbox**: 병리 이미지 분석 파이프라인, 고수준 추상화 필요 시

### 3. 해상도 및 단위

#### a. Resolution Units

```python
# 1. Power (배율)
thumbnail = reader.slide_thumbnail(resolution=1.25, units="power")
# 1.25배 축소 (원본의 1/1.25 크기)

# 2. MPP (Microns Per Pixel)
patch = reader.read_rect(location, size, resolution=0.5, units="mpp")
# 1픽셀 = 0.5 마이크론 (더 확대)

# 3. Level (피라미드 레벨)
patch = reader.read_rect(location, size, resolution=0, units="level")
# Level 0 = 최고 해상도
```

#### b. 해상도 선택 기준

| 목적 | 권장 해상도 | 단위 |
|------|------------|------|
| 전체 개요 | 5.0 | power |
| 썸네일 | 1.25-2.5 | power |
| 세부 분석 | 0.25-0.5 | mpp |
| 패치 추출 | 0.5 | mpp |

### 4. Tissue Masking

#### a. 동작 원리

```python
mask_reader = reader.tissue_mask(
    method="morphological", # Otsu + morphological ops
    resolution=4, # 낮은 해상도로 계산 (속도)
    units="mpp"
)
```

1. **썸네일 생성**: 낮은 해상도로 계산 속도 향상
2. **Otsu Thresholding**: 자동으로 최적 임계값 계산
3. **Morphological Operations**:
   - Erosion: 작은 노이즈 제거
   - Dilation: 조직 영역 확장 (보수적 마스크)

#### b. 1주차 방법과 비교

| 항목 | 1주차 | 2주차 |
|------|-------|-------|
| 방법 | 밝기 <200 | Otsu method |
| 임계값 | 고정 | 자동 계산 |
| 후처리 | X | Morphological ops |
| 정확도 | 중간 | 높음 |
| 유연성 | 높음 | 중간 |

#### c. VirtualWSIReader

```python
# 핵심 장점: 동일 좌표계 사용
tissue = reader.read_rect((1500, 1500), (500, 500), 0.5, "mpp")
mask = mask_reader.read_rect((1500, 1500), (500, 500), 0.5, "mpp")
# 좌표 변환 불필요!
```

---

## 어려웠던 점과 해결 과정

### 1. Python 버전 및 의존성 문제

**어려움**:
- 1주차에서 Python 3.11로 설정했다고 생각했으나 실제로는 3.13 사용
- shapely 1.8.5가 Python 3.13과 호환 안 됨
- UV 캐시에 Python 3.13 환경 남음

**해결 과정**:
1. 에러 메시지 분석
   - `AttributeError: module 'pkgutil' has no attribute 'ImpImporter'`
   - → Python 3.13 문제 파악

2. 가상환경 확인
   - `python --version` # 3.13.5!
   - `which python` # pyenv 경로!
   - → 가상환경이 제대로 활성화 안 됨

3. 완전 재구축
   - 가상환경 삭제
   - UV 캐시 삭제
   - Python 3.11로 명시적 생성
   - 터미널 재시작

4. 의존성 순서 조정
   - shapely >= 2.0.0 먼저 설치
   - TIAToolbox 나중에 설치

**학습**:
- 환경 문제는 완전히 정리하고 재구축하는 것이 빠름
- `which python`으로 항상 검증

### 2. Google Colab 포기 결정

**상황**:
- 원래 계획: Google Colab에서 실습
- 문제: `from tiatoolbox import logger` 에러 반복 발생
- 고려사항: 로컬 환경은 1주차에 이미 구축됨

**의사결정**:

**Colab의 장점**: GPU, 설치 불필요

**Colab의 단점**: 세션 제한, 파일 휘발성, 디버깅 어려움

**로컬의 장점**: 연속성, 파일 관리, 에러 제어

**로컬의 단점**: 설치 복잡도

**결론**:
- 2주차는 GPU 불필요 (WSI 읽기, 시각화)
- 로컬 환경에서 진행하는 것이 더 효율적
- 학습 목표는 "환경 구축 없이 실습"이 아닌 "TIAToolbox 기능 학습"

**학습**:
- 도구 선택은 목적에 맞게
- 유연한 계획 변경이 때로는 더 나음
- 로컬 환경의 가치 재인식

### 3. matplotlib 시각화

**문제**:
- 제목 잘림
- 색상 범위 설정 (`vmin`, `vmax`)
- 레이아웃 조정

**해결**:

```python
# 1. figsize 증가
fig, axes = plt.subplots(1, 3, figsize=(15, 6)) # height 증가

# 2. padding 추가
axes[idx].set_title(title, fontsize=12, pad=15)

# 3. tight_layout 파라미터
plt.tight_layout(pad=2.0)

# 4. bbox_inches
plt.savefig(path, dpi=150, bbox_inches='tight')

# 5. mask 색상 범위 고정
axes[1].imshow(mask, vmin=0, vmax=1, cmap='gray')
```

**학습**:
- matplotlib는 자동 레이아웃이 완벽하지 않음
- 수동 조정 필요
- 파라미터 조합으로 해결 가능

---

## 결론 및 향후 계획

### 1. 2주차 성과

#### a. 기술적 성과
- TIAToolbox 1.3.0 성공적 설치 및 활용
- 의존성 문제 독립적 해결
- WSI 읽기, 해상도 변환, Tissue Masking 실습 완료
- 9개의 분석 결과 이미지 생성

#### b. 학습적 성과
- Python 의존성 관리 심화 학습
- TIAToolbox vs OpenSlide 비교 이해
- 해상도 단위(power, mpp, level) 개념 확립
- Tissue Masking 알고리즘 이해

#### c. 문제 해결 능력
- Python 버전 충돌 → 가상환경 재구축
- shapely 빌드 오류 → 선행 설치 전략
- Google Colab 오류 → 로컬 환경 활용
- matplotlib 시각화 → 파라미터 조정

### 2. 추가 개선 방향

#### a. 코드 개선
- 공통 함수 모듈화 (예: 이미지 저장 함수)
- 설정 파일 분리 (config.yaml)
- 로깅 시스템 추가

#### b. 분석 확장
- 여러 WSI 파일 배치 처리
- Tissue Mask 품질 정량화
- 조직 영역별 통계 추출

#### c. 성능 최적화
- 멀티프로세싱으로 속도 향상
- 메모리 사용량 모니터링
- 캐싱 전략

### 3. 3주차 계획: Docker 환경 구축

**목표**:
- Docker로 재현 가능한 환경 컨테이너화
- 1-2주차 코드의 Docker화
- 팀 협업을 위한 표준 환경 구축

**준비 사항**:
- Docker Desktop 설치
- Dockerfile 작성 학습
- 볼륨 마운트 개념 이해

**예상 도전 과제**:
- Python 3.11 + TIAToolbox 의존성을 Docker에 구현
- macOS M1 환경에서 Docker 성능
- 이미지 크기 최적화

---

## 참고 자료

### 1. 공식 문서
- **TIAToolbox**: https://tia-toolbox.readthedocs.io
- **TIAToolbox GitHub**: https://github.com/TissueImageAnalytics/tiatoolbox
- **OpenSlide**: https://openslide.org
- **UV**: https://github.com/astral-sh/uv

### 2. 예제 코드
- **TIAToolbox Examples**:
  - 01-wsi-reading.ipynb
  - https://github.com/TissueImageAnalytics/tiatoolbox/tree/develop/examples

### 3. 학습 자원
- **Python 의존성 관리**:
  - PEP 621 (pyproject.toml)
  - UV 공식 문서

- **병리 이미지 분석**:
  - Otsu's Method for Thresholding
  - Morphological Operations in Image Processing

### 4. 트러블슈팅
- **shapely 빌드 이슈**: https://github.com/shapely/shapely/issues
- **Python 3.13 호환성**: Python Release Notes
- **UV 캐시 관리**: UV GitHub Issues

---

## 부록

### A. 환경 재구축 체크리스트

```bash
# 1. 가상환경 완전 삭제
cd ~/Desktop/wsi_processing
deactivate
rm -rf .venv

# 2. UV 캐시 삭제
rm -rf ~/.cache/uv

# 3. Python 버전 확인
python3.11 --version

# 4. 가상환경 생성
uv venv --python python3.11

# 5. 터미널 재시작
exec zsh

# 6. 활성화 및 검증
source .venv/bin/activate
which python
python --version

# 7. 패키지 설치
uv sync
uv add "shapely>=2.0.0"
uv add tiatoolbox

# 8. 설치 확인
python -c "import tiatoolbox; print(tiatoolbox.__version__)"
```

### B. 파일 구조

```
wsi_processing/
├── data/
│   └── CMU-1-Small-Region.svs
├── src/
│   ├── main.py (1주차)
│   ├── week2_wsi_reading.py
│   ├── week2_resolution_comparison.py
│   └── week2_tissue_masking.py
├── results/
│   ├── patches/ (1주차)
│   └── week2/
│       ├── thumbnail.png
│       ├── patch_sample.png
│       ├── patch_comparison.png
│       ├── thumbnail_resolution_comparison.png
│       ├── patch_mpp_comparison.png
│       ├── wsi_region_exploration.png
│       ├── tissue_mask_overview.png
│       ├── tissue_mask_region.png
│       └── tissue_mask_multiple_locations.png
├── .venv/
├── pyproject.toml
└── uv.lock
```

### C. 주요 명령어 학습

```bash
# 가상환경 관리
uv venv --python python3.11
source .venv/bin/activate
deactivate

# 패키지 관리
uv add [package]
uv sync
uv pip list

# 실행
python src/week2_wsi_reading.py
python src/week2_resolution_comparison.py
python src/week2_tissue_masking.py

# 결과 확인
ls -lh results/week2/
open results/week2/*.png
```
</artifact>
