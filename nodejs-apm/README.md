# Whatap Node.js APM Init Container

이 프로젝트는 Whatap Node.js APM 에이전트를 Kubernetes InitContainer로 사용하기 위한 Docker 이미지를 빌드하는 도구입니다.

## 개요

이 도구는 지정된 버전의 Whatap Node.js APM 에이전트를 npm으로 설치하고, 적절히 설정한 후 InitContainer로 사용할 수 있는 **Multi-Platform Docker 이미지**를 생성합니다.

## Multi-Platform 지원

이 프로젝트는 **Docker Buildx**를 사용하여 다음 플랫폼을 지원합니다:

- **linux/amd64** (Intel/AMD 64-bit)
- **linux/arm64** (ARM 64-bit, Apple Silicon 등)

## 사용법

### 전제 조건

- Docker가 설치되어 있어야 합니다
- **Docker Buildx**가 활성화되어 있어야 합니다 (Docker Desktop 19.03+ 또는 Docker CE 19.03+)
- Docker 레지스트리에 푸시할 권한이 있어야 합니다 (현재 설정: `public.ecr.aws/whatap`)

### 빌드 및 푸시

```bash
# 실행 권한 부여 (최초 1회)
chmod +x build.sh

# 특정 버전으로 Multi-Platform 빌드 및 푸시
./build.sh <version>

# 예시
./build.sh 0.4.98
```

## 프로젝트 구조

```
nodejs-apm/
├── Dockerfile          # Multi-stage Docker 이미지 빌드 설정
├── build.sh            # Multi-Platform 빌드 및 푸시 자동화 스크립트
└── README.md           # 이 파일
```

## 설정

`build.sh` 파일에서 다음 설정을 수정할 수 있습니다:

```bash
# Docker 레지스트리 설정
REGISTRY="public.ecr.aws/whatap"

# 이미지 이름 설정
IMAGE_NAME="apm-init-nodejs"

# 지원할 플랫폼 설정
PLATFORMS="linux/amd64,linux/arm64"
```

## Dockerfile 동작

Multi-stage 빌드를 사용하여 최종 이미지 크기를 최소화합니다:

### Stage 1: Builder (`node:20-alpine`)
1. `npm install whatap@{version}`으로 에이전트 및 의존성 패키지 설치
2. `node_modules/` 디렉토리에 다음 패키지가 포함됩니다:
   - `whatap` (에이전트 본체)
   - `graceful-fs`, `long`, `proper-lockfile`, `retry`, `signal-exit`, `uuid` 등 의존성

### Stage 2: Runtime (`alpine:3.20`)
1. Builder에서 `node_modules/`를 `/opt/whatap-agent-dist/node_modules/`로 복사
2. `init.sh` 스크립트 생성
3. Node.js 런타임이 포함되지 않아 이미지가 경량화됩니다

### InitContainer 실행 시 (`init.sh`)
1. `/opt/whatap-agent-dist/node_modules/` → `/whatap-agent/node_modules/`로 복사 (공유 볼륨)
2. 환경변수 기반으로 `/whatap-agent/whatap.conf` 생성
3. 권한 설정

## Kubernetes에서의 동작 방식

### 볼륨 공유 구조

```
EmptyDir 볼륨 (whatap-agent-volume)
├── whatap.conf              ← init.sh가 환경변수로 생성
└── node_modules/            ← init.sh가 복사
    ├── whatap/
    ├── graceful-fs/
    ├── long/
    ├── proper-lockfile/
    ├── retry/
    ├── signal-exit/
    └── uuid/

Init Container:    마운트 → /whatap-agent (파일 생성)
App Container:     마운트 → /whatap-agent (같은 볼륨 공유)
```

### Operator가 앱 컨테이너에 주입하는 환경변수

| 환경변수 | 값 | 설명 |
|---|---|---|
| `WHATAP_HOME` | `/whatap-agent` | whatap.conf 위치 (`/whatap-agent/whatap.conf`) |
| `NODE_PATH` | `/whatap-agent/node_modules` | Node.js 모듈 검색 경로 추가 |
| `NODE_OPTIONS` | `-r whatap` | 앱 시작 시 whatap 에이전트 자동 로드 |

### 모듈 로딩 흐름

```
1. 앱 컨테이너 시작
2. NODE_OPTIONS=-r whatap → require('whatap') 자동 실행
3. NODE_PATH=/whatap-agent/node_modules → 해당 경로에서 whatap 모듈 탐색
4. whatap 에이전트가 WHATAP_HOME=/whatap-agent 에서 whatap.conf 읽기
5. APM 모니터링 시작
```

### Kubernetes 매니페스트 예시 (수동 설정 시)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-nodejs-app
spec:
  selector:
    matchLabels:
      app: my-nodejs-app
  template:
    metadata:
      labels:
        app: my-nodejs-app
    spec:
      initContainers:
      - name: whatap-agent-init
        image: public.ecr.aws/whatap/apm-init-nodejs:0.4.98
        env:
        - name: WHATAP_LICENSE
          value: "your-license-key"
        - name: WHATAP_HOST
          value: "13.124.11.223/13.209.172.35"
        - name: WHATAP_PORT
          value: "6600"
        volumeMounts:
        - name: whatap-agent-volume
          mountPath: /whatap-agent
      containers:
      - name: my-app
        image: my-nodejs-app:latest
        env:
        - name: WHATAP_HOME
          value: "/whatap-agent"
        - name: NODE_PATH
          value: "/whatap-agent/node_modules"
        - name: NODE_OPTIONS
          value: "-r whatap"
        volumeMounts:
        - name: whatap-agent-volume
          mountPath: /whatap-agent
      volumes:
      - name: whatap-agent-volume
        emptyDir: {}
```

> Whatap Operator를 사용하면 위 설정이 자동으로 주입되므로 수동 설정이 필요 없습니다.

## 문제 해결

### Docker Buildx 설정
```bash
# Docker Buildx 활성화 (필요한 경우)
docker buildx install

# 새로운 builder 생성
docker buildx create --name mybuilder --use --bootstrap
```

### Docker 레지스트리 로그인
```bash
# AWS ECR
aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws

# Docker Hub
docker login
```

### 버전 확인
사용 가능한 Whatap Node.js 에이전트 버전은 [npm](https://www.npmjs.com/package/whatap)에서 확인할 수 있습니다.

## 참고사항

- 빌드 시 인터넷 연결이 필요합니다 (npm에서 에이전트 다운로드)
- Multi-platform 빌드는 단일 플랫폼 빌드보다 시간이 더 걸릴 수 있습니다
- 최종 이미지에는 Node.js 런타임이 포함되지 않습니다 (파일 복사만 수행)
- 에이전트 버전은 Whatap 공식 릴리스 버전을 사용해야 합니다

## 관련 링크

- [Whatap Node.js APM 공식 문서](https://docs.whatap.io/nodejs/introduction)
- [npm - whatap](https://www.npmjs.com/package/whatap)
- [Docker Buildx 문서](https://docs.docker.com/buildx/)
