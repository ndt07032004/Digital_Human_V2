# app/services/asr_service.py

import io
import torch
import whisper
import webrtcvad
import numpy as np
from pydub import AudioSegment
from app.core.config import ASR_MODEL
from app.core.logger import get_logger

logger = get_logger(__name__)

# ⚙️ Cấu hình FFmpeg
try:
    AudioSegment.converter = "C:/ProgramData/chocolatey/bin/ffmpeg.exe"
    AudioSegment.ffprobe   = "C:/ProgramData/chocolatey/bin/ffprobe.exe"
    logger.info("✅ FFmpeg configured for Pydub.")
except Exception:
    logger.error("❌ FFmpeg not found! Check installation path.")

class ASRService:
    def __init__(self):
        """Khởi tạo mô hình Whisper + VAD."""
        logger.info(f"🔊 Loading Whisper ASR model: {ASR_MODEL} ...")
        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model = whisper.load_model(ASR_MODEL, device=device)
            self.vad = webrtcvad.Vad(mode=2)
            logger.info(f"✅ Whisper model '{ASR_MODEL}' loaded on {device}.")
        except Exception as e:
            logger.error(f"❌ Failed to load Whisper model: {e}", exc_info=True)
            raise

    def transcribe(self, audio_bytes: bytes) -> str:
        """Nhận bytes âm thanh (WAV hoặc WebM) → text tiếng Việt."""
        if not isinstance(audio_bytes, bytes) or len(audio_bytes) < 2000:
            logger.warning(f"⚠️ Invalid or too short audio: {len(audio_bytes)} bytes.")
            return ""

        try:
            # 🧩 Cố đọc theo thứ tự: WAV → WebM
            try:
                audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format="wav")
                logger.info("✅ Đọc thành công file WAV.")
            except Exception as e_wav:
                logger.warning(f"⚠️ Không đọc được WAV ({e_wav}), thử WebM...")
                try:
                    audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format="webm")
                    logger.info("✅ Đọc thành công file WebM.")
                except Exception as e_webm:
                    logger.error(f"❌ Không thể đọc audio (WAV/WebM): {e_webm}", exc_info=True)
                    return "Lỗi định dạng âm thanh (không đọc được)."

            # Chuẩn hóa: 16kHz mono PCM
            audio_segment = audio_segment.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            pcm_data = audio_segment.raw_data

            # Voice Activity Detection
            frame_ms = 30
            frame_bytes = int(16000 * frame_ms / 1000) * 2
            frames = [
                pcm_data[i:i + frame_bytes]
                for i in range(0, len(pcm_data), frame_bytes)
                if len(pcm_data[i:i + frame_bytes]) == frame_bytes
                and self.vad.is_speech(pcm_data[i:i + frame_bytes], 16000)
            ]

            if not frames:
                logger.warning("⚠️ VAD không phát hiện giọng nói. Dùng toàn bộ audio.")
                frames = [pcm_data]

            trimmed_pcm = b"".join(frames)
            audio_np = np.frombuffer(trimmed_pcm, dtype=np.int16).astype(np.float32) / 32768.0
            duration = len(audio_np) / 16000

            logger.info(f"🧠 Nhận dạng giọng nói ({duration:.2f}s)...")
            result = self.model.transcribe(audio_np, language="vi", fp16=torch.cuda.is_available())
            text = result.get("text", "").strip()
            logger.info(f"✅ Kết quả ASR: “{text}”")

            return text or "Không nhận dạng được giọng nói."

        except Exception as e:
            logger.error(f"❌ Lỗi khi xử lý nhận dạng: {e}", exc_info=True)
            return "Lỗi hệ thống nhận dạng giọng nói."

# Instance toàn cục
asr_service = ASRService()
