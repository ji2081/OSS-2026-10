# 파이썬 3.9 버전을 기반으로 시작합니다.
FROM python:3.11-slim

# 도커 컨테이너 내부의 작업 폴더를 /app으로 지정합니다.
WORKDIR /app

# requirements.txt를 먼저 복사해서 패키지들을 설치합니다.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 나머지 백엔드 코드(main.py 등)를 모두 도커 안으로 복사합니다.
COPY . .

# FastAPI 서버를 실행하는 명령어입니다.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]