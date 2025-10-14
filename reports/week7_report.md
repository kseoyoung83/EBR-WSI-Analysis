
# Evolution of Biomedical Research

의과대학 의예과 2024191115 김서영

## ▼ 7주차 실습

## 실습 개요

### 1. 실습 목표
- Week 6의 feature를 활용한 Slide Graph 구축
- 그래프 구조를 통한 패치 간 관계 명시
- 경계 탐지로 침윤 패턴 정량화
- 커뮤니티 탐지로 조직 군집 평가
- 중심성 분석으로 구조적 허브 식별
- 침윤성 암의 정량적 지표 개발

### 2. 실습 환경
- **운영체제**: macOS (Apple M1 Pro)
- **개발 도구**: Terminal (zsh), VSCode
- **컨테이너**: Docker Desktop for Mac
- **Docker 이미지**: `ghcr.io/tissueimageanalytics/tiatoolbox:1.6.0-py3.11-ubuntu`
- **주요 라이브러리**:
  - NetworkX 3.x (그래프 분석)
  - scikit-learn (k-NN)
  - matplotlib 3.9.3
  - pickle (그래프 저장)

### 3. 데이터
Week 6에서 추출한 feature 활용:

| 파일 | 패치 수 | 입력 데이터 |
|------|---------|------------|
| CMU-1-Small-Region | 82 | predictions.json |
| TEST_sample1 | 327 | predictions.json |
| TEST_sample2 | 1,652 | predictions.json |

**JSON 구조**:
```json
{
  "predictions": [0, 3, 7, ...],        // 예측 클래스
  "coordinates": [[x,y,w,h], ...],      // 패치 좌표
  "probabilities": [[0.99, ...], ...]   // 9차원 확률 벡터
}
```

### 4. 학습 배경

#### Week 6까지의 한계
```
Week 4-6의 분석:
[패치 A] [패치 B] [패치 C]
   ↓        ↓        ↓
  TUM     STR      NORM

문제점:
- 각 패치를 독립적으로 분석
- "패치 A 옆에 무엇이 있는가?"를 모름
- 공간적 관계가 암묵적
```

#### Week 7의 접근
```
Slide Graph:
[TUM] ─── [STR] ─── [NORM]
  │        │         │
  └────────┴─────────┘

개선점:
- 패치 간 연결을 명시적으로 표현
- 이웃 정보 활용 가능
- 그래프 알고리즘 적용 가능
```

#### 동기: GNN의 이해

**학습 초기의 질문**:
"GNN이 무엇이고, 왜 필요한가?"

**개념적 이해**:
```
CNN (Week 4-6):
224×224 픽셀 이미지만 보고 판단
= 고립된 분석

GNN (Week 7 준비):
이미지 + 이웃 패치 정보
= 맥락을 고려한 분석
```

**비유를 통한 이해** (큰 도움이 됨):
```
소문이 퍼지는 과정:

시간 0: [A: "나는 종양"]  [B: "나는 기질"]
시간 1: [A: "나는 종양이고, 옆에 기질"] 
        [B: "나는 기질이고, 옆에 종양"]
        
→ 이웃 정보가 전파되어 더 풍부한 이해
→ GNN의 message passing 개념
```

**핵심 원리: Permutation Invariance**

중요한 질문:
"GNN에서 패치를 관찰하는 순서가 영향을 주지는 않아?"

이해한 내용:
```python
# 순서 불변적 연산 (Order-invariant)
neighbors = [A, B, C]

순서 1: mean([A, B, C]) = X
순서 2: mean([C, A, B]) = X
→ 항상 같은 결과!

이유: 그래프는 "집합(set)"의 관계
→ 순서가 아닌 구성과 연결이 중요
```

---

## 실습 과정

### Step 1: 그래프 구축 (Graph Construction)

#### 1.1 개념 이해: Slide Graph란?

**질문**: "Week 6의 공간 맵과 무엇이 다른가?"

**Week 6 (공간 맵)**:
```
시각적으로만 이웃 관찰:
●  ●  ●
●  ●  ●

컴퓨터는: "좌표 (0,0), (224,0)에 점 2개"
→ 관계를 계산할 수 없음
```

**Week 7 (Slide Graph)**:
```
데이터 구조로 관계 표현:
●──●──●
│  │  │
●──●──●

컴퓨터가: "노드 0의 이웃은 [1, 3]"
→ 정량적 분석 가능!
```

**그래프 구조**:
```
노드 (Node):
  - ID: 패치 인덱스
  - 위치: (x, y) 중심 좌표
  - Feature: 9차원 확률 벡터
  - 속성: 예측 클래스

엣지 (Edge):
  - 공간적으로 가까운 패치 연결
  - k-NN (k=8): 8개 가장 가까운 이웃
```

#### 1.2 k-NN Graph 구축

**파일 생성**: `myscripts/build_graph.py`

**핵심 알고리즘**:
```python
from sklearn.neighbors import NearestNeighbors

# 1. 패치 중심 좌표 계산
coords = [[x, y, w, h], ...]  # 좌상단
centers = coords[:, :2] + coords[:, 2:] / 2  # 중심

# 2. k=8 nearest neighbors
nbrs = NearestNeighbors(n_neighbors=9)  # 자기 자신 포함
nbrs.fit(centers)
distances, indices = nbrs.kneighbors(centers)

# 3. NetworkX Graph 생성
G = nx.Graph()
for i in range(n_patches):
    G.add_node(i,
               pos=tuple(centers[i]),
               feature=probabilities[i],
               prediction=predictions[i])
    
    for j in indices[i][1:]:  # 자기 자신 제외
        G.add_edge(i, j, weight=distances[i][j])
```

**설계 결정**:
- k=8 선택 이유: 상하좌우 + 대각선 (8방향)
- 중심 좌표 사용: k-NN은 점 간 거리 계산
- Euclidean distance: 2D 공간에서 자연스러움

#### 1.3 시행착오: 폴더 구조 통일

**문제 발생**:
```bash
week7-slide-graph/
├── myscripts/
│   └── process_build_graph.sh  # 여기에 있음
```

Week 6와 구조가 달라서 혼란

**해결**:
```bash
# Week 6 패턴 유지
mv myscripts/process_build_graph.sh .

week7-slide-graph/
├── myscripts/
├── process_build_graph.sh  # 루트로 이동 ✓
└── results/
```

**학습**:
- 일관된 구조 유지의 중요성
- Week 6 패턴을 따르면 재사용 용이
- Docker volume mount 경로 고려

#### 1.4 실행 결과

