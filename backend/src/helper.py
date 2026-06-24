# prépare les documents utilisés par le rag
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings


def load_pdf_file(data):

    loader = DirectoryLoader(
        data,
        glob="*.pdf",
        loader_cls=PyPDFLoader
    )

    documents = loader.load()

    return documents


def filter_to_minimal_docs(documents):

    filtered = []

    for doc in documents:

        if doc.page_content.strip():
            filtered.append(doc)

    return filtered


def text_split(extracted_data):

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    text_chunks = text_splitter.split_documents(extracted_data)

    return text_chunks


def download_hugging_face_embeddings():

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    return embeddings
