
# EBR WSI Analysis

의과대학 의예과 "Evolution of Biomedical Research" 실습 프로젝트

전체슬라이드이미지(Whole Slide Image) 분석을 위한 파이프라인 구축 및 AI 모델 활용

---

## 📋 프로젝트 개요

**기간**: 7주차 실습 (Week 1-7)

**목표**: 
- WSI 패치 추출 및 AI 기반 조직 분류
- 색상 표준화 및 Feature 추출
- **Slide Graph 구축 및 침윤성 정량화**

**핵심 성과**:
- ✅ 재현 가능한 Docker 파이프라인 구축
- ✅ 3개 WSI, 2,061개 패치 자동 분류
- ✅ **그래프 구조로 조직 관계 명시**
- ✅ **침윤성 암의 정량적 평가 지표 개발**

---

## 주차별 학습 내용

### Week 1: OpenSlide 기초
- 로컬 환경 구축 (UV + OpenSlide)
- 그리드 패치 추출 파이프라인
- 배경 자동 제거 (Tissue Masking)
- **결과**: 88개 패치 중 39개 조직 패치 추출

[코드](week1-openslide/) | [상세 레포트](reports/week1_report.md)

---

### Week 2: TIAToolbox 고급 기능
- 해상도 및 단위 개념 (power, mpp, level)
- Morphological Tissue Masking
- WSI 썸네일 및 다중 해상도 비교
- **결과**: 조직 비율 43.06% 자동 계산

[코드](week2-tiatoolbox-basics/) | [상세 레포트](reports/week2_report.md)

---

### Week 3: Docker 환경 구축
- 재현 가능한 컨테이너 환경
- Volume Mount를 통한 데이터 연결
- 썸네일 자동 생성 스크립트
- **결과**: 5.6GB Docker 이미지 구축 성공

[코드](week3-docker/) | [Dockerfile](docker/3.11/Ubuntu/Dockerfile) | [상세 레포트](reports/week3_report.md)

---

### Week 4: AI 모델 추론
- 사전훈련 모델 (resnet18-kather100k)
- 3개 WSI 배치 처리 (총 2061 패치)
- 예측 결과 시각화 및 분석
- **결과**: 조직 타입별 분포 자동 분류

[코드](week4-model-inference/) | [상세 레포트](reports/week4_report.md)

---

### Week 5: Stain Normalization
- 3가지 정규화 알고리즘 비교 (Macenko, Vahadane, Reinhard)
- WSI 간 색상 편차 보정
- Before/After 시각화 (2×3 grid)
- **결과**: 일관된 H&E 염색 색상으로 표준화

[코드](week5-stain-normalization/) | [상세 레포트](reports/week5_report.md)

---

### Week 6: Feature Extraction & Spatial Analysis
- WSI 패치에서 feature 추출 (9차원 확률 벡터)
- 공간적 조직 분포 분석 및 시각화
- 예측 불확실성(Entropy) 정량화
- 종양 영역 자동 탐지
- **결과**: 3개 WSI, 2061개 패치 분석 완료

[코드](week6-slide-graph/) | [상세 레포트](reports/week6_report.md)

---

### Week 7: Slide Graph & Infiltration Analysis 🎯

**목표**: 패치 간 관계를 명시적으로 표현하고 침윤 패턴 정량화

**구현 내용**:
- **k-NN Graph 구축** (k=8, NetworkX)
  - 노드: 패치 (좌표, feature, 예측 클래스)
  - 엣지: 공간적 인접성 (Euclidean distance)

- **4단계 그래프 분석**:
  1. **Boundary Detection**: 조직 간 경계 탐지
  2. **Community Detection**: Louvain 알고리즘으로 군집 분석
  3. **Centrality Analysis**: 구조적 중요 노드 식별
  4. **Infiltration Score**: 정량적 침윤성 지표 개발

**핵심 발견** (CMU-1-Small-Region):
- 경계 엣지 **63.0%** → 높은 침윤성
- Community Purity **0.48** → 조직 혼재
- 경계 노드 **100%** → 순수 영역 없음
- 종양 노드가 **구조적 허브** (betweenness centrality)

