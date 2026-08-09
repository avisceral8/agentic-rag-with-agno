"""Agno agent factory for the RAG chat interface.

Key design:
  - Agno Agent handles agentic RAG (search_knowledge=True)
  - Knowledge wraps the LanceDB vector store for retrieval only (no insert/chunking)
  - OpenTelemetry traces are stored in SQLite if packages installed
  - Chat logs (question + answer) are written to data/chat_logs/interactions.jsonl
"""

import json
from datetime import datetime, timezone

from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.embedder.sentence_transformer import SentenceTransformerEmbedder
from agno.vectordb.lancedb import LanceDb, SearchType
from agno.db.sqlite import SqliteDb

from src.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    LLM_MODEL,
    LLM_MAX_TOKENS,
    LANCEDB_DIR,
    LANCEDB_TABLE_NAME,
    SESSIONS_DB,
    EMBEDDING_MODEL,
    LANCEDB_SEARCH_TYPE,
    MAX_SEARCH_RESULTS,
    SESSION_HISTORY_RUNS,
    CHAT_LOG_FILE,
)

_SEARCH_TYPE_MAP = {
    "hybrid": SearchType.hybrid,
    "vector": SearchType.vector,
    "keyword": SearchType.keyword,
}


def create_agent(session_id: str) -> Agent:
    """Create an Agno agent wired to the LanceDB knowledge base.
    
    Args:
        session_id: Chainlit session ID for conversation persistence.
    
    Raises:
        ValueError: If OPENROUTER_API_KEY is not set.
    """
    if not OPENROUTER_API_KEY:
        raise ValueError(
            "OPENROUTER_API_KEY is not set. "
            "Add it to your .env file: OPENROUTER_API_KEY=sk-or-v1-..."
        )

    # Session database (also stores traces when OpenTelemetry is enabled)
    session_db = SqliteDb(db_file=str(SESSIONS_DB))

    # Enable OpenTelemetry tracing (stores agent runs, model calls, tool calls)
    try:
        from agno.tracing import setup_tracing
        setup_tracing(db=session_db)
    except ImportError:
        pass

    # Embedder — same model as ingestion pipeline
    embedder = SentenceTransformerEmbedder(id=EMBEDDING_MODEL)

    search_type = _SEARCH_TYPE_MAP.get(LANCEDB_SEARCH_TYPE, SearchType.vector)

    vector_db = LanceDb(
        uri=str(LANCEDB_DIR),
        table_name=LANCEDB_TABLE_NAME,
        search_type=search_type,
        embedder=embedder,
    )

    # Knowledge — used ONLY for retrieval (no readers, no chunkers, no inserts)
    knowledge = Knowledge(vector_db=vector_db, max_results=MAX_SEARCH_RESULTS)

    agent = Agent(
        model=OpenRouter(
            id=LLM_MODEL,
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
            max_tokens=LLM_MAX_TOKENS,
        ),
        knowledge=knowledge,
        search_knowledge=True,
        instructions=[
            "You are a helpful research assistant with access to a knowledge base of documents.",
            "When the user asks a question, search the knowledge base to find relevant information.",
            "Always ground your answers in the retrieved content. Cite sources when possible.",
            "If the knowledge base doesn't contain relevant information, be honest about it.",
            "Use markdown formatting for clear, structured responses.",
        ],
        add_datetime_to_context=True,
        db=session_db,
        session_id=session_id,
        add_history_to_context=True,
        num_history_runs=SESSION_HISTORY_RUNS,
        markdown=True,
    )

    agent._rag_session_id = session_id
    return agent


def log_interaction(session_id: str, question: str, answer: str):
    """Write question + answer to the JSONL chat log.
    
    Retrieved chunks are captured from the agent's trace database
    (not via a redundant LanceDB search).
    """
    try:
        CHAT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CHAT_LOG_FILE, "a", encoding="utf-8") as f:
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": session_id,
                "question": question,
                "answer": answer,
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Warning: Failed to write chat log: {e}")