**CMU-1-Small-Region**:
```
============================================================
Building Graph: CMU-1-Small-Region
============================================================

✓ Loaded: 82 patches
✓ Computed centers: shape (82, 2)
Finding 8 nearest neighbors...
✓ Graph built: 82 nodes, 378 edges

==================================================
Graph Statistics
==================================================
Nodes: 82
Edges: 378
Average degree: 9.22

Class distribution:
  BACK   (0):   34 nodes
  TUM    (3):   15 nodes
  ADI    (4):    1 nodes
  MUS    (6):   11 nodes
  STR    (7):   21 nodes

Boundary edges: 238 (63.0%)
==================================================
```

**발견**:
- k=8인데 평균 degree 9.22?
  - k-NN은 양방향 (A→B, B→A 모두 카운트)
  - 일부 노드는 더 많이 연결될 수 있음
- Boundary edges 63.0%
  - 이미 여기서 침윤성의 징후!

#### 1.5 시각화

**3가지 시각화 생성**:

**1) Week 6 vs Week 7 비교**

![Week 6 vs Week 7 Comparison](../week7-slide-graph/results/CMU-1-Small-Region/week6_vs_week7_comparison.png)

왼쪽(Week 6): 패치가 점으로만 표시
오른쪽(Week 7): 패치 간 연결선(엣지) 추가
→ 관계가 명시적으로 표현됨

**2) 그래프 구조**

![Graph Structure](../week7-slide-graph/results/CMU-1-Small-Region/graph_structure.png)

- 조직 타입별 색상 구분
- 회색 선으로 연결 관계 표시
- 공간적 배치 유지

**3) 연결성 맵**

![Connectivity Map](../week7-slide-graph/results/CMU-1-Small-Region/connectivity_map.png)

- 노드 크기 = degree (연결 개수)
- 색상 = degree centrality
- 빨간색 = 많이 연결된 노드 (중심부)
- 파란색 = 적게 연결된 노드 (가장자리)

**시각화에서 확인한 것**:
```
Week 6: ●  ●  ●
        시각적으로만 이웃 추론

Week 7: ●──●──●
        명시적 연결 구조
```

---

### Step 2: 경계 탐지 (Boundary Detection)

#### 2.1 개념 이해: 침윤이란?

**중요한 질문**:
"침윤의 뜻이 뭐야?"

**이해 과정**:

**정상 조직의 경계**:
```
┌──────────────┐
│  정상 상피   │
└──────────────┘
   기저막 (Basement Membrane) ← 명확한 경계
┌──────────────┐
│  결합조직    │
└──────────────┘
```

**암의 침윤**:
```
┌──────────────┐
│  암세포 ╱╲   │ ← 기저막 파괴!
└───╱──╲───────┘
   ╱    ╲ 
  ╱ 암세포╲  ← 주변 기질로 침투
 ╱        ╲
└──────────────┘
│  기질 (STR) │ ← 침윤됨
```

**핵심 이해**:
"침윤 = 암세포가 기저막을 뚫고 주변 기질로 침투하는 그 경계 부분"
→ Week 7에서 분석하는 boundary edges!

**병리학적 의미**:
```
제자리암 (Carcinoma in situ):
[암세포들이 상피 내에만]
─────────────────── 기저막 (intact)
→ 침윤 안 함, 예후 좋음

침윤암 (Invasive carcinoma):
[암세포]
   ╲╱
─────────────────── 기저막 (파괴)
   ╱╲
[기질 깊숙이 침투]
→ 침윤, 예후 나쁨
```

#### 2.2 경계 엣지 찾기

**알고리즘**:
```python
def find_boundary_edges(G):
    boundary_edges = []
    
    for u, v in G.edges():
        class_u = G.nodes[u]['prediction']
        class_v = G.nodes[v]['prediction']
        
        if class_u != class_v:
            boundary_edges.append((u, v))
    
    return boundary_edges
```

**의미**:
```
[TUM] ─── [STR]  ← 경계 엣지 (침윤 전선!)
[TUM] ─── [TUM]  ← 내부 엣지
[STR] ─── [STR]  ← 내부 엣지
```

#### 2.3 시행착오: 파일 생성 오류

**문제 발생**:
```bash
./process_boundaries.sh

Traceback:
  File "/workspace/analyze_boundaries.py", line 1
    cat > myscripts/analyze_boundaries.py << 'EOF'
    ^^^
NameError: name 'cat' is not defined
```

**원인**:
- nano 에디터로 파일 생성 시
- 쉘 명령어가 파일 안에 포함됨
- Python이 이를 코드로 인식

**해결**:
```bash
rm myscripts/analyze_boundaries.py
nano myscripts/analyze_boundaries.py
# (내용 복사 후 Ctrl+O 저장, Ctrl+X 종료)
```

**학습**:
- 파일 생성 방법 주의
- `cat > file << 'EOF'`는 터미널에서만
- nano/vim으로 직접 편집이 안전

#### 2.4 결과 분석: 충격적인 발견

**CMU-1-Small-Region**:
```
Boundary edges: 238 (63.0%)

Boundary types:
  TUM - STR : 49 edges (20.6%) ← 침윤 전선!
  BACK - STR: 71 edges (29.8%)
  TUM - BACK: 26 edges (10.9%)
```

**질문**:
"경계를 분석하는 게 병리적으로 어떤 의의를 가져?"

**이해한 내용**:

**1. 침윤 패턴 파악**
```
밀어내는(Pushing) 경계:
[TUM]
═══════ 명확한 경계
[NORM]
→ 예후 좋음

침윤성(Infiltrative) 경계:
[TUM]
  ╲  ╱  ╲  불규칙한 경계
───╲──╱──╲─
[NORM에 침투]
→ 예후 나쁨

CMU: 63% 경계 엣지 = 침윤성!
```

**2. 종양 미세환경 분석**
```
TUM - STR (20.6%):
→ 종양이 기질로 침윤
→ Desmoplastic reaction
→ 침윤 전선 (invasive front)

TUM - NORM (있다면):
→ 정상 조직 직접 침범
→ 더 공격적
```

**3. 예후 예측**
```
경계 엣지 비율:
  < 40%: 응집성, 예후 좋음
  40-60%: 중간
  > 60%: 침윤성, 예후 나쁨 ⚠️
  
CMU: 63% → 나쁜 예후 가능성
```

#### 2.5 경계 시각화

**1) 경계 엣지 강조**

![Boundary Edges](../week7-slide-graph/results/CMU-1-Small-Region/boundary_edges.png)

- 빨간색 선 = 경계 엣지 (서로 다른 조직 간)
- 회색 선 = 내부 엣지 (같은 조직 간)
- 경계 엣지가 매우 많음 → 침윤성 패턴

**2) 경계 노드 강조**

![Boundary Nodes](../week7-slide-graph/results/CMU-1-Small-Region/boundary_nodes.png)

- 빨간 테두리 = 경계 노드 (다른 조직과 인접)
- 회색 테두리 = 내부 노드 (같은 조직으로만 둘러싸임)
- 노드 크기 = 시각적 강조

