# app/core/config.py

# --- Cấu hình Model ---
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# LLM_MODEL giữ nguyên (không động)
# ASR_MODEL: Thay từ "vinai/PhoWhisper-small" sang "small" để dùng openai/whisper-small như VietGuiBot
ASR_MODEL = "small"  # Full
PARTIAL_ASR_MODEL = "tiny"  # <-- THÊM: Nhẹ cho real-time
VAD_MODE = 3  # 0-3 aggressiveness (từ VietGuiBot)

# GEMINI_API_KEY = "AIzaSyDjfseeIv8haRB139pXLnYvmMZXcCf1YRQ"  # Giữ nguyên
GEMINI_API_KEY = "AIzaSyAyfrmjggJCkJHDkb648YX_FIb137v5saA"  # Giữ nguyên
# --- Cấu hình Đường dẫn --- (giữ nguyên)
CHROMA_DB_PATH = "vector_store"
KNOWLEDGE_BASE_DIR = "data/knowledge_base_files"