import os
import subprocess
import sys

# Set environment variables
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

print("Starting Medical AI Assistant...")
print("The app will open in your web browser")
print("URL: http://localhost:8501")
print("\nNote: The first load may take a moment to initialize the AI system")
print("Use Ctrl+C to stop the server")
print("\n" + "="*50)

try:
    # Run Streamlit app
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", "frontend/app.py",
        "--server.port", "8501",
        "--server.address", "localhost"
    ])
except KeyboardInterrupt:
    print("\nMedical AI Assistant stopped")
except Exception as e:
    print(f"\nError starting app: {e}")
    print("\nTry running manually with: streamlit run frontend/app.py")