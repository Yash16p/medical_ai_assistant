import os
from dotenv import load_dotenv, find_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# Load environment variables from .env file
env_path = find_dotenv(usecwd=True)
if not env_path:
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(env_path, override=True)

def _get_gemini_key():
    """Return GEMINI_API_KEY from env or .env file, and set it in os.environ."""
    key = os.getenv('GEMINI_API_KEY')
    if key:
        return key
    try:
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip().startswith('GEMINI_API_KEY'):
                        parts = line.strip().split('=', 1)
                        if len(parts) == 2:
                            val = parts[1].strip().strip('"').strip("'")
                            if val:
                                os.environ['GEMINI_API_KEY'] = val
                                return val
    except Exception:
        pass
    return None

# Set environment variables
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Load API key
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_DIR = os.path.join(BASE_DIR, "data", "chroma_db")

def load_rag_pipeline():
    """Load ChromaDB index and build RAG pipeline."""
    print("📦 Loading ChromaDB index...")
    
    # Use LOCAL embeddings (no API key needed!)
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    vectorstore = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
        collection_name="medical_knowledge"
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    # Define Gemini model for generation (still uses API)
    _api_key = _get_gemini_key()
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.2,
        google_api_key=_api_key
    )

    # Custom prompt template
    template = """You are a medical assistant trained on the book 'Comprehensive Clinical Nephrology'.
Use the provided context to answer the question accurately and clearly.
If unsure, say you are not certain.

IMPORTANT: 
- Do NOT include file paths, page numbers, or source citations in your response
- Do NOT include signatures, "Best regards", or "Sincerely" at the end
- Provide only the medical information and guidance
- Keep the response professional but concise

Context:
{context}

Question:
{question}

Medical Response:
"""
    prompt = ChatPromptTemplate.from_template(template)

    # Use LCEL to create the chain (LangChain 1.x compatible)
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    qa_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    print("✅ RAG pipeline loaded successfully!")
    return qa_chain

def query_rag(question: str):
    """Query the RAG system."""
    qa_chain = load_rag_pipeline()
    print(f"🔍 Querying RAG for: {question}")
    response = qa_chain.invoke(question)
    return response

if __name__ == "__main__":
    try:
        print("🚀 Starting RAG tool test...")
        
        # Example test query
        sample_q = "What are the treatment recommendations for chronic kidney disease?"
        print(f"📝 Question: {sample_q}")
        
        answer = query_rag(sample_q)
        print(f"\n🩺 Answer:\n{answer}")
        
        print("\n✅ RAG tool test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
