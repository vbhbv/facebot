# Dockerfile
# استخدام صورة بايثون أساسية
FROM python:3.11-slim

# تثبيت ffmpeg والأدوات الأساسية
# هذا يحل مشكلة "الصوت فقط"
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# تعيين مجلد العمل
WORKDIR /app

# نسخ ملفات المشروع وتثبيت المتطلبات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ كود FastAPI
COPY main_api.py .
# ❌❌ إزالة السطر: COPY Procfile . ❌❌ (كان هنا)

# أمر بدء التشغيل الحاسم: استخدام CMD مع Gunicorn لضمان قراءة $PORT
CMD gunicorn main_api:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:"$PORT"
