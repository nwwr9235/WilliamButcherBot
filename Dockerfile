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

# تثبيت uv عبر pip (بدلاً من تحميله من الموقع)
RUN pip install --no-cache-dir uv

# نسخ ملفات تعريف الحزمة
COPY pyproject.toml uv.lock ./

# تثبيت الاعتماديات والمشروع في بيئة افتراضية
RUN uv sync --no-dev

# نسخ باقي الملفات
COPY . .

# تشغيل البوت باستخدام uv run لتفعيل البيئة الافتراضية
CMD ["uv", "run", "python", "-m", "wbb"]
