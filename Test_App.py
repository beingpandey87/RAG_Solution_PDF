#Custom RAG Logic
import VectorLogic
import EmbeddingLogic

#Langchain Library
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate

#------------ Directory Library-------------------#
import os
from dotenv import load_dotenv

#Loading Keys From env
load_dotenv(override=True)

def get_llm():

    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0
    )
    

def create_rag_chain():    
    # Set up Retriever to fetch top 3 matching documents
    retriever = VectorLogic.create_retriever()
    
    # Define LLM and explicit Grounding Prompt
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    system_prompt = (
        "You are a helpful assistant. Use only the provided context to answer "
        "the question. If you do not know the answer, say that you don't know.\n\n"
        "Context:\n{context}"
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{question}"),
    ])
    
    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        #| StrOutputParser()
        )
    return rag_chain

def ask_rag(question, top_k=5):
    ragchain = create_rag_chain()
    response = ragchain.invoke(question)
    return response

if __name__ == "__main__":
    rag_chain = create_rag_chain()
    answer=rag_chain.invoke("Create a short summary about PDF")
    print(answer.content)