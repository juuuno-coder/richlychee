FROM python:3.12-slim

WORKDIR /app

# 시스템 의존성
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]" 2>/dev/null || pip install --no-cache-dir .

# Playwright 브라우저 설치
RUN playwright install --with-deps chromium

# 소스 코드
COPY . .

# 업로드 디렉토리
RUN mkdir -p uploads

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
