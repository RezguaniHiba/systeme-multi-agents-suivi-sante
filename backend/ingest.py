# prépare les documents utilisés par le rag
import os
import uuid
from dotenv import load_dotenv

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME       = os.getenv("PINECONE_INDEX")

PDF_FILES = [
    {"path": "data/cbtskills.pdf",        "source": "CBT Skills Workbook (NHS / clinique)"},
    {"path": "data/cbt_Anxiety.pdf",      "source": "ANXIETY CBT WORKBOOK"},
    {"path": "data/nimh_depression.pdf",  "source": "NIMH – Depression"},
]


def load_all_documents():
    all_docs = []

    for entry in PDF_FILES:
        if not os.path.exists(entry["path"]):
            print(f"[SKIP] Fichier introuvable : {entry['path']}")
            continue
        try:
            loader = PyPDFLoader(entry["path"])
            docs   = loader.load()
            for doc in docs:
                doc.metadata["source"] = entry["source"]
            all_docs.extend(docs)
            print(f"[OK] PDF chargé : {entry['source']} ({len(docs)} pages)")
        except Exception as e:
            print(f"[ERROR] {entry['path']} : {e}")

    return all_docs


print("=" * 50)
print("INGEST — Chargement des sources (mental health)")
print("=" * 50)

documents = load_all_documents()

if not documents:
    print("\n[ERREUR] Aucun document chargé. Vérifie tes sources.")
    exit(1)

print(f"\nTotal : {len(documents)} document(s) chargé(s)")


splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
)
docs = splitter.split_documents(documents)
print(f"Chunks créés : {len(docs)}")

print("Chargement du modèle d'embeddings HuggingFace...")
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

import time
pc = Pinecone(api_key=PINECONE_API_KEY)

if INDEX_NAME not in [idx.name for idx in pc.list_indexes()]:
    pc.create_index(
        name=INDEX_NAME,
        dimension=384,      
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
    )
    print(f"Index '{INDEX_NAME}' créé (dim=384).")
else:
    print(f"Index '{INDEX_NAME}' existant trouvé.")

index = pc.Index(INDEX_NAME)


BATCH_SIZE = 100
vectors    = []

print("\nGénération des embeddings et upload...")

for i, doc in enumerate(docs):
    try:
        vector = embeddings.embed_query(doc.page_content)
    except Exception as e:
        print(f"  [RETRY] Erreur chunk {i}, attente 5s... ({e})")
        time.sleep(5)
        vector = embeddings.embed_query(doc.page_content)

    vectors.append({
        "id": str(uuid.uuid4()),
        "values": vector,
        "metadata": {
            "text":   doc.page_content,
            "source": doc.metadata.get("source", "unknown"),
        },
    })

    if (i + 1) % 50 == 0:
        print(f"  [{i+1}/{len(docs)}] chunks traités...")

    if len(vectors) >= BATCH_SIZE:
        index.upsert(vectors=vectors)
        print(f"  Batch uploadé ({i + 1}/{len(docs)} chunks)")
        vectors = []

if vectors:
    index.upsert(vectors=vectors)
    print(f"  Dernier batch uploadé ({len(docs)}/{len(docs)} chunks)")

print("\n✅ Ingestion terminée.")
print(f"   {len(docs)} chunks indexés dans Pinecone (index: {INDEX_NAME})")