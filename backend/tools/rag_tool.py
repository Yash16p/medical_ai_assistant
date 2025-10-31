import os
from dotenv import load_dotenv, find_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# Load environment variables from .env file
env_path = find_dotenv(usecwd=True)
if not env_path:
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(env_path, override=True)

def _get_openai_key():
    """Return OPENAI_API_KEY from env or .env file, and set it in os.environ."""
    key = os.getenv('OPENAI_API_KEY')
    if key:
        return key
    try:
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip().startswith('OPENAI_API_KEY'):
                        parts = line.strip().split('=', 1)
                        if len(parts) == 2:
                            val = parts[1].strip().strip('"').strip("'")
                            if val:
                                os.environ['OPENAI_API_KEY'] = val
                                return val
    except Exception:
        pass
    return None

# Set environment variables
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Load API key
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_DIR = os.path.join(BASE_DIR, "data", "faiss_index")

def load_rag_pipeline():
    """Load FAISS index and build RAG pipeline."""
    print("📦 Loading FAISS index...")
    # Explicitly pass API key to avoid environment loading issues
    _api_key = _get_openai_key()
    embeddings = OpenAIEmbeddings(openai_api_key=_api_key)
    vectorstore = FAISS.load_local(INDEX_DIR, embeddings, allow_dangerous_deserialization=True)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    # Define model
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2,
        openai_api_key=_api_key
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
    response = qa_chain.invoke(question)  # LCEL expects query string directly
    return response  # LCEL returns string directly

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