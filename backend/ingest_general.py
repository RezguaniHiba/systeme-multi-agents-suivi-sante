# prépare les documents utilisés par le rag
import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_community.document_loaders import PyPDFLoader
from src.helper import text_split, download_hugging_face_embeddings

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY


print("Chargement de Medical_book.pdf...")
loader = PyPDFLoader("data/General/Medical_book.pdf")
documents = loader.load()
documents = [doc for doc in documents if doc.page_content.strip()]
print(f"Pages chargées : {len(documents)}")


text_chunks = text_split(documents)
print(f"Total chunks : {len(text_chunks)}")


embeddings = download_hugging_face_embeddings()


pc = Pinecone(api_key=PINECONE_API_KEY)
index_name = "medical-chatbot"

if index_name not in pc.list_indexes().names():
    print("Création de l'index 'medical-chatbot'...")
    pc.create_index(
        name=index_name,
        dimension=384,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
else:
    print("Index 'medical-chatbot' déjà existant.")


print("Upload vers Pinecone...")
PineconeVectorStore.from_documents(
    documents=text_chunks,
    index_name=index_name,
    embedding=embeddings
)

print(f"\n✅ {len(text_chunks)} chunks indexés dans 'medical-chatbot'")
