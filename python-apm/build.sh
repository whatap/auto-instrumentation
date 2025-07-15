#!/bin/bash

# ===================================================================
# Docker 이미지 빌드 및 푸시 자동화 스크립트
# 사용법: ./build_and_push.sh <version>
# 예시:   ./build_and_push.sh 2.2.61
# ===================================================================

# --- ⚠️ 설정 (사용자 환경에 맞게 수정하세요) ---

# 이미지를 푸시할 Docker 레지스트리 주소 또는 Docker Hub 사용자 이름을 입력하세요.
# 예: docker.io/myusername (Docker Hub)
# 예: 1234567890.dkr.ecr.ap-northeast-2.amazonaws.com (AWS ECR)
# 예: gcr.io/my-gcp-project (Google GCR)
REGISTRY="public.ecr.aws/whatap"

# 생성할 이미지의 이름을 입력하세요.
IMAGE_NAME="apm-init-java"

# --- 설정 끝 ---


# 스크립트 실행 중 오류가 발생하면 즉시 중단합니다.
set -e

# 버전 인자 확인
if [ -z "$1" ]; then
    echo "❌ 오류: 빌드할 에이전트 버전을 첫 번째 인자로 전달해야 합니다."
    echo "   사용법: $0 <version>"
    echo "   예시: $0 2.2.61"
    exit 1
fi

# 변수 설정
VERSION=$1
FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}"
TAG_VERSION="${FULL_IMAGE_NAME}:${VERSION}"
TAG_LATEST="${FULL_IMAGE_NAME}:latest"

# 스크립트 시작
echo "=================================================="
echo "🚀 Whatap Agent 이미지 빌드 및 푸시 시작"
echo "--------------------------------------------------"
echo "  - Agent Version : ${VERSION}"
echo "  - Image Name    : ${FULL_IMAGE_NAME}"
echo "  - Version Tag   : ${TAG_VERSION}"
echo "  - Latest Tag    : ${TAG_LATEST}"
echo "=================================================="
echo

# 1. Docker 이미지 빌드
echo "▶️ 1. Docker 이미지 빌드를 시작합니다..."
docker build \
  --build-arg WHATAP_AGENT_VERSION=${VERSION} \
  -t ${TAG_VERSION} \
  -t ${TAG_LATEST} .
echo "✅ 빌드 완료!"
echo

# 2. Docker 이미지 푸시 (버전 태그)
echo "▶️ 2. Version 태그(${TAG_VERSION})를 푸시합니다..."
docker push ${TAG_VERSION}
echo "✅ 푸시 완료!"
echo

# 3. Docker 이미지 푸시 (latest 태그)
echo "▶️ 3. Latest 태그(${TAG_LATEST})를 푸시합니다..."
docker push ${TAG_LATEST}
echo "✅ 푸시 완료!"
echo

echo "🎉 모든 작업이 성공적으로 완료되었습니다."
