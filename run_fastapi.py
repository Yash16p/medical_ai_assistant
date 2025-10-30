import os
import subprocess
import sys

# Set environment variables
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

print("🚀 Starting Medical AI Assistant FastAPI Backend...")
print("🔗 API will be available at: http://localhost:8000")
print("📚 API Documentation: http://localhost:8000/docs")
print("🔍 Interactive API: http://localhost:8000/redoc")
print("\n⚠️  Note: The first request may take a moment to initialize the LangGraph workflow")
print("💡 Use Ctrl+C to stop the server")
print("\n" + "="*60)

try:
    # Run FastAPI with uvicorn
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "backend.api.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ])
except KeyboardInterrupt:
    print("\n\n🛑 FastAPI server stopped")
except Exception as e:
    print(f"\n❌ Error starting FastAPI server: {e}")
    print("\n💡 Try running manually with: uvicorn backend.api.main:app --reload")