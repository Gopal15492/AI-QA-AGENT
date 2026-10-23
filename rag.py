
from pathlib import Path

from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

DB_DIR = "chroma_db"

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150
)


def load_file(file_path: str):
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        loader = PyPDFLoader(str(path))
    elif suffix == ".docx":
        loader = Docx2txtLoader(str(path))
    elif suffix in [".txt", ".md"]:
        loader = TextLoader(
            str(path),
            encoding="utf-8"
        )
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    return loader.load()


def index_documents(file_paths: list[str]):
    documents = []

    for file_path in file_paths:
        docs = load_file(file_path)

        for doc in docs:
            doc.metadata["source"] = Path(file_path).name

        documents.extend(docs)

    if not documents:
        raise ValueError("No readable document content found.")

    chunks = splitter.split_documents(documents)

    # Create/update the persistent vector database
    db = Chroma(
        collection_name="qa_requirements",
        persist_directory=DB_DIR,
        embedding_function=embeddings,
    )

    # Add only the newly uploaded chunks
    db.add_documents(chunks)

    return len(chunks)


def retrieve_requirements(question: str, k: int = 5):
    db = Chroma(
        collection_name="qa_requirements",
        persist_directory=DB_DIR,
        embedding_function=embeddings,
    )

    results = db.similarity_search(question, k=k)

    return "\n\n".join(
        f"Source: {doc.metadata.get('source', 'Unknown')}\n"
        f"Requirement: {doc.page_content}"
        for doc in results
    )
