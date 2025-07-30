FROM openjdk:8-jdk-slim

# 빌드 인자로 에이전트 버전을 받습니다
ARG WHATAP_AGENT_VERSION=2.2.58

WORKDIR /whatap

# 1️⃣ 에이전트 다운로드
ADD https://repo.whatap.io/maven/io/whatap/whatap.agent/${WHATAP_AGENT_VERSION}/whatap.agent-${WHATAP_AGENT_VERSION}.jar .

# 2️⃣ 공식 Rename 수행
RUN java -cp whatap.agent-${WHATAP_AGENT_VERSION}.jar whatap.agent.setup.Rename -from whatap.agent-${WHATAP_AGENT_VERSION}.jar -to whatap.agent.java.jar

# 3️⃣ 불필요한 원본 삭제 (선택)
RUN rm -f whatap.agent-${WHATAP_AGENT_VERSION}.jar

# 4️⃣ init.sh 스크립트 생성 (설정 파일 생성 포함)
RUN echo '#!/bin/bash' > /init.sh && \
    echo 'set -e' >> /init.sh && \
    echo '' >> /init.sh && \
    echo 'echo "Starting Whatap Java APM agent initialization..."' >> /init.sh && \
    echo '' >> /init.sh && \
    echo '# 대상 디렉터리가 마운트되어 있는지 확인' >> /init.sh && \
    echo 'if [ ! -d "/whatap-agent" ]; then' >> /init.sh && \
    echo '    echo "Error: /whatap-agent directory not mounted"' >> /init.sh && \
    echo '    exit 1' >> /init.sh && \
    echo 'fi' >> /init.sh && \
    echo '' >> /init.sh && \
    echo '# Java agent 복사' >> /init.sh && \
    echo 'echo "Copying Java agent to /whatap-agent..."' >> /init.sh && \
    echo 'cp /whatap/whatap.agent.java.jar /whatap-agent/' >> /init.sh && \
    echo '' >> /init.sh && \
    echo '# whatap.conf 파일 생성' >> /init.sh && \
    echo 'echo "Generating whatap.conf..."' >> /init.sh && \
    echo 'cat > /whatap-agent/whatap.conf << CONF' >> /init.sh && \
    echo 'license=${WHATAP_LICENSE}' >> /init.sh && \
    echo 'whatap.server.host=${WHATAP_HOST}' >> /init.sh && \
    echo 'whatap.server.port=${WHATAP_PORT}' >> /init.sh && \
    echo 'whatap.micro.enabled=true' >> /init.sh && \
    echo 'CONF' >> /init.sh && \
    echo '' >> /init.sh && \
    echo '# Additional args 추가 (환경변수로 전달된 경우)' >> /init.sh && \
    echo 'if [ ! -z "$ADDITIONAL_ARGS" ]; then' >> /init.sh && \
    echo '    echo "Adding additional configuration..."' >> /init.sh && \
    echo '    echo "$ADDITIONAL_ARGS" >> /whatap-agent/whatap.conf' >> /init.sh && \
    echo 'fi' >> /init.sh && \
    echo '' >> /init.sh && \
    echo '# 권한 설정' >> /init.sh && \
    echo 'chmod 644 /whatap-agent/whatap.conf' >> /init.sh && \
    echo 'chmod 644 /whatap-agent/whatap.agent.java.jar' >> /init.sh && \
    echo '' >> /init.sh && \
    echo 'echo "Java agent installation completed successfully"' >> /init.sh && \
    echo 'echo "Agent file: /whatap-agent/whatap.agent.java.jar"' >> /init.sh && \
    echo 'echo "Config file: /whatap-agent/whatap.conf"' >> /init.sh && \
    chmod +x /init.sh

# 5️⃣ InitContainer 실행 명령 변경
CMD ["/init.sh"]
