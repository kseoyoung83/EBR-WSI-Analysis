
<artifact identifier="week5-report" type="text/markdown" title="5주차 Stain Normalization 실습 레포트">
# Evolution of Biomedical Research

의과대학 의예과 2024191115 김서영

## ▼ 5주차 실습

## 실습 개요

### 1. 실습 목표
- Stain Normalization 개념 이해 및 실습
- 3가지 정규화 알고리즘 비교 (Macenko, Vahadane, Reinhard)
- Docker 환경에서 배치 처리 구현
- WSI 간 색상 편차 보정
- Before/After 시각화

### 2. 실습 환경
- **운영체제**: macOS (Apple M1 Pro)
- **개발 도구**: Terminal (zsh), VSCode
- **컨테이너**: Docker Desktop for Mac
- **Docker 이미지**: `ghcr.io/tissueimageanalytics/tiatoolbox:1.6.0-py3.11-ubuntu`
- **주요 라이브러리**:
  - TIAToolbox 1.6.0
  - scikit-image
  - matplotlib 3.9.3

### 3. 데이터
총 3개의 WSI 파일:

| 파일명 | 역할 | 크기 |
|--------|------|------|
| CMU-1-Small-Region.svs | Target (기준) | 1.8MB |
| TEST_sample1.svs | Source (정규화 대상) | 미확인 |
| TEST_sample2.svs | Source (정규화 대상) | 미확인 |

### 4. 학습 배경
- **1-2주차**: 로컬 환경에서 WSI 처리 기초
- **3주차**: Docker 환경 구축
- **4주차**: AI 모델로 패치 분류 (색상 편차 발견)
- **5주차 동기**: 
  - 4주차에서 WSI별 색상 차이 관찰
  - 일관된 염색 색상으로 통일 필요
  - 모델 입력 데이터 표준화

---

## 실습 과정

### 1. Stain Normalization 개념 학습

#### a. TIAToolbox 예제 분석

```bash
cd ~/Desktop/tiatoolbox/examples
open -a "Visual Studio Code" 02-stain-normalization.ipynb
```

**예제에서 확인한 내용**:
- 4가지 normalization 방법: Macenko, Vahadane, Reinhard, Ruifrok
- Source/Target 개념
- 2×2 grid 시각화 패턴

**예제 핵심 코드 패턴**:
```python
# Custom stain matrix 방식
stain_matrix = skimage.color.fgx_from_rgb[:2]
custom_normalizer = stainnorm.CustomNormalizer(stain_matrix)
custom_normalizer.fit(target_image)

# Vahadane 방식
vahadane_normalizer = stainnorm.VahadaneNormalizer()
vahadane_normalizer.fit(target_image)

# 변환
normed_sample1 = custom_normalizer.transform(sample.copy())
normed_sample2 = vahadane_normalizer.transform(sample.copy())

# 시각화 (2×2)
plt.subplot(2, 2, 1): Source Image
plt.subplot(2, 2, 2): Custom Stain Matrix
plt.subplot(2, 2, 3): Target Image
plt.subplot(2, 2, 4): Vahadane
```

#### b. 핵심 개념 이해

**Target Image (목표 이미지)**:
- "이런 색상으로 통일하고 싶다"는 기준
- 이상적인 H&E 염색 색상을 가진 이미지
- Normalizer가 이 색상을 학습

**Source Image (원본 이미지)**:
- 색상 편차가 있는 변환 대상
- Target과 다른 염색 결과
- Normalizer가 이 이미지를 Target처럼 변환

**동작 원리**:
```python
# 1. Target의 색상 패턴 학습
normalizer.fit(target_image)
# → "분홍은 RGB(200, 100, 150), 보라는 RGB(150, 50, 200)" 학습

# 2. Source를 Target처럼 변환
normalized = normalizer.transform(source_image)
# → Source의 색상이 Target처럼 변환됨
```

**중요한 이해**:
- 실제 슬라이드를 다시 염색하는 게 아님
- 디지털 이미지의 픽셀 값을 수학적으로 변환
- 실제 염색 = 벽을 다시 칠하기
- Stain Normalization = 사진 필터 (Instagram 필터)

