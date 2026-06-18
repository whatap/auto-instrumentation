FROM node:20-alpine AS builder

# 빌드 인자로 에이전트 버전을 받습니다
ARG WHATAP_AGENT_VERSION=2.0.2

WORKDIR /build

# Whatap Node.js 에이전트 및 의존성 설치
RUN npm install whatap@${WHATAP_AGENT_VERSION} && \
    rm -f package.json package-lock.json

# ---

FROM alpine:3.20

LABEL maintainer="Whatap Labs" \
      description="Whatap Node.js APM Agent InitContainer Image"

# node_modules를 배포 경로에 복사 (whatap + 의존성 패키지 전체)
COPY --from=builder /build/node_modules /opt/whatap-agent-dist/node_modules

WORKDIR /whatap-agent
RUN echo '#!/bin/sh' > /init.sh && \
    echo 'set -e' >> /init.sh && \
    echo 'echo "[whatap-nodejs-init] starting..."' >> /init.sh && \
    echo 'mkdir -p /whatap-agent' >> /init.sh && \
    echo 'if [ ! -d "/whatap-agent/node_modules/whatap" ]; then' >> /init.sh && \
    echo '  echo "[whatap-nodejs-init] node_modules not found under /whatap-agent. Seeding from /opt/whatap-agent-dist..."' >> /init.sh && \
    echo '  mkdir -p /whatap-agent/node_modules' >> /init.sh && \
    echo '  cp -a /opt/whatap-agent-dist/node_modules/. /whatap-agent/node_modules/ 2>/dev/null || true' >> /init.sh && \
    echo 'else' >> /init.sh && \
    echo '  echo "[whatap-nodejs-init] node_modules already present. Skipping seed."' >> /init.sh && \
    echo 'fi' >> /init.sh && \
    echo '# Resolve arch-specific native binary to a stable path for WHATAP_NODEJS_AGENT_PATH (container-id mapping)' >> /init.sh && \
    echo 'ARCH=$(uname -m)' >> /init.sh && \
    echo 'case "$ARCH" in' >> /init.sh && \
    echo '  x86_64|amd64) NARCH="amd64" ;;' >> /init.sh && \
    echo '  aarch64|arm64) NARCH="arm64" ;;' >> /init.sh && \
    echo '  *) NARCH="" ;;' >> /init.sh && \
    echo 'esac' >> /init.sh && \
    echo 'AGENT_DIR="/whatap-agent/node_modules/whatap/agent"' >> /init.sh && \
    echo 'if [ -n "$NARCH" ] && [ -f "$AGENT_DIR/linux/$NARCH/whatap_nodejs" ]; then' >> /init.sh && \
    echo '  cp -f "$AGENT_DIR/linux/$NARCH/whatap_nodejs" "$AGENT_DIR/whatap_nodejs" 2>/dev/null || true' >> /init.sh && \
    echo '  chmod 755 "$AGENT_DIR/whatap_nodejs" 2>/dev/null || true' >> /init.sh && \
    echo '  echo "[whatap-nodejs-init] resolved native agent binary for arch=$NARCH -> $AGENT_DIR/whatap_nodejs"' >> /init.sh && \
    echo 'else' >> /init.sh && \
    echo '  echo "[whatap-nodejs-init] WARN: could not resolve native agent binary (arch=$ARCH)"' >> /init.sh && \
    echo 'fi' >> /init.sh && \
    echo 'WHATAP_HOME="/whatap-agent"' >> /init.sh && \
    echo 'TARGET_FILE="${WHATAP_HOME}/whatap.conf"' >> /init.sh && \
    echo 'if [ -f "$TARGET_FILE" ]; then' >> /init.sh && \
    echo '  echo "[whatap-nodejs-init] Existing $TARGET_FILE detected. Skipping generation."' >> /init.sh && \
    echo 'else' >> /init.sh && \
    echo '  L="${WHATAP_LICENSE:-$license}"' >> /init.sh && \
    echo '  H="${WHATAP_HOST:-$whatap_server_host}"' >> /init.sh && \
    echo '  P="${WHATAP_PORT:-$whatap_server_port}"' >> /init.sh && \
    echo '  AN="${APP_NAME:-$app_name}"' >> /init.sh && \
    echo '  APN="${APP_PROCESS_NAME:-$app_process_name}"' >> /init.sh && \
    echo '  [ -n "$AN" ] || AN="nodejs-app"' >> /init.sh && \
    echo '  [ -n "$APN" ] || APN="node"' >> /init.sh && \
    echo '  echo "[whatap-nodejs-init] Generating $TARGET_FILE"' >> /init.sh && \
    echo '  cat > "$TARGET_FILE" << EOF' >> /init.sh && \
    echo 'license=$L' >> /init.sh && \
    echo 'whatap.server.host=$H' >> /init.sh && \
    echo 'whatap.server.port=$P' >> /init.sh && \
    echo 'app_name=$AN' >> /init.sh && \
    echo 'app_process_name=$APN' >> /init.sh && \
    echo 'EOF' >> /init.sh && \
    echo '  chmod 644 "$TARGET_FILE" 2>/dev/null || true' >> /init.sh && \
    echo 'fi' >> /init.sh && \
    echo 'echo "[whatap-nodejs-init] done. whatap.conf: $TARGET_FILE"' >> /init.sh && \
    chmod +x /init.sh

# Run as non-root by default for security/OpenShift compatibility
USER 1001
CMD ["/init.sh"]
