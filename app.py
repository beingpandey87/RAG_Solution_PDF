import streamlit as st

#Custom RAG Logic
import VectorLogic
import TextEmbedding

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

#------------------------Common Function-------------------------#

def get_llm():

    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0
    )
    
@st.cache_resource
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
        | StrOutputParser()
        )
    return rag_chain

def ask_rag(question):
    ragchain = create_rag_chain()
    response = ragchain.invoke(question)
    return response

#Initialize Rag Chain
rag_chain=create_rag_chain()

#------------------------------------------------------------------------------------#


# Setup page configuration
st.set_page_config(
    page_title="RAG Assistant using LCEL",
    page_icon="🤖",
    layout="wide"
)
# ST Session History
if 'message_history' not in st.session_state:
    st.session_state['message_history']=[] 

# Display old message as well
for message in st.session_state['message_history']:
     with st.chat_message(message["role"]):
            st.text(message["content"])
   
# Chat Interface
user_input=st.chat_input("Type here")

if user_input:
    # First add the message to message history
    st.session_state['message_history'].append({
        "role":"user",
        "content":user_input
    })
    with st.chat_message('user'):
        st.text(user_input)
    
    #----------------------------#
           
    with st.chat_message('assistant'):
        with st.spinner("Searching documents..."):
            #rag_chain = create_rag_chain()
            answer=rag_chain.invoke(user_input)
            st.write(answer)
            
    st.session_state['message_history'].append({
                "role":"assistant",
                "content":answer
            }) 