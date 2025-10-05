<artifact identifier="week3-report" type="text/markdown" title="3주차 Docker 환경 구축 실습 레포트">
# Evolution of Biomedical Research

의과대학 의예과 2024191115 김서영

## ▼ 3주차 실습

## 실습 개요

### 1. 실습 목표
- Docker를 이용한 재현 가능한 TIAToolbox 환경 구축
- Dockerfile 이해 및 수정
- Volume Mount를 통한 로컬-Container 데이터 연결
- WSI 썸네일 자동 생성 파이프라인 구현
- 1-2주차 로컬 환경과 Docker 환경 비교

### 2. 실습 환경
- **운영체제**: macOS (Apple M1 Pro)
- **개발 도구**: Terminal (zsh), VSCode, Docker Desktop
- **Docker 버전**: Docker Desktop for Mac
- **주요 이미지**: 
  - 직접 빌드: `tiatoolbox:3.11-ubuntu` (실패)
  - 직접 빌드 (수정): `tiatoolbox:3.11-ubuntu-fixed` (실패)
  - 공식 이미지: `ghcr.io/tissueimageanalytics/tiatoolbox:1.6.0-py3.11-ubuntu` (성공)

### 3. 데이터
- **파일명**: CMU-1-Small-Region.svs
- **크기**: 1.8MB
- **위치**: `~/Desktop/tiatoolbox/data/`
- **출처**: 1-2주차에서 사용한 동일 파일

### 4. 학습 배경
- **1주차**: UV 가상환경 + OpenSlide로 로컬에서 패치 추출
- **2주차**: 동일 로컬 환경에서 TIAToolbox 고급 기능 학습
- **3주차 목표**: Docker로 완전히 재현 가능한 환경 구축
- **동기**: 환경 의존성 문제 해결, 팀 협업 및 배포 준비

---

## 실습 과정

### 1. Docker Desktop 확인

#### a. Docker 실행 확인

```bash
# Docker 버전 확인
docker --version

# Docker 데몬 상태 확인
docker ps
```

**초기 문제**:
```
ERROR: Cannot connect to the Docker daemon at unix:///Users/ksy/.docker/run/docker.sock
```

**해결**:
```bash
# Docker Desktop 실행
open -a Docker

# 고래 아이콘이 상단 메뉴바에 나타날 때까지 대기 (~30초)

# 재확인
docker --version
docker ps
```

**학습 포인트**:
- Docker Desktop은 GUI 애플리케이션으로 항상 실행 중이어야 함
- Docker 데몬(백그라운드 서비스)이 없으면 명령어 실행 불가

### 2. TIAToolbox 저장소 클론

```bash
cd ~/Desktop

# TIAToolbox GitHub 저장소 클론
git clone https://github.com/TissueImageAnalytics/tiatoolbox.git

cd tiatoolbox

# 폴더 구조 확인
ls -la

# Docker 폴더 확인
ls -la docker/
```

**출력**:
```
drwxr-xr-x  docker/
  ├── 3.9/
  ├── 3.10/
  ├── 3.11/  ← 사용할 버전
  └── 3.12/
```

**Docker 폴더 구조 탐색**:
```bash
ls -la docker/3.11/

# Ubuntu와 Alpine 옵션 확인
# Ubuntu: 범용적, 패키지 풍부, 학습용 적합
# Alpine: 경량, 프로덕션용
```

### 3. Dockerfile 분석

```bash
cd ~/Desktop/tiatoolbox/docker/3.11/Ubuntu
cat Dockerfile
```

**Dockerfile 내용 및 분석**:

```dockerfile
FROM ubuntu:22.04 AS builder-image
# → Ubuntu 22.04를 베이스 OS로 사용

ENV DEBIAN_FRONTEND=noninteractive
# → 패키지 설치 시 대화형 질문 방지 (자동 설치)

# Python 3.11 설치
RUN apt-get update && \
    apt install software-properties-common -y && \
    add-apt-repository ppa:deadsnakes/ppa -y && apt update && \
    apt-get install -y --no-install-recommends python3.11-venv && \
    apt-get install libpython3.11-dev -y && \
    apt-get install python3.11-dev -y && \
    apt-get install build-essential -y && \
    apt-get clean

# 가상환경 생성
RUN python3.11 -m venv /venv
ENV PATH=/venv/bin:$PATH

# 시스템 라이브러리 설치 (OpenSlide 포함!)
RUN apt-get update && apt-get install --no-install-recommends -y \
    libopenjp2-7-dev libopenjp2-tools \
    openslide-tools \
    libgl1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# TIAToolbox 설치
RUN pip install --no-cache-dir tiatoolbox

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
```

**핵심 이해**:
- 1-2주차에서 수동으로 했던 모든 설치가 자동화됨
- OpenSlide 시스템 라이브러리가 이미 포함됨
- DYLD_LIBRARY_PATH 설정 불필요

### 4. Docker 이미지 빌드 (첫 시도)

```bash
cd ~/Desktop/tiatoolbox/docker/3.11/Ubuntu

# 이미지 빌드
docker build -t tiatoolbox:3.11-ubuntu .
```

**빌드 과정** (약 5-10분):
```
[+] Building ...
 => [1/8] FROM ubuntu:22.04
 => [2/8] RUN apt-get update && apt install ...
 => [3/8] RUN python3.11 -m venv /venv
 => [4/8] RUN apt-get update && apt-get install ...
 => [5/8] RUN pip install --no-cache-dir tiatoolbox
 => exporting to image
```

**결과 확인**:
```bash
docker images

# REPOSITORY    TAG           IMAGE ID       CREATED         SIZE
# tiatoolbox    3.11-ubuntu   29b5d6416b99   2 minutes ago   3.97GB
```

### 5. Container 실행 및 검증

#### a. 대화형 모드로 실행

```bash
# Container 내부 진입
docker run -it tiatoolbox:3.11-ubuntu

# 프롬프트 변경됨
root@5df74d3b20ff:/#
```

#### b. Container 내부에서 확인

```bash
# 1. OS 확인
cat /etc/os-release
# → Ubuntu 22.04.5 LTS

# 2. Python 버전 확인
python3 --version
# → Python 3.11.13

# 3. TIAToolbox import 테스트
python3 -c "import tiatoolbox; print('TIAToolbox version:', tiatoolbox.__version__)"
# → TIAToolbox version: 1.6.0

# 4. 파일 시스템 확인
ls -l /
# → bin, usr, var, venv 등 Linux 디렉토리 구조

# 5. 종료
exit
```

**학습 포인트**:
- Container는 완전히 독립된 Ubuntu 22.04 환경
- Mac(Host)과는 완전히 분리됨
- exit 후 Container는 중지되지만 삭제되지는 않음

### 6. Volume Mount 개념 이해

#### a. 문제 인식

Container 내부에서 로컬 파일에 접근 불가:
```bash
docker run -it tiatoolbox:3.11-ubuntu
ls /data
# → No such file or directory
```

#### b. Volume Mount 해결

**개념**:
```
Mac (Host)                           Container (Guest)
~/Desktop/tiatoolbox/data         →  /data
~/Desktop/tiatoolbox/results      →  /results
~/Desktop/tiatoolbox/myscripts    →  /scripts
```

실시간 양방향 동기화:
- Container에서 `/data` 읽기 → Mac의 파일 읽음
- Container에서 `/results` 쓰기 → Mac의 폴더에 저장

#### c. `-v` 옵션 문법

```bash
-v "호스트경로:컨테이너경로"

# 예시
-v "$(pwd)/data:/data"
# $(pwd): 현재 경로 (/Users/ksy/Desktop/tiatoolbox)
# $(pwd)/data: Mac의 data 폴더
# :/data: Container에서 /data로 보임
```

### 7. 실습 준비 - 폴더 구조 생성

```bash
cd ~/Desktop/tiatoolbox

# 필요한 폴더 생성
mkdir -p data results myscripts

# WSI 파일 복사
cp ~/Desktop/wsi_processing/data/CMU-1-Small-Region.svs data/

# 확인
ls -lh data/
# -rw-r--r--  1.8M CMU-1-Small-Region.svs
```