**결과**:
```python
침윤성 점수 = 3.19 (Highly infiltrative)
→ 예후: Poor
→ 권고: 광범위 절제, 보조 항암치료
```

**의의**:
- ✅ 주관적 "침윤성으로 보임" → 객관적 수치화
- ✅ 경계 패턴, 조직 구조, 중심성 통합 평가
- ✅ GNN(Graph Neural Network) 학습 준비 완료

[코드](week7-slide-graph/) | [상세 레포트](reports/week7_report.md)

**시각화 예시**:
- 그래프 구조 (노드-엣지)
- 경계 엣지 강조 (빨간선)
- 커뮤니티 vs 실제 조직
- 중심성 맵 (degree, betweenness)

---

## 주요 결과

| 주차 | 처리 WSI | 생성 패치/이미지 | 주요 성과 |
|------|---------|-----------------|----------|
| Week 1 | 1개 | 39개 조직 패치 | 배경 제거 파이프라인 |
| Week 2 | 1개 | 9개 시각화 | 다중 해상도 분석 |
| Week 3 | 1개 | 5개 썸네일 | Docker 환경 구축 |
| Week 4 | 3개 | 2061 패치 분석 | AI 모델 배치 처리 |
| Week 5 | 3개 | 8개 정규화 이미지 | 색상 표준화 (3가지 방법) |
| Week 6 | 3개 | 2061 패치, 15개 시각화 | Feature extraction & 공간 분석 |
| **Week 7** | **3개** | **2061 노드, 39개 결과 파일** | **Slide Graph & 침윤성 정량화** |

---

## 침윤성 평가 결과 (Week 7)

| WSI | 경계 엣지 | Purity | 경계 노드 | 침윤성 점수 | 평가 |
|-----|----------|--------|----------|------------|------|
| **CMU-1** | 63.0% | 0.480 | 100% | **3.19** | Highly infiltrative ⚠️ |
| TEST_sample1 | 54.7% | 0.478 | 97.9% | **2.85** | Moderately infiltrative |
| TEST_sample2 | 41.5% | 0.506 | 86.7% | **2.54** | Relatively cohesive ✓ |

**침윤성 점수 해석**:
- **> 3.0**: 고위험, 광범위 절제 필요
- **2.0-3.0**: 중위험, 표준 치료
- **< 2.0**: 저위험, 경과 관찰

---

## 환경 요구사항

- Python 3.11+
- Docker Desktop
- macOS / Linux (Windows WSL2)
- 주요 라이브러리: OpenSlide, TIAToolbox, PyTorch, **NetworkX**

---

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

### Week 3-6 (Docker 환경)
```bash
cd week4-model-inference
docker pull ghcr.io/tissueimageanalytics/tiatoolbox:1.6.0-py3.11-ubuntu
./process_all_wsi.sh
```

### Week 7 (Slide Graph 분석)
```bash
cd week7-slide-graph

# 전체 파이프라인 실행
./process_build_graph.sh      # 1. 그래프 구축
./process_visualization.sh     # 2. 시각화
./process_boundaries.sh        # 3. 경계 탐지
./process_communities.sh       # 4. 커뮤니티 탐지
./process_centrality.sh        # 5. 중심성 분석

# 결과 확인
tree -L 2 results/
```

---

## 프로젝트 구조

