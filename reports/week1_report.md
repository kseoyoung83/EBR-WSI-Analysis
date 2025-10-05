<artifact identifier="week1-report-markdown" type="text/markdown" title="1주차 OpenSlide 실습 레포트">
# Evolution of Biomedical Research

의과대학 의예과 2024191115 김서영

## ▼ 1주차 실습

## 실습 개요

### 1. 실습 목표
- OpenSlide를 이용한 WSI(Whole Slide Image) 파일 처리
- 그리드 방식 패치 추출 파이프라인 구축
- 배경 자동 제거 기능 구현
- Claude Code를 활용한 AI 기반 코드 생성 및 디버깅

### 2. 실습 환경
- **운영체제**: macOS (Apple M1 Pro)
- **개발 도구**: VS Code, Claude Code Extension
- **패키지 관리자**: UV (Rust 기반, Python 3.11)
- **주요 라이브러리**:
  - openslide-python 1.3.1
  - pillow 11.0.0
  - numpy 2.1.3
  - opencv-python 4.10.0.84

### 3. 데이터
- **파일명**: CMU-1-Small-Region.svs
- **크기**: 1.8MB
- **출처**: TIAToolbox 샘플 데이터
- **포맷**: Aperio SVS (병리 슬라이드 이미지)

---

## 실습 과정

### 1. 환경 구축

#### a. Step 1: 작업 폴더 생성

```bash
mkdir -p ~/Desktop/wsi_processing/{data,src,results,docs}
cd ~/Desktop/wsi_processing
code .
```

**폴더 구조**:
```
wsi_processing/
├── data/       # WSI 파일 저장
├── src/        # 소스 코드
├── results/    # 결과물 저장
└── docs/       # 문서
```

#### b. Step 2: Homebrew로 OpenSlide 설치

```bash
# 설치
brew install openslide

# 확인
brew list openslide
```

**출력**:
```
/opt/homebrew/Cellar/openslide/4.0.0/bin/openslide-quickhash1sum
/opt/homebrew/Cellar/openslide/4.0.0/bin/openslide-show-properties
/opt/homebrew/Cellar/openslide/4.0.0/lib/libopenslide.1.dylib
...
```

#### c. Step 3: UV 설치 및 프로젝트 초기화

```bash
# UV 설치
curl -LsSf https://astral.sh/uv/install.sh | sh

# 터미널 재시작 후
uv --version
```

**출력**:
```
uv 0.8.22 (ade2bdbd2 2025-09-23)
```

**프로젝트 초기화**:
```bash
uv init
uv venv --python 3.11
source .venv/bin/activate
```

**프롬프트 변환**:
```bash
(base) ksy@Geonungui-MacBookPro-2 wsi_processing %
↓
(wsi_processing) (base) ksy@Geonungui-MacBookPro-2 wsi_processing %
```

#### d. Step 4: Python 버전 요구사항 수정

**문제 발생**:
```
warning: The requested interpreter resolved to Python 3.11.13, 
which is incompatible with the project's Python requirement: `>=3.13`
```

**해결**:
```bash
sed -i '' 's/>=3.13/>=3.11/' pyproject.toml
rm -rf .venv
uv venv --python 3.11
source .venv/bin/activate
```

**이유**: 향후 Docker 환경(Python 3.11)과의 일치성을 위해 3.11 버전 사용 결정

#### e. Step 5: 패키지 설치

```bash
uv add openslide-python pillow numpy opencv-python tifffile matplotlib
```

**출력**:
```
Resolved 15 packages
Prepared 8 packages
Installed 14 packages
```

---

### 2. 시행착오 및 해결 과정

#### a. 문제 1: OpenSlide 라이브러리 연동 실패

##### i. 에러 메시지

```bash
python3 -c "import openslide; print('Success')"
```

```
OSError: dlopen(libopenslide.1.dylib, 0x0006): tried: 'libopenslide.1.dylib' (no such file)
...
ModuleNotFoundError: Couldn't locate OpenSlide dylib.
```

##### ii. 원인 분석

- openslide-python (Python 패키지)는 설치됨
- OpenSlide 시스템 라이브러리는 설치되었으나 Python이 찾지 못함
- macOS의 동적 라이브러리 검색 경로에 `/opt/homebrew/opt/openslide/lib` 가 포함되지 않음

##### iii. 해결 과정