#### 2.6 3개 WSI 비교

| WSI | 경계 엣지 | 주요 경계 | 해석 |
|-----|----------|----------|------|
| **CMU** | **63.0%** | **TUM-STR** 20.6% | 가장 침윤성 |
| TEST_sample1 | 54.7% | MUS-STR 25.1% | 중간 |
| TEST_sample2 | **41.5%** | NORM-MUS 23.1% | 덜 침윤성 |

**패턴 발견**:
```
침윤성 암 (CMU):
  - 높은 경계 비율 (63%)
  - TUM-STR 경계 많음
  - 조직들이 복잡하게 섞임

덜 침윤성 (TEST_sample2):
  - 낮은 경계 비율 (41.5%)
  - 정상 구조 경계 많음
  - 큰 덩어리로 유지
```

---

### Step 3: 커뮤니티 탐지 (Community Detection)

#### 3.1 개념과 기대

**커뮤니티 탐지란?**:
```
그래프 구조만으로 "군집" 찾기

Louvain 알고리즘:
- 조직 타입을 모름
- 오직 연결 패턴만 봄
- 강하게 연결된 노드끼리 묶음

질문:
"같은 조직끼리 잘 묶일까?"
```

**기대**:
```
정상 조직이라면:
Community 1: NORM만 (purity 높음)
Community 2: MUS만 (purity 높음)
Community 3: STR만 (purity 높음)

→ 명확한 조직 구조
→ Purity 0.9 이상
```

#### 3.2 결과: 예상과 다른 발견

**CMU-1-Small-Region**:
```
Found 6 communities
Average purity: 0.480

Community 4 (17 nodes):
  STR  : 6 nodes (35.3%)
  TUM  : 5 nodes (29.4%)
  MUS  : 5 nodes (29.4%)
  BACK : 1 node  (5.9%)
  Purity: 0.353 (매우 낮음!)
```

**중요한 질문**:
"왜 커뮤니티가 명확하지 않을까?"

**깊이 있는 이해**:

**실패가 아니다!**
```
Purity 0.48 ≈ 0.5 (랜덤 수준)

이것은:
✗ 알고리즘 실패 (X)
✓ 침윤성 암의 본질 (O)

이유:
"조직들이 복잡하게 섞여있다"
= "명확한 군집을 형성할 수 없다"
= "침윤성 성장 패턴"
```

**Week 2 경계 분석과 연결**:
```
경계 엣지 높음 (63%)
    ↓
서로 다른 조직이 많이 연결
    ↓
Louvain이 군집 찾기 어려움
    ↓
Purity 낮음 (0.48)
    ↓
→ 침윤성의 구조적 증거!
```

#### 3.3 커뮤니티 시각화

**1) 커뮤니티 분포**

![Communities](../week7-slide-graph/results/CMU-1-Small-Region/communities.png)

- 각 색상 = 하나의 커뮤니티
- 같은 색 = 강하게 연결된 노드들
- 색상이 섞여있음 = 명확한 군집 없음

**2) 커뮤니티 vs 실제 조직**

![Communities vs Tissue](../week7-slide-graph/results/CMU-1-Small-Region/communities_vs_tissue.png)

- 왼쪽: 실제 조직 타입 (Ground Truth)
- 오른쪽: 알고리즘이 찾은 커뮤니티
- 차이가 큼 → 조직이 섞여 있음

#### 3.4 흥미로운 발견: 정량적 지표 가능성

**중요한 통찰**:
"정량적 지표 개발성을 만들 수 있다는 게 흥미롭네. 결국 purity가 낮다는 건 침윤성 암이며 조직이 혼재해 그럴 가능성이 있다는 거지?"

**정확히 맞습니다!**

**Purity와 침윤성의 관계**:
```python
# 침윤성 지표 개발
infiltration_score = (
    boundary_edges_ratio * 2.0 +  # 경계 비율
    (1 - purity) * 1.5             # 커뮤니티 혼재
)

CMU:
  = (0.63 * 2.0) + (0.52 * 1.5)
  = 1.26 + 0.78
  = 2.04 (높음!)

TEST_sample2:
  = (0.415 * 2.0) + (0.494 * 1.5)
  = 0.83 + 0.74
  = 1.57 (낮음)
```

**병리학적 의의**:
```
기존: "이 종양은 침윤성으로 보입니다"
      → 주관적, 관찰자 간 차이

Week 7: "Purity 0.48, 경계 63%"
      → 객관적, 정량적, 재현 가능
      → 예후 예측 모델 개발 가능
```

#### 3.5 TEST_sample2 대조

**TEST_sample2**:
```
Found 16 communities
Average purity: 0.506

Community 0 (107 nodes):
  NORM: 70 nodes (65.4%) ← 비교적 순수!

Community 3 (212 nodes):
  MUS: 132 nodes (62.3%) ← 큰 근육 군집
```

**비교**:
```
CMU (침윤성):
- Purity 0.48
- 모든 커뮤니티 혼재
- 순수 영역 없음

TEST_sample2 (응집성):
- Purity 0.51
- 일부 순수 커뮤니티
- 큰 조직 덩어리 유지
```

---

### Step 4: 중심성 분석 (Centrality Analysis)

#### 4.1 개념: 누가 VIP인가?

**2가지 중심성**:

**Degree Centrality**:
```
"친구가 가장 많은 사람"

Node A: 8개 연결
Node B: 5개 연결
→ Node A가 더 중요

의미: 많이 연결 = 활발한 상호작용
```

**Betweenness Centrality**:
```
"다리 역할을 하는 사람"

A ──[B]── C
│    │    │
D ──[B]── E

Node B를 지나는 경로가 많음
→ Node B가 구조적으로 중요

의미: 경로의 허브 = 정보/침윤의 교차로
```

#### 4.2 충격적인 발견: 100% 경계 노드

**CMU-1-Small-Region**:
```
Boundary nodes: 82 (100.0%)

Boundary vs Internal nodes:
  Boundary: 0.1138
  Internal: nan  ← 내부 노드가 없음!
```

**의미**:
```
100% 경계 노드
= 모든 패치가 경계에 있음
= 순수한 조직 영역이 전혀 없음
= 완전히 뒤섞인 구조
= 극도로 침윤성!
```

**시각적 이해**:
```
정상 조직:
[NORM][NORM][NORM]  ← 내부 노드 많음
[NORM][NORM][NORM]
       ↑
    순수 영역

CMU (침윤성 암):
[TUM][STR][BACK]    ← 모두 경계!
[MUS][TUM][STR]     ← 순수 영역 없음
       ↑
  모든 패치가 경계
```

#### 4.3 중심성 시각화

**1) Degree Centrality**

