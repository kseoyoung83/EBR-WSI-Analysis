# EBR WSI Analysis

의과대학 의예과 "Evolution of Biomedical Research" 실습 프로젝트

전체슬라이드이미지(Whole Slide Image) 분석을 위한 파이프라인 구축 및 AI 모델 활용

## 주차별 학습 내용

### Week 1: OpenSlide 기초
- 로컬 환경 구축 (UV + OpenSlide)
- 그리드 패치 추출 파이프라인
- 배경 자동 제거 (Tissue Masking)
- **결과**: 88개 패치 중 39개 조직 패치 추출

[코드](week1-openslide/) | [상세 레포트](reports/week1_report.md)

### Week 2: TIAToolbox 고급 기능
- 해상도 및 단위 개념 (power, mpp, level)
- Morphological Tissue Masking
- WSI 썸네일 및 다중 해상도 비교
- **결과**: 조직 비율 43.06% 자동 계산

[코드](week2-tiatoolbox-basics/) | [상세 레포트](reports/week2_report.md)

### Week 3: Docker 환경 구축
- 재현 가능한 컨테이너 환경
- Volume Mount를 통한 데이터 연결
- 썸네일 자동 생성 스크립트
- **결과**: 5.6GB Docker 이미지 구축 성공

[코드](week3-docker/) | [Dockerfile](docker/3.11/Ubuntu/Dockerfile) | [상세 레포트](reports/week3_report.md)

### Week 4: AI 모델 추론
- 사전훈련 모델 (resnet18-kather100k)
- 3개 WSI 배치 처리 (총 2061 패치)
- 예측 결과 시각화 및 분석
- **결과**: 조직 타입별 분포 자동 분류

[코드](week4-model-inference/) | [상세 레포트](reports/week4_report.md)

### Week 5: Stain Normalization
- 3가지 정규화 알고리즘 비교 (Macenko, Vahadane, Reinhard)
- WSI 간 색상 편차 보정
- Before/After 시각화 (2×3 grid)
- **결과**: 일관된 H&E 염색 색상으로 표준화

[코드](week5-stain-normalization/) | [상세 레포트](reports/week5_report.md)

### Week 6: Feature Extraction & Spatial Analysis
- WSI 패치에서 feature 추출 (9차원 확률 벡터)
- 공간적 조직 분포 분석 및 시각화
- 예측 불확실성(Entropy) 정량화
- 종양 영역 자동 탐지
- **결과**: 3개 WSI, 2061개 패치 분석 완료

[코드](week6-slide-graph/) | [상세 레포트](reports/week6_report.md)

## 환경 요구사항

- Python 3.11+
- Docker Desktop
- macOS / Linux (Windows WSL2)
- 주요 라이브러리: OpenSlide, TIAToolbox, PyTorch

## 빠른 시작

### Week 1-2 (로컬 환경)
```bash
cd week1-openslide
uv venv --python 3.11
source .venv/bin/activate
uv add openslide-python pillow numpy opencv-python

export DYLD_LIBRARY_PATH=/opt/homebrew/opt/openslide/lib:$DYLD_LIBRARY_PATH
python src/main.py
```

### Week 3-5 (Docker 환경)
```bash
cd week4-model-inference
docker pull ghcr.io/tissueimageanalytics/tiatoolbox:1.6.0-py3.11-ubuntu
./process_all_wsi.sh
```
<artifact identifier="readme-bottom-section" type="text/markdown" title="README.md 하단 섹션 (주요 결과~끝)">

<artifact identifier="readme-bottom-section" type="text/markdown" title="README.md 하단 섹션 (주요 결과~끝)">
## 주요 결과

| 주차 | 처리 WSI | 생성 패치/이미지 | 주요 성과 |
|------|---------|-----------------|----------|
| Week 1 | 1개 | 39개 조직 패치 | 배경 제거 파이프라인 |
| Week 2 | 1개 | 9개 시각화 | 다중 해상도 분석 |
| Week 3 | 1개 | 5개 썸네일 | Docker 환경 구축 |
| Week 4 | 3개 | 2061 패치 분석 | AI 모델 배치 처리 |
| Week 5 | 3개 | 8개 정규화 이미지 | 색상 표준화 (3가지 방법) |
| Week 6 | 3개 | 2061 패치, 15개 시각화 | Feature extraction & 공간 분석 |

## 프로젝트 구조

```
EBR-WSI-Analysis/
├── week1-openslide/
├── week2-tiatoolbox-basics/
├── week3-docker/
├── week4-model-inference/
├── week5-stain-normalization/
├── docker/
└── reports/
```

## 참고 자료

- TIAToolbox: https://github.com/TissueImageAnalytics/tiatoolbox
- OpenSlide: https://openslide.org
- Sample Data: https://tiatoolbox.dcs.warwick.ac.uk/sample_wsis/

## 데이터 파일

WSI 파일(.svs)은 용량이 커서 저장소에 포함되지 않습니다:

```bash
curl -L -o data/CMU-1-Small-Region.svs \
  "https://tiatoolbox.dcs.warwick.ac.uk/sample_wsis/CMU-1-Small-Region.svs"
```

## 저자

김서영 (2024191115) - 의과대학 의예과

## 라이선스

MIT License
</artifact>
