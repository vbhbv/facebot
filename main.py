import os
import logging
import requests
import asyncio
import threading
from dotenv import load_dotenv
from io import BytesIO

# مكتبات البوت
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# مكتبات FastAPI (نحتفظ بها للاستخلاص)
import yt_dlp
from typing import Dict, Any

# 1. إعداد المتغيرات والتسجيل
load_dotenv() 

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("FACEBOOK_VIDEO_API_URL", "http://0.0.0.0:8000/download") # نستخدم رابط داخلي إذا لزم الأمر

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------------------------------------------
# 💡 الوظيفة الشرارية (1): استخلاص رابط الفيديو (بديل لخدمة FastAPI الخارجية)
# ---------------------------------------------

def get_facebook_video_url(url: str) -> Dict[str, Any]:
    """يستخرج معلومات التنزيل مباشرة داخل عملية البوت."""
    ydl_opts = {
        # طلب أفضل صيغة MP4 مدمجة فقط (يتطلب ffmpeg)
        'format': 'best[ext=mp4]/best', 
        'noplaylist': True,
        'skip_download': True,
        'logger': logger,
        'verbose': False,
        # إضافة رأسيات للمحاكاة
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            best_format = info['formats'][0] if 'formats' in info and info['formats'] else None
            
            if best_format:
                return {
                    "success": True,
                    "title": info.get('title', 'Facebook Video'),
                    "duration": info.get('duration', 0), 
                    "direct_url": best_format.get('url'),
                    "ext": best_format.get('ext', 'mp4')
                }
            else:
                return {"success": False, "error": "لم يتم العثور على صيغ فيديو قابلة للتنزيل."}

    except yt_dlp.DownloadError as e:
        logger.error(f"خطأ في الاستخلاص لـ {url}: {e}")
        return {"success": False, "error": f"فشل الاستخلاص (yt-dlp): {e}"}
    except Exception as e:
        logger.error(f"خطأ غير متوقع: {e}")
        return {"success": False, "error": "حدث خطأ غير متوقع في الخادم."}

# ---------------------------------------------
# 💡 الوظيفة الشرارية (2): متابعة وإرسال مباشر (التنزيل والتحميل)
# ---------------------------------------------

def get_final_url(url: str, headers: dict) -> str:
    """يتبع إعادة التوجيه 302 للحصول على الرابط النهائي النظيف."""
    try:
        response = requests.head(url, headers=headers, allow_redirects=True, timeout=15)
        response.raise_for_status()
        return response.url
    except Exception:
        return url

async def handle_facebook_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالجة الروابط وإرسال الفيديو عبر التنزيل والتحميل المباشر."""
    link = update.message.text
    
    if not link or "facebook.com" not in link:
        await update.message.reply_text('الرجاء إرسال رابط صحيح لفيديو من فيسبوك.')
        return

    wait_message = await update.message.reply_text('⏳ جارٍ تحليل الرابط وتطبيق الحل الثوري: التنزيل والتحميل المباشر...')
    
    tele_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # 1. استخلاص الرابط (مباشرة داخل هذه العملية)
    result = await asyncio.to_thread(get_facebook_video_url, link)

    if result.get("success") and result.get("direct_url"):
        
        title = result.get("title", "الفيديو المطلوب")
        direct_url = result.get("direct_url")
        duration = result.get("duration", 0)
        ext = result.get("ext", "mp4")
        
        final_url = get_final_url(direct_url, tele_headers) 
        
        # 2. التنزيل المباشر للمحتوى (الخطوة الحاسمة)
        try:
            # زيادة المهلة لملفات الفيديو الكبيرة
            file_response = await asyncio.to_thread(requests.get, final_url, stream=False, timeout=300, headers=tele_headers)
            file_response.raise_for_status()
        except Exception as download_e:
            logger.error(f"فشل التنزيل المباشر من رابط CDN: {download_e}")
            await wait_message.delete()
            await update.message.reply_text("⚠️ فشل التنزيل المباشر من مصدر فيسبوك. حاول مرة أخرى.")
            return

        # استخدام BytesIO لتمرير البيانات الثنائية
        video_file = BytesIO(file_response.content)
        video_file.name = f"{title}.{ext}"

        try:
            # 3. الإرسال كملف ثنائي (يضمن التشغيل بالصوت والصورة)
            await update.message.reply_video(
                video=video_file,
                caption=f"✅ تم التحميل بنجاح (تحميل مباشر): {title}",
                duration=duration, 
                supports_streaming=True,
                filename=f"{title}.{ext}",
                read_timeout=120
            )
            
            await wait_message.delete()
            
        except Exception as upload_e:
            logger.error(f"فشل إرسال الفيديو كملف: {upload_e}")
            await wait_message.delete()
            await update.message.reply_text(
                f"⚠️ فشل الإرسال إلى تليجرام. يمكنك التنزيل عبر الرابط المباشر:\n`{direct_url}`",
                parse_mode='Markdown'
            )

    else:
        await wait_message.delete()
        await update.message.reply_text(f"❌ فشل تحليل الفيديو: {result.get('error', 'خطأ غير معروف في الاستخلاص.')}")


# ---------------------------------------------
# --- تشغيل البوت والخدمة ---
# ---------------------------------------------

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('مرحباً! أرسل لي رابط فيديو من فيسبوك.')

def main() -> None:
    """تشغيل البوت في وضع Polling (مناسب لـ Railway)."""
    if not BOT_TOKEN:
        logger.error("🚫 لم يتم العثور على متغير BOT_TOKEN. يرجى إضافته يدوياً في إعدادات Railway.")
        return

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_facebook_link))
    logger.info("✅ تم تشغيل البوت بنجاح...")
    application.run_polling()

if __name__ == '__main__':
    # لتشغيل المشروع على Railway، يجب أن نستخدم أمر Gunicorn في Dockerfile
    # Gunicorn سيقوم بتشغيل هذا الملف كـ تطبيق ASGI (FastAPI) لو كنا نستخدمه، 
    # لكن في هذا النموذج، نعتمد على أن Gunicorn يستخدم `main:app` وهو ما يتسبب في الفشل.
    # لذا، نستخدم هذا الهيكل لضمان العمل على Railway:
    try:
        main()
    except Exception as e:
        logger.error(f"خطأ في تشغيل البوت: {e}")

    # بما أننا دمجنا الكود، فإننا نعتمد على أمر CMD في Dockerfile لتشغيل البوت
    # إذا كنت تريد تشغيل FastAPI كخادم فعلي (في حالتنا لا نحتاجه لأننا دمجنا الوظيفة)
    # فإننا نكتب:
    # app = FastAPI()
    # @app.get("/")
    # def read_root(): return {"message": "الخدمة تعمل."}
    # لكن هذا ليس مطلوبًا لعملية التنزيل الآن.
