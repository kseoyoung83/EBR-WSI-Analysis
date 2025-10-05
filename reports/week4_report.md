# Evolution of Biomedical Research

의과대학 의예과 2024191115 김서영

## ▼ 4주차 실습

## 실습 개요

### 1. 실습 목표
- Docker 환경에서 사전훈련된 AI 모델 실행
- WSI 패치 자동 분류 파이프라인 구축
- 여러 WSI 파일 배치(Batch) 처리
- 예측 결과 시각화 및 분석
- Shell 스크립트를 통한 작업 자동화

### 2. 실습 환경
- **운영체제**: macOS (Apple M1 Pro)
- **개발 도구**: Terminal (zsh), VSCode
- **컨테이너**: Docker Desktop for Mac
- **Docker 이미지**: `ghcr.io/tissueimageanalytics/tiatoolbox:1.6.0-py3.11-ubuntu`
- **이미지 크기**: 5.6GB
- **주요 라이브러리**:
  - TIAToolbox 1.6.0
  - PyTorch (CPU 모드)
  - matplotlib 3.9.3

### 3. 데이터
총 3개의 WSI 파일 처리:

| 파일명 | 크기 | 전체 해상도 | 패치 수 |
|--------|------|------------|---------|
| CMU-1-Small-Region.svs | 1.8MB | 2220 × 2967 | 82 |
| TEST_sample1.svs | 미확인 | 미확인 | 미확인 |
| TEST_sample2.svs | 미확인 | 12376 × 14074 | 1652 |

### 4. 학습 배경
- **1주차**: UV 가상환경 + OpenSlide로 패치 추출
- **2주차**: TIAToolbox 고급 기능 (Tissue Masking, 해상도 변환)
- **3주차**: Docker로 재현 가능한 환경 구축
- **4주차 목표**: 
  - 사전훈련 모델로 실전 분석
  - 여러 파일 자동 처리
  - 결과 시각화 및 해석

---

## 실습 과정

### 1. 사전훈련 모델 이해

#### a. resnet18-kather100k 모델

**출처**: Kather et al. (2019) 논문

**학습 데이터**:
- 100,000개의 대장암(colorectal cancer) 병리 이미지
- 9개 조직 클래스로 라벨링
- 224×224 픽셀 패치

**클래스 정의**:

| ID | 약어 | 전체 이름 (영어) | 한국어 |
|----|------|-----------------|--------|
| 0 | BACK | Background | 배경 |
| 1 | NORM | Normal colon mucosa | 정상 대장 점막 |
| 2 | DEB | Debris | 파편 |
| 3 | TUM | Colorectal adenocarcinoma epithelium | 종양 |
| 4 | ADI | Adipose tissue | 지방 조직 |
| 5 | MUC | Mucus | 점액 |
| 6 | MUS | Smooth muscle | 평활근 |
| 7 | STR | Cancer-associated stroma | 기질 |
| 8 | LYM | Lymphocytes | 림프구 |

**모델 특징**:
- ResNet-18 아키텍처 (18개 레이어)
- 대장암 전용으로 학습됨
- 다른 조직에 적용 시 의미 제한적

#### b. 모델의 한계 인식

**중요**: 이 모델은 입력 이미지가 무엇이든 **대장암 9개 클래스 중 하나로 분류**합니다.

**예시**:
```
CMU 샘플 (출처 불명) → 억지로 대장암 클래스에 매핑
TEST 샘플 (출처 불명) → 억지로 대장암 클래스에 매핑
```

**학습 목적**: 
- ✓ Docker에서 모델 실행 방법 습득
- ✓ 배치 처리 파이프라인 구축
- ✗ 의학적으로 유효한 진단 (불가능)

---

### 2. 예측 스크립트 작성

#### a. 기본 버전 (patch_prediction.py - 초기)

**파일 위치**: `myscripts/patch_prediction.py`

```python
#!/usr/bin/env python3
from tiatoolbox.models.engine.patch_predictor import (
    IOPatchPredictorConfig,
    PatchPredictor,
)
import torch
from pathlib import Path

# Device 설정
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# WSI 파일 경로
wsi_path = "/data/CMU-1-Small-Region.svs"

# IOPatchPredictorConfig 설정
wsi_ioconfig = IOPatchPredictorConfig(
    input_resolutions=[{"units": "mpp", "resolution": 0.5}],
    patch_input_shape=[224, 224],
    stride_shape=[224, 224],  # 겹치지 않는 패치
)

# 모델 로드
predictor = PatchPredictor(
    pretrained_model="resnet18-kather100k",
    batch_size=32
)

# 예측 실행
wsi_output = predictor.predict(
    imgs=[Path(wsi_path)],
    mode="wsi",
    ioconfig=wsi_ioconfig,
    save_dir=Path("/results/wsi_predictions"),
    device=DEVICE
)
```