**왜 필요한가?**:
- 병원마다 염색 프로토콜 다름
- 슬라이드 스캐너마다 색상 다름
- 시간 경과에 따라 염색 시약 변화
- → 같은 조직인데 색상이 다르게 보임
- → AI 모델이 혼란 (같은 조직을 다른 타입으로 분류)

### 2. 프로젝트 구조 생성

```bash
cd ~/Desktop/EBR-WSI-Analysis
mkdir -p week5-stain-normalization/{data,myscripts,results}
cd week5-stain-normalization
```

**최종 구조**:
```
week5-stain-normalization/
├── data/
│   ├── CMU-1-Small-Region.svs (Target)
│   ├── TEST_sample1.svs (Source)
│   └── TEST_sample2.svs (Source)
├── myscripts/
│   └── stain_normalization.py
├── process_stain_norm.sh
└── results/
    ├── TEST_sample1/
    └── TEST_sample2/
```

### 3. 정규화 스크립트 작성

#### a. stain_normalization.py

**파일 생성**:
```bash
nano myscripts/stain_normalization.py
```

**전체 코드**:
```python
#!/usr/bin/env python3
"""
Week 5: Stain Normalization
Compare different normalization methods on WSI thumbnails
"""

import sys
import numpy as np
from pathlib import Path
from PIL import Image
import matplotlib.pyplot as plt
from tiatoolbox.wsicore.wsireader import WSIReader
from tiatoolbox.tools import stainnorm

def load_wsi_thumbnail(wsi_path, resolution=4.0, units="mpp"):
    """Load WSI thumbnail"""
    reader = WSIReader.open(wsi_path)
    thumbnail = reader.slide_thumbnail(resolution=resolution, units=units)
    return thumbnail

def compare_normalization_methods(target_img, source_img, output_dir):
    """
    Compare different stain normalization methods
    
    Args:
        target_img: Target image (reference)
        source_img: Source image (to be normalized)
        output_dir: Output directory
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Normalization methods
    methods = {
        'Macenko': stainnorm.MacenkoNormalizer(),
        'Vahadane': stainnorm.VahadaneNormalizer(),
        'Reinhard': stainnorm.ReinhardNormalizer()
    }
    
    # Fit normalizers with target image
    print("Fitting normalizers with target image...")
    for name, normalizer in methods.items():
        normalizer.fit(target_img)
        print(f"  - {name}: fitted")
    
    # Transform source image
    print("\nNormalizing source image...")
    normalized_images = {}
    for name, normalizer in methods.items():
        normalized = normalizer.transform(source_img)
        normalized_images[name] = normalized
        print(f"  - {name}: transformed")
    
    # Visualize: 2x3 grid
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    axes[0, 0].imshow(source_img)
    axes[0, 0].set_title("Source Image", fontsize=14, pad=10)
    axes[0, 0].axis('off')
    
    axes[0, 1].imshow(target_img)
    axes[0, 1].set_title("Target Image (Reference)", fontsize=14, pad=10)
    axes[0, 1].axis('off')
    
    axes[0, 2].imshow(normalized_images['Macenko'])
    axes[0, 2].set_title("Macenko Normalized", fontsize=14, pad=10)
    axes[0, 2].axis('off')
    
    axes[1, 0].imshow(normalized_images['Vahadane'])
    axes[1, 0].set_title("Vahadane Normalized", fontsize=14, pad=10)
    axes[1, 0].axis('off')
    
    axes[1, 1].imshow(normalized_images['Reinhard'])
    axes[1, 1].set_title("Reinhard Normalized", fontsize=14, pad=10)
    axes[1, 1].axis('off')
    
    # 빈칸 숨기기
    axes[1, 2].axis('off')
    
    plt.tight_layout(pad=2.0)
    plt.savefig(output_dir / "normalization_comparison.png", dpi=150, bbox_inches='tight')
    print(f"\n✓ Saved: normalization_comparison.png")
    
    # Save individual normalized images
    for name, img in normalized_images.items():
        Image.fromarray(img).save(output_dir / f"normalized_{name.lower()}.png")
        print(f"✓ Saved: normalized_{name.lower()}.png")
    
    return normalized_images

def main():
    # WSI files
    target_wsi = "/data/CMU-1-Small-Region.svs"
    source_wsi = "/data/TEST_sample1.svs"
    output_dir = "/results"
    
    # Allow command-line override
    if len(sys.argv) > 1:
        source_wsi = f"/data/{sys.argv[1]}.svs"
    
    print("=" * 60)
    print("Stain Normalization Comparison")
    print("=" * 60)
    print(f"\nTarget (reference): {target_wsi}")
    print(f"Source (to normalize): {source_wsi}")
    
    # Load thumbnails
    print("\nLoading WSI thumbnails...")
    target_thumbnail = load_wsi_thumbnail(target_wsi)
    source_thumbnail = load_wsi_thumbnail(source_wsi)
    print(f"Target shape: {target_thumbnail.shape}")
    print(f"Source shape: {source_thumbnail.shape}")
    
    # Compare normalization methods
    normalized = compare_normalization_methods(
        target_thumbnail,
        source_thumbnail,
        output_dir
    )
    
    print("\n" + "=" * 60)
    print("Stain normalization complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
```

