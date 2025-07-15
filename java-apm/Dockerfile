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

# 4️⃣ InitContainer 실행 명령
CMD ["cp", "/whatap/whatap.agent.java.jar", "/whatap-agent/"]