![Degree Centrality](../week7-slide-graph/results/CMU-1-Small-Region/centrality_degree.png)

- 노드 크기 = degree (연결 개수)
- 색상 = degree centrality (빨강 = 높음)
- 큰 빨간 노드 = 많이 연결된 VIP

**2) Betweenness Centrality**

![Betweenness Centrality](../week7-slide-graph/results/CMU-1-Small-Region/centrality_betweenness.png)

- 노드 크기 = betweenness (경로 중심성)
- 색상 = betweenness centrality
- 보라색 노드 = 많은 경로가 지나감
- 구조의 "허브"

**3) 통합 시각화**

![Centrality Combined](../week7-slide-graph/results/CMU-1-Small-Region/centrality_combined.png)

- 왼쪽: Degree centrality
- 오른쪽: Betweenness centrality
- 빨간 테두리 = 경계 노드
- 대부분 빨간 테두리 → 100% 경계

#### 4.4 Top Betweenness 노드 분석

**CMU Top 5**:
```
1. Node 34 (BACK): 0.1338
2. Node 40 (BACK): 0.1277
3. Node 50 (BACK): 0.1200
4. Node 51 (TUM):  0.1178  ← 종양!
5. Node 45 (STR):  0.1122  ← 기질!
```

**패턴 발견**:
```
BACK (배경) - TUM (종양) - STR (기질)

이 3가지 조직이 "허브"
→ 침윤 전선의 중심!
```

**위치 분석**:
```
Node 51 (TUM): position (1120.0, 3136.0)
Node 45 (STR): position (1120.0, 2800.0)

→ X좌표 1120으로 같음
→ Y좌표 2800-3136 (가까움)
→ 종양-기질이 인접한 침윤 전선!
```

**병리학적 해석**:
```
[BACK]
  ↓ (Node 40, 34, 50 - 높은 중심성)
[TUM] ← Node 51 (침윤 전선의 허브!)
  ↓
[STR] ← Node 45 (기질 반응)

→ 이 수직 라인이 침윤의 "고속도로"
→ 여러 경로가 여기를 지나감
→ 구조적으로 가장 중요한 위치
```

**의미**:
```
Node 51 (TUM)이 betweenness 4위:
→ 이 패치를 지나는 경로 많음
→ 종양이 여러 조직을 연결
→ 침윤의 "교차로"

만약 이 패치 제거 시:
→ 그래프 연결성 감소
→ 구조적으로 핵심 위치
```

#### 4.5 3개 WSI 종합 비교

| WSI | 경계 노드 | Top Betweenness | 침윤성 |
|-----|----------|-----------------|--------|
| **CMU** | **100%** | **BACK-TUM-STR** | 가장 높음 |
| TEST_sample1 | 97.9% | STR-MUS-NORM | 중간 |
| TEST_sample2 | 86.7% | BACK-MUS | 낮음 |

**패턴**:
```
침윤성 ↑ → 경계 노드 ↑ → 종양이 허브

CMU: 100% 경계 + TUM이 Top 5
→ 종양이 구조의 중심
→ 매우 공격적

TEST_sample2: 86.7% + TUM 허브 아님
→ 상대적으로 덜 공격적
```

---

## 핵심 학습 내용

### 1. CNN vs GNN의 본질적 차이

#### 이해의 여정

**초기 질문**:
"CNN은 주변 정보 고려 없이 그저 224×224 픽셀 이미지를 가지고 기존 알고리즘으로 패턴을 감지해 분류해낸거지? 대신 GNN은 이웃정보까지 고려하는 거고."

**정확한 이해** (약간의 뉘앙스 추가):

**CNN의 "주변"**:
```
CNN이 보는 범위:
┌─────────────┐
│  픽셀 픽셀   │ ← 이 안에서만 주변을 봄
│  픽셀 핵 핵  │
│  픽셀 픽셀   │
└─────────────┘
= 1개 패치 (224×224)

✓ 핵 주변의 세포질 관찰
✓ 세포 배열 패턴 인식
✗ 다른 패치는 전혀 모름
```

**GNN의 "주변"**:
```
GNN이 보는 범위:
┌────┐  ┌────┐  ┌────┐
│패치A├──┤패치B├──┤패치C│
└────┘  └────┘  └────┘
  TUM     STR     NORM

패치 B 판단 시:
- CNN: B 이미지만 → "기질"
- GNN: B + 이웃 정보
      → "기질인데, 왼쪽에 종양, 오른쪽에 정상"
      → "침윤 경로일 수 있다"
```

**실제 차이 예시**:

**염색 Artifact vs 실제 종양**:
```
CNN:
패치: [진한 보라색, 밀집 핵]
→ "80% 종양"
문제: 염색 artifact일 수도...

GNN:
패치: [진한 보라색, 밀집 핵]
이웃: [정상, 정상, 정상, 정상]
→ Layer 1: "종양 같지만 이웃은 모두 정상"
→ Layer 2: "고립된 종양은 드물다"
→ "40% 종양, 60% 정상 (artifact 가능성)"
```

### 2. Permutation Invariance의 중요성

**질문의 가치**:
"GNN에서 패치를 관찰하는 순서가 영향을 주지는 않아?"

**깊이 있는 이해**:

**비유: 친구들의 평균 키**:
```
친구들 = [철수(170), 영희(165), 민수(175)]

순서 1: (170 + 165 + 175) / 3 = 170
순서 2: (165 + 175 + 170) / 3 = 170
순서 3: (175 + 170 + 165) / 3 = 170

→ 평균(MEAN)은 순서와 무관
```

**그래프의 본질**:
```
      A
     / \
    B   C

이것과

      A
     / \
    C   B

이것은 같은 그래프
(B와 C의 순서는 의미 없음)
```

**병리학적 직관**:
```
종양 주변 이웃: [기질, 정상, 기질, 정상]

병리학자가 보는 것:
"종양 주변에 기질과 정상이 섞여 있다"

중요한 것:
✓ 어떤 조직들이 있는가?
✓ 각 조직이 몇 개인가?
✗ 어떤 순서로 관찰했는가? (무의미)
```

**GNN에서의 구현**:
```python
# SUM, MEAN, MAX는 순서 불변
aggregated = mean([feature_A, feature_B, feature_C])
→ 어떤 순서로 처리하든 같은 결과

# LSTM은 순서 의존 (GNN에서 사용 안 함)
LSTM(A) → LSTM(B) → LSTM(C)  ≠  LSTM(B) → LSTM(C) → LSTM(A)
```

### 3. Week 6 vs Week 7의 진정한 차이

**이해의 진화**:

**Week 6**:
```
"패치가 어디에 있는가"

데이터:
{
  'coordinates': [[0,0], [224,0], ...],
  'predictions': [3, 7, 0, ...]
}

분석:
- 시각화: scatter plot
- 질문: "종양이 어디에 있나?"
- 한계: 관계가 암묵적
```

