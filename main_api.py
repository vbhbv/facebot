import yt_dlp
import logging
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

# إعدادات التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# نموذج طلب المستخدم
class VideoRequest(BaseModel):
    facebook_url: str

app = FastAPI(
    title="Facebook Video Downloader API",
    description="استخلاص رابط التنزيل المباشر من فيسبوك باستخدام yt-dlp.",
    version="1.0.0"
)

def get_facebook_video_url(url: str) -> Dict[str, Any]:
    """يستخرج معلومات التنزيل (الرابط المباشر والمدة) لفيديو فيسبوك."""
    ydl_opts = {
        # التعديل الحاسم: طلب أفضل صيغة فيديو وصوت مدمجة
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best', 
        'noplaylist': True,
        'skip_download': True,
        'logger': logger,
        'verbose': False, 
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # يُعتمد على الصيغة الأولى التي تم دمجها أو اختيارها
            best_format = info['formats'][0] if 'formats' in info and info['formats'] else None
            
            if best_format:
                return {
                    "success": True,
                    "title": info.get('title', 'Facebook Video'),
                    "duration": info.get('duration', 0), 
                    "direct_url": best_format.get('url'),
                }
            else:
                return {"success": False, "error": "لم يتم العثور على صيغ فيديو قابلة للتنزيل."}

    except yt_dlp.DownloadError as e:
        logger.error(f"خطأ في الاستخلاص لـ {url}: {e}")
        return {"success": False, "error": f"فشل الاستخلاص (yt-dlp): {e}"}
    except Exception as e:
        logger.error(f"خطأ غير متوقع: {e}")
        return {"success": False, "error": "حدث خطأ غير متوقع في الخادم."}

@app.post("/download")
async def download_facebook_video(request: VideoRequest):
    """نقطة النهاية التي يستدعيها بوت تليجرام."""
    if "facebook.com" not in request.facebook_url:
        raise HTTPException(status_code=400, detail="الرجاء إدخال رابط صحيح من فيسبوك.")
        
    result = get_facebook_video_url(request.facebook_url)
    
    if result["success"]:
        return {
            "status": "success",
            "title": result["title"],
            "duration": result["duration"], 
            "direct_download_url": result["direct_url"]
        }
    else:
        raise HTTPException(status_code=500, detail=result["error"])

@app.get("/")
def read_root():
    return {"message": "خدمة تنزيل فيديوهات فيسبوك تعمل."}