**1. OpenSlide 설치 확인**:
```bash
brew list openslide
# 출력: 설치되어 있음을 확인
```

**2. 설치 경로 확인**:
```bash
brew --prefix openslide
# 출력: /opt/homebrew/opt/openslide
```

**3. 환경 변수 설정**:
```bash
export DYLD_LIBRARY_PATH=/opt/homebrew/opt/openslide/lib:$DYLD_LIBRARY_PATH
```

**4. 재시도**:
```bash
python3 -c "import openslide; import numpy; import PIL; print('All packages imported successfully!')"
# 출력: All packages imported successfully!
```

**5. 영구 설정**:
```bash
echo 'export DYLD_LIBRARY_PATH=/opt/homebrew/opt/openslide/lib:$DYLD_LIBRARY_PATH' >> ~/.zshrc
source ~/.zshrc
```

##### iv. 학습 내용

- Python 패키지와 시스템 라이브러리의 차이
- openslide-python은 인터페이스일 뿐, 실제 기능은 시스템 라이브러리에 의존
- macOS의 동적 라이브러리 검색 메커니즘 (DYLD_LIBRARY_PATH)

---

### 3. WSI 샘플 다운로드

```bash
cd data
curl -L -o CMU-1-Small-Region.svs "https://tiatoolbox.dcs.warwick.ac.uk/sample_wsis/CMU-1-Small-Region.svs"
```

**출력**:
```
% Total % Received % Xferd Average Speed Time Time Time Current
                                Dload Upload Total Spent Left Speed
100 1893k 100 1893k 0 0 441k 0 0:00:04 0:00:04 --:--:-- 503k
```

**확인**:
```bash
ls -lh CMU-1-Small-Region.svs
# 출력: -rw-r--r--@ 1 ksy staff 1.8M Oct 3 17:15 CMU-1-Small-Region.svs
```

---

### 4. Claude Code를 이용한 코드 생성

#### a. 기본 패치 추출

**프롬프트**:
```
💡 WSI 파일에서 256x256 픽셀 패치를 그리드 방식으로 추출하는 Python 스크립트를 작성해줘.

요구사항:
- OpenSlide 사용
- 클래스명: WSIPatchExtractor
- 메서드: extract_patches_grid(patch_size=256, overlap=0, level=0)
- 입력: data/CMU-1-Small-Region.svs
- 출력: results/patches/ 폴더에 PNG 파일로 저장
- 각 패치 파일명: patch_x{x좌표}_y{y좌표}.png
```

**생성된 코드 (main.py - 초기 버전)**:

```python
import openslide
from pathlib import Path
from PIL import Image

class WSIPatchExtractor:
    def __init__(self, wsi_path):
        self.wsi_path = wsi_path
        self.slide = openslide.OpenSlide(wsi_path)
    
    def extract_patches_grid(self, patch_size=256, overlap=0, level=0):
        output_dir = Path("results/patches")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        level_dims = self.slide.level_dimensions[level]
        width, height = level_dims
        
        step = patch_size - overlap
        
        patches = []
        
        for y in range(0, height - patch_size + 1, step):
            for x in range(0, width - patch_size + 1, step):
                patch = self.slide.read_region(
                    (x, y), level, (patch_size, patch_size)
                )
                patch = patch.convert("RGB")
                
                filename = f"patch_x{x}_y{y}.png"
                filepath = output_dir / filename
                patch.save(filepath)
                
                patches.append({
                    'x': x,
                    'y': y,
                    'filename': filename,
                    'filepath': str(filepath)
                })
        
        print(f"Extracted {len(patches)} patches to {output_dir}")
        return patches
    
    def close(self):
        self.slide.close()

def main():
    wsi_path = "data/CMU-1-Small-Region.svs"
    
    extractor = WSIPatchExtractor(wsi_path)
    patches = extractor.extract_patches_grid(patch_size=256, overlap=0, level=0)
    extractor.close()

if __name__ == "__main__":
    main()
```

**실행**:
```bash
python main.py
# 출력: Extracted 88 patches to results/patches
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

---

### 5. 배경 제거 기능 추가

#### a. 개선 요구 사항

기본 패치 추출 결과를 확인한 결과, 조직이 없는 빈 배경 패치도 다수 포함되어 있음을 발견. 실제 분석에는 조직 영역만 필요하므로 배경 자동 제거 기능 추가 결정.

**프롬프트**:
```
💡 main.py를 수정해주라. 배경제거 기능을 추가하고 싶어.