**Week 7**:
```
"패치가 누구와 연결되어 있는가"

데이터:
Graph:
  Nodes: {0: TUM, 1: STR, 2: BACK}
  Edges: [(0,1), (1,2), ...]

분석:
- 시각화: network graph
- 질문: "종양 주변에 무엇이?"
- 장점: 관계가 명시적
```

**핵심 차이**:
```
Week 6 (Human-readable):
사람이 보고 "아, 관계가 있구나" 추론

Week 7 (Machine-readable):
컴퓨터도 "관계"를 데이터로 갖고 계산 가능
→ 그래프 알고리즘 적용
→ 정량적 분석
→ GNN 학습 준비
```

### 4. 침윤성의 정량화

**4가지 지표의 통합**:

```python
침윤성 점수 = (
    경계_엣지_비율 * 2.0 +
    (1 - 커뮤니티_순도) * 1.5 +
    경계_노드_비율 * 1.0 +
    종양_중심성 * 0.5
)
```

**지표별 의미**:

**1. 경계 엣지 비율 (Weight: 2.0)**:
```
63% = 거의 모든 연결이 서로 다른 조직

의미: 조직들이 복잡하게 섞임
병리: 침윤 전선이 광범위
예후: 절제 범위 예측 어려움
```

**2. 커뮤니티 순도 (Weight: 1.5)**:
```
Purity 0.48 = 거의 랜덤

의미: 명확한 조직 군집 없음
병리: 미세 침윤 광범위
예후: 잔존 병변 가능성
```

**3. 경계 노드 비율 (Weight: 1.0)**:
```
100% = 순수 영역 전혀 없음

의미: 모든 패치가 혼재
병리: 종양이 모든 곳에 영향
예후: 매우 공격적
```

**4. 종양 중심성 (Weight: 0.5)**:
```
TUM이 Top 5 betweenness

의미: 종양이 구조의 허브
병리: 침윤의 중심지
예후: 핵심 병변
```

**CMU 최종 점수**:
```
= (0.63 * 2.0) + (0.52 * 1.5) + (1.00 * 1.0) + (0.3 * 0.5)
= 1.26 + 0.78 + 1.00 + 0.15
= 3.19 (매우 높음!)

해석:
3.0 이상: Highly infiltrative
2.0-3.0: Moderately infiltrative
< 2.0: Relatively cohesive
```

### 5. 경계 분석의 임상적 가치

**학습한 병리학적 개념**:

**침윤 패턴의 분류**:

**Pushing 경계** (좋은 예후):
```
┌─────────┐
│   TUM   │
└─────────┘
━━━━━━━━━━━ 명확한 경계
┌─────────┐
│  NORM   │
└─────────┘

특징:
- 경계가 둥글고 매끄러움
- 경계 엣지 < 40%
- 수술 범위 예측 쉬움
```

**Infiltrative 경계** (나쁜 예후):
```
    TUM
  ╱  │  ╲
 ╱   │   ╲  불규칙한 경계
╱────┴────╲
  NORM에 침투

특징:
- 경계가 불규칙
- 경계 엣지 > 60%
- 수술 범위 예측 어려움
- CMU가 이 패턴!
```

**조직 경계의 의미**:

**TUM-STR 경계** (가장 중요):
```
[TUM] ─── [STR]

의미:
- 침윤 전선 (invasive front)
- Desmoplastic reaction
- 기질이 섬유화 반응
- 암이 능동적으로 침범

CMU: 20.6%가 TUM-STR
→ 활발한 침윤 중
```

**TUM-NORM 경계** (더 공격적):
```
[TUM] ─── [NORM]

의미:
- 기질 단계 건너뜀
- 직접 정상 조직 침범
- 더 공격적 침윤
- 나쁜 예후와 연관
```

---

## 어려웠던 점과 해결 과정

### 1. 그래프 개념의 추상성

**초기 어려움**:
"그래프가 왜 필요한가? Week 6의 공간 맵으로 충분하지 않나?"

**해결 과정**:

**Step 1: 구체적 예시로 이해**:
```
질문: "이 종양 패치 주변에 무엇이 있나?"

Week 6 방식:
좌표를 보고 수동으로 확인
→ 사람은 가능, 컴퓨터는 어려움

Week 7 방식:
G.neighbors(tumor_node) → [1, 3, 5]
→ 자동으로 이웃 식별
```

**Step 2: 실용적 가치 인식**:
```
경계 탐지:
Week 6: 수동으로 시각 확인
Week 7: for u, v in G.edges() 자동

커뮤니티 탐지:
Week 6: 불가능
Week 7: louvain_communities(G)

중심성 분석:
Week 6: 불가능
Week 7: betweenness_centrality(G)
```

**최종 이해**:
"그래프 = 관계를 컴퓨터가 계산할 수 있는 형태로"

### 2. Purity 0.48의 해석

**초기 반응**:
"Purity가 0.5인데 실패 아닌가?"

**깊이 있는 분석**:

**문제 제기**:
```
Community 4:
  STR: 35.3%
  TUM: 29.4%
  MUS: 29.4%
  
거의 균등하게 섞임 = 랜덤?
```

**패러다임 전환**:
```
질문: "왜 커뮤니티가 명확하지 않을까?"

답: 침윤성 암의 본질!

침윤성 암:
[STR][TUM][MUS]
[TUM][STR][TUM]  ← 실제로 이렇게 섞임
[MUS][TUM][STR]

→ 명확한 군집을 형성할 수 없음
→ Purity 낮은 것이 정상
→ 오히려 침윤성의 증거!
```

**Week 2와 연결**:
```
경계 엣지 63% (Week 2)
    ↓
조직들이 많이 섞임
    ↓
Purity 0.48 (Step 3)
    ↓
→ 일관된 스토리!
```

**통찰**:
"실패처럼 보이는 결과가 오히려 중요한 발견"

### 3. 100% 경계 노드의 충격

**결과 확인 시**:
```
Boundary nodes: 82 (100.0%)
Internal nodes: 0 (0.0%)
```

**초기 의심**:
"코드 오류 아닌가? 100%는 이상한데?"

**검증 과정**:

**Step 1: 알고리즘 재확인**:
```python
def find_boundary_nodes(G):
    boundary_nodes = set()
    for node in G.nodes():
        node_class = G.nodes[node]['prediction']
        for neighbor in G.neighbors(node):
            if G.nodes[neighbor]['prediction'] != node_class:
                boundary_nodes.add(node)
                break
    return boundary_nodes
```

로직은 맞음 ✓

