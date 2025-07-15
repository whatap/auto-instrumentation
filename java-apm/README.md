# Whatap Java APM Init Container

이 프로젝트는 Whatap Java APM 에이전트를 Kubernetes InitContainer로 사용하기 위한 Docker 이미지를 빌드하는 도구입니다.

## 📋 개요

이 도구는 지정된 버전의 Whatap Java APM 에이전트를 다운로드하고, 적절히 설정한 후 InitContainer로 사용할 수 있는 **Multi-Platform Docker 이미지**를 생성합니다.

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
# 버전 2.2.61로 Multi-Platform 빌드
./build.sh 2.2.61

# 버전 2.2.58로 Multi-Platform 빌드
./build.sh 2.2.58
```

## 📁 프로젝트 구조

```
java-apm/
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
IMAGE_NAME="apm-init-java"

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

1. **에이전트 다운로드**: Maven 저장소에서 지정된 버전의 에이전트 다운로드
2. **공식 Rename 수행**: Whatap 공식 방법으로 에이전트 파일명 변경
3. **불필요한 파일 삭제**: 원본 에이전트 파일 삭제
4. **InitContainer 설정**: 에이전트를 `/whatap-agent/` 디렉토리로 복사하는 명령 설정

## 🎯 Kubernetes에서 사용

생성된 Multi-Platform 이미지는 Kubernetes에서 InitContainer로 다음과 같이 사용할 수 있습니다:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-java-app
spec:
  selector:
    matchLabels:
      app: my-java-app
  template:
    metadata:
      labels:
        app: my-java-app
    spec:
      initContainers:
      - name: whatap-agent
        image: public.ecr.aws/whatap/apm-init-java:2.2.61
        volumeMounts:
        - name: whatap-agent
          mountPath: /whatap-agent
      containers:
      - name: my-app
        image: my-java-app:latest
        volumeMounts:
        - name: whatap-agent
          mountPath: /whatap
        env:
        - name: JAVA_OPTS
          value: "-javaagent:/whatap/whatap.agent.java.jar"
      volumes:
      - name: whatap-agent
        emptyDir: {}
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
사용 가능한 Whatap 에이전트 버전은 [Maven 저장소](https://repo.whatap.io/maven/io/whatap/whatap.agent/)에서 확인할 수 있습니다.


## 📝 참고사항

- 빌드 시 인터넷 연결이 필요합니다 (에이전트 다운로드)
- Multi-platform 빌드는 단일 플랫폼 빌드보다 시간이 더 걸릴 수 있습니다
- 생성된 이미지는 플랫폼당 약 200MB 크기입니다
- 에이전트 버전은 Whatap 공식 릴리스 버전을 사용해야 합니다
- Docker Buildx는 QEMU 에뮬레이션을 사용하여 다른 아키텍처를 빌드합니다

## 🔍 빌드 로그 예시

```
🚀 Whatap Agent 이미지 빌드 및 푸시 시작 (Multi-Platform)
--------------------------------------------------
  - Agent Version : 2.2.61
  - Image Name    : public.ecr.aws/whatap/apm-init-java
  - Version Tag   : public.ecr.aws/whatap/apm-init-java:2.2.61
  - Latest Tag    : public.ecr.aws/whatap/apm-init-java:latest
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
   - public.ecr.aws/whatap/apm-init-java:2.2.61 (linux/amd64,linux/arm64)
   - public.ecr.aws/whatap/apm-init-java:latest (linux/amd64,linux/arm64)
```