**최종 폴더 구조**:
```
tiatoolbox/
├── data/
│   └── CMU-1-Small-Region.svs
├── myscripts/
│   └── (Python 스크립트)
└── results/
    └── (썸네일 저장 위치)
```

### 8. 썸네일 생성 스크립트 작성

#### a. 파일 생성

VSCode GUI로 `myscripts/generate_thumbnail.py` 생성

**스크립트 내용**:
```python
#!/usr/bin/env python3
"""
Generate thumbnail image from WSI file using TIAToolbox
"""

import os
from PIL import Image
from tiatoolbox.wsicore.wsireader import WSIReader

def generate_thumbnail(input_path, output_dir, resolution=1.25, units="power"):
    """
    Generate thumbnail from WSI file and save to output directory
    
    Args:
        input_path (str): Path to input WSI file
        output_dir (str): Directory to save thumbnail
        resolution (float): Resolution for thumbnail (default: 1.25)
        units (str): Units for resolution (default: "power")
    """
    
    # Check if input file exists
    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} does not exist!")
        return False
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Open WSI file
        print(f"Opening WSI file: {input_path}")
        reader = WSIReader.open(input_path)
        
        # Generate thumbnail
        thumbnail = reader.slide_thumbnail(resolution=resolution, units=units)
        
        # Save thumbnail
        filename = os.path.basename(input_path).replace('.svs', '_thumbnail.png')
        output_path = os.path.join(output_dir, filename)
        Image.fromarray(thumbnail).save(output_path)
        
        print(f"Success! Thumbnail saved to: {output_path}")
        print(f"Thumbnail size: {thumbnail.shape}")
        
        return True
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return False

if __name__ == "__main__":
    input_path = "/data/CMU-1-Small-Region.svs"
    output_dir = "/results"
    
    generate_thumbnail(input_path, output_dir)
```

**주요 포인트**:
- 경로가 Container 내부 경로 (`/data`, `/results`)
- 1-2주차와 동일한 TIAToolbox API
- 에러 처리 포함

---

## 시행착오 및 해결 과정

### 1. zarr Import 에러 (첫 실행)

#### a. 문제 발생

```bash
docker run --rm \
  -v "$(pwd)/data:/data" \
  -v "$(pwd)/results:/results" \
  -v "$(pwd)/myscripts:/scripts" \
  tiatoolbox:3.11-ubuntu \
  python3 /scripts/generate_thumbnail.py
```

**에러**:
```
ImportError: cannot import name 'cbuffer_sizes' from 'numcodecs.blosc'
```

#### b. 원인 분석

- TIAToolbox 1.6.0 → zarr → numcodecs 의존성 체인
- numcodecs 버전이 zarr와 호환되지 않음
- 2주차의 shapely 문제와 유사한 **의존성 지옥**

#### c. 해결 시도 1: Dockerfile 수정

**수정 내용**:
```dockerfile
# 기존
RUN pip install --no-cache-dir tiatoolbox

# 수정
RUN pip install --no-cache-dir tiatoolbox && \
    pip install --upgrade zarr numcodecs
```

**재빌드**:
```bash
cd ~/Desktop/tiatoolbox/docker/3.11/Ubuntu
docker build -t tiatoolbox:3.11-ubuntu-fixed .
```

**결과**: 빌드 성공 (약 2-5분, 대부분 캐시 사용)

#### d. 재실행

```bash
docker run --rm \
  -v "$(pwd)/data:/data" \
  -v "$(pwd)/results:/results" \
  -v "$(pwd)/myscripts:/scripts" \
  tiatoolbox:3.11-ubuntu-fixed \
  python3 /scripts/generate_thumbnail.py
```

**새로운 에러**:
```
Error occurred: module 'zarr.errors' has no attribute 'FSPathExistNotDir'
```

#### e. 최종 해결: 공식 이미지 사용

**의사결정 과정**:

**옵션 1**: Dockerfile을 더 정교하게 수정 (zarr 특정 버전 지정)
- 장점: 완전한 제어
- 단점: 정확한 버전 조합 찾기 위해 여러 번 시도 필요

**옵션 2**: 공식 이미지 사용
- 장점: TIAToolbox 팀이 이미 의존성 해결
- 재현성: 버전이 명시됨 (`1.6.0-py3.11-ubuntu`)
- 단점: "블랙박스" 느낌

**선택**: 옵션 2 (재현성 + 효율성)

```bash
# 공식 이미지 다운로드
docker pull ghcr.io/tissueimageanalytics/tiatoolbox:1.6.0-py3.11-ubuntu

# 실행
docker run --rm \
  -v "$(pwd)/data:/data" \
  -v "$(pwd)/results:/results" \
  -v "$(pwd)/myscripts:/scripts" \
  ghcr.io/tissueimageanalytics/tiatoolbox:1.6.0-py3.11-ubuntu \
  python3 /scripts/generate_thumbnail.py
```

### 2. Platform 불일치 경고

#### a. 경고 메시지

```
WARNING: The requested image's platform (linux/amd64) does not match the detected host platform (linux/arm64/v8)
```

#### b. 의미

- 공식 이미지: `linux/amd64` (Intel/AMD x86_64용)
- Mac M1 Pro: `linux/arm64/v8` (Apple Silicon)
- 아키텍처 불일치

#### c. 실질적 영향

- ✓ **작동은 함**: Docker Desktop이 Rosetta 2로 에뮬레이션
- ✗ **성능 저하**: 네이티브보다 2-3배 느림
- 작은 파일(1.8MB)이라 체감 안 됨

#### d. 해결 옵션 (선택사항)

```bash
# ARM64 네이티브 이미지 시도
docker pull --platform linux/arm64 ghcr.io/tissueimageanalytics/tiatoolbox:1.6.0-py3.11-ubuntu
```

하지만 ARM64 버전이 없을 수 있음. 학습/실습 목적으로는 경고 무시 가능.

### 3. 성공!

**최종 출력**:
```
Opening WSI file: /data/CMU-1-Small-Region.svs
Success! Thumbnail saved to: /results/CMU-1-Small-Region_thumbnail.png
Thumbnail size: (185, 139, 3)
```

**결과 확인**:
```bash
ls -lh results/
open results/CMU-1-Small-Region_thumbnail.png
```

썸네일이 2주차 결과와 동일하게 생성됨.

---

## 최종 결과물

### 1. 정량적 결과

| 항목 | 값 |
|------|-----|
| Docker 이미지 크기 | ~5.6GB (공식) |
| 빌드한 이미지 | 3개 (직접 2개, 공식 1개) |
| 생성된 스크립트 | 2개 |
| 생성된 썸네일 | 5개 (개별 4개 + 비교 1개) |
| Volume Mount 경로 | 3개 (data, results, scripts) |

### 2. 생성된 파일

**폴더 구조**:
```
tiatoolbox/
├── data/
│   └── CMU-1-Small-Region.svs
├── myscripts/
│   ├── generate_thumbnail.py
│   └── multi_resolution.py
└── results/
    ├── CMU-1-Small-Region_thumbnail.png
    ├── thumbnail_res_0.5x.png
    ├── thumbnail_res_1.25x.png
    ├── thumbnail_res_2.5x.png
    ├── thumbnail_res_5.0x.png
    └── resolution_comparison.png
```

### 3. Docker 이미지 목록

```bash
docker images

REPOSITORY                                              TAG                 SIZE
ghcr.io/tissueimageanalytics/tiatoolbox                1.6.0-py3.11-ubuntu 5.6GB
tiatoolbox                                             3.11-ubuntu-fixed   3.97GB
tiatoolbox                                             3.11-ubuntu         3.97GB
```

### 4. 시각적 결과

**개별 썸네일 (해상도별)**:
- `thumbnail_res_0.5x.png`: 370 × 278 픽셀 (가장 상세)
- `thumbnail_res_1.25x.png`: 185 × 139 픽셀 (기본)
- `thumbnail_res_2.5x.png`: 93 × 70 픽셀
- `thumbnail_res_5.0x.png`: 47 × 35 픽셀 (전체 개요)

