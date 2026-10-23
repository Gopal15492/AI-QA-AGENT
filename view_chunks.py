from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

db = Chroma(
    collection_name="qa_requirements",
    persist_directory="chroma_db",
    embedding_function=HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    ),
)

data = db.get(include=["documents", "metadatas"])

print("Total chunks:", len(data["documents"]))

for i, document in enumerate(data["documents"], start=1):
    metadata = data["metadatas"][i - 1]

    print(f"\n{'=' * 50}")
    print(f"Chunk {i}")
    print("Source:", metadata.get("source", "Unknown"))
    print("-" * 50)
    print(document)