**실행**:
```bash
docker run --rm \
  -v "$(pwd)/data:/data" \
  -v "$(pwd)/results:/results" \
  -v "$(pwd)/myscripts:/workspace" \
  ghcr.io/tissueimageanalytics/tiatoolbox:1.6.0-py3.11-ubuntu \
  python3 /workspace/patch_prediction.py
```

---

### 3. 시행착오 및 해결

#### a. 에러 1: on_gpu 파라미터

**문제**:
```python
TypeError: PatchPredictor.predict() got an unexpected keyword argument 'on_gpu'
```

**원인**: TIAToolbox 1.6.0에서 API 변경

**해결**:
```python
# 이전
on_gpu=False

# 수정
device=DEVICE
```

#### b. 에러 2: 문자열 vs Path 객체

**문제**:
```python
AttributeError: 'str' object has no attribute 'parent'
```

**원인**: `imgs`에 문자열 전달, Path 객체 필요

**해결**:
```python
# 이전
imgs=[wsi_path]

# 수정
from pathlib import Path
imgs=[Path(wsi_path)]
```

#### c. 에러 3: FileExistsError

**문제**:
```python
FileExistsError: [Errno 17] File exists: '/results/wsi_predictions'
```

**원인**: 
- 첫 번째 파일 처리 시 `/results/wsi_predictions` 폴더 생성
- 두 번째 파일 처리 시 TIAToolbox가 `exist_ok=False`로 재생성 시도
- 충돌 발생

**해결 1차 시도 (실패)**: 코드에서 `mkdir()` 제거
→ 여전히 TIAToolbox 내부에서 충돌

**해결 2차 시도 (성공)**: 파일별 하위 폴더 생성
```python
# 이전
save_dir = Path("/results/wsi_predictions")

# 수정
save_dir = Path(f"/results/wsi_predictions/{wsi_filename}")
```

**최종 구조**:
```
results/wsi_predictions/
├── CMU-1-Small-Region/
│   └── predictions.json
├── TEST_sample1/
│   └── predictions.json
└── TEST_sample2/
    └── predictions.json
```

---

### 4. 배치 처리 자동화

#### a. 명령줄 인자 방식

**문제**: 여러 WSI 파일을 어떻게 자동으로 처리할까?

**옵션 비교**:

| 방법 | 장점 | 단점 | 선택 |
|------|------|------|------|
| 수동 반복 | 단순 | 비효율적 | ✗ |
| sed로 파일 수정 | Shell만으로 해결 | 실패함 | ✗ |
| 명령줄 인자 | 간단, 안정적 | Python 수정 필요 | ✓ |

**patch_prediction.py 수정**:
```python
import sys

# 명령줄 인자로 파일명 받기
if len(sys.argv) > 1:
    wsi_filename = sys.argv[1]
else:
    wsi_filename = "CMU-1-Small-Region"  # 기본값

wsi_path = f"/data/{wsi_filename}.svs"
save_dir = Path(f"/results/wsi_predictions/{wsi_filename}")
```

**visualize_wsi_prediction.py도 동일하게 수정**:
```python
import sys

if len(sys.argv) > 1:
    wsi_filename = sys.argv[1]
else:
    wsi_filename = "CMU-1-Small-Region"

predictions_json = f"/results/wsi_predictions/{wsi_filename}/predictions.json"
output_dir = Path(f"/results/visualizations/{wsi_filename}")
```

#### b. Shell 스크립트 작성

**파일**: `process_all_wsi.sh`

```bash
#!/bin/bash

# 처리할 WSI 파일 목록
WSI_FILES=("CMU-1-Small-Region" "TEST_sample1" "TEST_sample2")

for WSI in "${WSI_FILES[@]}"; do
    echo "========================================"
    echo "Processing: $WSI.svs"
    echo "========================================"
    
    # 예측 실행
    echo "[Step 1] Running prediction..."
    docker run --rm \
      -v "$(pwd)/data:/data" \
      -v "$(pwd)/results:/results" \
      -v "$(pwd)/myscripts:/workspace" \
      ghcr.io/tissueimageanalytics/tiatoolbox:1.6.0-py3.11-ubuntu \
      python3 /workspace/patch_prediction.py "$WSI"
    
    # 시각화 실행
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
```

