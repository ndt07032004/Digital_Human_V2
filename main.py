# main.py

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager # <-- THÊM DÒNG NÀY
from app.api import routes
from app.services.vector_store_service import vector_store
from app.core.logger import get_logger
import uvicorn

logger = get_logger(__name__)

# --- BẮT ĐẦU PHẦN CẬP NHẬT ---
# Sử dụng 'lifespan' thay cho on_event('startup')
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code chạy khi server khởi động
    logger.info("Server bắt đầu khởi động...")
    vector_store.feed_knowledge_base()
    logger.info("Server đã sẵn sàng hoạt động. Truy cập http://localhost:8000")
    yield
    # Code chạy khi server tắt (nếu cần)
    logger.info("Server đang tắt...")

# Thêm 'lifespan=lifespan' vào khi khởi tạo app
app = FastAPI(title="Digital Human V2 API", lifespan=lifespan)
# --- KẾT THÚC PHẦN CẬP NHẬT ---


# Các phần còn lại giữ nguyên
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(routes.router)



@app.get("/", include_in_schema=False)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)