"""Configuration for the Agentic RAG system.

Every tunable value is read from environment variables with sensible defaults.
No hardcoded values anywhere in the pipeline.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ---- Paths ----
BASE_DIR = Path(__file__).resolve().parent.parent
DOCUMENTS_DIR = BASE_DIR / "documents"
DATA_DIR = BASE_DIR / "data"
LANCEDB_DIR = DATA_DIR / "lancedb"
SESSIONS_DB = DATA_DIR / "sessions.db"
VECTORIZED_TRACKER = DATA_DIR / "vectorized.json"
CHAT_LOG_FILE = DATA_DIR / "chat_logs" / "interactions.jsonl"

for d in [DOCUMENTS_DIR, DATA_DIR, CHAT_LOG_FILE.parent]:
    d.mkdir(parents=True, exist_ok=True)

# ---- OpenRouter ----
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek/deepseek-v4-flash")
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4096"))

# ---- Embedding Model ----
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# ---- Chonkie SemanticChunker ----
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "2048"))
CHUNK_THRESHOLD = float(os.getenv("CHUNK_THRESHOLD", "0.5"))
CHUNK_MIN_SENTENCES = int(os.getenv("CHUNK_MIN_SENTENCES", "1"))
CHUNK_MIN_CHARS_PER_SENTENCE = int(os.getenv("CHUNK_MIN_CHARS_PER_SENTENCE", "24"))

# ---- LanceDB ----
LANCEDB_TABLE_NAME = os.getenv("LANCEDB_TABLE_NAME", "documents")
LANCEDB_SEARCH_TYPE = os.getenv("LANCEDB_SEARCH_TYPE", "hybrid")

# ---- Retrieval ----
MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", "10"))
SESSION_HISTORY_RUNS = int(os.getenv("SESSION_HISTORY_RUNS", "5"))