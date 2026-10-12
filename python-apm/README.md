# Whatap Python APM Init Container

이 프로젝트는 Whatap Python APM 에이전트를 Kubernetes InitContainer로 사용하기 위한 Docker 이미지를 빌드하는 도구입니다.

## 📋 개요

이 도구는 지정된 버전의 Whatap Python APM 에이전트를 다운로드하고, 적절히 설정한 후 InitContainer로 사용할 수 있는 **Multi-Platform Docker 이미지**를 생성합니다.

## 🏗️ Multi-Platform 지원

이 프로젝트는 **Docker Buildx**를 사용하여 다음 플랫폼을 지원합니다:

- **linux/amd64** (Intel/AMD 64-bit)
- **linux/arm64** (ARM 64-bit, Apple Silicon 등)

## 🚀 사용법

### 전제 조건

- Docker가 설치되어 있어야 합니다
- **Docker Buildx**가 활성화되어 있어야 합니다 (Docker Desktop 19.03+ 또는 Docker CE 19.03+)
- Docker 레지스트리에 푸시할 권한이 있어야 합니다 (현재 설정: `public.ecr.aws/whatap`)

### Docker Buildx 확인

```bash
# Docker Buildx 버전 확인
docker buildx version

# 사용 가능한 플랫폼 확인
docker buildx ls
```

### 빌드 및 푸시

```bash
# 실행 권한 부여 (최초 1회)
chmod +x build.sh

# 특정 버전으로 Multi-Platform 빌드 및 푸시
./build.sh <version>
```

### 사용 예시

```bash
# 버전 1.8.5로 Multi-Platform 빌드
./build.sh 1.8.5

# 버전 1.8.4로 Multi-Platform 빌드
./build.sh 1.8.4
```

## 📁 프로젝트 구조

```
python-apm/
├── Dockerfile          # Docker 이미지 빌드 설정
├── build.sh            # Multi-Platform 빌드 및 푸시 자동화 스크립트
└── README.md           # 이 파일
```

## ⚙️ 설정

`build.sh` 파일에서 다음 설정을 수정할 수 있습니다:

```bash
# Docker 레지스트리 설정
REGISTRY="public.ecr.aws/whatap"

# 이미지 이름 설정
IMAGE_NAME="apm-init-python"

# 지원할 플랫폼 설정
PLATFORMS="linux/amd64,linux/arm64"
```

### 지원하는 레지스트리 예시

- **Docker Hub**: `docker.io/myusername`
- **AWS ECR**: `1234567890.dkr.ecr.ap-northeast-2.amazonaws.com`
- **Google GCR**: `gcr.io/my-gcp-project`

## 🔄 빌드 프로세스

스크립트는 다음 단계를 수행합니다:

1. **Docker Buildx Builder 설정**: Multi-platform 빌드를 위한 builder 생성 및 설정
2. **Multi-Platform 이미지 빌드**: 지정된 플랫폼들에 대해 동시에 이미지 생성
3. **자동 푸시**: 빌드와 동시에 레지스트리에 푸시
   - `{REGISTRY}/{IMAGE_NAME}:{VERSION}` 형태로 푸시
   - `{REGISTRY}/{IMAGE_NAME}:latest` 형태로 푸시

## 🐳 Dockerfile 동작

Dockerfile은 다음 작업을 수행합니다:

1. **에이전트 다운로드**: PyPI에서 지정된 버전의 `whatap-python` 배포물을 내려받아 `whatap/` 패키지를 번들링합니다.
2. **LLM Go 모듈 다운로드**: 공식 `repo.whatap.io` 배포물을 빌드 시 내려받고, `bundle_llm.py`에 고정된 SHA-256과 Linux ELF 아키텍처를 검증합니다. Linux AMD64·ARM64 실행파일만 포함합니다.
3. **InitContainer 스크립트**: 패키지를 `/whatap-agent/whatap/`으로, LLM 실행파일을 `/whatap-agent/linux/{amd64,arm64}/whatap_python`으로 복사합니다. LLM 파일은 기존 패키지 존재 여부와 무관하게 복사하고 누락·복사 실패를 숨기지 않습니다.
4. **자동 시작**: Operator가 설정한 `PYTHONPATH`의 `sitecustomize.py`로 SDK가 기동합니다. 일반 APM과 LLM의 활성화·연결 설정은 서로 별개입니다.