**핵심 기능**:
1. WSI 썸네일 로드 (4.0 mpp)
2. 3가지 normalizer 생성 및 학습
3. Source 이미지 변환
4. 2×3 grid 시각화

#### b. 시각화 개선 과정

**초기 버전**: 2×2 grid (4칸)
```python
fig, axes = plt.subplots(2, 2, figsize=(12, 12))
# Source, Target, Macenko, Vahadane만 표시
# Reinhard 누락
```

**문제**: 3가지 방법을 모두 보여주지 못함

**개선 버전**: 2×3 grid (6칸)
```python
fig, axes = plt.subplots(2, 3, figsize=(18, 12))

# Row 1: Source, Target, Macenko
# Row 2: Vahadane, Reinhard, (빈칸)
axes[1, 2].axis('off')  # 빈칸 숨기기
```

**결과**: 3가지 방법 모두 표시

### 4. 배치 처리 스크립트

#### a. process_stain_norm.sh 작성

```bash
nano process_stain_norm.sh
```

**전체 코드**:
```bash
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
```

**주요 특징**:
- CMU를 Target으로 고정
- TEST_sample1, TEST_sample2를 순회
- 결과를 샘플별 하위 폴더로 정리

#### b. 스크립트 위치 선택

**고민**: myscripts 안에 넣을까, 루트에 넣을까?

**결정**: 루트 (week3-4 구조 참조)
```
week5-stain-normalization/
├── myscripts/           # Python 스크립트
│   └── stain_normalization.py
├── process_stain_norm.sh  # ← Shell 스크립트는 루트
```

**이유**:
- Python: Docker 내부에서 실행
- Shell: Docker 실행 명령어 포함

### 5. 데이터 준비 및 실행

#### a. WSI 파일 복사

```bash
cp ~/Desktop/tiatoolbox/data/CMU-1-Small-Region.svs data/
cp ~/Desktop/tiatoolbox/data/TEST_sample1.svs data/
cp ~/Desktop/tiatoolbox/data/TEST_sample2.svs data/

ls -lh data/
```

#### b. 실행 권한 설정

**시행착오**:
```bash
./process_stain_norm.sh
# 출력: zsh: permission denied: ./process_stain_norm.sh
```

**원인**: 실행 권한 없음

**해결**:
```bash
chmod +x process_stain_norm.sh
ls -la process_stain_norm.sh
# 출력: -rwxr-xr-x (x가 있어야 함)
```

#### c. 배치 실행

```bash
./process_stain_norm.sh
```

**출력**:
```
========================================
Stain Normalization Pipeline
Target: CMU-1-Small-Region
========================================

Processing: TEST_sample1.svs
----------------------------------------
============================================================
Stain Normalization Comparison
============================================================

Target (reference): /data/CMU-1-Small-Region.svs
Source (to normalize): /data/TEST_sample1.svs

Loading WSI thumbnails...
Target shape: (185, 139, 3)
Source shape: (224, 321, 3)

Fitting normalizers with target image...
  - Macenko: fitted
  - Vahadane: fitted
  - Reinhard: fitted

Normalizing source image...
  - Macenko: transformed
  - Vahadane: transformed
  - Reinhard: transformed

✓ Saved: normalization_comparison.png
✓ Saved: normalized_macenko.png
✓ Saved: normalized_vahadane.png
✓ Saved: normalized_reinhard.png

============================================================
Stain normalization complete!
============================================================
✓ Results saved to: results/TEST_sample1/

Processing: TEST_sample2.svs
----------------------------------------
(동일한 과정 반복)
✓ Results saved to: results/TEST_sample2/

========================================
All normalizations complete!
========================================
```