요구사항:
1. extract_patches_grid 메서드에 tissue_threshold 파라미터 추가 (기본값 0.3)
2. 각 패치에서 조직 영역 비율 계산
3. 조직 비율이 threshold 미만이면 해당 패치 건너뛰기
4. 조직/배경 판단 로직:
   - Grayscale 변환
   - 임계값 적용 (밝기 < 200인 픽셀을 조직으로 간주)
   - 조직 픽셀 비율 계산
5. 저장된 패치 수와 건너뛴 패치 수를 출력
6. 배경을 포함한 패치 폴더와, 배경을 제외한 조직만 있는 폴더 이렇게 두 개를 결과물 만들기
```

#### b. 수정된 코드 (main.py - 최종 버전)

```python
import openslide
from pathlib import Path
from PIL import Image
import numpy as np

class WSIPatchExtractor:
    def __init__(self, wsi_path):
        self.wsi_path = wsi_path
        self.slide = openslide.OpenSlide(wsi_path)
    
    def _calculate_tissue_ratio(self, patch, brightness_threshold=200):
        """Calculate tissue ratio in a patch."""
        gray = patch.convert('L')
        gray_array = np.array(gray)
        
        tissue_pixels = np.sum(gray_array < brightness_threshold)
        total_pixels = gray_array.size
        
        tissue_ratio = tissue_pixels / total_pixels
        return tissue_ratio
    
    def extract_patches_grid(self, patch_size=256, overlap=0, level=0, tissue_threshold=0.3):
        # Create output directories
        all_patches_dir = Path("results/patches/all")
        tissue_patches_dir = Path("results/patches/tissue_only")
        all_patches_dir.mkdir(parents=True, exist_ok=True)
        tissue_patches_dir.mkdir(parents=True, exist_ok=True)
        
        level_dims = self.slide.level_dimensions[level]
        width, height = level_dims
        
        step = patch_size - overlap
        
        all_patches = []
        tissue_patches = []
        skipped_count = 0
        
        for y in range(0, height - patch_size + 1, step):
            for x in range(0, width - patch_size + 1, step):
                patch = self.slide.read_region(
                    (x, y), level, (patch_size, patch_size)
                )
                patch = patch.convert("RGB")
                
                # Calculate tissue ratio
                tissue_ratio = self._calculate_tissue_ratio(patch)
                
                filename = f"patch_x{x}_y{y}.png"
                
                # Save to all patches folder
                all_filepath = all_patches_dir / filename
                patch.save(all_filepath)
                
                all_patches.append({
                    'x': x,
                    'y': y,
                    'filename': filename,
                    'filepath': str(all_filepath),
                    'tissue_ratio': tissue_ratio
                })
                
                # Save to tissue-only folder if threshold is met
                if tissue_ratio >= tissue_threshold:
                    tissue_filepath = tissue_patches_dir / filename
                    patch.save(tissue_filepath)
                    
                    tissue_patches.append({
                        'x': x,
                        'y': y,
                        'filename': filename,
                        'filepath': str(tissue_filepath),
                        'tissue_ratio': tissue_ratio
                    })
                else:
                    skipped_count += 1
        
        print(f"Total patches extracted: {len(all_patches)}")
        print(f"Tissue patches saved: {len(tissue_patches)}")
        print(f"Background patches skipped: {skipped_count}")
        print(f"All patches saved to: {all_patches_dir}")
        print(f"Tissue-only patches saved to: {tissue_patches_dir}")
        
        return {
            'all_patches': all_patches,
            'tissue_patches': tissue_patches,
            'skipped_count': skipped_count
        }
    
    def close(self):
        self.slide.close()

def main():
    wsi_path = "data/CMU-1-Small-Region.svs"
    
    extractor = WSIPatchExtractor(wsi_path)
    result = extractor.extract_patches_grid(
        patch_size=256, 
        overlap=0, 
        level=0, 
        tissue_threshold=0.3
    )
    extractor.close()

if __name__ == "__main__":
    main()
```

#### c. 실행 결과

```bash
rm -rf results/patches
python main.py
```

**출력**:
```
Total patches extracted: 88
Tissue patches saved: 39
Background patches skipped: 49
All patches saved to: results/patches/all
Tissue-only patches saved to: results/patches/tissue_only
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

