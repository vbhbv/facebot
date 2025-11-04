# Dockerfile
# استخدام صورة بايثون أساسية
FROM python:3.11-slim

# 1. تثبيت ffmpeg والأدوات الأساسية (يحل مشكلة "الصوت فقط")
# هذا يتطلب صلاحيات root لتثبيت الحزم
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# تعيين مجلد العمل
WORKDIR /app

# 2. نسخ ملفات المشروع وتثبيت المتطلبات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. نسخ كود FastAPI (بدون Procfile)
COPY main_api.py .

# 4. أمر بدء التشغيل الحاسم ( CMD )
# استخدام Gunicorn لضمان قراءة $PORT بشكل صحيح في بيئة Railway/Docker
CMD gunicorn main_api:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:"$PORT"