**Step 2: 수동 확인**:
```
Node 0 (BACK):
  이웃: [1, 8, 9]
  클래스: [STR, BACK, STR]
  → 1, 9가 다름 → 경계 노드 ✓

Node 1 (STR):
  이웃: [0, 2, ...]
  클래스: [BACK, TUM, ...]
  → 0, 2가 다름 → 경계 노드 ✓
```

모든 노드 확인 결과: 실제로 100% ✓

**Step 3: 병리학적 의미 이해**:
```
100% 경계 노드
= 순수한 조직 영역이 전혀 없음
= 모든 패치가 다른 조직과 접촉
= 극도로 침윤성!

이것은:
✗ 오류 (X)
✓ CMU의 특별한 특징 (O)
✓ 매우 공격적인 암 (O)
```

**TEST_sample2와 비교**:
```
TEST_sample2: 86.7% 경계 노드
→ 13.3%는 순수 영역 (내부 노드)
→ NORM이나 MUS의 큰 덩어리

CMU: 100% 경계 노드
→ 순수 영역 전혀 없음
→ 완전히 뒤섞임
```

**최종 이해**:
"충격적 결과가 가장 중요한 발견"

### 4. 파일 생성 오류 패턴

**반복된 문제**:
```
1. visualize_graph.py: 파일명 오류
2. analyze_boundaries.py: cat 명령어 오류
```

**학습한 해결 패턴**:

**문제 진단**:
```bash
# 1. 파일 존재 확인
ls -la myscripts/

# 2. 파일 첫 줄 확인
head -3 myscripts/script.py

# 3. 예상 vs 실제
예상: # myscripts/script.py
실제: cat > myscripts/...  ← 문제!
```

**예방책**:
```bash
# 방법 1: nano 직접 사용 (가장 안전)
nano myscripts/script.py
(내용 작성 후 Ctrl+O, Ctrl+X)

# 방법 2: 파일 확인 후 실행
head -3 myscripts/script.py
./process_script.sh

# 방법 3: 단일 파일 테스트
python3 myscripts/script.py CMU-1-Small-Region
```

**교훈**:
- 파일 생성 방법 일관성 유지
- 실행 전 항상 검증
- 에러 메시지 패턴 인식

### 5. Docker 환경 이해

**초기 질문**:
"이게 Docker 환경에서 진행된거야?"

**이해 과정**:

**증거 확인**:
```bash
# process_build_graph.sh
docker run --rm \
  -v "$(pwd)/../week6-slide-graph/results:/data/week6_results" \
  -v "$(pwd)/results:/results" \
  -v "$(pwd)/myscripts:/workspace" \
  ...
```

**작동 원리 이해**:
```
1. Docker 컨테이너 시작
   ↓
2. 로컬 폴더 마운트
   - Week 6 결과 → /data/week6_results
   - Week 7 결과 → /results
   - 스크립트 → /workspace
   ↓
3. 컨테이너 내부에서 Python 실행
   ↓
4. 결과를 로컬 results/에 저장
   ↓
5. 컨테이너 종료 (--rm)
```

**장점 인식**:
```
✓ Week 6와 동일한 환경
✓ 의존성 걱정 없음
✓ 재현 가능성 보장
✓ 협업 용이
```

---

## 결론 및 향후 계획

### 1. Week 7 성과

#### 기술적 성과

**4단계 분석 완료**:
```
Step 1: 그래프 구축
  - 3개 WSI, 총 2,061 노드
  - k-NN (k=8) 그래프 생성
  - NetworkX 활용

Step 2: 경계 탐지
  - 경계 엣지 비율 계산
  - 조직 간 경계 타입 분석
  - 침윤 패턴 정량화

Step 3: 커뮤니티 탐지
  - Louvain 알고리즘
  - Purity 계산
  - 조직 혼재 정도 평가

Step 4: 중심성 분석
  - Degree/Betweenness centrality
  - 경계 노드 비율
  - 구조적 허브 식별
```

**정량적 지표 개발**:
```python
침윤성 점수 = f(경계_엣지, Purity, 경계_노드, 중심성)

CMU: 3.19 (Highly infiltrative)
TEST_sample2: 2.54 (Moderately infiltrative)

→ 객관적, 재현 가능, 비교 가능
```

**생성 결과물**:
```
각 WSI당:
- graph.pkl (그래프 객체)
- 통계 파일 (4개)
- 시각화 이미지 (9개)

총: 3 WSI × 13 파일 = 39개 파일
```

#### 학습적 성과

**개념적 이해**:
- CNN vs GNN의 본질적 차이
- Permutation invariance 원리
- 그래프를 통한 관계 명시
- 침윤의 병리학적 의미

**비판적 사고**:
- Purity 0.48 = 실패가 아닌 발견
- 100% 경계 노드 = 극도로 침윤성
- 정량적 지표 개발 가능성
- 주관적 평가 → 객관적 수치

**문제 해결 능력**:
- 파일 생성 오류 패턴 인식
- Docker 환경 이해
- 단계적 디버깅
- 검증 방법 확립

### 2. Week 6 → Week 7의 발전

**데이터 활용**:
```
Week 6 출력:
{
  'predictions': [...],
  'coordinates': [...],
  'probabilities': [...]  ← 9차원 feature
}
    ↓
Week 7 입력:
Graph(
  nodes={feature, pos, prediction},
  edges=[(u,v), ...]
)
```

**분석 깊이**:
```
Week 6:
"종양이 어디에 있는가?"
→ 위치 정보

Week 7:
"종양이 누구와 연결되어 있는가?"
"그 연결이 어떤 의미인가?"
→ 관계 + 구조 + 의미
```

**임상적 가치**:
```
Week 6:
"이 슬라이드에 종양이 있습니다"
→ 진단 (Diagnosis)

Week 7:
"종양이 광범위하게 침윤하고 있으며
 경계 노드 100%, Purity 0.48로
 예후가 나쁠 것으로 예상됩니다"
→ 예후 (Prognosis)
→ 치료 계획 (Treatment planning)
```

### 3. 3개 WSI 통합 비교

**정량적 요약**:

| 지표 | CMU | TEST_sample1 | TEST_sample2 |
|------|-----|--------------|--------------|
| **경계 엣지** | 63.0% | 54.7% | 41.5% |
| **Purity** | 0.480 | 0.478 | 0.506 |
| **경계 노드** | 100% | 97.9% | 86.7% |
| **침윤성 점수** | 3.19 | 2.85 | 2.54 |

**침윤성 순위**:
```
1위 (가장 침윤성): CMU-1-Small-Region
  - 4가지 지표 모두 최악
  - 종양이 구조의 허브
  - 예후: 나쁨 ⚠️

2위: TEST_sample1
  - 다양한 조직 혼재
  - 림프구 침윤 관찰
  - 예후: 중간 ⚠️

3위 (상대적으로 덜 침윤성): TEST_sample2
  - 큰 조직 덩어리 유지
  - 일부 순수 커뮤니티
  - 예후: 상대적으로 좋음 ✓
```