**실행**:
```bash
chmod +x process_all_wsi.sh
./process_all_wsi.sh
```

**소요 시간**: 약 10-15분 (3개 파일, M1 Mac CPU 기준)

---

### 5. 시각화 스크립트

#### a. visualize_wsi_prediction.py 구조

**주요 기능**:
1. JSON에서 예측 결과 로드
2. 클래스 분포 막대 그래프
3. WSI 썸네일 생성
4. 예측 맵 생성 (merge_predictions)
5. 오버레이 시각화
6. 범례 생성

**핵심 코드**:
```python
from tiatoolbox.wsicore.wsireader import WSIReader
from tiatoolbox.models.engine.patch_predictor import PatchPredictor
from tiatoolbox.utils.visualization import overlay_prediction_mask

# 1. 예측 결과 로드
with open(predictions_json, 'r') as f:
    result = json.load(f)
predictions = result['predictions']
coordinates = result['coordinates']

# 2. 클래스 분포 분석
from collections import Counter
class_counts = Counter(predictions)

# 3. WSI 썸네일
reader = WSIReader.open(wsi_path)
wsi_thumbnail = reader.slide_thumbnail(resolution=4, units="mpp")

# 4. 예측 맵 병합
predictor = PatchPredictor(pretrained_model="resnet18-kather100k")
pred_map = predictor.merge_predictions(
    wsi_path,
    wsi_output_dict,
    resolution=4,
    units="mpp"
)

# 5. 오버레이
overlay = overlay_prediction_mask(
    wsi_thumbnail,
    pred_map,
    alpha=0.5,
    label_info=label_color_dict
)
```

#### b. 범례 다국어 지원

**요구사항**: 영어 + 한국어 또는 전체 영어 이름

**최종 구현**:
```python
CLASS_NAMES = {
    0: "BACK",
    1: "NORM",
    ...
}

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

# 범례 생성
for class_id in sorted(class_counts.keys()):
    label = f"{CLASS_NAMES[class_id]}: {CLASS_NAMES_FULL[class_id]} ({count} patches)"
    legend_patches.append(mpatches.Patch(color=color, label=label))
```

---

### 6. 대량 경고 메시지

#### a. 경고 내용

```
Read: Scale > 1. This means that the desired resolution is higher 
than the WSI baseline (maximum encoded resolution). 
Interpolation of read regions may occur.
```

**발생 빈도**: 수백~수천 번 반복

#### b. 의미

- 요청한 해상도(0.5 mpp) > WSI 최대 해상도
- TIAToolbox가 이미지를 **보간(확대)** 처리
- 결과는 정상, 품질 약간 저하 가능

#### c. 해결 옵션

**옵션 1**: 해상도 낮추기
```python
input_resolutions=[{"units": "mpp", "resolution": 1.0}]  # 0.5 → 1.0
```

**옵션 2**: 경고 억제
```python
import warnings
warnings.filterwarnings("ignore", message="Read: Scale > 1")
```

**옵션 3**: 무시
- 결과에 큰 영향 없음
- 로그가 길어지는 것만 감수

**선택**: 옵션 3 (무시)

---

TEST_sample1 정보를 반영해서 레포트의 **"최종 결과물"** 섹션을 수정하겠습니다. 전체 레포트에서 해당 부분만 업데이트합니다.

---

## 최종 결과물

### 1. 정량적 결과

| 항목 | 값 |
|------|-----|
| 처리한 WSI 파일 | 3개 |
| 총 추출 패치 수 | 2061개 (82 + 327 + 1652) |
| 생성된 시각화 이미지 | 12개 (3×4) |
| 생성된 JSON 파일 | 3개 |
| 총 처리 시간 | 약 10-15분 |
| Docker 이미지 크기 | 5.6GB |

**WSI별 패치 수**:
- CMU-1-Small-Region: 82개
- TEST_sample1: 327개
- TEST_sample2: 1652개

### 2. WSI별 예측 결과

#### a. CMU-1-Small-Region (82 패치)