### LLM 자동 주입 (SDK 2.2.1 계약)

이 이미지에는 LLM Go 모듈이 포함되지만 **LLM을 자동으로 활성화하거나 기존 APM 액세스 키를 재사용하지 않습니다.** 일반 APM 실행파일 `/whatap-agent/whatap_python`도 덮어쓰지 않습니다. Pod 기동 시에는 별도의 다운로드가 필요하지 않습니다.

**실제 배포물 기준 경로:** SDK 2.2.1과 공식 tar는 `$WHATAP_HOME/linux/<arch>/whatap_python`을 사용합니다. `$WHATAP_HOME/whatap-python-llm/` 아래에만 압축을 풀면 이 SDK가 찾지 못합니다. 공식 URL은 버전 없는 주소이므로 내용이 변경되면 빌드를 실패시키며, 새 배포물의 경로·플랫폼을 검증한 뒤 `bundle_llm.py`의 해시를 갱신해야 합니다.

LLM을 사용할 대상에만 다음 설정을 **기존 APM 설정에 추가**합니다. Operator의 대상별 `config.mode: custom` 및 `config.configMapRef`로 기존과 같이 `whatap.conf`를 전달할 수 있습니다. 실제 키는 예제나 저장소에 기록하지 마세요.

```properties
llm_enabled=true
llm_accesskey=<LLM_PROJECT_ACCESS_KEY>
llm.whatap.server.host=<LLM_COLLECTOR_HOST>
counter_thread_enabled=true
```

- SDK 2.2.1은 `llm_accesskey`를 읽습니다. `llm_license`만 설정하면 LLM이 비활성화됩니다.
- init의 기존 `whatap_code_start=true`, `apm_enabled=true` 정책은 유지합니다. 별도의 `whatap-llm-setting-config` 명령은 APM을 비활성화하므로 APM·LLM 동시 계측을 위해 여기에서 호출하지 않습니다. 이 변경은 LLM-only 모드의 정책 변경이 아닙니다.
- **앱 Python 의존성은 별도입니다.** `datasketches>=5.2.0`, `genai-prices` 및 전이 의존성을 앱 이미지의 실제 Python 버전·아키텍처에 맞춰 설치해야 합니다. init 이미지의 Python 3.10 네이티브 라이브러리를 다른 Python ABI에 복사하지 않습니다. 누락 시 분위수·비용 등 일부 데이터가 빠질 수 있으며, Go 프로세스 기동만으로 전체 LLM 수집이 검증되지는 않습니다.
- 승인된 새 init 이미지 참조로 변경한 뒤 해당 애플리케이션 Pod를 재생성해야 적용됩니다. 이미지 빌드·게시와 고객 Pod 적용은 별개입니다. 기존 공개 태그를 덮어쓰지 마세요.

회귀 검증:

```bash
python3 -m unittest discover -s tests -v
# 네트워크 차단·비루트 컨테이너 안에서 실행하는 추가 검증:
# tests/image_smoke.py — 실제 sitecustomize → SDK → APM/LLM Go 기동 확인
```

`image_smoke.py`는 가짜 키와 loopback 주소만 사용하며, 실제 수집 서버 전송이나 LLM 토큰·비용 데이터 수집을 검증하지 않습니다.

## 🎯 Kubernetes에서 사용

생성된 Multi-Platform 이미지는 Kubernetes에서 InitContainer로 다음과 같이 사용할 수 있습니다:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-python-app
spec:
  selector:
    matchLabels:
      app: my-python-app
  template:
    metadata:
      labels:
        app: my-python-app
    spec:
      initContainers:
      - name: whatap-agent
        image: public.ecr.aws/whatap/apm-init-python:1.8.5
        volumeMounts:
        - name: whatap-agent
          mountPath: /whatap-agent
      containers:
      - name: my-app
        image: my-python-app:latest
        volumeMounts:
        - name: whatap-agent
          mountPath: /whatap
        env:
        - name: PYTHONPATH
          value: "/whatap/lib:$PYTHONPATH"
        - name: WHATAP_HOME
          value: "/whatap"
        - name: WHATAP_CONFIG
          value: "/whatap/whatap.conf"
      volumes:
      - name: whatap-agent
        emptyDir: {}
