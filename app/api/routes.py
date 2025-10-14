# app/api/routes.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.vector_store_service import vector_store
from app.services.llm_service import llm_service
from app.services.asr_service import asr_service
from app.services.tts_service import tts_service
from app.core.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.websocket("/fay/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            try:
                # Chờ nhận dữ liệu từ client
                data = await websocket.receive()
                user_input = ""

                # Xử lý input là audio hay text
                if "bytes" in data:
                    audio_bytes = data["bytes"]
                    user_input = asr_service.transcribe(audio_bytes)
                    # Gửi lại text đã nhận dạng cho client
                    await websocket.send_json({"type": "user_text", "content": user_input})
                elif "text" in data:
                    user_input = data["text"]
                
                # Bỏ qua nếu không có input hợp lệ
                if not user_input:
                    continue

                # 1. Tìm kiếm ngữ cảnh trong ChromaDB
                context = vector_store.query(user_input)
                
                # 2. Tạo câu trả lời từ LLM (Gemini)
                ai_response_text = llm_service.generate_response(user_input, context)
                
                # 3. Gửi câu trả lời text về client
                await websocket.send_json({"type": "ai_text", "content": ai_response_text})
                
                # 4. Tạo âm thanh và gửi về client
                audio_response_bytes = await tts_service.text_to_speech(ai_response_text) # <-- THÊM AWAIT Ở ĐÂY
                if audio_response_bytes: # Thêm kiểm tra để chắc chắn có dữ liệu audio
                    await websocket.send_bytes(audio_response_bytes)

            except WebSocketDisconnect:
                # Xử lý khi client chủ động ngắt kết nối (F5, đóng tab)
                logger.info("Client đã ngắt kết nối một cách bình thường.")
                break # Thoát khỏi vòng lặp while True một cách an toàn
            
            except RuntimeError as e:
                # Bẫy lỗi khi client ngắt kết nối trong lúc server đang gửi đi
                if "once a disconnect message has been received" in str(e):
                    logger.warning(f"Kết nối đã bị đóng bởi client trong lúc xử lý: {e}")
                    break # Thoát khỏi vòng lặp
                else:
                    raise # Ném lại các lỗi RuntimeError khác không liên quan

    except Exception as e:
        # Bẫy các lỗi không mong muốn khác
        logger.error(f"Một lỗi không xác định đã xảy ra trong WebSocket: {e}", exc_info=True)
        