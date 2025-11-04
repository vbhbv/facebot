import yt_dlp
import logging

# إعدادات التسجيل للمساعدة في تتبع الأخطاء
logging.basicConfig(level=logging.INFO)

def get_facebook_video_url(url: str) -> dict:
    """
    يستخرج معلومات التنزيل (بما في ذلك الرابط المباشر) لفيديو فيسبوك.
    """
    ydl_opts = {
        'format': 'best',  # اختيار أفضل جودة متاحة
        'noplaylist': True,
        'skip_download': True, # لا تقم بالتنزيل، فقط استخرج المعلومات
        'logger': logging.getLogger(),
        'verbose': True, # لعرض معلومات مفصلة (يمكن تعطيلها عند النشر)
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # استخراج المعلومات
            info = ydl.extract_info(url, download=False)
            
            # البحث عن أفضل تنسيق (عادةً يكون أول عنصر في قائمة formats)
            best_format = info['formats'][0] if 'formats' in info and info['formats'] else None
            
            if best_format:
                # إرجاع البيانات المطلوبة
                return {
                    "success": True,
                    "title": info.get('title', 'Facebook Video'),
                    "duration": info.get('duration'),
                    "direct_url": best_format.get('url'),
                    "ext": best_format.get('ext', 'mp4')
                }
            else:
                return {"success": False, "error": "لم يتم العثور على صيغ فيديو قابلة للتنزيل."}

    except yt_dlp.DownloadError as e:
        logging.error(f"خطأ في التنزيل/الاستخلاص لـ {url}: {e}")
        return {"success": False, "error": f"فشل الاستخلاص: {e}"}
    except Exception as e:
        logging.error(f"خطأ غير متوقع: {e}")
        return {"success": False, "error": "حدث خطأ غير متوقع في الخادم."}

# مثال بسيط للاختبار (سيتم استخدامه في main.py)
if __name__ == '__main__':
    # ضع هنا رابط فيديو فيسبوك عام للاختبار
    test_url = "https://www.facebook.com/facebookapp/videos/1234567890" 
    result = get_facebook_video_url(test_url)
    print(result)
