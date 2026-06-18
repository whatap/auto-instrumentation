#!/bin/bash

# ===================================================================
# Docker 이미지 빌드 및 푸시 자동화 스크립트 (Multi-Platform 지원)
# 사용법: ./build.sh <version>
# 예시:   ./build.sh 0.4.98
# ===================================================================

# --- 설정 (사용자 환경에 맞게 수정하세요) ---

# 이미지를 푸시할 Docker 레지스트리 주소
REGISTRY="public.ecr.aws/whatap"

# 생성할 이미지의 이름
IMAGE_NAME="apm-init-nodejs"

# 지원할 플랫폼을 설정하세요.
PLATFORMS="linux/amd64,linux/arm64"

# --- 설정 끝 ---


# 스크립트 실행 중 오류가 발생하면 즉시 중단합니다.
set -e

# 버전 인자 확인
if [ -z "$1" ]; then
    echo "오류: 빌드할 에이전트 버전을 첫 번째 인자로 전달해야 합니다."
    echo "   사용법: $0 <version>"
    echo "   예시: $0 2.0.2"
    exit 1
fi

# 변수 설정
VERSION=$1
FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}"
TAG_VERSION="${FULL_IMAGE_NAME}:${VERSION}"
TAG_LATEST="${FULL_IMAGE_NAME}:latest"

# 스크립트 시작
echo "=================================================="
echo "Whatap Node.js Agent 이미지 빌드 및 푸시 시작 (Multi-Platform)"
echo "--------------------------------------------------"
echo "  - Agent Version : ${VERSION}"
echo "  - Image Name    : ${FULL_IMAGE_NAME}"
echo "  - Version Tag   : ${TAG_VERSION}"
echo "  - Latest Tag    : ${TAG_LATEST}"
echo "  - Platforms     : ${PLATFORMS}"
echo "=================================================="
echo

# 1. Docker buildx builder 설정 확인 및 생성
echo "1. Docker buildx builder 설정을 확인합니다..."
BUILDER_NAME="multiarch-builder"

# 기존 builder가 있는지 확인
if ! docker buildx ls | grep -q "${BUILDER_NAME}"; then
    echo "   새로운 buildx builder를 생성합니다..."
    docker buildx create --name ${BUILDER_NAME} --use --bootstrap
else
    echo "   기존 buildx builder를 사용합니다..."
    docker buildx use ${BUILDER_NAME}
fi
echo "Builder 설정 완료!"
echo

# 2. Multi-platform Docker 이미지 빌드 및 푸시
echo "2. Multi-platform 이미지 빌드 및 푸시를 시작합니다..."
echo "   지원 플랫폼: ${PLATFORMS}"
docker buildx build \
  --platform ${PLATFORMS} \
  --build-arg WHATAP_AGENT_VERSION=${VERSION} \
  -t ${TAG_VERSION} \
  -t ${TAG_LATEST} \
  --push .
echo "Multi-platform 빌드 및 푸시 완료!"
echo

echo "모든 작업이 성공적으로 완료되었습니다."
echo "빌드된 이미지:"
echo "   - ${TAG_VERSION} (${PLATFORMS})"
echo "   - ${TAG_LATEST} (${PLATFORMS})"
