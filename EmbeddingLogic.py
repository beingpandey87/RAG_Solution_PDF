from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
import os

load_dotenv()
 
def embedding_content(text_content:str, embedding_algo: str="text-embedding-3-small"):   
    embeddings = OpenAIEmbeddings(
        model=embedding_algo
    )
    query_embedding = embeddings.embed_query(text_content)
    return query_embedding

def embedding_content_list(list_content:list[str], embedding_algo: str="text-embedding-3-small"):   
    embeddings = OpenAIEmbeddings(
        model=embedding_algo,
    )
    content_embeddings = embeddings.embed_documents(list_content)
    return content_embeddings

def creating_embedding_object(embedding_algo: str="text-embedding-3-small"):
    return OpenAIEmbeddings(
        model=embedding_algo,
    )