**소요 시간**: 약 1-2분 (2개 샘플)

---

## 최종 결과물

### 1. 정량적 결과

| 항목 | 값 |
|------|-----|
| 처리한 WSI 파일 | 3개 (Target 1 + Source 2) |
| 생성된 이미지 | 8개 (비교 2 + 개별 정규화 6) |
| 정규화 방법 | 3가지 (Macenko, Vahadane, Reinhard) |
| 총 처리 시간 | 약 1-2분 |
| Docker 이미지 크기 | 5.6GB |

### 2. 생성된 파일

```
results/
├── TEST_sample1/
│   ├── normalization_comparison.png (2×3 grid)
│   ├── normalized_macenko.png
│   ├── normalized_vahadane.png
│   └── normalized_reinhard.png
└── TEST_sample2/
    ├── normalization_comparison.png (2×3 grid)
    ├── normalized_macenko.png
    ├── normalized_vahadane.png
    └── normalized_reinhard.png
```

### 3. 시각적 결과 분석

#### a. TEST_sample1 결과

**2×3 Grid 구성**:
- **Row 1**: Source | Target (CMU) | Macenko
- **Row 2**: Vahadane | Reinhard | (빈칸)

**색상 변화 관찰**:
- **Source**: 연한 분홍색 조직, 흰색 배경
- **Target (CMU)**: 진한 분홍-보라 조직, 구조가 명확
- **Macenko**: Target과 매우 유사, 배경에 약간 푸른 색조
- **Vahadane**: Macenko와 거의 동일, 미세하게 더 선명
- **Reinhard**: 배경이 순백색으로 가장 깨끗, 조직 색상도 자연스러움

#### b. 배경 색상 차이 발견

**주요 관찰**:
- **Reinhard**: 배경이 완전한 흰색
- **Macenko/Vahadane**: 배경에 보라끼거나 푸르딩딩한 색조

**차이의 원인**:

**Reinhard 방식**:
- 이미지 전체의 평균 색상만 조정
- 픽셀별 염색 분해 없음
- 흰색 배경 → 흰색 배경 유지
- 결과: 배경이 깨끗한 흰색, 자연스러워 보임

**Macenko/Vahadane 방식**:
- 각 픽셀을 H(보라) + E(분홍)로 분해
- 배경도 약간의 염색 성분으로 추정됨
- "완벽한 흰색"이 없음을 가정
- 결과: 배경에 미세한 색조 생김

**물리적 의미**:
- 실제 슬라이드 배경도 완벽한 흰색 아님
- 유리는 투명하지만 미세한 색상 있음
- 스캐너 조명 편차, 먼지, 얼룩 존재
- Macenko/Vahadane가 이런 현실을 반영

#### c. TEST_sample2 결과

TEST_sample1과 유사한 패턴:
- 3가지 방법 모두 Target(CMU)과 유사한 색상으로 변환
- Reinhard의 배경이 가장 깨끗
- Macenko/Vahadane는 거의 동일한 결과

### 4. 조직 구조 유지도

**확인 사항**:
- Source의 조직 디테일이 정규화 후에도 유지됨
- 색상만 변환되고 형태는 그대로
- 핵, 세포질, 조직 경계 모두 선명

**결론**: 3가지 방법 모두 구조를 잘 유지

---

## 핵심 학습 내용

### 1. Stain Normalization 알고리즘 비교

#### a. Macenko Method

**원리**: Non-negative Matrix Factorization (NMF)
- RGB 이미지를 광학 밀도(Optical Density)로 변환
- 2개의 주요 염색(H&E)을 선형 분해
- SVD(Singular Value Decomposition) 사용

**수식 개념**:
```
RGB → OD (Optical Density)
OD = Stain_Matrix × Concentration
→ H 성분 + E 성분으로 분해
```

**장점**:
- 빠른 속도 (~1초)
- 안정적, 거의 실패 안 함
- 병리학 분야에서 가장 널리 사용

**단점**:
- 과도한 염색 영역에서 정확도 떨어짐
- 밝기 변화에 민감

#### b. Vahadane Method