```
EBR-WSI-Analysis/
├── week1-openslide/              # 기본 패치 추출
├── week2-tiatoolbox-basics/      # 고급 기능
├── week3-docker/                 # Docker 환경
├── week4-model-inference/        # AI 모델 추론
├── week5-stain-normalization/    # 색상 표준화
├── week6-slide-graph/            # Feature 추출
├── week7-slide-graph/            # 🆕 Slide Graph 분석
│   ├── myscripts/
│   │   ├── build_graph.py           # k-NN 그래프 구축
│   │   ├── visualize_graph.py       # 시각화
│   │   ├── analyze_boundaries.py    # 경계 탐지
│   │   ├── detect_communities.py    # 커뮤니티 탐지
│   │   └── compute_centrality.py    # 중심성 분석
│   ├── process_*.sh                 # 배치 실행 스크립트 (5개)
│   └── results/                     # WSI별 분석 결과
│       ├── CMU-1-Small-Region/
│       ├── TEST_sample1/
│       └── TEST_sample2/
├── docker/                       # Dockerfile
└── reports/                      # 주차별 상세 보고서
    ├── week1_report.md
    ├── week2_report.md
    ├── week3_report.md
    ├── week4_report.md
    ├── week5_report.md
    ├── week6_report.md
    └── week7_report.md           # 🆕
```

---

## 핵심 개념 정리

### Week 1-6: 패치 기반 분석
```
픽셀 → 패치 → AI 분류 → Feature 추출
```

### Week 7: 그래프 기반 분석
```
패치 + 관계 → 그래프 → 구조 분석 → 침윤성 평가
```

**CNN vs GNN**:
- **CNN** (Week 4-6): 개별 패치만 분석
- **GNN** (Week 7 준비): 패치 + 이웃 정보 활용

**주요 그래프 개념**:
- **Node**: 패치 (위치, feature, 예측 클래스)
- **Edge**: 공간적 인접성 (k-NN, k=8)
- **Boundary Edge**: 서로 다른 조직 간 연결 (침윤 전선)
- **Community**: 강하게 연결된 노드 군집
- **Centrality**: 구조적 중요도 (degree, betweenness)

---

## 향후 계획

### 단기 (코호트 연구)
- [ ] 더 많은 WSI 샘플 분석 (n > 20)
- [ ] 실제 예후 데이터와 침윤성 점수 상관관계 검증
- [ ] 다른 암종에 적용 (유방암, 폐암 등)

### 중기 (GNN 구현)
- [ ] PyTorch Geometric으로 그래프 데이터 변환
- [ ] GNN 모델 학습 (Node classification)
- [ ] 이웃 정보 활용한 패치 재분류

### 장기 (임상 적용)
- [ ] 슬라이드 수준 예후 예측 모델
- [ ] 멀티모달 분석 (WSI + 임상 정보 + 유전자)
- [ ] 진단 보조 시스템 개발

---

## 참고 자료

### 공식 문서
- **TIAToolbox**: https://github.com/TissueImageAnalytics/tiatoolbox
- **OpenSlide**: https://openslide.org
- **NetworkX**: https://networkx.org
- **PyTorch Geometric**: https://pytorch-geometric.readthedocs.io/

### 주요 논문
- Kipf & Welling (2017) - Semi-Supervised Classification with GCNs
- Litjens et al. (2016) - Deep learning in histopathology
- Lu et al. (2021) - Weakly supervised computational pathology on WSIs

### 샘플 데이터
- TIAToolbox Sample WSIs: https://tiatoolbox.dcs.warwick.ac.uk/sample_wsis/

---

## 데이터 파일

WSI 파일(.svs)은 용량이 커서 저장소에 포함되지 않습니다:

```bash
# CMU-1-Small-Region
curl -L -o data/CMU-1-Small-Region.svs \
  "https://tiatoolbox.dcs.warwick.ac.uk/sample_wsis/CMU-1-Small-Region.svs"

# TEST_sample1
curl -L -o data/TEST_sample1.svs \
  "https://tiatoolbox.dcs.warwick.ac.uk/sample_wsis/TEST_sample1.svs"

# TEST_sample2
curl -L -o data/TEST_sample2.svs \
  "https://tiatoolbox.dcs.warwick.ac.uk/sample_wsis/TEST_sample2.svs"
```

---

## 저자

김서영 (2024191115) - 의과대학 의예과

**연락처**: GitHub Issues

---

## 라이선스

MIT License

---

## Acknowledgments

- Evolution of Biomedical Research 담당 교수님
- TIAToolbox 개발팀
- OpenSlide 커뮤니티
- Claude AI (LLM 활용 학습)
```

---
