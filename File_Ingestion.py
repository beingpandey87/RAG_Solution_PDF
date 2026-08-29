import pandas as pd
from langchain_core.documents import Document 

from datetime import datetime
import os
from pathlib import Path

#customr lib
import utils
import LocalDB
import PDF_Extractor
import ChunkingLogic
import EmbeddingLogic
import VectorLogic_ChromaDB

from dotenv import load_dotenv

load_dotenv(override=True)
base_output_dir = "E:\\ML Live AI ML Projects\\Document RAG\\ExtractedContents" 

def index_pdf(file_path:str):
    # Creating Local Storage Directory
    file_name,images_dir, tables_dir, content_dir = utils.create_directories(file_path, base_output_dir)
    
    # Add records to local db
    document_id=LocalDB.insert_file_meta(file_name,"pdf",file_path,0,datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"")
    
    # Extract content from file in sub catory folders
    reult=PDF_Extractor.extract_pdf_data(file_path,images_dir,tables_dir,content_dir)
    
    # -----------------------------Ingestion Process on extracted data---------------------------- #
    
    # Extract the text data first #
    for file_dir in content_dir.glob("*.txt"):
        with open(file_dir, "r", encoding="utf-8") as file:
            file_data = file.read()
            chunk_data,chunk_ids=ChunkingLogic.text_content_chunking(file_data,400,50)
            embedded_data=EmbeddingLogic.embedding_content_list(chunk_data)
            page_no = int(Path(file_dir).stem.split("_")[2])
            for chunk,id, embedd in zip(chunk_data, chunk_ids, embedded_data):
                VectorLogic_ChromaDB.save_documents_vectors(str(id),chunk,[embedd],document_id,file_name,page_no)
    
    # Extracting the tabular data next
    for file_dir in tables_dir.glob("*.html"):
        with open(file_dir, "r", encoding="utf-8") as file:
            file_data = file.read()
            chunk_data,chunk_ids=ChunkingLogic.html_content_recursive_chunking_with_markdown(file_data,400,50)
            embedded_data=EmbeddingLogic.embedding_content_list(chunk_data)
            page_no = int(Path(file_dir).stem.split("_")[2])
            for chunk,id, embedd in zip(chunk_data, chunk_ids, embedded_data):
                VectorLogic_ChromaDB.save_documents_vectors(str(id),chunk,[embedd],document_id,file_name,page_no)
                   
    
            
if __name__ == "__main__":
    #SAMPLE_PDF = "C:\\RAG_Practice_Advance\\SampleFiles\\sample20page.pdf" 
    #index_pdf(SAMPLE_PDF)
    
    files_dir = "E:\\ML Live AI ML Projects\\Document RAG\\SampleFiles" 
    for file_dir in Path(files_dir).glob("*.pdf"):
        index_pdf(str(file_dir))