**원리**: Sparse NMF
- Macenko와 유사하지만 sparsity constraint 추가
- 더 정교한 최적화 알고리즘
- 각 픽셀이 단일 염색에 더 순수하게 분류됨

**수식 개념**:
```
min ||OD - Stain_Matrix × Concentration||
subject to: sparsity on Concentration
→ 각 픽셀이 H 또는 E에 더 치우치게
```

**장점**:
- Macenko보다 정확함
- 복잡한 조직 구조에서 우수
- 색상 분리가 더 명확

**단점**:
- 느림 (~5-10초)
- 계산량 많음
- 때때로 수렴 실패

#### c. Reinhard Method

**원리**: Color Statistics Matching
- 이미지 전체의 평균/표준편차만 조정
- LAB 색공간에서 작동
- 염색 분해 없이 통계적 매칭

**수식 개념**:
```
RGB → LAB
Target: mean_T, std_T
Source: mean_S, std_S

Normalized = (Source - mean_S) / std_S × std_T + mean_T
```

**장점**:
- 매우 빠름 (~0.1초)
- 단순하고 robust
- 모든 타입 이미지에 적용 가능

**단점**:
- 물리적 의미 없음 (염색 개념 무시)
- H&E 특성 고려 안 함
- 조직 타입에 따라 결과 차이 큼

#### d. 비교표

| 항목 | Macenko | Vahadane | Reinhard |
|------|---------|----------|----------|
| 속도 | 빠름 (1초) | 느림 (5-10초) | 매우 빠름 (0.1초) |
| 정확도 | 높음 | 매우 높음 | 중간 |
| 안정성 | 매우 안정적 | 때때로 실패 | 매우 안정적 |
| 물리적 의미 | O (H&E 분리) | O (H&E 분리) | X (통계만) |
| 배경 처리 | 색조 추가 | 색조 추가 | 순백색 유지 |
| 사용 사례 | 일반적 | 연구용 | 빠른 프로토타입 |

### 2. 배경 색상 차이의 물리적 의미

#### a. Macenko/Vahadane의 관점

**가정**: 모든 픽셀은 H + E의 혼합

**배경 처리**:
- 흰색 배경도 약간의 H, E 성분 포함
- 실제 유리 슬라이드는 완벽한 투명 아님
- 스캐너 조명, 먼지, 얼룩 존재

**결과**: 배경에 미세한 보라/파란 색조

#### b. Reinhard의 관점

**가정**: 통계적 분포만 중요

**배경 처리**:
- 흰색은 흰색으로 유지
- 밝기 평균/표준편차만 조정

**결과**: 순백색 배경

#### c. 어느 것이 "더 좋은가"?

**AI 모델 학습용**: Macenko/Vahadane
- 물리적 의미 있음
- 염색 일관성 보장
- 배경 색조는 모델에 큰 영향 없음

**시각적 프레젠테이션**: Reinhard
- 깨끗해 보임
- 배경이 하얀 게 자연스러움

**실제 선택**:
- 대부분의 연구: Macenko (속도+정확도 균형)
- 최고 품질: Vahadane (시간 여유 있을 때)
- 대량 처리: Reinhard (속도 우선)

### 3. Docker 환경 활용

#### a. 3-4-5주차 연계성

**3주차**: Docker 환경 구축
- Dockerfile 이해
- Volume Mount 개념
- 재현성 확보

**4주차**: AI 모델 실행
- 사전훈련 모델 추론
- 배치 처리
- 색상 편차 발견 ← 5주차 동기

**5주차**: Stain Normalization
- 색상 편차 해결
- 3가지 방법 비교
- Docker 환경 재활용

#### b. Docker의 가치

**재현성**:
- 동일한 이미지 사용 (1.6.0-py3.11-ubuntu)
- 어떤 컴퓨터에서든 동일 결과
- 의존성 문제 없음

**효율성**:
- 환경 재구축 불필요
- Volume Mount로 데이터 연결
- 코드 수정 즉시 반영

### 4. 실전 워크플로우

#### a. 일반적인 WSI 분석 파이프라인

```
1. WSI 획득
   ↓
2. Quality Check (염색 상태, 스캔 품질)
   ↓
3. Stain Normalization ← 5주차
   ↓
4. Tissue Masking (배경 제거) ← 1-2주차
   ↓
5. Patch Extraction ← 1주차
   ↓
6. AI 모델 추론 ← 4주차
   ↓
7. 결과 시각화 및 분석
```

