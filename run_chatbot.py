#!/usr/bin/env python3
"""
Launcher script for the Clinical AI Assistant Streamlit chatbot.
"""
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def check_requirements():
    """Check if all requirements are installed."""
    try:
        import langchain
        import langchain_groq
        import streamlit

        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("Please install requirements: pip install -r requirements.txt")
        return False


def check_env_file():
    """Check if .env file exists and has API keys."""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        print("Please create .env file with your API keys")
        return False

    # Check if API keys are set in environment
    groq_key = os.getenv("GROQ_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if not groq_key:
        print("❌ GROQ_API_KEY not found in environment")
        return False

    if not gemini_key:
        print("⚠️  GEMINI_API_KEY not found - Gemini model will not be available")
    else:
        print("✅ GEMINI_API_KEY found")

    print("✅ .env file configured")
    return True


def main():
    """Main launcher function."""
    print("🚀 Starting Clinical AI Assistant Chatbot...")
    print("=" * 50)

    # Check requirements
    if not check_requirements():
        sys.exit(1)

    # Check environment
    if not check_env_file():
        sys.exit(1)

    # Get the path to the Streamlit app
    app_path = Path(__file__).parent / "agent" / "chat" / "streamlit_app.py"

    if not app_path.exists():
        print(f"❌ Streamlit app not found at {app_path}")
        sys.exit(1)

    print("✅ All checks passed!")
    print("\n🌐 Starting Streamlit app...")
    print("📱 The chatbot will open in your default browser")
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 50)

    try:
        # Run Streamlit
        subprocess.run(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                str(app_path),
                "--server.port",
                "8501",
                "--server.address",
                "localhost",
            ]
        )
    except KeyboardInterrupt:
        print("\n👋 Chatbot stopped. Goodbye!")


if __name__ == "__main__":
    main()
