# app/services/vector_store_service.py

# ĐÃ CẬP NHẬT IMPORT THEO CHUẨN MỚI NHẤT
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from app.core import config
from app.utils.document_loader import load_documents_from_directory
from app.core.logger import get_logger

logger = get_logger(__name__)

class VectorStoreService:
    def __init__(self):
        logger.info(f"Khởi tạo embedding model: {config.EMBEDDING_MODEL}")
        self.embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)
        
        logger.info("Khởi tạo cơ sở dữ liệu vector ChromaDB.")
        self.vectordb = Chroma(
            persist_directory=config.CHROMA_DB_PATH,
            embedding_function=self.embeddings
        )

    def feed_knowledge_base(self):
        logger.info("Bắt đầu quá trình nạp tri thức từ file.")
        docs = load_documents_from_directory(config.KNOWLEDGE_BASE_DIR)
        if not docs:
            logger.warning("Không tìm thấy tài liệu nào để nạp. Bỏ qua.")
            return
        
        logger.info(f"Chuẩn bị thêm {len(docs)} mẩu văn bản vào ChromaDB.")
        self.vectordb.add_documents(documents=docs)
        logger.info("Nạp tri thức vào ChromaDB thành công.")

    def query(self, query_text: str, k: int = 3) -> list[str]:
        logger.info(f"Thực hiện truy vấn ngữ nghĩa cho: '{query_text}'")
        results = self.vectordb.similarity_search(query_text, k=k)
        return [doc.page_content for doc in results]

vector_store = VectorStoreService()