#### b. 5주차의 위치

**역할**: 데이터 전처리의 핵심 단계

**영향**:
- 모델 입력 데이터 일관성 확보
- 병원 간, 배치 간 색상 차이 제거
- 모델 성능 향상

**실무 적용**:
- 여러 병원 데이터 통합 분석 시 필수
- 시간 경과에 따른 데이터 일관성 유지
- Transfer Learning 시 domain shift 완화

---

## 어려웠던 점과 해결 과정

### 1. 시각화 Grid 크기 결정

**문제**:
- 초기 2×2 grid에서 Reinhard 방법이 누락됨
- 3가지 방법을 모두 보여주고 싶음

**해결 과정**:
1. 2×3 grid로 변경 (6칸)
2. 5개 이미지 배치: Source, Target, Macenko, Vahadane, Reinhard
3. 1개 빈칸은 `axes[1, 2].axis('off')`로 숨김

**학습**:
- matplotlib subplot은 유연하게 조정 가능
- 빈 칸도 시각적으로 처리 가능

### 2. 실행 권한 에러

**문제**:
```bash
./process_stain_norm.sh
# zsh: permission denied
```

**원인**: Shell 스크립트에 실행 권한 없음

**해결**:
```bash
chmod +x process_stain_norm.sh
ls -la process_stain_norm.sh
# -rwxr-xr-x 확인
```

**학습**:
- Unix 파일 권한 시스템 이해
- `x` (execute) 권한 필요
- `chmod +x`로 부여

### 3. 배경 색상 차이 해석

**문제**:
- Reinhard는 배경이 흰색
- Macenko/Vahadane는 배경에 색조 있음
- 어느 것이 "정상"인가?

**해결 과정**:
1. 각 알고리즘의 원리 재학습
2. 물리적 의미 이해
3. 실제 슬라이드 배경의 특성 고려

**결론**:
- 둘 다 "정상"
- 용도에 따라 선택
- Macenko/Vahadane: 물리적 의미 중시
- Reinhard: 시각적 깔끔함 중시

**학습**:
- 알고리즘 선택은 목적에 따라
- "최고의 방법"은 없음
- 장단점 이해하고 선택

### 4. Target/Source 개념 혼동

**초기 이해**: 
- "염색을 다시 한다"고 생각

**수정된 이해**:
- 디지털 이미지의 픽셀 값 변환
- 실제 슬라이드는 변하지 않음
- 사진 필터와 유사

**학습**:
- Digital Pathology의 본질 이해
- 물리적 과정 vs 디지털 처리 구분

---

## 결론 및 향후 계획

### 1. 5주차 성과

#### a. 기술적 성과

- ✓ 3가지 Stain Normalization 알고리즘 실행
- ✓ 2개 WSI의 색상 편차 성공적 보정
- ✓ Docker 환경에서 배치 처리 구현
- ✓ Before/After 시각화 (2×3 grid)
- ✓ 총 8개 정규화 이미지 생성

#### b. 학습적 성과

- Stain Normalization의 원리와 필요성 이해
- Macenko, Vahadane, Reinhard 알고리즘 비교
- 배경 색상 차이의 물리적 의미 파악
- Target/Source 개념 명확화
- Docker 환경 재활용 경험

#### c. 1-5주차 통합 성과

| 주차 | 핵심 주제 | 주요 도구 | 학습 결과 |
|------|----------|----------|----------|
| 1주차 | 로컬 환경 구축 | UV, OpenSlide | 패치 추출 파이프라인 |
| 2주차 | 고급 기능 | TIAToolbox | 해상도, Tissue Masking |
| 3주차 | 재현성 | Docker | 컨테이너 환경 구축 |
| 4주차 | 실전 적용 | 사전훈련 모델 | 배치 처리, 색상 편차 발견 |
| 5주차 | 데이터 전처리 | Stain Normalization | 색상 표준화 |

### 2. 실습의 의의

#### a. 4주차 문제 해결

**4주차 발견**:
- CMU, TEST_sample1, TEST_sample2의 색상 차이
- 같은 모델(resnet18-kather100k)에도 다른 예측 분포

