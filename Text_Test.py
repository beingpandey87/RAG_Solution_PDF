import TextLoader
import TextChunking
import TextEmbedding
import TextSqlDB
import VectorLogic
import pandas as pd

from langchain_core.documents import Document 
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv(override=True)

def index_text_doc(path:str):
    doc=TextLoader.load_text_file(path)
    file_name=doc.metadata["file_name"]
    chunks=TextChunking.recursive_character_splitting(doc.page_content,500,40)
    print(chunks[0])
        
    TextSqlDB.create_table()
    file_id=TextSqlDB.insert_file_meta(file_name, "text", 0,datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"")
    print(TextSqlDB.get_file_by_id(file_id))
        
    VectorLogic.create_new_index("rag-index")
        
    for i,chunk in enumerate(chunks):
        embeddedContents=TextEmbedding.embedding_content(chunk)
        #file_name=doc.metadata["file_name"]
        vector_id=f"{file_name}-chunk-{i}"
        new_meta={
            "source":doc.metadata["source"],
            "file_name": doc.metadata["file_name"],
            "document_id":file_id,
            "document_type":"txt",
            "doc_page":i,
            "text":chunk
        }
        VectorLogic.save_data_index(index_name="rag-index", vector_id=vector_id,values=embeddedContents,metadata=new_meta,namespace="Test_App")
        
def query_information(query_data:str):
     vector_query=TextEmbedding.embedding_content(query_data)
     result=VectorLogic.query_data("rag-index",query_vector=vector_query)
     return result
 
 
if __name__ == "__main__": 
    #First Index File
    #path="C:\\RAG_Practice\\mycode\\TestDocs\\text_sample4.txt"
    #index_text_doc(path)
    
    #Query Data
    result=query_information("Create a short summary about PDF")
    print(result)
    
    #Query local DB data
    result=pd.DataFrame(TextSqlDB.get_file_meta_list())
    print(result)
    
    