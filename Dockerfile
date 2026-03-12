# ============= SINGLE STAGE =============
FROM python:3.12-slim-bullseye

WORKDIR /wbb

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# تثبيت الاعتماديات النظامية
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    git gcc build-essential \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# نسخ ملفات المشروع (بما في ذلك pyproject.toml)
COPY . .

# تثبيت المشروع واعتمادياته باستخدام pip
RUN pip install --no-cache-dir .

# تشغيل البوت
CMD ["python", "-m", "wbb"]
