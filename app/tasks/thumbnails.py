from celery import shared_task
from PIL import Image, UnidentifiedImageError
import io, asyncio, requests

from app.database import async_session_maker
from app.models.file import File



@shared_task(name="app.tasks.thumbnails.resize_image")
def resize_image(file_id: int, get_url: str, put_url: str, thumb_key: str):

    """
    Create a 256px JPEG thumbnail
    """
    try:
        with requests.get(get_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            img = Image.open(r.raw).convert("RGB")

        img.thumbnail((256, 256))

        output = io.BytesIO()
        img.save(output, format="JPEG", quality=82, optimize=True)
        output.seek(0)

        # Upload to S3
        put_resp = requests.put(
            put_url,
            data= output.getvalue(),
            headers={"Content-Type": "image/jpeg"},
            timeout=60,
        )
        put_resp.raise_for_status()
    except UnidentifiedImageError:
        return {"ok": False, "reason": "unidentified_image"}

    except requests.RequestException as e:
        return {"ok": False, "reason": f"http_error: {e}"}
    
    
    #save tumbnail_key in db
    async def _update():
        async with async_session_maker() as session:
            obj = await session.get(File, file_id)
            if obj:
                obj.thumbnail_key = thumb_key
                await session.commit()

    asyncio.run(_update())
    return {"ok": True}


