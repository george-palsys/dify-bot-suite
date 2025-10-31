FROM python:3.9-slim

WORKDIR /app

# 安裝 chromium + driver + 基本套件
RUN apt-get update && apt-get install -y chromium chromium-driver && \
    pip install flask selenium pillow && \
    rm -rf /var/lib/apt/lists/*

COPY scripts /app/scripts
EXPOSE 8082
CMD ["python3", "/app/scripts/app.py"]

