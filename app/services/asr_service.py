# Thay thế toàn bộ file: app/services/asr_service.py

import torch
import whisper
import webrtcvad
import numpy as np
import io
from pydub import AudioSegment
from app.core.config import ASR_MODEL
from app.core.logger import get_logger

logger = get_logger(__name__)

# QUAN TRỌNG: Hãy chắc chắn rằng đường dẫn FFmpeg là chính xác
try:
    AudioSegment.converter = "C:/ProgramData/chocolatey/bin/ffmpeg.exe"
    AudioSegment.ffprobe   = "C:/ProgramData/chocolatey/bin/ffprobe.exe"
    logger.info("✅ Pydub has been configured to use FFmpeg.")
except Exception:
    logger.error("❌ FFMPEG NOT FOUND! Voice recording will fail.")

class ASRService:
    def __init__(self):
        logger.info(f"Loading ASR model: {ASR_MODEL}...")
        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model = whisper.load_model(ASR_MODEL, device=device)
            self.vad = webrtcvad.Vad(mode=3)
            logger.info(f"✅ Whisper model '{ASR_MODEL}' loaded on '{device}'.")
        except Exception as e:
            logger.error(f"Fatal error loading ASR model: {e}", exc_info=True)
            raise

    def transcribe(self, audio_bytes: bytes) -> str:
        if not isinstance(audio_bytes, bytes) or len(audio_bytes) < 1000:
            logger.warning("Invalid or too short audio data, skipping.")
            return ""

        try:
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
            audio_segment = audio_segment.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            pcm_data = audio_segment.raw_data

            frame_duration_ms = 30
            frame_size = int(16000 * frame_duration_ms / 1000) * 2
            speech_frames = [
                pcm_data[i:i + frame_size]
                for i in range(0, len(pcm_data), frame_size)
                if len(pcm_data[i:i + frame_size]) == frame_size and self.vad.is_speech(pcm_data[i:i + frame_size], 16000)
            ]

            if not speech_frames:
                logger.warning("VAD did not detect any speech.")
                return ""

            trimmed_pcm_data = b"".join(speech_frames)
            trimmed_audio_float = np.frombuffer(trimmed_pcm_data, dtype=np.int16).astype(np.float32) / 32768.0

            logger.info(f"Transcribing {len(trimmed_audio_float)/16000:.2f}s of audio...")
            result = self.model.transcribe(trimmed_audio_float, language="vi", fp16=torch.cuda.is_available())
            text = result.get("text", "").strip()
            logger.info(f"✅ Transcription result: '{text}'")
            return text

        except Exception as e:
            logger.error(f"Error during transcription: {e}", exc_info=True)
            return "Lỗi hệ thống nhận dạng giọng nói."

asr_service = ASRService()