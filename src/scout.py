import os
import streamlit as st
from langchain_postgres.vectorstores import PGVector
from langchain_ollama import OllamaEmbeddings
from sqlalchemy import create_engine, text

CONNECTION_STRING = os.getenv("DATABASE_URL")
if not CONNECTION_STRING:
    raise ValueError("DATABASE_URL non impostata nelle variabili d'ambiente!")

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")

embeddings = OllamaEmbeddings(model="mxbai-embed-large", base_url=OLLAMA_URL)

@st.cache_resource
def get_vectorstore():
    return PGVector(
        embeddings=embeddings,
        collection_name="player_stats",
        connection=CONNECTION_STRING,
        distance_strategy="l2",
        use_jsonb=True,
    )

def get_document_count():
    engine = create_engine(CONNECTION_STRING)
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT COUNT(*) FROM langchain_pg_embedding")
        )
        return result.scalar()

def similarity_search_with_score(query_text, k=5):
    store = get_vectorstore()
    return store.similarity_search_with_score(query_text, k=k)

def clear_database():
    store = get_vectorstore()
    store.delete_collection()
    store.create_collection()