| 클래스 | 약어 | 패치 수 | 비율 |
|--------|------|---------|------|
| 0 | BACK | 18 | 22.0% |
| 1 | NORM | 2 | 2.4% |
| 2 | DEB | 0 | 0% |
| 3 | TUM | 6 | 7.3% |
| 4 | ADI | 4 | 4.9% |
| 5 | MUC | 15 | 18.3% |
| 6 | MUS | 0 | 0% |
| 7 | STR | 30 | 36.6% |
| 8 | LYM | 7 | 8.5% |

**주요 특징**: 기질(STR) 36.6%, 배경 22.0%로 주로 기질 조직으로 분류됨

#### b. TEST_sample1 (327 패치)

| 클래스 | 약어 | 패치 수 | 비율 |
|--------|------|---------|------|
| 0 | BACK | 15 | 4.6% |
| 1 | NORM | 72 | 22.0% |
| 2 | DEB | 37 | 11.3% |
| 3 | TUM | 5 | 1.5% |
| 4 | ADI | 5 | 1.5% |
| 5 | MUC | 3 | 0.9% |
| 6 | MUS | 91 | 27.8% |
| 7 | STR | 76 | 23.2% |
| 8 | LYM | 23 | 7.0% |

**주요 특징**: 평활근(MUS) 27.8%, 기질(STR) 23.2%, 정상(NORM) 22.0%로 비교적 고르게 분포

#### c. TEST_sample2 (1652 패치)

| 클래스 | 약어 | 패치 수 | 비율 |
|--------|------|---------|------|
| 0 | BACK | 84 | 5.1% |
| 1 | NORM | 456 | 27.6% |
| 2 | DEB | 73 | 4.4% |
| 3 | TUM | 161 | 9.7% |
| 4 | ADI | 37 | 2.2% |
| 5 | MUC | 11 | 0.7% |
| 6 | MUS | 718 | 43.5% |
| 7 | STR | 68 | 4.1% |
| 8 | LYM | 44 | 2.7% |

**주요 특징**: 평활근(MUS) 43.5%로 압도적 우세

### 3. 3개 WSI 비교 분석

#### a. 클래스 분포 비교

| 클래스 | CMU | TEST1 | TEST2 | 평균 |
|--------|-----|-------|-------|------|
| BACK | 22.0% | 4.6% | 5.1% | 10.6% |
| NORM | 2.4% | 22.0% | 27.6% | 17.3% |
| DEB | 0% | 11.3% | 4.4% | 5.2% |
| TUM | 7.3% | 1.5% | 9.7% | 6.2% |
| ADI | 4.9% | 1.5% | 2.2% | 2.9% |
| MUC | 18.3% | 0.9% | 0.7% | 6.6% |
| MUS | 0% | 27.8% | 43.5% | 23.8% |
| STR | 36.6% | 23.2% | 4.1% | 21.3% |
| LYM | 8.5% | 7.0% | 2.7% | 6.1% |

#### b. 패턴 분석

**CMU-1-Small-Region**:
- 기질(STR) 중심
- 점액(MUC) 높음 (18.3%)
- 평활근(MUS) 없음

**TEST_sample1**:
- 평활근(MUS), 기질(STR), 정상(NORM) 균형
- 중간 크기 (327 패치)
- 가장 고른 분포

**TEST_sample2**:
- 평활근(MUS) 압도적
- 가장 큰 이미지 (1652 패치)
- 정상(NORM) 조직도 27.6%

#### c. 가설적 해석 (주의: 대장암 모델 사용의 한계)

**평활근(MUS) 높은 비율**:
- TEST1: 27.8%
- TEST2: 43.5%
- 실제 평활근 조직일 가능성
- 또는 다른 조직이 평활근으로 오분류

**CMU vs TEST 차이**:
- CMU: 기질 중심, 작은 크기
- TEST: 평활근 중심, 큰 크기
- 서로 다른 출처의 조직으로 추정

**중요**: 이 해석은 대장암 모델을 사용한 결과이므로, 실제 조직 타입과 다를 수 있음

### 4. 결과 해석의 한계

**반복 강조**:
- resnet18-kather100k는 **대장암 전용** 모델
- 3개 샘플의 실제 조직 타입은 **알 수 없음**
- 예측 결과는 "대장암 9개 클래스에 억지로 매핑"한 것
- **의학적 진단으로 사용 불가**

**학습 의의**:
- ✓ Docker 환경에서 모델 실행 성공
- ✓ 배치 처리 파이프라인 구축 (3개 파일 자동 처리)
- ✓ 총 2061개 패치 분석
- ✓ 시각화 자동화
- ✗ 실제 조직 타입 판별 (불가능)

