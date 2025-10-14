# app/services/tts_service.py

import asyncio
import edge_tts
from app.core.logger import get_logger

logger = get_logger(__name__)

# --- Cấu hình giọng nói và tốc độ ---
VOICE = "vi-VN-HoaiMyNeural" # Giọng nữ miền Nam
RATE = "+35%"                # Tốc độ nhanh hơn 35%

class TTSService:
    """
    Sử dụng dịch vụ TTS của Microsoft Edge, được viết lại để hoạt động
    hoàn toàn bất đồng bộ (async) với FastAPI.
    """
    async def text_to_speech(self, text: str) -> bytes:
        """
        Đây là một hàm coroutine (async def).
        Nó sẽ chạy mượt mà trên event loop của FastAPI.
        """
        logger.info(f"Bắt đầu tạo giọng nói với tốc độ {RATE}...")
        try:
            communicate = edge_tts.Communicate(text, VOICE, rate=RATE)
            
            # Sử dụng list comprehension để thu thập các chunk audio một cách hiệu quả
            audio_chunks = [chunk["data"] async for chunk in communicate.stream() if chunk["type"] == "audio"]
            
            if not audio_chunks:
                logger.warning("Không tạo được dữ liệu audio từ TTS.")
                return b""
                
            logger.info("Tạo giọng nói thành công.")
            # Ghép các chunk lại thành một mảng bytes hoàn chỉnh
            return b"".join(audio_chunks)
            
        except Exception as e:
            logger.error(f"Lỗi khi tạo TTS với edge-tts: {e}", exc_info=True)
            return b""

# Khởi tạo instance duy nhất để tái sử dụng
tts_service = TTSService()