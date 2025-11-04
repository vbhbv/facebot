import yt_dlp
import logging
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

# إعدادات التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoRequest(BaseModel):
    facebook_url: str

app = FastAPI(title="Facebook Video Downloader API", version="1.0.0")

def get_facebook_video_url(url: str) -> Dict[str, Any]:
    """يستخرج معلومات التنزيل مع فرض صيغة مدمجة."""
    ydl_opts = {
        # أمر معقد لفرض دمج الصوت والفيديو:
        # 1. يبحث عن أفضل صيغة (صوت وفيديو مدمجين) 
        # 2. إذا لم يجد، يدمج أفضل فيديو MP4 مع أفضل صوت M4A
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best', 
        'noplaylist': True,
        'skip_download': True,
        'logger': logger,
        'verbose': False,
        'format_sort': ['res', 'ext:mp4:m4a'], # إعطاء الأولوية للـ MP4 و M4A
        # إضافة رأسيات للمحاكاة (للتغلب على قيود فيسبوك)
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # يُعتمد على الصيغة الأولى التي تم اختيارها (المفروض أن تكون مدمجة)
            best_format = info['formats'][0] if 'formats' in info and info['formats'] else None
            
            if best_format:
                return {
                    "success": True,
                    "title": info.get('title', 'Facebook Video'),
                    "duration": info.get('duration', 0), 
                    "direct_url": best_format.get('url'),
                    "ext": best_format.get('ext', 'mp4') # نوع الامتداد
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
    result = get_facebook_video_url(request.facebook_url)
    
    if result["success"]:
        return {
            "status": "success",
            "title": result["title"],
            "duration": result["duration"], 
            "ext": result["ext"],
            "direct_download_url": result["direct_url"]
        }
    else:
        raise HTTPException(status_code=500, detail=result["error"])

@app.get("/")
def read_root():
    return {"message": "خدمة تنزيل فيديوهات فيسبوك تعمل."}
