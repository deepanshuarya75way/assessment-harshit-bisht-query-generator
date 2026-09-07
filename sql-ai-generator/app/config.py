import os
from dotenv import load_dotenv

load_dotenv()

# "ollama" = free, runs locally, no API key needed (default)
# "anthropic" = paid API, better SQL accuracy, needs ANTHROPIC_API_KEY
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "ollama").lower()

# Ollama (local, free) settings
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5-coder")

# Anthropic (paid API) settings
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")

DATABASE_PATH = os.environ.get("DATABASE_PATH", "./sample.db")
MAX_ROWS_RETURNED = int(os.environ.get("MAX_ROWS_RETURNED", "500"))
QUERY_TIMEOUT_SECONDS = int(os.environ.get("QUERY_TIMEOUT_SECONDS", "5"))

if LLM_PROVIDER == "anthropic" and not ANTHROPIC_API_KEY:
    print(
        "WARNING: LLM_PROVIDER is 'anthropic' but ANTHROPIC_API_KEY is not set. "
        "Copy .env.example to .env and add your key, or set LLM_PROVIDER=ollama to use a free local model instead."
    )
elif LLM_PROVIDER == "ollama":
    print(f"Using local Ollama model '{OLLAMA_MODEL}' at {OLLAMA_HOST} -- make sure `ollama serve` is running.")
