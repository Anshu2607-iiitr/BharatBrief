FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg tzdata \
    && rm -rf /var/lib/apt/lists/*

# Server UTC pe hota hai; hamari saari timings (8 AM digest, "aaj", 24 ghante) IST mein
ENV TZ=Asia/Kolkata
# Summary queue worker chalayega (website pe koi aaye ya na aaye)
ENV BB_WORKER=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN sed -i 's/\r$//' start.sh

ENV PYTHONUNBUFFERED=1
CMD ["bash", "start.sh"]