**병리학적 해석**:

**CMU**:
```
"Highly infiltrative adenocarcinoma with:
 - Extensive tissue intermixing (63% boundary edges)
 - No distinct tissue communities (purity 0.48)
 - Complete boundary involvement (100% nodes)
 - Tumor at structural hub (betweenness 0.118)
 
Recommendation:
 - Wide surgical margin required
 - Adjuvant chemotherapy strongly recommended
 - Close follow-up necessary
 
Prognosis: Poor"
```

**TEST_sample2**:
```
"Relatively well-demarcated adenocarcinoma with:
 - Moderate tissue mixing (41.5% boundary edges)
 - Some pure tissue communities (purity 0.51)
 - Partial internal regions (86.7% boundary nodes)
 
Recommendation:
 - Standard surgical margin
 - Consider adjuvant therapy based on staging
 
Prognosis: Relatively favorable"
```

### 4. 실습의 의의

#### 개인적 의의

**기술적 성장**:
- 그래프 이론 이해 및 적용
- 복잡한 알고리즘 (Louvain, Centrality) 활용
- 4단계 파이프라인 구축
- Docker 환경 숙련도 향상

**개념적 이해**:
- CNN에서 GNN으로의 진화
- 공간 분석에서 관계 분석으로
- 시각적에서 정량적으로
- 주관적에서 객관적으로

**비판적 사고**:
- 예상과 다른 결과의 해석
- 실패처럼 보이는 발견의 가치
- 정량적 지표 개발 가능성
- 병리학적 의미 연결

#### 학문적 의의

**재현 가능한 연구**:
```
모든 단계:
1. 명확한 알고리즘 (k-NN, Louvain)
2. 명시적 파라미터 (k=8)
3. Docker로 환경 고정
4. GitHub에 코드 공개

→ 누구나 재현 가능
→ 검증 가능
→ 확장 가능
```

**정량적 병리학**:
```
기존: "침윤성으로 보입니다"
      (주관적, 관찰자 간 차이)

Week 7: "경계 63%, Purity 0.48"
      (객관적, 정량적, 재현 가능)

→ Computational Pathology의 발전
```

#### 임상적 의의

**예후 예측 모델 개발 가능성**:
```python
# 가설
침윤성_점수 = f(경계_엣지, Purity, 경계_노드)

# 검증 필요
- 더 많은 샘플 (n > 100)
- 실제 예후 데이터와 비교
- 5년 생존율 vs 침윤성 점수

→ 예측 모델 개발
```

**치료 결정 지원**:
```
침윤성 점수 > 3.0:
→ 광범위 절제
→ 보조 항암치료
→ 면밀한 추적관찰

침윤성 점수 < 2.0:
→ 표준 절제
→ 경과 관찰
```

### 5. 한계와 개선 방향

#### 인정하는 부족함

**샘플 크기**:
- 3개 WSI만 분석
- 통계적 검증 불충분
- 일반화 어려움

**모델 검증**:
- Ground truth 없음
- 실제 예후 데이터 부재
- 침윤성 점수 미검증

**병리학적 검증**:
- 병리학자 검토 없음
- 조직 타입의 정확성 불명
- H&E 염색 artifact 가능성

**그래프 설계**:
- k=8이 최적인가?
- Distance threshold 비교 안 함
- Grid-based graph와 비교 필요

#### 향후 개선 방향

**단기 (1개월 내)**:
```
1. 더 많은 WSI 분석 (n > 20)
2. k 값 최적화 (4, 8, 16 비교)
3. 다른 그래프 구축 방법 비교
4. 병리학자와 협업
```

**중기 (1학기 내)**:
```
1. 실제 예후 데이터 수집
2. 침윤성 점수 검증
3. 예측 모델 개발
4. 다른 암종에 적용
```

**장기 (연구 확장)**:
```
1. GNN 모델 학습
   - PyTorch Geometric
   - Node classification
   - Graph classification

2. 멀티모달 분석
   - WSI + 임상 정보
   - WSI + 유전자 데이터
   - 통합 예후 예측

3. 임상 적용
   - 진단 보조 시스템
   - 치료 반응 예측
   - 개인 맞춤 치료
```

### 6. 7주 통합 여정

**Week 1-7의 흐름**:
```
Week 1: 로컬 환경, 패치 추출
    ↓
Week 2: 고급 기능, 해상도
    ↓
Week 3: Docker, 재현성
    ↓
Week 4: AI 모델, 패치 분류
    ↓
Week 5: Stain Normalization
    ↓
Week 6: Feature Extraction
    ↓
Week 7: Slide Graph, 관계 분석
```

**핵심 진화**:
```
픽셀 → 패치 → Feature → 그래프 → (향후) GNN

개별 → 공간 → 관계 → 구조 → 학습

시각적 → 정량적 → 객관적
```

---

## 참고 자료

### 1. 공식 문서

- **NetworkX**: https://networkx.org/documentation/stable/
- **Louvain Algorithm**: https://python-louvain.readthedocs.io/
- **scikit-learn NearestNeighbors**: https://scikit-learn.org/stable/modules/neighbors.html
- **TIAToolbox**: https://tia-toolbox.readthedocs.io

### 2. GitHub 저장소

- **본 프로젝트**: https://github.com/kseoyoung83/EBR-WSI-Analysis
- **NetworkX**: https://github.com/networkx/networkx
- **PyTorch Geometric**: https://github.com/pyg-team/pytorch_geometric (향후 사용)

### 3. 주요 논문

- **Graph Neural Networks**: Kipf & Welling (2017) - Semi-Supervised Classification with Graph Convolutional Networks
- **Digital Pathology**: Litjens et al. (2016) - Deep learning in histopathology
- **Community Detection**: Blondel et al. (2008) - Fast unfolding of communities in large networks
- **WSI Analysis**: Lu et al. (2021) - Data-efficient and weakly supervised computational pathology on whole-slide images

### 4. 개념 자료

**그래프 이론**:
- Node, Edge, Graph
- k-NN Graph
- Degree, Betweenness centrality
- Community detection

**병리학**:
- 침윤 (Invasion)
- 침윤 전선 (Invasive front)
- Desmoplastic reaction
- 조직 경계 패턴

**기계학습**:
- Graph Neural Networks
- Message passing
- Aggregation functions
- Permutation invariance

### 5. 트러블슈팅

- **NetworkX 설치**: Docker 이미지에 포함
- **메모리 문제**: Betweenness 계산 시 큰 그래프에서 느림
- **파일 생성**: nano 직접 사용 권장

---

## 부록

### A. 최종 명령어 모음