---

## 핵심 학습 내용

### 1. 사전훈련 모델의 이해

#### a. Transfer Learning의 한계

**원리**:
```
대장암 100K 이미지로 학습된 모델
    ↓
입력: 어떤 조직 이미지든
    ↓
출력: 대장암 9개 클래스 중 하나
```

**문제**:
- 모델은 입력이 대장암인지 아닌지 **판단하지 않음**
- 간 조직, 폐 조직을 넣어도 대장암 클래스로 분류
- 결과의 의학적 의미는 **제한적**

#### b. 모델-데이터 적합성

**올바른 워크플로우**:
1. 데이터의 실제 조직 타입 확인
2. 해당 조직에 맞는 모델 선택 (또는 직접 학습)
3. 예측 실행
4. 병리학자 검증

**우리가 한 것**:
1. 데이터 타입 미확인
2. 대장암 모델 무작정 적용
3. 예측 실행
4. 결과 의미 불명

**학습 목적으로는 충분**:
- 기술적 실행 방법 습득
- 파이프라인 구축 경험

### 2. Batch 처리의 개념

#### a. Batch = 일괄 처리

**정의**: 여러 항목을 묶음으로 한 번에 처리

**예시**:
- 개별: WSI 파일을 하나씩 수동 처리
- Batch: 여러 WSI 파일을 자동으로 순회하며 처리

#### b. 자동화 방법 비교

| 측면 | Shell Script | Python Batch |
|------|--------------|--------------|
| 구현 복잡도 | 낮음 | 중간 |
| 에러 처리 | 기본적 | 체계적 |
| 복잡한 로직 | 제한적 | 가능 |
| 플랫폼 | macOS/Linux | 모든 OS |
| 재사용성 | 중간 | 높음 |

**선택 기준**:
- 파일 3개, 단순 반복 → Shell Script
- 파일 100개, 복잡한 조건 → Python Batch

#### c. 우리의 Shell Script

**장점**:
- 간단한 반복문으로 해결
- Docker 명령어 직접 실행
- 디버깅 용이

**한계**:
- 복잡한 조건 분기 어려움
- 에러 발생 시 재시도 로직 구현 번거로움

### 3. Docker 환경의 가치

#### a. 3주차와의 연계

**3주차**: Docker 환경 구축 및 이해
**4주차**: Docker 환경에서 실전 작업

**이점**:
- 모델 다운로드, 의존성 모두 포함
- 다른 컴퓨터에서도 동일하게 작동
- 재현성 완벽 보장

#### b. Volume Mount 활용

```bash
-v "$(pwd)/data:/data"           # WSI 파일
-v "$(pwd)/results:/results"     # 결과 저장
-v "$(pwd)/myscripts:/workspace" # 스크립트
```

**효과**:
- Container 내부에서 로컬 파일 접근
- 결과가 로컬에 자동 저장
- 코드 수정이 즉시 반영

### 4. TIAToolbox API

#### a. IOPatchPredictorConfig

**목적**: 패치 추출 및 예측 설정

```python
wsi_ioconfig = IOPatchPredictorConfig(
    input_resolutions=[{"units": "mpp", "resolution": 0.5}],
    patch_input_shape=[224, 224],
    stride_shape=[224, 224],
)
```

**파라미터**:
- `input_resolutions`: 읽을 해상도
- `patch_input_shape`: 패치 크기
- `stride_shape`: 패치 간격 (겹침 제어)

#### b. PatchPredictor

**메서드**:
- `predict()`: 패치 예측 실행
- `merge_predictions()`: 예측 맵 생성

**predict() 주요 파라미터**:
```python
predictor.predict(
    imgs=[Path(wsi_path)],     # Path 객체 필수
    mode="wsi",                # tile, patch, wsi
    ioconfig=wsi_ioconfig,     # 또는 resolution, units
    save_dir=save_dir,         # 결과 저장 위치
    device="cpu",              # cuda 또는 cpu
)
```

#### c. overlay_prediction_mask

**목적**: 예측 맵을 원본 이미지에 오버레이

```python
from tiatoolbox.utils.visualization import overlay_prediction_mask

overlay = overlay_prediction_mask(
    wsi_thumbnail,      # 원본 썸네일
    pred_map,           # 예측 맵
    alpha=0.5,          # 투명도
    label_info=label_color_dict  # 클래스별 색상
)
```

---

## 어려웠던 점과 해결 과정

### 1. API 변경 대응