**5주차 해결**:
- 3개 WSI를 동일한 색상으로 표준화
- CMU를 기준(Target)으로 통일
- 모델 입력 데이터 일관성 확보

#### b. 실전 워크플로우 구축

**완성된 파이프라인**:
```
WSI 파일
  ↓
Stain Normalization (5주차)
  ↓
Tissue Masking (2주차)
  ↓
Patch Extraction (1주차)
  ↓
AI Model Inference (4주차)
  ↓
결과 분석
```

**재현 가능성**:
- 모든 단계가 Docker로 실행 가능
- GitHub에 코드 공유됨
- 어떤 환경에서든 동일 결과

### 3. 추가 개선 방향

#### a. 모델 성능 비교 (선택)

**아이디어**: 
- Week 4 모델을 정규화된 이미지로 재실행
- 정규화 전후 예측 결과 비교

**예상 효과**:
- 조직 타입 분포가 더 일관되게 나올 것
- 색상 편차로 인한 오분류 감소

**구현 방법**:
```bash
# 1. 정규화된 이미지로 썸네일 교체
# 2. Week 4 스크립트 재실행
# 3. 클래스 분포 비교
```

#### b. 다양한 Target 테스트

**현재**: CMU를 Target으로 고정

**확장**: 
- TEST_sample1을 Target으로 사용
- TEST_sample2를 Target으로 사용
- 각각의 결과 비교

**학습 목표**: Target 선택이 결과에 미치는 영향 이해

#### c. 정량적 평가

**색상 유사도 측정**:
- Target과 Normalized의 색상 히스토그램 비교
- SSIM (Structural Similarity Index) 계산
- 방법별 정량적 비교

### 4. 장기 목표

#### a. 임상 데이터 적용

**현재**: 샘플 WSI (출처 불명)

**목표**: 실제 병원 데이터
- 같은 조직, 다른 병원 슬라이드
- 시간 경과에 따른 염색 편차
- Stain Normalization으로 통일

#### b. 자체 Target 생성

**현재**: 기존 WSI를 Target으로 사용

**고급**: 
- 이상적인 H&E 색상 정의
- Custom Stain Matrix 생성
- 표준화된 Target 확립

#### c. 실시간 처리

**현재**: 배치 처리 (수 분)

**목표**: 
- 실시간 stain normalization
- 웹 인터페이스 구축
- 병리학자 협업 도구

---

## 참고 자료

### 1. 공식 문서

- **TIAToolbox**: https://tia-toolbox.readthedocs.io
- **TIAToolbox Stain Normalization**: https://tia-toolbox.readthedocs.io/en/latest/usage.html#stain-normalization
- **TIAToolbox API**: https://tia-toolbox.readthedocs.io/en/latest/api.html

### 2. GitHub 저장소

- **TIAToolbox**: https://github.com/TissueImageAnalytics/tiatoolbox
- **TIAToolbox Examples**: https://github.com/TissueImageAnalytics/tiatoolbox/tree/develop/examples
- **02-stain-normalization.ipynb**: 공식 예제

### 3. 논문

- **Macenko et al. (2009)**: "A method for normalizing histology slides for quantitative analysis"
- **Vahadane et al. (2016)**: "Structure-preserving color normalization and sparse stain separation for histological images"
- **Reinhard et al. (2001)**: "Color transfer between images"

### 4. 개념 자료

- **H&E Staining**: https://en.wikipedia.org/wiki/H%26E_stain
- **Optical Density**: Beer-Lambert Law
- **Color Spaces**: RGB, LAB

### 5. 트러블슈팅

- **TIAToolbox GitHub Issues**: https://github.com/TissueImageAnalytics/tiatoolbox/issues
- **Stack Overflow**: `[tiatoolbox]`, `[stain-normalization]` 태그

---

## 부록

### A. 최종 명령어 모음

```bash
# 1. 프로젝트 폴더 생성
cd ~/Desktop/EBR-WSI-Analysis
mkdir -p week5-stain-normalization/{data,myscripts,results}
cd week5-stain-normalization

# 2. WSI 파일 복사
cp ~/Desktop/tiatoolbox/data/*.svs data/

# 3. 스크립트 작성 (VSCode 또는 nano)
# myscripts/stain_normalization.py
# process_stain_norm.sh

# 4. 실행 권한 부여
chmod +x process_stain_norm.sh

# 5. 배치 실행
./process_stain_norm.sh

# 6. 결과 확인
tree results/
open results/TEST_sample1/normalization_comparison.png
open results/TEST_sample2/normalization_comparison.png
```