**비교 이미지**:
- 2×2 그리드로 4개 해상도 동시 비교
- 각 이미지에 해상도 및 크기 표시

---

## 핵심 학습 내용

### 1. Docker 핵심 개념

#### a. Image vs Container

**Image (이미지)**:
- 읽기 전용 템플릿
- OS + 모든 소프트웨어가 패키징됨
- 비유: 프로그램 설치 파일 (.dmg)

**Container (컨테이너)**:
- Image를 실행한 것
- 격리된 프로세스
- 비유: 실행 중인 애플리케이션

**관계**:
```
Image (tiatoolbox:3.11-ubuntu)
   ↓ docker run
Container (5df74d3b20ff)
```

#### b. Volume Mount

**개념**:
```
Mac 폴더 ←─ 실시간 동기화 ─→ Container 폴더
```

**문법**:
```bash
-v "호스트경로:컨테이너경로"
```

**효과**:
- Container에서 파일 읽기/쓰기
- 실제로는 Mac의 파일에 접근
- Container 재시작해도 데이터 유지

### 2. Docker vs UV 가상환경

#### a. 격리 수준 비교

**UV 가상환경 (1-2주차)**:
```
격리 수준: Python 패키지만
필요: Python은 시스템에 미리 설치
      OpenSlide는 별도 설치 (brew)
      DYLD_LIBRARY_PATH 설정

~/Desktop/wsi_processing/
└── .venv/  ← Python 패키지만 격리
```

**Docker (3주차)**:
```
격리 수준: OS 전체 (커널 제외)
필요: Docker만 설치

tiatoolbox:3.11-ubuntu (Image)
├── Ubuntu 22.04
├── Python 3.11
├── OpenSlide (시스템 라이브러리)
└── TIAToolbox + 의존성
```

#### b. 비교표

| 항목 | UV 가상환경 | Docker |
|------|------------|--------|
| 격리 수준 | Python 패키지만 | OS + 전체 |
| 설치 복잡도 | 중간 (시스템 라이브러리 별도) | 낮음 (Image 다운로드) |
| 재현성 | 낮음 (OS 의존) | 매우 높음 |
| 크기 | ~100MB | ~2-5GB |
| 시작 속도 | 빠름 (초) | 중간 (수 초) |
| 적합한 용도 | 빠른 개발, 실험 | 배포, 협업, 완전한 재현 |

#### c. 재현성 비교

**UV 환경 공유 시**:
```python
# pyproject.toml
[project]
dependencies = [
    "openslide-python>=1.3.1",
    "tiatoolbox>=1.3.0"
]
```

**문제**:
- 다른 사람이 받아도 OpenSlide 시스템 라이브러리 별도 설치 필요
- macOS/Linux/Windows마다 설치 방법 다름

**Docker 공유 시**:
```bash
docker pull ghcr.io/tissueimageanalytics/tiatoolbox:1.6.0-py3.11-ubuntu
```

**장점**:
- OS, Python, 모든 라이브러리가 포함됨
- 어떤 컴퓨터에서도 동일하게 작동
- 5년 후에도 동일한 Image 사용 가능

### 3. Docker 명령어 정리

#### a. Image 관련

```bash
# 이미지 빌드
docker build -t 이미지명:태그 .

# 이미지 목록 확인
docker images

# 이미지 다운로드
docker pull 이미지명:태그

# 이미지 삭제
docker rmi 이미지명:태그
```

#### b. Container 관련

```bash
# Container 실행 (대화형)
docker run -it 이미지명

# Container 실행 (명령 실행 후 종료)
docker run --rm 이미지명 명령어

# Container 실행 (백그라운드)
docker run -d 이미지명

# 실행 중인 Container 확인
docker ps

# 모든 Container 확인
docker ps -a

# Container 중지
docker stop 컨테이너ID

# Container 삭제
docker rm 컨테이너ID
```

#### c. Volume Mount