**어려움**:
- TIAToolbox 버전 업데이트로 API 변경
- 공식 노트북 예제가 구버전 기준
- `on_gpu` 파라미터가 `device`로 변경됨

**해결 과정**:
1. 에러 메시지 분석
   ```
   TypeError: ... unexpected keyword argument 'on_gpu'
   ```
2. TIAToolbox GitHub Issues 검색
3. 최신 문서 확인
4. `device` 파라미터로 수정

**학습**:
- 라이브러리는 계속 업데이트됨
- 에러 메시지가 가장 정확한 정보
- 공식 문서 > 예제 코드

### 2. 파일별 폴더 분리

**어려움**:
- 두 번째 파일부터 `FileExistsError` 발생
- TIAToolbox 내부에서 `exist_ok=False`로 폴더 생성
- 코드에서 미리 폴더를 만들면 충돌

**해결 과정**:
1. 에러 분석: `save_dir` 폴더가 이미 존재
2. 첫 시도: 코드에서 `mkdir()` 제거 → 실패
3. 두 번째 시도: 파일별 하위 폴더 생성 → 성공
   ```python
   save_dir = Path(f"/results/wsi_predictions/{wsi_filename}")
   ```

**학습**:
- 라이브러리 내부 동작 이해 중요
- 폴더 구조 설계로 충돌 회피
- 각 파일의 결과를 독립적으로 관리

### 3. Shell Script의 sed 실패

**어려움**:
- Shell Script에서 `sed`로 Python 파일 수정 시도
- 파일명이 제대로 변경되지 않음
- TEST_sample1 처리 중인데 CMU 파일이 처리됨

**해결**:
- `sed` 포기
- 명령줄 인자 방식으로 전환
- Python 스크립트에 `sys.argv` 추가

**학습**:
- 텍스트 치환보다 명령줄 인자가 안정적
- Shell Script의 한계 인식
- Python의 유연성

### 4. 대량 경고 메시지

**어려움**:
- "Scale > 1" 경고가 수백 번 반복
- 로그가 너무 길어져서 중요한 정보 놓칠 우려

**해결**:
- 경고의 의미 파악: 해상도 보간 발생
- 결과에 영향 없음 확인
- 무시하기로 결정

**대안**:
- 해상도 낮추기: 0.5 → 1.0 mpp
- 경고 억제: `warnings.filterwarnings()`

**학습**:
- 모든 경고를 해결할 필요는 없음
- 경고의 의미를 이해하고 판단
- 결과 품질과 편의성 트레이드오프

---

## 결론 및 향후 계획

### 1. 4주차 성과

#### a. 기술적 성과

- ✓ Docker 환경에서 사전훈련 모델 성공적 실행
- ✓ 3개 WSI 파일 배치 처리 자동화
- ✓ 총 1816개 패치 분석 (82 + 미확인 + 1652)
- ✓ 12개 시각화 이미지 생성
- ✓ Shell Script로 반복 작업 자동화
- ✓ 명령줄 인자 방식으로 코드 재사용성 향상

#### b. 학습적 성과

- 사전훈련 모델의 작동 원리 이해
- 모델-데이터 적합성의 중요성 인식
- Batch 처리 개념 학습
- Shell vs Python 자동화 비교
- TIAToolbox API 심화 학습
- 대량 경고 메시지 대응 방법

#### c. 1-2-3-4주차 통합 성과

| 주차 | 핵심 주제 | 주요 도구 | 학습 결과 |
|------|----------|----------|----------|
| 1주차 | 로컬 환경 구축 | UV, OpenSlide | 패치 추출 파이프라인 |
| 2주차 | 고급 기능 | TIAToolbox | 해상도, Tissue Masking |
| 3주차 | 재현성 | Docker | 컨테이너 환경 구축 |
| 4주차 | 실전 적용 | 사전훈련 모델 | 배치 처리, 시각화 |

### 2. 모델의 한계 재인식

**실습 결과의 의미**:
- ✓ 기술적 실행 방법 습득: 성공
- ✓ 파이프라인 구축 경험: 성공
- ✗ 의학적 진단 결과: 무의미

**이유**:
- CMU, TEST 샘플의 실제 조직 타입 미확인
- 대장암 전용 모델을 무작정 적용
- 모델은 어떤 입력이든 대장암 클래스로 분류

**교훈**:
- AI 모델은 만능이 아님
- 데이터-모델 적합성 검증 필수
- 병리학자의 검증이 반드시 필요

