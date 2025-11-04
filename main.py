from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from downloader import get_facebook_video_url
import uvicorn

# تعريف نموذج البيانات (Schema) للطلب الوارد
class VideoRequest(BaseModel):
    facebook_url: str

# تهيئة التطبيق
app = FastAPI(
    title="Facebook Video Downloader API",
    description="واجهة برمجية لتنزيل فيديوهات فيسبوك باستخدام yt-dlp.",
    version="1.0.0"
)

@app.post("/download")
async def download_facebook_video(request: VideoRequest):
    """
    نقطة النهاية لاستلام رابط فيسبوك وإرجاع رابط التنزيل المباشر.
    """
    # التحقق من أن الرابط يحتوي على كلمة "facebook"
    if "facebook.com" not in request.facebook_url:
        raise HTTPException(status_code=400, detail="الرجاء إدخال رابط صحيح من فيسبوك.")
        
    # استدعاء دالة الاستخلاص
    result = get_facebook_video_url(request.facebook_url)
    
    if result["success"]:
        return {
            "status": "success",
            "title": result["title"],
            "direct_download_url": result["direct_url"]
        }
    else:
        # إرجاع خطأ API إذا فشل الاستخلاص
        raise HTTPException(status_code=500, detail=result["error"])

@app.get("/")
def read_root():
    """رسالة ترحيب بسيطة."""
    return {"message": "مرحباً بك في خدمة تنزيل فيديوهات فيسبوك. استخدم نقطة النهاية /download"}

if __name__ == "__main__":
    # تشغيل الخادم
    # Host '0.0.0.0' ضروري للتشغيل على بيئات سحابية مثل Replit
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
  