### B. 폴더 구조 (최종)

```
week5-stain-normalization/
├── data/
│   ├── CMU-1-Small-Region.svs
│   ├── TEST_sample1.svs
│   └── TEST_sample2.svs
├── myscripts/
│   └── stain_normalization.py
├── process_stain_norm.sh
└── results/
    ├── TEST_sample1/
    │   ├── normalization_comparison.png
    │   ├── normalized_macenko.png
    │   ├── normalized_vahadane.png
    │   └── normalized_reinhard.png
    └── TEST_sample2/
        ├── normalization_comparison.png
        ├── normalized_macenko.png
        ├── normalized_vahadane.png
        └── normalized_reinhard.png
```

### C. 주요 개념 정리

**Stain Normalization**:
- H&E 염색 색상을 표준화하는 디지털 처리
- 픽셀 값 변환 (실제 염색 아님)
- Target/Source 개념 사용

**Macenko Method**:
- NMF 기반
- 빠르고 안정적
- 가장 널리 사용

**Vahadane Method**:
- Sparse NMF
- 더 정확하지만 느림
- 연구용으로 적합

**Reinhard Method**:
- 통계적 매칭
- 매우 빠름
- 배경이 깨끗

**Target Image**:
- 기준 색상
- Normalizer 학습용

**Source Image**:
- 변환 대상
- Target처럼 변환됨

**Docker Volume Mount**:
- Host ↔ Container 폴더 연결
- 데이터 영속성 보장
- 실시간 파일 공유

### D. 체크리스트

**환경 설정**:
- [x] Docker Desktop 실행 중
- [x] WSI 파일 data/ 폴더에 존재
- [x] Docker 이미지 다운로드 완료

**스크립트 준비**:
- [x] stain_normalization.py 작성 및 테스트
- [x] process_stain_norm.sh 작성
- [x] 실행 권한 부여 (chmod +x)

**실행 전 확인**:
- [x] Target: CMU-1-Small-Region.svs
- [x] Source: TEST_sample1.svs, TEST_sample2.svs
- [x] Volume Mount 경로 확인

**결과 검증**:
- [x] 각 샘플별 4개 이미지 생성
- [x] 2×3 grid에 5개 이미지 표시
- [x] 색상 변화 확인
- [x] 조직 구조 유지 확인

---

## 마치며

### 핵심 메시지

**"색상 표준화는 AI 모델 성능의 기초다."**

5주차 실습을 통해:
- ✓ Stain Normalization의 원리를 이해했습니다
- ✓ 3가지 알고리즘을 비교 실행했습니다
- ✓ WSI 간 색상 편차를 성공적으로 보정했습니다
- ✓ 디지털 병리학의 전처리 과정을 경험했습니다

### 실습의 진정한 가치

이 실습은:
- "염색을 다시 하는 법"이 아니라
- "디지털 이미지를 표준화하는 법"을 배우는 것입니다
- 물리적 염색과 디지털 처리의 차이를 이해했습니다
- 알고리즘 선택의 중요성을 깨달았습니다

### 실전 적용을 위한 준비

실무에서는:
1. 여러 병원/배치의 데이터 통합 시 필수
2. 시간 경과에 따른 데이터 일관성 유지
3. Transfer Learning 시 domain shift 완화
4. 병리학자와 협업 시 표준화된 색상 제공

### 1-5주차 통합 여정

- **1주차**: 로컬 환경에서 패치 추출
- **2주차**: TIAToolbox로 고급 기능 탐색
- **3주차**: Docker로 재현 가능한 환경 구축
- **4주차**: AI 모델로 실전 분석 (색상 편차 발견)
- **5주차**: Stain Normalization으로 문제 해결

이제 여러분은:
- WSI 병리 이미지를 전처리할 수 있습니다
- 색상 표준화의 필요성을 이해합니다
- 3가지 정규화 방법을 비교할 수 있습니다
- Docker로 재현 가능한 파이프라인을 만들 수 있습니다

**그리고 가장 중요하게는:**
알고리즘의 원리를 이해하고, 목적에 맞는 방법을 선택할 수 있습니다.
</artifact>
