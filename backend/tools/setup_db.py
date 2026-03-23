# backend/tools/setup_db.py

import os
import time
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Load API key from .env (still needed for Gemini LLM)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_file = os.path.join(BASE_DIR, ".env")

load_dotenv(env_file, override=True)
load_dotenv(override=True)

# Paths
PDF_PATH = os.path.join(BASE_DIR, "data", "comprehensive-clinical-nephrology.pdf")
CHROMA_DIR = os.path.join(BASE_DIR, "data", "chroma_db")

def build_chroma_index():
    print("🚀 Loading the PDF... This may take a few minutes...")
    loader = PyPDFLoader(PDF_PATH)
    documents = loader.load()

    print(f"✅ Loaded {len(documents)} pages from the PDF")

    # Split into smaller chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " "]
    )
    chunks = text_splitter.split_documents(documents)
    print(f"🧩 Created {len(chunks)} text chunks")

    # Create LOCAL embeddings using HuggingFace (NO API LIMITS!)
    print("✨ Creating embeddings with HuggingFace (local, no API limits)...")
    print("📥 Downloading model 'all-MiniLM-L6-v2' (first time only)...")
    
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

    # Build ChromaDB index with batching
    print("⚙️ Building ChromaDB index...")
    print("💡 Using local embeddings - no API rate limits!")
    
    # Process in batches for progress tracking
    batch_size = 500  # Larger batches since it's local
    total_batches = (len(chunks) + batch_size - 1) // batch_size
    
    vectorstore = None
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        print(f"📦 Processing batch {batch_num}/{total_batches} ({len(batch)} chunks)...")
        
        if vectorstore is None:
            # Create new vectorstore with first batch
            vectorstore = Chroma.from_documents(
                documents=batch,
                embedding=embeddings,
                persist_directory=CHROMA_DIR,
                collection_name="medical_knowledge"
            )
        else:
            # Add to existing vectorstore
            vectorstore.add_documents(batch)

    print(f"🎉 ChromaDB index successfully created and saved at: {CHROMA_DIR}")
    print(f"📊 Total chunks indexed: {len(chunks)}")
    print("✅ Using local embeddings - no API costs or rate limits!")

if __name__ == "__main__":
    try:
        build_chroma_index()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
