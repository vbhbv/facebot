# Dockerfile
# استخدام صورة بايثون أساسية
FROM python:3.11-slim

# 1. تثبيت ffmpeg والأدوات الأساسية (يحل مشكلة "الصوت فقط" ويدعم yt-dlp)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# تعيين مجلد العمل
WORKDIR /app

# 2. نسخ ملفات المشروع وتثبيت المتطلبات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. نسخ الكود المدمج
COPY main.py .
COPY .env . # نسخ ملف .env (للاستخدام المحلي فقط)

# 4. أمر بدء التشغيل (يحل مشكلة $PORT باستخدام Gunicorn)
# نستخدم Gunicorn لتشغيل Uvicorn (خادم FastAPI)
CMD gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:"$PORT"