### 3. 추가 개선 방향

#### a. 코드 리팩토링

**모듈화**:
```python
# 공통 함수 분리
from wsi_utils import load_predictions, save_visualization

# 설정 파일 분리
import yaml
config = yaml.load('config.yaml')
```

**에러 처리 강화**:
```python
try:
    process_wsi(filename)
except FileNotFoundError:
    log_error("File not found", filename)
except OutOfMemoryError:
    # 해상도 낮춰서 재시도
    process_wsi(filename, resolution=2.0)
```

#### b. 성능 최적화

**GPU 사용** (가능한 환경):
```bash
docker run --gpus all ...
device = "cuda"
```

**멀티프로세싱**:
```python
from multiprocessing import Pool
with Pool(4) as p:
    results = p.map(process_wsi, wsi_list)
```

#### c. 분석 확장

**비교 분석**:
- 3개 WSI의 클래스 분포를 하나의 그래프로
- WSI별 특징 요약

**통계적 분석**:
- 클래스 간 상관관계
- 조직 타입별 공간 분포

### 4. 실전 적용을 위한 다음 단계

#### a. 데이터 검증

- WSI 출처 확인
- 실제 조직 타입 파악
- 병리학자 협업

#### b. 모델 선택

- 조직 타입에 맞는 모델 찾기
- 또는 자체 데이터로 모델 학습
- Transfer Learning 적용

#### c. 검증 파이프라인

- Ground Truth 라벨 확보
- 정확도, F1-score 계산
- Confusion Matrix 생성
- 병리학자 검토

### 5. 장기 목표

#### a. 연구 재현성

- 모든 분석을 Docker로 표준화
- GitHub에 코드 + Dockerfile 공유
- 논문 Methods 섹션에 포함

#### b. 실전 배포

- 병원/연구소 서버에 Docker 배포
- REST API 서버 구축
- 웹 인터페이스 개발

#### c. 지속적 학습

- 최신 논문의 모델 재현
- 다양한 조직 타입 학습
- Multi-task Learning 탐색

---

## 참고 자료

### 1. 공식 문서

- **TIAToolbox**: https://tia-toolbox.readthedocs.io
- **TIAToolbox API**: https://tia-toolbox.readthedocs.io/en/latest/api.html
- **Docker**: https://docs.docker.com
- **PyTorch**: https://pytorch.org/docs/

### 2. GitHub 저장소

- **TIAToolbox**: https://github.com/TissueImageAnalytics/tiatoolbox
- **TIAToolbox Examples**: https://github.com/TissueImageAnalytics/tiatoolbox/tree/develop/examples

### 3. 논문

- **Kather et al. (2019)**: "Predicting survival from colorectal cancer histology slides using deep learning"
- **100K Dataset**: https://zenodo.org/record/1214456

### 4. 예제 노트북

- **05-patch-prediction.ipynb**: 공식 패치 예측 예제
- **Colab**: https://colab.research.google.com

### 5. 트러블슈팅

- **TIAToolbox GitHub Issues**: https://github.com/TissueImageAnalytics/tiatoolbox/issues
- **Stack Overflow**: `[tiatoolbox]` 태그

---

## 부록

### A. 최종 명령어 모음

```bash
# 1. Docker 이미지 다운로드 (최초 1회)
docker pull ghcr.io/tissueimageanalytics/tiatoolbox:1.6.0-py3.11-ubuntu

# 2. Shell Script 실행 (배치 처리)
cd ~/Desktop/tiatoolbox
chmod +x process_all_wsi.sh
./process_all_wsi.sh

# 3. 개별 WSI 처리 (수동)
docker run --rm \
  -v "$(pwd)/data:/data" \
  -v "$(pwd)/results:/results" \
  -v "$(pwd)/myscripts:/workspace" \
  ghcr.io/tissueimageanalytics/tiatoolbox:1.6.0-py3.11-ubuntu \
  python3 /workspace/patch_prediction.py TEST_sample1

# 4. 시각화 실행
docker run --rm \
  -v "$(pwd)/data:/data" \
  -v "$(pwd)/results:/results" \
  -v "$(pwd)/myscripts:/workspace" \
  ghcr.io/tissueimageanalytics/tiatoolbox:1.6.0-py3.11-ubuntu \
  python3 /workspace/visualize_wsi_prediction.py TEST_sample1

# 5. 결과 확인
ls -lh results/visualizations/*/
open results/visualizations/TEST_sample1/*.png
```