```

## 🐍 Python 애플리케이션 설정

### 자동 계측 (권장)

InitContainer가 설치한 에이전트는 `sitecustomize.py`를 통해 자동으로 활성화됩니다:

```python
# 애플리케이션 코드에 추가 설정 불필요
# sitecustomize.py가 자동으로 에이전트를 초기화합니다
```

### 수동 계측

필요한 경우 수동으로 에이전트를 초기화할 수 있습니다:

```python
import whatap
whatap.agent()

# 애플리케이션 코드
```

### 설정 파일

`whatap.conf` 파일을 통해 에이전트를 설정할 수 있습니다:

```ini
license=YOUR_LICENSE_KEY
whatap.server.host=13.124.11.223/13.209.172.35
app_name=my-python-app
app_process_name=my-python-app
```

## 🛠️ 문제 해결

### 권한 오류
```bash
chmod +x build.sh
```

### Docker Buildx 설정
```bash
# Docker Buildx 활성화 (필요한 경우)
docker buildx install

# 새로운 builder 생성
docker buildx create --name mybuilder --use --bootstrap
```

### Docker 레지스트리 로그인
```bash
# AWS ECR 예시
aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws

# Docker Hub 예시
docker login
```

### 버전 확인
사용 가능한 Whatap Python 에이전트 버전은 [PyPI](https://pypi.org/project/whatap-python/#history)에서 확인할 수 있습니다.

### Python 경로 문제
```bash
# 컨테이너 내에서 Python 경로 확인
python -c "import sys; print(sys.path)"

# PYTHONPATH 환경변수 설정 확인
echo $PYTHONPATH
```

## 🚀 Multi-Platform 빌드의 장점

- **ARM 기반 시스템 지원**: Apple Silicon Mac, AWS Graviton 인스턴스 등에서 네이티브 성능
- **자동 플랫폼 선택**: Kubernetes가 노드 아키텍처에 맞는 이미지를 자동으로 선택
- **단일 이미지 태그**: 하나의 태그로 모든 플랫폼 지원
- **향상된 호환성**: 다양한 클라우드 환경에서 일관된 동작

## 📝 참고사항

- 빌드 시 인터넷 연결이 필요합니다 (에이전트 다운로드)
- Multi-platform 빌드는 단일 플랫폼 빌드보다 시간이 더 걸릴 수 있습니다
- 생성된 이미지는 플랫폼당 약 150MB 크기입니다
- 에이전트 버전은 Whatap 공식 릴리스 버전을 사용해야 합니다
- Docker Buildx는 QEMU 에뮬레이션을 사용하여 다른 아키텍처를 빌드합니다
- Python 3.6 이상이 필요합니다

## 🔍 빌드 로그 예시

```
🚀 Whatap Python Agent 이미지 빌드 및 푸시 시작 (Multi-Platform)
--------------------------------------------------
  - Agent Version : 1.8.5
  - Image Name    : public.ecr.aws/whatap/apm-init-python
  - Version Tag   : public.ecr.aws/whatap/apm-init-python:1.8.5
  - Latest Tag    : public.ecr.aws/whatap/apm-init-python:latest
  - Platforms     : linux/amd64,linux/arm64
==================================================

▶️ 1. Docker buildx builder 설정을 확인합니다...
   새로운 buildx builder를 생성합니다...
✅ Builder 설정 완료!

▶️ 2. Multi-platform 이미지 빌드 및 푸시를 시작합니다...
   지원 플랫폼: linux/amd64,linux/arm64
✅ Multi-platform 빌드 및 푸시 완료!

🎉 모든 작업이 성공적으로 완료되었습니다.
📋 빌드된 이미지:
   - public.ecr.aws/whatap/apm-init-python:1.8.5 (linux/amd64,linux/arm64)
   - public.ecr.aws/whatap/apm-init-python:latest (linux/amd64,linux/arm64)
```

## 🔗 관련 링크

- [Whatap Python APM 공식 문서](https://docs.whatap.io/python/introduction)
- [PyPI - whatap-python](https://pypi.org/project/whatap-python/)
- [Docker Buildx 문서](https://docs.docker.com/buildx/)