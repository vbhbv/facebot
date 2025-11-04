# Dockerfile
# استخدام صورة بايثون أساسية
FROM python:3.11-slim

# تثبيت ffmpeg والأدوات الأساسية
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
COPY Procfile .

# أمر بدء التشغيل (يستخدم Procfile)
CMD ["/bin/bash", "-c", "python -m uvicorn main_api:app --host 0.0.0.0 --port $PORT"] 
