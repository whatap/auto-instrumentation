FROM python:3.10-slim

# 빌드 인자로 에이전트 버전을 받습니다 (정식 PyPI의 stable 버전 기본값)
ARG WHATAP_AGENT_VERSION=2.0.2

# 에이전트를 받을 PyPI 인덱스 (정식 PyPI 기본값)
# dev 프리릴리스 등 특수한 경우에만 test.pypi 등으로 override 하세요.
# 예: --build-arg WHATAP_PYPI_INDEX_URL=https://test.pypi.org/simple/
ARG WHATAP_PYPI_INDEX_URL=https://pypi.org/simple/

# 작업 디렉터리 설정
WORKDIR /tmp

# 새 whatap-python 에이전트는 self-contained로 배포되며 setuptools/pkg_resources에
# 의존하지 않습니다. 배포물(wheel 또는 sdist)을 내려받아 whatap 패키지만 번들링합니다(설치 불필요).
# - 정식 PyPI(stable): sdist(.tar.gz)로 배포될 수 있음
# - test.pypi(dev): wheel(.whl)로 배포될 수 있음
RUN pip download --no-deps --no-cache-dir \
        --index-url ${WHATAP_PYPI_INDEX_URL} \
        "whatap-python==${WHATAP_AGENT_VERSION}" -d /tmp/whatap-dl && \
    mkdir -p /tmp/whatap-extracted && \
    WHL=$(ls /tmp/whatap-dl/whatap_python-*.whl 2>/dev/null | head -n1) && \
    if [ -n "${WHL}" ]; then \
        echo "다운로드한 wheel: ${WHL}" && \
        python -m zipfile -e "${WHL}" /tmp/whatap-extracted; \
    else \
        SDIST=$(ls /tmp/whatap-dl/whatap_python-*.tar.gz 2>/dev/null | head -n1) && \
        echo "다운로드한 sdist: ${SDIST}" && \
        tar xzf "${SDIST}" -C /tmp/whatap-extracted --strip-components=1; \
    fi && \
    test -d /tmp/whatap-extracted/whatap && \
    mkdir -p /opt/whatap-agent-dist && \
    cp -r /tmp/whatap-extracted/whatap /opt/whatap-agent-dist/ && \
    rm -rf /tmp/whatap-dl /tmp/whatap-extracted

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
    echo 'apm_enabled=true' >> /init.sh && \
    echo 'EOF' >> /init.sh && \
    echo '  chmod 644 "$TARGET_FILE" 2>/dev/null || true' >> /init.sh && \
    echo 'fi' >> /init.sh && \
    echo '# Ensure whatap_code_start=true is present even for existing configs' >> /init.sh && \
    echo 'if grep -q "^whatap_code_start=" "$TARGET_FILE" 2>/dev/null; then' >> /init.sh && \
    echo '  sed "s/^whatap_code_start=.*/whatap_code_start=true/" "$TARGET_FILE" > "${TARGET_FILE}.tmp" && mv "${TARGET_FILE}.tmp" "$TARGET_FILE"' >> /init.sh && \
    echo 'else' >> /init.sh && \
    echo '  echo "whatap_code_start=true" >> "$TARGET_FILE"' >> /init.sh && \
    echo 'fi' >> /init.sh && \
    echo '# Ensure apm_enabled=true is present even for existing configs' >> /init.sh && \
    echo 'if grep -q "^apm_enabled=" "$TARGET_FILE" 2>/dev/null; then' >> /init.sh && \
    echo '  sed "s/^apm_enabled=.*/apm_enabled=true/" "$TARGET_FILE" > "${TARGET_FILE}.tmp" && mv "${TARGET_FILE}.tmp" "$TARGET_FILE"' >> /init.sh && \
    echo 'else' >> /init.sh && \
    echo '  echo "apm_enabled=true" >> "$TARGET_FILE"' >> /init.sh && \
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