---

## 최종 결과물

### 1. 정량적 결과

| 항목 | 값 |
|------|-----|
| WSI 파일 크기 | 1.8MB |
| 전체 추출 패치 수 | 88개 |
| 조직 포함 패치 수 | 39개 (44.3%) |
| 배경 패치 수 | 49개 (55.7%) |
| 패치 크기 | 256 × 256 픽셀 |
| 해상도 레벨 | 0 (최고) |
| 조직 임계값 | 30% |

### 2. 정성적 결과

#### a. 전체 패치 (all)
- 슬라이드의 모든 영역을 포함
- 흰색 배경 영역 다수 포함
- 조직 경계부 패치 포함

#### b. 조직 패치 (tissue_only)
- 분홍-보라색 조직 영역만 선별
- H&E 염색된 병리 조직 구조 확인 가능

### 3. 시각적 결과

tissue_only 폴더의 패치들은 모두 분홍-보라색 조직 영역을 포함하며, 흰색 배경이 효과적으로 제거되었음을 확인할 수 있다. 각 패치는 H&E 염색된 병리 조직의 특징을 명확히 보여준다.

**39개의 조직 패치 모두에서 다음과 같은 공통 특징이 관찰되었다**:
- 배경(흰색 영역)이 30% 미만으로 제거됨
- 분홍색 및 보라색 염색 영역이 명확히 관찰됨
- 조직의 형태학적 구조가 식별 가능한 수준으로 유지됨

구체적인 조직학적 구조 분석(세포 타입, 조직 분류 등)은 병리학 전문가의 검토가 필요하므로 본 레포트에서는 생략한다.

---

## 핵심 학습 내용

### 1. 기술적 학습

#### a. Python 패키지 vs 시스템 라이브러리

**openslide-python**: Python 인터페이스 (래퍼)
**OpenSlide**: 실제 WSI 처리 기능을 수행하는 C 라이브러리

두 계층 간 연결이 필수적이며, 환경 변수를 통한 라이브러리 경로 설정 필요

#### b. RGBA vs RGB

- **OpenSlide는 RGBA 반환**: Alpha 채널로 배경 투명도 표현
- **PIL의 .convert("RGB")**: Alpha 채널 제거, 투명 영역 흰색 처리
- 병리 이미지 분석에서는 RGB로 변환하여 처리하는 것이 일반적

#### c. 조직/배경 분리 알고리즘

```python
# Grayscale 변환 후 밝기 기반 판단
tissue_mask = gray_array < 200  # 어두운 픽셀 = 조직
tissue_ratio = np.sum(tissue_mask) / total_pixels
```

**원리**:
- 조직: H&E 염색으로 분홍-보라색 (밝기 낮음)
- 배경: 염색 안 됨, 흰색 (밝기 높음)

### 2. 환경 관리 학습

#### a. UV vs Conda

**UV**:
- Rust 기반, 빠른 속도 (수 초)
- PyPI 직접 사용
- Python 패키지만 관리

**Conda**:
- Python 기반, 느림 (수 분)
- 별도 저장소
- 시스템 라이브러리까지 관리 가능

프로젝트 특성에 맞는 도구 선택 중요

#### b. 가상환경의 필요성

- 프로젝트별 독립된 Python 버전 및 패키지 관리
- 의존성 충돌 방지
- 재현 가능한 환경 구축

### 3. AI 도구 활용 학습

#### a. Claude Code 활용법

1. **명확한 요구사항 전달**: 클래스명, 메서드명, 입출력 경로 구체화
2. **단계적 개선**: 기본 기능 → 고급 기능 순차적 구현
3. **에러 피드백**: 에러 메시지 전달 시 해결 방안 제시 받음

#### b. 효과적인 프롬프트 작성

- 구체적 기능 명시
- 입출력 형식 정의
- 파일 구조 제시
- 예상 결과 설명

---

## 어려웠던 점과 해결 과정

### 1. OpenSlide 라이브러리 연동

**문제**:
- openslide-python 설치 완료했으나 import 실패
- 에러 메시지가 길고 복잡하여 원인 파악 어려움

