FROM python:3.10-slim

# 빌드 인자로 에이전트 버전을 받습니다
ARG WHATAP_AGENT_VERSION=1.8.5

# 작업 디렉터리 설정
WORKDIR /tmp

# Python APM 에이전트 다운로드 및 압축 해제
RUN apt-get update && apt-get install -y wget && \
    wget https://files.pythonhosted.org/packages/source/w/whatap_python/whatap_python-${WHATAP_AGENT_VERSION}.tar.gz && \
    tar xzvf whatap_python-${WHATAP_AGENT_VERSION}.tar.gz && \
    mkdir -p /whatap-agent && \
    cp -r whatap_python-${WHATAP_AGENT_VERSION}/* /whatap-agent/ && \
    rm -rf whatap_python-${WHATAP_AGENT_VERSION}* && \
    apt-get remove -y wget && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Python 패키지 설치 - 이때 whatap-setting-config, whatap-start-agent 명령어 자동 생성됨
WORKDIR /whatap-agent
RUN python setup.py build && \
    python setup.py install --prefix=/whatap-agent --install-lib=/whatap-agent/lib --install-scripts=/whatap-agent/bin && \
    # bootstrap 디렉터리 복사 (sitecustomize.py 포함)
    cp -r whatap/bootstrap /whatap-agent/

# 빌드된 에이전트를 별도 위치에 백업 (InitContainer에서 사용)
RUN cp -r /whatap-agent /whatap-agent-source

# 초기화 스크립트 생성 (Java APM과 동일한 구조)
RUN echo '#!/bin/bash' > /init.sh && \
    echo 'set -e' >> /init.sh && \
    echo '' >> /init.sh && \
    echo '# 대상 디렉터리가 마운트되어 있는지 확인' >> /init.sh && \
    echo 'if [ ! -d "/whatap-agent" ]; then' >> /init.sh && \
    echo '    echo "Error: /whatap-agent directory not mounted"' >> /init.sh && \
    echo '    exit 1' >> /init.sh && \
    echo 'fi' >> /init.sh && \
    echo '' >> /init.sh && \
    echo 'echo "Copying Whatap Python agent to /whatap-agent..."' >> /init.sh && \
    echo '' >> /init.sh && \
    echo '# 기존 파일이 있으면 백업' >> /init.sh && \
    echo 'if [ "$(ls -A /whatap-agent 2>/dev/null)" ]; then' >> /init.sh && \
    echo '    echo "Target directory not empty, cleaning up..."' >> /init.sh && \
    echo '    rm -rf /whatap-agent/*' >> /init.sh && \
    echo 'fi' >> /init.sh && \
    echo '' >> /init.sh && \
    echo '# whatap-agent 디렉터리 전체를 대상 위치로 복사' >> /init.sh && \
    echo 'cp -r /whatap-agent-source/* /whatap-agent/' >> /init.sh && \
    echo '' >> /init.sh && \
    echo '# 권한 설정' >> /init.sh && \
    echo 'chmod -R 755 /whatap-agent' >> /init.sh && \
    echo 'chmod +x /whatap-agent/bin/whatap-setting-config' >> /init.sh && \
    echo 'chmod +x /whatap-agent/bin/whatap-start-agent' >> /init.sh && \
    echo '' >> /init.sh && \
    echo 'echo "Whatap Python agent installation completed successfully"' >> /init.sh && \
    echo 'echo "Available commands:"' >> /init.sh && \
    echo 'ls -la /whatap-agent/bin/whatap-*' >> /init.sh && \
    chmod +x /init.sh

# 기본 명령어 설정
CMD ["/init.sh"]