```bash
# Volume Mount로 실행
docker run --rm \
  -v "$(pwd)/data:/data" \
  -v "$(pwd)/results:/results" \
  이미지명 \
  명령어
```

#### d. 실전 패턴

**패턴 1: 대화형 탐색**
```bash
docker run -it tiatoolbox:3.11-ubuntu
# Container 내부에서 명령 실행
exit
```

**패턴 2: 일회성 작업**
```bash
docker run --rm \
  -v "$(pwd)/data:/data" \
  tiatoolbox:3.11-ubuntu \
  python3 /scripts/script.py
```

**패턴 3: 백그라운드 + 반복 실행**
```bash
# 백그라운드 실행
docker run -d -it --name my-container tiatoolbox:3.11-ubuntu

# 명령 전달
docker exec my-container python3 /scripts/script1.py
docker exec my-container python3 /scripts/script2.py

# 종료
docker stop my-container
docker rm my-container
```

### 4. Dockerfile 이해

#### a. 주요 명령어

```dockerfile
FROM ubuntu:22.04
# 베이스 이미지 지정

ENV DEBIAN_FRONTEND=noninteractive
# 환경 변수 설정

RUN apt-get update && apt-get install -y python3.11
# 명령 실행 (패키지 설치 등)

ENV PATH=/venv/bin:$PATH
# 환경 변수 추가
```

#### b. 레이어 개념

Dockerfile의 각 `RUN` 명령은 **레이어**를 생성:
```
Layer 1: Ubuntu 22.04
Layer 2: + Python 3.11
Layer 3: + OpenSlide
Layer 4: + TIAToolbox
─────────────────────
Final Image (3.97GB)
```

**캐싱**:
- 재빌드 시 변경된 레이어부터만 다시 실행
- 변경 없는 레이어는 캐시 사용 → 빠름

### 5. 의존성 관리 전략

#### a. 의존성 지옥 (Dependency Hell)

```
TIAToolbox 1.6.0
  └─ zarr
      └─ numcodecs
          └─ blosc (cbuffer_sizes 필요)
              └─ Python 3.11 호환성 문제
```

#### b. 해결 전략

**전략 1**: 특정 버전 명시
```dockerfile
RUN pip install zarr==2.17.0 numcodecs==0.12.1
RUN pip install tiatoolbox
```

**전략 2**: 선행 설치 후 업그레이드
```dockerfile
RUN pip install tiatoolbox && \
    pip install --upgrade zarr numcodecs
```

**전략 3**: 검증된 이미지 사용 (채택)
```bash
docker pull ghcr.io/tissueimageanalytics/tiatoolbox:1.6.0-py3.11-ubuntu
```

---

## 어려웠던 점과 해결 과정

### 1. Docker 개념 이해

**어려움**:
- Image와 Container의 차이
- Volume Mount의 작동 원리
- `-v` 옵션의 의미

**해결**:
- LLM과의 대화를 통해 비유로 이해
  - Image = 설치 파일
  - Container = 실행 중인 프로그램
  - Volume Mount = 폴더 바로가기
- 실제로 실행해보며 개념 체득

**학습**:
- 추상적 개념은 비유와 실습으로 이해
- `docker ps`, `docker images`로 상태 확인하며 학습

### 2. zarr 의존성 문제

**어려움**:
- Dockerfile 빌드는 성공했으나 실행 시 Import 에러
- 에러가 2번 바뀜 (cbuffer_sizes → FSPathExistNotDir)
- 정확한 패키지 버전 조합을 찾기 어려움

**해결 과정**:
1. Dockerfile에 `pip install --upgrade zarr numcodecs` 추가
2. 재빌드 (약 2-5분)
3. 여전히 에러 발생
4. 시간 vs 효율성 고민
5. 공식 이미지 사용 결정

**학습**:
- 의존성 문제는 깊게 파고들수록 복잡해짐
- 때로는 "검증된 솔루션 사용"이 현명한 선택
- 재현성은 Dockerfile 직접 작성뿐 아니라 버전 명시된 공식 이미지로도 달성 가능

