from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import time
from app.services.logger import log_queue

router = APIRouter()

def log_stream():
    while True:
        try:
            message = log_queue.get(timeout=1)
            yield f"data: {message}\n\n"
        except:
            time.sleep(0.5)

@router.get("/stream")
def stream_logs():
    return StreamingResponse(
        log_stream(),
        media_type="text/event-stream"
    )