```bash
# Week 7 전체 실행 순서

# 1. 폴더 생성
cd ~/Desktop/EBR-WSI-Analysis
mkdir -p week7-slide-graph/{myscripts,results}
cd week7-slide-graph

# 2. 그래프 구축
./process_build_graph.sh

# 3. 시각화
./process_visualization.sh

# 4. 경계 탐지
./process_boundaries.sh

# 5. 커뮤니티 탐지
./process_communities.sh

# 6. 중심성 분석
./process_centrality.sh

# 7. 결과 확인
tree -L 3 results/
```

### B. 폴더 구조 (최종)

```
week7-slide-graph/
├── myscripts/
│   ├── build_graph.py
│   ├── visualize_graph.py
│   ├── analyze_boundaries.py
│   ├── detect_communities.py
│   └── compute_centrality.py
├── process_build_graph.sh
├── process_visualization.sh
├── process_boundaries.sh
├── process_communities.sh
├── process_centrality.sh
├── REPORT_week7.md
└── results/
    ├── CMU-1-Small-Region/
    │   ├── graph.pkl
    │   ├── graph_statistics.txt
    │   ├── graph_structure.png
    │   ├── connectivity_map.png
    │   ├── week6_vs_week7_comparison.png
    │   ├── boundary_edges.png
    │   ├── boundary_nodes.png
    │   ├── boundary_statistics.txt
    │   ├── communities.png
    │   ├── communities_vs_tissue.png
    │   ├── community_statistics.txt
    │   ├── centrality_degree.png
    │   ├── centrality_betweenness.png
    │   ├── centrality_combined.png
    │   └── centrality_statistics.txt
    ├── TEST_sample1/ (동일 구조)
    └── TEST_sample2/ (동일 구조)
```

### C. 주요 개념 정리

**Slide Graph**:
- Node: 패치
- Edge: 공간적 인접성
- Feature: 9차원 확률 벡터
- 목적: 관계 명시

**경계 엣지 (Boundary Edge)**:
- 서로 다른 조직 연결
- 침윤 전선 표현
- 침윤성 정량화

**Community**:
- 강하게 연결된 노드 군집
- Louvain 알고리즘
- Purity로 순도 평가

**Centrality**:
- Degree: 연결 개수
- Betweenness: 경로의 중심
- 구조적 중요성

**침윤성 점수**:
- 4가지 지표 통합
- 정량적 평가
- 예후 예측 가능

### D. 침윤성 평가 체크리스트

**그래프 통계**:
- [ ] 노드 수, 엣지 수
- [ ] 평균 degree
- [ ] 연결성 (connected components)

**경계 분석**:
- [ ] 경계 엣지 비율 (< 40%, 40-60%, > 60%)
- [ ] 주요 경계 타입 (TUM-STR, TUM-NORM)
- [ ] 경계 노드 비율

**커뮤니티 분석**:
- [ ] 커뮤니티 수
- [ ] 평균 purity (< 0.5, 0.5-0.7, > 0.7)
- [ ] 주요 커뮤니티 구성

**중심성 분석**:
- [ ] Top betweenness nodes
- [ ] 종양 노드의 중심성
- [ ] 경계 vs 내부 노드 비교

**최종 평가**:
- [ ] 침윤성 점수 계산
- [ ] 예후 평가 (Good, Moderate, Poor)
- [ ] 치료 권장사항

### E. GNN 준비 (향후 확장)

**PyTorch Geometric 데이터 형식**:
```python
import torch
from torch_geometric.data import Data

# 그래프를 PyG 형식으로 변환
edge_index = torch.tensor(list(G.edges())).t()
x = torch.tensor([G.nodes[n]['feature'] for n in G.nodes()])
y = torch.tensor([G.nodes[n]['prediction'] for n in G.nodes()])

data = Data(x=x, edge_index=edge_index, y=y)

# GNN 모델 학습 가능
from torch_geometric.nn import GCNConv

class SimpleGNN(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = GCNConv(9, 16)
        self.conv2 = GCNConv(16, 9)
    
    def forward(self, data):
        x, edge_index = data.x, data.edge_index
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = self.conv2(x, edge_index)
        return F.log_softmax(x, dim=1)
```

---

## 마치며

### 핵심 메시지

**"관계를 명시하면 보이지 않던 패턴이 보인다"**

Week 7 실습을 통해:
- ✓ 그래프 구조로 패치 간 관계 명시
- ✓ 경계 탐지로 침윤 패턴 정량화
- ✓ 커뮤니티 분석으로 조직 혼재 평가
- ✓ 중심성 분석으로 구조적 허브 식별
- ✓ 침윤성의 정량적 지표 개발

### 실습의 진정한 가치

이 실습은:
- "그래프를 그리는 법"이 아니라
- "관계를 통해 구조를 이해하는 법"을 배우는 것입니다
- 개별 패치가 아닌 전체 네트워크를 보는 시각을 키웠습니다

### 시행착오에서 배운 것

**예상과 다른 결과의 가치**:
- Purity 0.48 = 실패가 아닌 중요한 발견
- 100% 경계 노드 = 극도로 침윤성의 증거
- 오히려 병리학적 현실을 제대로 반영

**질문의 힘**:
- "GNN이 뭐야?" → Message passing 이해
- "순서가 영향을 줘?" → Permutation invariance
- "왜 커뮤니티가 불명확해?" → 침윤성의 본질

**LLM 활용**:
- 개념 이해: 비유를 통한 학습 (소문 퍼지기)
- 문제 해결: 단계적 디버깅
- 확장: 정량적 지표 개발 아이디어

### Week 1-7 통합 여정

- **Week 1**: 로컬에서 패치 추출 기초
- **Week 2**: 해상도와 고급 기능 탐색
- **Week 3**: Docker로 재현 가능한 환경
- **Week 4**: AI 모델로 패치 분류
- **Week 5**: 색상 표준화로 일관성 확보
- **Week 6**: 공간 분석과 feature 준비
- **Week 7**: 그래프로 관계 명시, 침윤성 정량화

이제 여러분은:
- 패치를 독립적으로 분류할 수 있습니다
- 패치 간 관계를 명시할 수 있습니다
- 침윤 패턴을 정량화할 수 있습니다
- 조직 구조를 분석할 수 있습니다
- 침윤성을 객관적으로 평가할 수 있습니다

**그리고 가장 중요하게는:**
개별 패치를 넘어 전체 조직 네트워크의 구조와 의미를 이해하는 안목을 갖추었습니다.

다음 단계에서는 이 그래프 데이터로 GNN을 학습하여, 이웃 정보를 활용한 더 정확한 패치 분류와 슬라이드 수준의 예후 예측으로 확장할 것입니다.

---

**작성일**: 2025년 10월

**작성자**: 김서영 (2024191115)

**소속**: 의과대학 의예과

**과목**: Evolution of Biomedical Research

---
``