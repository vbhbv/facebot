# Dockerfile - التكوين النهائي الموحد والثابت
# ------------------------------------

# 1. تحديد الصورة الأساسية (لحل خطأ no build stage)
FROM python:3.11-slim

# 2. تثبيت ffmpeg (مهم جداً لـ yt-dlp وحل مشكلة الصوت فقط)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# تعيين مجلد العمل
WORKDIR /app

# 3. نسخ الملفات وتثبيت المتطلبات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. نسخ كود التشغيل (main.py)
COPY main.py .

# 5. أمر بدء التشغيل (استخدام المنفذ الثابت 8000)
CMD gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
