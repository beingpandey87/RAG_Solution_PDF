import os
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
import EmbeddingLogic as TextEmbedding

load_dotenv()
client=OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc=Pinecone(api_key=os.getenv("PINECONE_API_KEY"))


index_name=os.getenv("PINECONE_INDEX")

def create_new_index(index_name:str):
    if index_name not in [i["name"] for i in pc.list_indexes()]:
        pc.create_index( name=index_name, dimension=1536, metric="cosine", spec=ServerlessSpec(cloud="aws", region="us-east-1"))
        index=pc.Index(index_name)
        print(f"Index named {index_name} was successfully created")
        return index
    else:
        print(f"Index named {index_name} is already present")

   
def save_data_index(index_name: str, vector_id: str, values, metadata: dict, namespace: str):
    """
    Upsert a single vector into Pinecone.
    Sample calling Logic:
    #
    pinecone_manager.upsert_vector(
        index_name="rag-index",
        vector_id="doc1",
        values=embedding,
        metadata={
            "source": "sample.pdf",
            "page": 1,
            "text": "This is a sample chunk"
        }
    
    )
    #
    """

    index=pc.Index(index_name)
    record={
        "id":vector_id,
        "values":values,
        "metadata":metadata,
    }

    index.upsert(
                vectors=[record],
                namespace=namespace
            )

    print(f"Vector '{vector_id}' uploaded successfully.")
    
def query_data(index_name:str,query_vector:list[float]):
    index = pc.Index(index_name)
    results = index.query(
    vector=query_vector,
    top_k=5,
    namespace="Test_App",
    include_metadata=True,
    include_values=True,           
    )
    return results

def create_retriever():
    embeddings = TextEmbedding.creating_embedding_object()
    vectorstore = PineconeVectorStore.from_existing_index(
        index_name="rag-index", embedding=embeddings, namespace="Test_App", pool_threads=6
    )
    return vectorstore.as_retriever()