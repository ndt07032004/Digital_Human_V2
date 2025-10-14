# app/utils/document_loader.py

import os
# Sửa lại import cho đúng chuẩn mới
from langchain_community.document_loaders import PyPDFLoader, CSVLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

def load_documents_from_directory(directory_path: str):
    all_docs = []
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        if filename.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
            all_docs.extend(loader.load())
        elif filename.endswith(".csv"):
            loader = CSVLoader(file_path)
            all_docs.extend(loader.load())
        elif filename.endswith(".txt"):
            loader = TextLoader(file_path)
            all_docs.extend(loader.load())
            
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    split_docs = text_splitter.split_documents(all_docs)
    return split_docs