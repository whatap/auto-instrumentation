#!/usr/bin/env bash
# dev-build.sh — auto-instrumentation 이미지를 DEV(DockerHub whatap) 로 빌드/푸시.
#
# dev 레지스트리 = docker.io/whatap, 이미지명 = dev_<원래이름>, 태그 = <ver>-dev (latest 미푸시).
# 릴리스(prod)는 각 디렉토리의 build.sh 를 인자만 주고 직접 호출(기본 public.ecr.aws/whatap).
#
# 전제: 빌드 호스트에서 `docker login -u whatap`(docker.io) 완료, buildx multiarch 빌더 존재.
#
# 사용:
#   ./dev-build.sh java   <agent_version>                  # dev_apm-init-java:<ver>-dev
#   ./dev-build.sh python <agent_version>                  # dev_apm-init-python:<ver>-dev
#   ./dev-build.sh nodejs <agent_version> [<image_base>]   # dev_apm-init-nodejs:<image_base>-dev
#                                                          # image_base 생략 시 agent_version 사용
#
# 결과: 성공 시 마지막 줄에 'PUSHED=<full image:tag>' 출력(검증 파이프라인용).
set -euo pipefail

DEV_REGISTRY="docker.io/whatap"
HERE="$(cd "$(dirname "$0")" && pwd)"

KIND="${1:?kind 필요: java|python|nodejs}"; shift
case "$KIND" in
  java)   DIR="java-apm";   BASE="apm-init-java" ;;
  python) DIR="python-apm"; BASE="apm-init-python" ;;
  nodejs) DIR="nodejs-apm"; BASE="apm-init-nodejs" ;;
  *) echo "ERROR: kind는 java|python|nodejs 중 하나여야 함 (입력: $KIND)" >&2; exit 2 ;;
esac

DEV_IMAGE="dev_${BASE}"

cd "$HERE/$DIR"

if [ "$KIND" = "nodejs" ]; then
  AGENT_VER="${1:?agent_version 필요}"
  IMAGE_BASE="${2:-$AGENT_VER}"
  IMAGE_VER="${IMAGE_BASE%-dev}-dev"   # 항상 정확히 하나의 -dev 접미사 보장
  echo ">>> DEV build: ${DEV_REGISTRY}/${DEV_IMAGE}:${IMAGE_VER} (agent=${AGENT_VER})" >&2
  REGISTRY="$DEV_REGISTRY" IMAGE_NAME="$DEV_IMAGE" ./build.sh "$AGENT_VER" "$IMAGE_VER"
  echo "PUSHED=${DEV_REGISTRY}/${DEV_IMAGE}:${IMAGE_VER}"
else
  AGENT_VER="${1:?agent_version 필요}"
  IMAGE_TAG="${AGENT_VER%-dev}-dev"
  echo ">>> DEV build: ${DEV_REGISTRY}/${DEV_IMAGE}:${IMAGE_TAG} (agent=${AGENT_VER})" >&2
  REGISTRY="$DEV_REGISTRY" IMAGE_NAME="$DEV_IMAGE" IMAGE_TAG="$IMAGE_TAG" ./build.sh "$AGENT_VER"
  echo "PUSHED=${DEV_REGISTRY}/${DEV_IMAGE}:${IMAGE_TAG}"
fi
