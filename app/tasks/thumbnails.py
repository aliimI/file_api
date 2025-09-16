from celery import shared_task
from PIL import Image, UnidentifiedImageError, ImageFile
import io, asyncio, requests
import logging

from app.database import async_session_maker
from app.models.file import File
from app.tasks.celery_app import celery_app

log = logging.getLogger(__name__)
ImageFile.LOAD_TRUNCATED_IMAGES = True



def _sniff(b: bytes) -> str:
    """
        Small format detector by signature

    """
    ms = b[:12] #ms - magic signature
    if ms.startswith(b"\xFF\xD8\xFF") : return "jpeg"
    if ms.startswith(b"\x89PNG\r\n\x1a\n"): return "png"
    if ms[:4] == b"RIFF" and b"WEBP" in ms[:12]: return "webp"
    if ms[4:8] == b"ftyp" and any(tag in ms[8:16] for tag in (b"avif", b"avis", b"mif1", b"heic", b"heix")):
        return "avif/heif"
    if ms.startswith(b"<"): return "xml/html"
    return "unknown"



@shared_task(name="app.tasks.thumbnails.resize_image")
def resize_image(file_id: int, get_url: str, put_url: str, thumb_key: str):

    """
    Create a 256px JPEG thumbnail
    """
    try:
        r = requests.get(get_url, timeout=60)
        r.raise_for_status()
        data = r.content

        ct  = r.headers.get("Content-Type")
        enc = r.headers.get("Content-Encoding")
        
        kind = _sniff(data)

        log.warning(f"[thumb] GET ok len={len(data)} ct={ct} enc={enc} kind={kind}")

        if kind in ("xml/html", "unknown"):
            sample = data[:64].hex()
            log.warning(f"[thumb] suspicious head={sample}")
            return {"ok": False, "reason": f"bad_content:{kind}"}

        # (bio + verify) быстрая проверка целостности чтобы отловить битые или обрезанные файлы
       
        try:
            Image.open(io.BytesIO(data)).verify()
        except UnidentifiedImageError:
            log.warning("[thumb] verify: unidentified_image")
            return {"ok": False, "reason": "unidentified_image"}
        

        
        img = Image.open(io.BytesIO(data)).convert("RGB")
        img.thumbnail((256, 256))

        output = io.BytesIO()
        img.save(output, format="JPEG", quality=82, optimize=True)
        output.seek(0)

        # Upload to S3
        put_resp = requests.put(
            put_url,
            data= output.getvalue(),
            headers={"Content-Type": "image/jpeg", "Cache-Control": "public, max-age=31536000"},
            timeout=60,
        )
        log.warning(f"[thumb] PUT status={put_resp.status_code} text={put_resp.text[:200]}")
        put_resp.raise_for_status()

        return {"ok": True, "thumb_key": thumb_key, "size": output.tell()}

    except UnidentifiedImageError:
        log.warning("[thumb] open: unidentified_image")
        return {"ok": False, "reason": "unidentified_image"}

    except Exception as e:
        log.exception(f"[thumb] ERROR:")
        return {"ok": False, "reason": f"http_error: {e}"}
    
    


