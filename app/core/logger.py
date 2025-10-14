# app/core/logger.py

import logging
import sys

# Cấu hình logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout) # In log ra màn hình console
        # Bạn có thể thêm FileHandler để ghi log ra file
        # logging.FileHandler("app.log") 
    ]
)

def get_logger(name):
    return logging.getLogger(name)