**해결 과정**:
1. 에러 메시지 분석: "libopenslide.1.dylib" 찾지 못함
2. Homebrew 설치 확인: 라이브러리는 존재함
3. 검색 경로 문제로 판단
4. DYLD_LIBRARY_PATH 설정으로 해결

**학습**:
- Python 패키지와 시스템 라이브러리의 이중 구조 이해
- macOS의 동적 라이브러리 검색 메커니즘 학습
- 환경 변수의 중요성 인식

### 2. Python 버전 호환성

**문제**:
- UV가 자동으로 Python 3.13 요구
- 실습 가이드는 Python 3.11 권장 (Docker 환경 고려)

**해결**:
- pyproject.toml 수정으로 버전 요구사항 변경
- 가상환경 재생성

**학습**:
- 프로젝트 메타데이터 파일(pyproject.toml)의 역할
- 장기적 관점에서 환경 일치성의 중요성

### 3. 배경 제거 임계값 설정

**문제**:
- 조직 임계값(30%)이 적절한지 판단 어려움

**향후 개선 방안**:
- 다양한 임계값(10%, 30%, 50%) 테스트
- 결과물 육안 확인 후 최적값 결정
- WSI 파일마다 최적값이 다를 수 있음

---

## 결론 및 향후 계획

### 1. 실습 성과

#### a. 환경 구축
macOS M1 환경에서 WSI 분석 환경 성공적 구축

#### b. 코드 구현
객체지향 설계로 재사용 가능한 코드 작성

#### c. 문제 해결
시스템 라이브러리 연동 문제 독립적으로 해결

#### d. 결과물
39개의 고해상도 조직 패치 추출

### 2. 추가 개선 방향

#### a. 기능 개선
- Overlap 기능 활성화 (overlap=64로 패치 수 증가)
- 다양한 해상도 레벨 비교 (level=0, 1, 2)
- 조직 임계값 동적 조정

#### b. 분석 확장
- 패치별 조직 타입 분류
- 색상 히스토그램 분석
- 통계적 특성 추출

### 3. 차주 학습 계획

#### 2주차: Google Colab + TIAToolbox
- GPU 환경에서 고급 기능 학습
- 썸네일 생성, 염색 정규화
- 사전훈련 모델 활용

#### 3주차: Docker 환경 구축
- 재현 가능한 컨테이너 환경
- 1주차 코드의 Docker화
- 환경 이식성 확보

---

## 참고 자료

### 1. 공식 문서
- **OpenSlide**: https://openslide.org
- **OpenSlide Python**: https://openslide.org/api/python/
- **UV**: https://github.com/astral-sh/uv
- **TIAToolbox**: https://tia-toolbox.readthedocs.io

### 2. 샘플 데이터
- **TIAToolbox Sample WSIs**: https://tiatoolbox.dcs.warwick.ac.uk/sample_wsis/

### 3. 사용한 AI 도구
- **Claude Code for VS Code**
- **Anthropic Claude** (대화형 지원)

---

## 부록

### A. 환경 재구축 체크리스트

```bash
# 1. 작업 폴더 생성
mkdir -p ~/Desktop/wsi_processing/{data,src,results,docs}
cd ~/Desktop/wsi_processing

# 2. OpenSlide 설치
brew install openslide

# 3. UV 설치
curl -LsSf https://astral.sh/uv/install.sh | sh
# 터미널 재시작 필요

# 4. 프로젝트 초기화
uv init
sed -i '' 's/>=3.13/>=3.11/' pyproject.toml

# 5. 가상환경 생성
uv venv --python 3.11
source .venv/bin/activate

# 6. 패키지 설치
uv add openslide-python pillow numpy opencv-python

# 7. 환경 변수 설정
echo 'export DYLD_LIBRARY_PATH=/opt/homebrew/opt/openslide/lib:$DYLD_LIBRARY_PATH' >> ~/.zshrc
source ~/.zshrc

# 8. 설치 확인
python -c "import openslide; import numpy; import PIL; print('All packages imported successfully!')"
```

### B. 파일 구조

```
wsi_processing/
├── data/
│   └── CMU-1-Small-Region.svs
├── src/
│   └── main.py
├── results/
│   └── patches/
│       ├── all/              # 88개 패치
│       └── tissue_only/      # 39개 패치
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
python src/main.py

# 결과 확인
ls -lh results/patches/all/
ls -lh results/patches/tissue_only/
open results/patches/tissue_only/*.png
```
</artifact>

