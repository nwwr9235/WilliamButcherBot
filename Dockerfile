# ============= SINGLE STAGE =============
FROM python:3.12-slim-bullseye

WORKDIR /wbb

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# تثبيت الاعتماديات النظامية المطلوبة
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    git gcc build-essential \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# نسخ ملف المتطلبات
COPY requirements.txt .

# تثبيت متطلبات Python باستخدام pip
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي الملفات
COPY . .

# تشغيل البوت
CMD ["python", "-m", "wbb"]