### 3. Platform 불일치 경고

**어려움**:
- `linux/amd64` vs `linux/arm64/v8` 경고
- 성능 영향이 있는지 불확실

**해결**:
- LLM에게 질문하여 의미 파악
- Rosetta 2 에뮬레이션으로 작동하지만 느릴 수 있음
- 학습 목적으로는 무시 가능 판단
- ARM64 네이티브 이미지 옵션 인지

**학습**:
- 경고 메시지를 항상 읽고 이해하기
- 성능과 편의성 트레이드오프 판단

### 4. 창의적 확장 과정

**과제**:
- 여러 해상도 썸네일을 하나의 비교 이미지로 만들기

**해결**:
1. 기존 `multi_resolution.py` 수정
2. matplotlib로 2×2 그리드 생성
3. 개별 썸네일과 비교 이미지를 한 스크립트에서 처리

**학습**:
- Docker 환경에서도 일반 Python 스크립트와 동일하게 개발 가능
- Volume Mount 덕분에 Mac에서 코드 수정 → Container에서 즉시 반영

---

## 결론 및 향후 계획

### 1. 3주차 성과

#### a. 기술적 성과

- Docker 핵심 개념 (Image, Container, Volume) 완전 이해
- Dockerfile 작성 및 빌드 경험
- 의존성 문제 해결 과정 경험
- 공식 이미지 활용으로 재현성 확보
- WSI 썸네일 자동 생성 파이프라인 구축
- 다중 해상도 비교 기능 구현

#### b. 학습적 성과

- Docker vs 가상환경 차이 명확히 이해
- 재현성의 다양한 구현 방법 학습
- 의존성 관리 전략 수립
- 문제 해결 시 트레이드오프 판단 능력 향상

#### c. 1-2-3주차 연계성

| 주차 | 환경 | 핵심 학습 | 도전 과제 |
|------|------|-----------|-----------|
| 1주차 | UV + OpenSlide | 로컬 환경 구축, 패치 추출 | DYLD_LIBRARY_PATH |
| 2주차 | UV + TIAToolbox | 고급 기능, 해상도 개념 | shapely 빌드 |
| 3주차 | Docker | 완전한 재현성 | zarr 의존성 |

**연계**:
- 1주차: 로컬 환경의 한계 인식
- 2주차: 의존성 문제 경험
- 3주차: Docker로 문제 해결 시도

### 2. Docker의 가치 재인식

#### a. 장점

**완벽한 재현성**:
- Dockerfile 또는 이미지 버전으로 환경 명시
- 5년 후에도 동일한 환경 재구성 가능

**환경 독립성**:
- macOS/Linux/Windows 어디서든 작동
- 시스템 라이브러리 설치 불필요

**협업 효율성**:
- 팀원에게 Image만 공유하면 끝
- "내 컴퓨터에서는 되는데" 문제 해결

#### b. 단점

**용량**:
- Image 크기가 큼 (3-5GB)
- 여러 프로젝트 사용 시 디스크 공간 필요

**복잡도**:
- 초기 학습 곡선
- Dockerfile 작성 및 디버깅 필요

**성능**:
- M1 Mac에서 amd64 이미지 사용 시 느림
- 네이티브 실행보다 2-3배 느릴 수 있음

### 3. 향후 계획

#### a. 4주차 예상 주제

**사전훈련 모델 활용**:
- Docker 환경에서 AI 모델 실행
- Patch Prediction (조직 타입 자동 분류)
- GPU 사용 (가능한 경우)

**예상 도전**:
- GPU 지원 Docker 이미지
- 모델 다운로드 및 로딩
- 대용량 WSI 처리

#### b. 추가 학습 방향

**Docker 심화**:
- Docker Compose (다중 Container 관리)
- Dockerfile 최적화 (레이어 최소화)
- .dockerignore 활용

**실전 응용**:
- 1주차 패치 추출 코드를 Docker화
- 배치 처리 (여러 WSI 자동 처리)
- REST API 서버 구축 (선택)

#### c. 장기 목표

