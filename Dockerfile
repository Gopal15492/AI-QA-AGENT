FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN npx playwright install --with-deps chromium

COPY agent002.py .

EXPOSE 10000

CMD ["streamlit", "run", "agent002.py", "--server.address=0.0.0.0", "--server.port=10000"]