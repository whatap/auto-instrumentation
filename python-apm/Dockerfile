FROM python:3.10-slim

# 빌드 인자로 에이전트 버전을 받습니다
ARG WHATAP_AGENT_VERSION=1.8.5

# 작업 디렉터리 설정
WORKDIR /tmp

# Python 3.12 이상에서는 setuptools가 기본 라이브러리에서 제외되므로 수동 설치 필요
# (whatap_python 에이전트가 setuptools에 종속, 82 버전 미만 필요)
# 앱 컨테이너에서도 사용할 수 있도록 PYTHONPATH 경로에 번들링합니다.
RUN pip install --no-cache-dir 'setuptools<82'

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
    mkdir -p /opt/whatap-agent-dist && \
    cp -r whatap_python-${WHATAP_AGENT_VERSION}/* /opt/whatap-agent-dist/ && \
    rm -rf whatap_python-${WHATAP_AGENT_VERSION}* && \
    apt-get remove -y wget && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# setuptools<82의 pkg_resources와 setuptools를 에이전트 bootstrap 경로에 번들링
# PYTHONPATH=/whatap-agent/whatap/bootstrap 으로 설정되므로, 앱 컨테이너에서
# 자체 setuptools(>=81) 대신 번들된 버전이 우선 로드되어 pkg_resources 경고 방지
RUN SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])") && \
    mkdir -p /opt/whatap-agent-dist/whatap/bootstrap && \
    cp -r ${SITE_PACKAGES}/pkg_resources /opt/whatap-agent-dist/whatap/bootstrap/ && \
    cp -r ${SITE_PACKAGES}/setuptools /opt/whatap-agent-dist/whatap/bootstrap/

WORKDIR /whatap-agent
RUN echo '#!/bin/sh' > /init.sh && \
    echo 'set -e' >> /init.sh && \
    echo 'echo "[whatap-python-init] starting..."' >> /init.sh && \
    echo 'mkdir -p /whatap-agent' >> /init.sh && \
    echo 'if [ ! -d "/whatap-agent/whatap" ]; then' >> /init.sh && \
    echo '  echo "[whatap-python-init] whatap package not found under /whatap-agent. Seeding from /opt/whatap-agent-dist..."' >> /init.sh && \
    echo '  cp -a /opt/whatap-agent-dist/. /whatap-agent/ 2>/dev/null || true' >> /init.sh && \
    echo 'else' >> /init.sh && \
    echo '  echo "[whatap-python-init] whatap package already present. Skipping seed."' >> /init.sh && \
    echo 'fi' >> /init.sh && \
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
    echo '# Apply standalone-related envs to whatap.conf if present' >> /init.sh && \
    echo '# Normalize lowercase envs to uppercase if uppercase is not set' >> /init.sh && \
    echo 'STANDALONE_ENABLED="${STANDALONE_ENABLED:-$standalone_enabled}"' >> /init.sh && \
    echo 'STANDALONE_TYPE="${STANDALONE_TYPE:-$standalone_type}"' >> /init.sh && \
    echo 'STANDALONE_TRANSACTION_PATTERNS="${STANDALONE_TRANSACTION_PATTERNS:-$standalone_transaction_patterns}"' >> /init.sh && \
    echo 'if [ -n "$STANDALONE_ENABLED" ]; then' >> /init.sh && \
    echo '  if grep -q "^standalone_enabled=" "$TARGET_FILE" 2>/dev/null; then' >> /init.sh && \
    echo '    sed "s|^standalone_enabled=.*|standalone_enabled=$STANDALONE_ENABLED|" "$TARGET_FILE" > "${TARGET_FILE}.tmp" && mv "${TARGET_FILE}.tmp" "$TARGET_FILE"' >> /init.sh && \
    echo '  else' >> /init.sh && \
    echo '    echo "standalone_enabled=$STANDALONE_ENABLED" >> "$TARGET_FILE"' >> /init.sh && \
    echo '  fi' >> /init.sh && \
    echo 'fi' >> /init.sh && \
    echo 'if [ -n "$STANDALONE_TYPE" ]; then' >> /init.sh && \
    echo '  if grep -q "^standalone_type=" "$TARGET_FILE" 2>/dev/null; then' >> /init.sh && \
    echo '    sed "s|^standalone_type=.*|standalone_type=$STANDALONE_TYPE|" "$TARGET_FILE" > "${TARGET_FILE}.tmp" && mv "${TARGET_FILE}.tmp" "$TARGET_FILE"' >> /init.sh && \
    echo '  else' >> /init.sh && \
    echo '    echo "standalone_type=$STANDALONE_TYPE" >> "$TARGET_FILE"' >> /init.sh && \
    echo '  fi' >> /init.sh && \
    echo 'fi' >> /init.sh && \
    echo 'if [ -n "$STANDALONE_TRANSACTION_PATTERNS" ]; then' >> /init.sh && \
    echo '  if grep -q "^standalone_transaction_patterns=" "$TARGET_FILE" 2>/dev/null; then' >> /init.sh && \
    echo '    sed "s|^standalone_transaction_patterns=.*|standalone_transaction_patterns=\"$STANDALONE_TRANSACTION_PATTERNS\"|" "$TARGET_FILE" > "${TARGET_FILE}.tmp" && mv "${TARGET_FILE}.tmp" "$TARGET_FILE"' >> /init.sh && \
    echo '  else' >> /init.sh && \
    echo '    echo "standalone_transaction_patterns=\"$STANDALONE_TRANSACTION_PATTERNS\"" >> "$TARGET_FILE"' >> /init.sh && \
    echo '  fi' >> /init.sh && \
    echo 'fi' >> /init.sh && \
    echo 'echo "[whatap-python-init] done. whatap.conf: $TARGET_FILE"' >> /init.sh && \
    chmod +x /init.sh

# CMD ["/init.sh"]는 기존대로 유지

# 기본 명령어 설정
# Run as non-root by default for security/OpenShift compatibility
USER 1001
CMD ["/init.sh"]
