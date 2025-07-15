FROM openjdk:8-jdk-slim

WORKDIR /whatap

# 1️⃣ 에이전트 다운로드
ADD https://repo.whatap.io/maven/io/whatap/whatap.agent/2.2.58/whatap.agent-2.2.58.jar .

# 2️⃣ 공식 Rename 수행
RUN java -cp whatap.agent-2.2.58.jar whatap.agent.setup.Rename -from whatap.agent-2.2.58.jar -to whatap.agent.java.jar

# 3️⃣ 불필요한 원본 삭제 (선택)
RUN rm -f whatap.agent-2.2.58.jar

# 4️⃣ InitContainer 실행 명령
CMD ["cp", "/whatap/whatap.agent.java.jar", "/whatap-agent/"]

