# Dockerfile
# ... (بقية الأكواد)

# 2. نسخ ملفات المشروع وتثبيت المتطلبات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. نسخ الكود المدمج
COPY main.py .
# ❌❌ إزالة سطر: COPY .env . ❌❌ 

# 4. أمر بدء التشغيل
CMD gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:"$PORT"
