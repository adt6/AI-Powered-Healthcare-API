"""
Configuration constants for the clinical AI agent.
"""

from pathlib import Path

# --- Configuration ---
# Path relative to this file's location (backend/src/agents/)
INSTRUCTIONS_FILE_PATH = (
    Path(__file__).parent.parent / "agents" / "prompts" / "clinical_instructions.md"
)
HAIKU_LLM_TYPE = "haiku"
SONNET_LLM_TYPE = "sonnet"
LLAMA_GROQ_LLM_TYPE = "llama_groq"
MIXTRAL_LLM_TYPE = "mixtral_groq"
OPENAI_LLM_TYPE = "openai"
GEMINI_LLM_TYPE = "gemini"

# Default to Gemini since Groq models have compatibility issues with LangChain's create_agent
DEFAULT_LLM_TYPE = GEMINI_LLM_TYPE  # Options: "haiku", "sonnet", "llama_groq", "mixtral_groq", "openai", "gemini"
# NOTE: Groq models (llama_groq, mixtral_groq) currently have issues with function calling in LangChain

FALLBACK_INSTRUCTIONS = (
    "You are a helpful clinical assistant. Assume today's date is {{CURRENT_DATE}}."
)

# Model IDs (Use official IDs)
MODEL_ID_HAIKU = "claude-3-haiku-20240307"
MODEL_ID_SONNET = "claude-3-5-sonnet-20241022"
MODEL_ID_LLAMA_GROQ = (
    "llama-3.3-70b-versatile"  # Llama 3.3 70B - Groq docs confirm tool use support
)
MODEL_ID_MIXTRAL_GROQ = "mistral-saba-24b"  # Updated from deprecated mixtral-8x7b-32768
MODEL_ID_OPENAI = "gpt-4o-mini"
MODEL_ID_GEMINI = (
    "gemini-2.5-flash"  # Latest Gemini 2.5 Flash model via Google AI Studio
)

# API Configuration
DEFAULT_API_BASE_URL = "http://localhost:8000/api/v2"
