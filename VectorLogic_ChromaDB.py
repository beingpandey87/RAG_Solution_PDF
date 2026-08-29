import chromadb
from chromadb.utils import embedding_functions
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
import EmbeddingLogic

import os
from dotenv import load_dotenv
# Initialize a Local, Persistent Client

client = chromadb.PersistentClient(path="./Databases/local_vector_db")

embedding_function = OpenAIEmbeddingFunction(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name="text-embedding-3-small"
    )

collection = client.get_or_create_collection(
    name="mycollection",
    embedding_function=embedding_function
    )

def save_documents_vectors(chunk_id,chunk_text,embedding,document_id,document_name,page_no):    
    try:
        collection.add(
            ids=[chunk_id],
            documents=[chunk_text],
            embeddings=embedding,
            metadatas=[{
                "document_id": document_id,
                "document_name": document_name,
                "page_number": page_no
            }]
        )
        print("Inserted")
    except Exception as e:
        print("Error:", str(e))
        
def update_documents_vectors(chunk_id,chunk_text,embedding,document_id,document_name,page_no):    
    try:
        collection.upsert(
            ids=[chunk_id],
            documents=[chunk_text],
            embeddings=embedding,
            metadatas=[{
                "document_id": document_id,
                "document_name": document_name,
                "page_number": page_no
            }]
        )
        print("Updated")
    except Exception as e:
        print("Error:", str(e))
      

def query_data(search_query,result_count):
    query_results = collection.query(
        query_texts=[search_query],
        n_results=result_count  # Number of closest matches to return
        )
    return query_results

def all_data():
    all_data = collection.get()
    return all_data

if __name__ == "__main__":
    
    print(f"Total documents stored: {collection.count()}")
    '''
    results=all_data()
    for chunk_id, document, metadata in zip(results['ids'], results['documents'], results['metadatas']):
        print(f"ID: {chunk_id}")
        print(f"Content: {document}")
        print(f"Metadata: {metadata}")
        print("-" * 20)
    '''
    #Query Data

    #results = query_data(  "Create a short summary about PDF",10 )
    #print(results)
        

