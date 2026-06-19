#!/bin/bash

# ===================================================================
# Docker 이미지 빌드 및 푸시 자동화 스크립트 (Multi-Platform 지원)
# 사용법: ./build.sh <agent_version> <image_version>
#   - agent_version : npm 으로 설치할 whatap nodejs 에이전트 버전
#   - image_version : 생성할 이미지 태그
# 예시:
#   ./build.sh 2.0.2 1.0.0-dev   # 에이전트 2.0.2, 이미지 태그 1.0.0-dev
# ===================================================================

# --- 설정 (사용자 환경에 맞게 수정하세요) ---

# 이미지를 푸시할 Docker 레지스트리 주소
# env REGISTRY 로 오버라이드 가능 (dev: docker.io/whatap, 기본 release: public.ecr.aws/whatap)
REGISTRY="${REGISTRY:-public.ecr.aws/whatap}"

# 생성할 이미지의 이름
# env IMAGE_NAME 으로 오버라이드 가능 (dev: dev_apm-init-nodejs)
IMAGE_NAME="${IMAGE_NAME:-apm-init-nodejs}"

# 지원할 플랫폼을 설정하세요.
PLATFORMS="linux/amd64,linux/arm64"

# --- 설정 끝 ---


# 스크립트 실행 중 오류가 발생하면 즉시 중단합니다.
set -e

# 버전 인자 확인: 에이전트 버전과 이미지 버전 2개가 모두 필요합니다.
if [ "$#" -ne 2 ]; then
    echo "오류: 인자 2개(에이전트 버전, 이미지 버전)가 모두 필요합니다. (입력: $# 개)"
    echo "   사용법: $0 <agent_version> <image_version>"
    echo "   예시: $0 2.0.2 1.0.0-dev"
    exit 1
fi

# 변수 설정
# AGENT_VERSION: npm 으로 설치할 whatap 에이전트 버전
# IMAGE_VERSION: 이미지 태그
AGENT_VERSION=$1
IMAGE_VERSION=$2
FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}"
TAG_VERSION="${FULL_IMAGE_NAME}:${IMAGE_VERSION}"
TAG_LATEST="${FULL_IMAGE_NAME}:latest"

# 이미지 버전에 '-'(예: -dev, -rc)가 포함되면 pre-release 로 보고 latest 태그는 건너뜁니다.
PUSH_LATEST=true
case "${IMAGE_VERSION}" in
    *-*) PUSH_LATEST=false ;;
esac

# 스크립트 시작
echo "=================================================="
echo "Whatap Node.js Agent 이미지 빌드 및 푸시 시작 (Multi-Platform)"
echo "--------------------------------------------------"
echo "  - Agent Version : ${AGENT_VERSION}"
echo "  - Image Version : ${IMAGE_VERSION}"
echo "  - Image Name    : ${FULL_IMAGE_NAME}"
echo "  - Version Tag   : ${TAG_VERSION}"
if [ "${PUSH_LATEST}" = "true" ]; then
    echo "  - Latest Tag    : ${TAG_LATEST}"
else
    echo "  - Latest Tag    : (skip: pre-release)"
fi
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
LATEST_ARG=""
if [ "${PUSH_LATEST}" = "true" ]; then
    LATEST_ARG="-t ${TAG_LATEST}"
fi
docker buildx build \
  --platform ${PLATFORMS} \
  --build-arg WHATAP_AGENT_VERSION=${AGENT_VERSION} \
  -t ${TAG_VERSION} \
  ${LATEST_ARG} \
  --push .
echo "Multi-platform 빌드 및 푸시 완료!"
echo

echo "모든 작업이 성공적으로 완료되었습니다."
echo "빌드된 이미지:"
echo "   - ${TAG_VERSION} (${PLATFORMS})"
if [ "${PUSH_LATEST}" = "true" ]; then
    echo "   - ${TAG_LATEST} (${PLATFORMS})"
fi