### B. 폴더 구조 (최종)

```
tiatoolbox/
├── data/
│   ├── CMU-1-Small-Region.svs
│   ├── TEST_sample1.svs
│   └── TEST_sample2.svs
├── myscripts/
│   ├── patch_prediction.py
│   └── visualize_wsi_prediction.py
├── results/
│   ├── wsi_predictions/
│   │   ├── CMU-1-Small-Region/
│   │   │   └── predictions.json
│   │   ├── TEST_sample1/
│   │   │   └── predictions.json
│   │   └── TEST_sample2/
│   │       └── predictions.json
│   └── visualizations/
│       ├── CMU-1-Small-Region/
│       │   └── (4개 이미지)
│       ├── TEST_sample1/
│       │   └── (4개 이미지)
│       └── TEST_sample2/
│           └── (4개 이미지)
├── process_all_wsi.sh
└── docker/
    └── 3.11/Ubuntu/
        └── Dockerfile
```

### C. 주요 개념 정리

**사전훈련 모델 (Pre-trained Model)**:
- 대규모 데이터셋으로 이미 학습된 모델
- 새로운 데이터에 즉시 적용 가능
- Transfer Learning의 기반

**Batch 처리 (Batch Processing)**:
- 여러 항목을 묶음으로 자동 처리
- 반복 작업의 효율화
- Shell Script 또는 Python으로 구현

**명령줄 인자 (Command-line Arguments)**:
- 스크립트 실행 시 외부에서 값 전달
- `sys.argv`로 접근
- 코드 재사용성 향상

**Volume Mount**:
- Docker Container ↔ Host 간 폴더 연결
- 데이터 영속성 보장
- 실시간 파일 공유

**Interpolation (보간)**:
- 해상도가 부족할 때 픽셀 값 추정
- 이미지 확대 시 발생
- 품질 약간 저하 가능

### D. 체크리스트

**환경 설정**:
- [ ] Docker Desktop 실행 중
- [ ] WSI 파일 `data/` 폴더에 존재
- [ ] Docker 이미지 다운로드 완료

**스크립트 준비**:
- [ ] `patch_prediction.py` 명령줄 인자 구현
- [ ] `visualize_wsi_prediction.py` 명령줄 인자 구현
- [ ] `process_all_wsi.sh` 실행 권한 부여

**실행 전 확인**:
- [ ] 파일별 하위 폴더 방식 구현
- [ ] Volume Mount 경로 확인
- [ ] 충분한 디스크 공간 (최소 10GB)

**결과 검증**:
- [ ] 각 WSI별 4개 이미지 생성
- [ ] predictions.json 파일 생성
- [ ] 클래스 분포 그래프 확인
- [ ] 오버레이 이미지 시각적 검증

---

## 마치며

### 핵심 메시지

**"기술적 실행 능력과 결과 해석 능력은 별개다."**

4주차 실습을 통해:
- ✓ Docker 환경에서 AI 모델을 실행하는 **기술**을 습득했습니다
- ✓ 배치 처리 파이프라인을 구축하는 **방법**을 배웠습니다
- ✓ 하지만 모델-데이터 적합성의 **중요성**도 깨달았습니다

### 실습의 진정한 가치

이 실습은:
- "대장암을 진단하는 법"이 아니라
- "AI 모델을 실행하는 법"을 배우는 것입니다
- 결과의 의학적 의미는 제한적이지만
- 기술적 파이프라인은 다른 프로젝트에 재사용 가능합니다

### 다음을 위한 준비

실전 적용을 위해서는:
1. 데이터의 실제 조직 타입 확인
2. 적합한 모델 선택 또는 직접 학습
3. 병리학자와 협업
4. 철저한 검증

### 1-4주차 통합 여정

- **1주차**: 로컬 환경에서 첫 걸음
- **2주차**: TIAToolbox로 고급 기능 탐색
- **3주차**: Docker로 재현 가능한 환경 구축
- **4주차**: 실전 모델로 파이프라인 완성

이제 여러분은:
- WSI 병리 이미지를 처리할 수 있습니다
- Docker로 재현 가능한 환경을 만들 수 있습니다
- 사전훈련 모델을 활용할 수 있습니다
- 배치 처리로 대량의 데이터를 다룰 수 있습니다

**그리고 가장 중요하게는:**
AI 모델의 한계를 이해하고, 결과를 비판적으로 해석할 수 있습니다.