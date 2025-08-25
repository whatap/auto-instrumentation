FROM python:3.10-slim

# 빌드 인자로 에이전트 버전을 받습니다
ARG WHATAP_AGENT_VERSION=1.8.5

# 작업 디렉터리 설정
WORKDIR /tmp

# Python APM 에이전트 다운로드 및 압축 해제
RUN apt-get update && apt-get install -y wget && \
    if [ ! -d "whatap_python-${WHATAP_AGENT_VERSION}" ]; then \
        echo "whatap_python-${WHATAP_AGENT_VERSION} 폴더가 없습니다. 다운로드를 시작합니다..." && \
        wget https://files.pythonhosted.org/packages/source/w/whatap_python/whatap_python-${WHATAP_AGENT_VERSION}.tar.gz && \
        tar xzvf whatap_python-${WHATAP_AGENT_VERSION}.tar.gz && \
        rm -f whatap_python-${WHATAP_AGENT_VERSION}.tar.gz; \
    else \
        echo "whatap_python-${WHATAP_AGENT_VERSION} 폴더가 이미 존재합니다. 기존 폴더를 사용합니다."; \
    fi && \
    mkdir -p /whatap-agent && \
    cp -r whatap_python-${WHATAP_AGENT_VERSION}/* /whatap-agent/ && \
    rm -rf whatap_python-${WHATAP_AGENT_VERSION}* && \
    apt-get remove -y wget && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /whatap-agent
RUN echo '#!/bin/sh' > /init.sh && \
    echo 'set -e' >> /init.sh && \
    echo 'echo "[whatap-python-init] starting..."' >> /init.sh && \
    echo 'if [ ! -d "/whatap-agent" ]; then echo "[whatap-python-init] Error: /whatap-agent directory not mounted"; exit 1; fi' >> /init.sh && \
    echo 'WHATAP_HOME="/whatap-agent"' >> /init.sh && \
    echo 'TARGET_FILE="${WHATAP_HOME}/whatap.conf"' >> /init.sh && \
    echo 'if [ -f "$TARGET_FILE" ]; then' >> /init.sh && \
    echo '  echo "[whatap-python-init] Existing $TARGET_FILE detected. Skipping generation."' >> /init.sh && \
    echo 'else' >> /init.sh && \
    echo '  L="${WHATAP_LICENSE:-$license}"' >> /init.sh && \
    echo '  H="${WHATAP_HOST:-$whatap_server_host}"' >> /init.sh && \
    echo '  P="${WHATAP_PORT:-$whatap_server_port}"' >> /init.sh && \
    echo '  AN="${APP_NAME:-$app_name}"' >> /init.sh && \
    echo '  APN="${APP_PROCESS_NAME:-$app_process_name}"' >> /init.sh && \
    echo '  [ -n "$AN" ] || AN="python-app"' >> /init.sh && \
    echo '  [ -n "$APN" ] || APN="python"' >> /init.sh && \
    echo '  echo "[whatap-python-init] Generating $TARGET_FILE"' >> /init.sh && \
    echo '  cat > "$TARGET_FILE" << EOF' >> /init.sh && \
    echo 'license=$L' >> /init.sh && \
    echo 'whatap.server.host=$H' >> /init.sh && \
    echo 'whatap.server.port=$P' >> /init.sh && \
    echo 'app_name=$AN' >> /init.sh && \
    echo 'app_process_name=$APN' >> /init.sh && \
    echo 'whatap_code_start=true' >> /init.sh && \
    echo 'EOF' >> /init.sh && \
    echo '  chmod 644 "$TARGET_FILE" 2>/dev/null || true' >> /init.sh && \
    echo 'fi' >> /init.sh && \
    echo '# Ensure whatap_code_start=true is present even for existing configs' >> /init.sh && \
    echo 'if grep -q "^whatap_code_start=" "$TARGET_FILE" 2>/dev/null; then' >> /init.sh && \
    echo '  sed "s/^whatap_code_start=.*/whatap_code_start=true/" "$TARGET_FILE" > "${TARGET_FILE}.tmp" && mv "${TARGET_FILE}.tmp" "$TARGET_FILE"' >> /init.sh && \
    echo 'else' >> /init.sh && \
    echo '  echo "whatap_code_start=true" >> "$TARGET_FILE"' >> /init.sh && \
    echo 'fi' >> /init.sh && \
    echo 'chmod 644 "$TARGET_FILE" 2>/dev/null || true' >> /init.sh && \
    echo 'echo "[whatap-python-init] done. whatap.conf: $TARGET_FILE"' >> /init.sh && \
    chmod +x /init.sh

# CMD ["/init.sh"]는 기존대로 유지

# 기본 명령어 설정
CMD ["/init.sh"]