**재현 가능한 연구 환경**:
- 모든 분석 과정을 Docker로 표준화
- GitHub에 코드 + Dockerfile 공유
- 논문 재현성 확보

**실전 배포**:
- 병원/연구소 서버에 Docker 배포
- 자동화된 WSI 분석 파이프라인 구축

---

## 참고 자료

### 1. 공식 문서

- **Docker**: https://docs.docker.com
- **TIAToolbox**: https://tia-toolbox.readthedocs.io
- **TIAToolbox GitHub**: https://github.com/TissueImageAnalytics/tiatoolbox
- **TIAToolbox Docker**: https://github.com/TissueImageAnalytics/tiatoolbox/tree/develop/docker

### 2. 사용한 Docker 이미지

- **공식 이미지**: `ghcr.io/tissueimageanalytics/tiatoolbox:1.6.0-py3.11-ubuntu`
- **베이스 이미지**: `ubuntu:22.04`

### 3. 학습 자원

- **Docker 입문**: Docker 공식 Getting Started
- **Dockerfile 작성법**: Best practices for writing Dockerfiles
- **Volume Mount**: Use bind mounts (Docker docs)

### 4. 트러블슈팅

- **zarr 에러**: TIAToolbox GitHub Issues
- **Platform 불일치**: Docker Desktop for Mac 문서
- **의존성 관리**: Python packaging best practices

---

## 부록

### A. 최종 명령어 모음

```bash
# 1. 공식 이미지 다운로드
docker pull ghcr.io/tissueimageanalytics/tiatoolbox:1.6.0-py3.11-ubuntu

# 2. 썸네일 생성
cd ~/Desktop/tiatoolbox
docker run --rm \
  -v "$(pwd)/data:/data" \
  -v "$(pwd)/results:/results" \
  -v "$(pwd)/myscripts:/scripts" \
  ghcr.io/tissueimageanalytics/tiatoolbox:1.6.0-py3.11-ubuntu \
  python3 /scripts/generate_thumbnail.py

# 3. 다중 해상도 비교
docker run --rm \
  -v "$(pwd)/data:/data" \
  -v "$(pwd)/results:/results" \
  -v "$(pwd)/myscripts:/scripts" \
  ghcr.io/tissueimageanalytics/tiatoolbox:1.6.0-py3.11-ubuntu \
  python3 /scripts/multi_resolution.py

# 4. 결과 확인
ls -lh results/
open results/*.png
```

### B. 폴더 구조 (최종)

```
~/Desktop/tiatoolbox/
├── data/
│   └── CMU-1-Small-Region.svs
├── myscripts/
│   ├── generate_thumbnail.py
│   └── multi_resolution.py
├── results/
│   ├── CMU-1-Small-Region_thumbnail.png
│   ├── thumbnail_res_0.5x.png
│   ├── thumbnail_res_1.25x.png
│   ├── thumbnail_res_2.5x.png
│   ├── thumbnail_res_5.0x.png
│   └── resolution_comparison.png
└── docker/
    └── 3.11/Ubuntu/
        └── Dockerfile
```

### C. 주요 개념 정리

**Image**: 실행 가능한 패키지 (OS + 소프트웨어)
**Container**: Image의 실행 인스턴스
**Volume Mount**: Host ↔ Container 폴더 연결
**Dockerfile**: Image 빌드 레시피
**Layer**: Dockerfile 각 명령의 결과물 (캐싱 단위)
**재현성**: 동일한 환경을 언제 어디서나 재구성 가능

### D. 의견 및 성찰

**Docker의 진정한 가치**:
- 기술적 도구를 넘어 "재현 가능한 과학"의 실천 방법
- 연구 결과의 신뢰성 확보
- 협업과 지식 공유의 장벽 제거

**학습 과정의 의미**:
- 에러는 학습의 기회
- 완벽한 해결책보다 현명한 선택이 중요
- LLM 활용으로 학습 속도 비약적 향상

**앞으로의 목표**:
- 단순히 도구를 사용하는 것을 넘어
- 재현 가능한 연구 문화를 만드는 데 기여하고 싶음
</artifact>

