# Agentic RAG

A fully local agentic Retrieval-Augmented Generation (RAG) system with a Chainlit chat interface. The agent **decides when to search** your documents, retrieves relevant passages via hybrid search, and grounds every answer in your content.

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        INGESTION PIPELINE                        │
│                                                                  │
│  documents/                                                      │
│    │                                                             │
│    ├── .pdf, .png, .jpg  ──→  liteparse (native)                 │
│    ├── .docx, .doc       ──→  python-docx                        │
│    ├── .csv, .tsv        ──→  plain text                         │
│    ├── .xlsx, .xls       ──→  openpyxl                           │
│    ├── .pptx, .ppt       ──→  python-pptx                        │
│    ├── .md               ──→  Chonkie MarkdownChef               │
│    └── .txt              ──→  Chonkie TextChef                   │
│    │                                                             │
│    ▼  Chonkie SemanticChunker (2048 tokens, threshold 0.5)       │
│    │                                                             │
│    ▼  SentenceTransformerEmbedder (all-MiniLM-L6-v2)             │
│    │                                                             │
│    ▼  LanceDB (384-dim vectors + FTS index)                      │
│    │                                                             │
│    ▼  vectorized.json (SHA-256 tracking)                         │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                          CHAT PIPELINE                           │
│                                                                  │
│  Chainlit UI ──→ Agno Agent                                      │
│                      │                                           │
│                      ├── search_knowledge=True                   │
│                      │   (agent decides when to search)          │
│                      │                                           │
│                      ▼  LanceDB hybrid search                    │
│                      │   (vector + keyword FTS)                  │
│                      │                                           │
│                      ▼  OpenRouter LLM                           │
│                      │   (deepseek/deepseek-v4-flash)            │
│                      │                                           │
│                      ▼  Grounded response                        │
│                                                                  │
│  Traces: OpenTelemetry → SQLite (sessions.db)                    │
│  Chat log: data/chat_logs/interactions.jsonl                     │
└──────────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

| Decision | Choice | Why |
|---|---|---|
| **Agentic RAG** | `search_knowledge=True` | Agent decides IF and WHAT to search — no blind context injection |
| **Chunking** | Chonkie `SemanticChunker` | Splits at natural topic boundaries, not arbitrary sizes |
| **No double-chunking** | Direct `LanceDb.upsert()` | Bypasses Agno's Knowledge readers entirely |
| **Embedding** | `all-MiniLM-L6-v2` (local) | Fast, 384-dim, no API costs |
| **Search** | LanceDB hybrid | Vector similarity + keyword FTS, fused ranking |
| **LLM** | OpenRouter → DeepSeek V4 | Fast, strong reasoning, affordable |
| **Persistence** | SQLite sessions + LanceDB | Zero infrastructure, everything local |
| **Tracking** | SHA-256 file hashes | Skip unchanged files on re-ingestion |

## Installation

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

### Setup

```bash
# 1. Clone or navigate to the project
cd AgenticRag\ V2

# 2. Create .env with your OpenRouter key
cp .env.example .env
# Edit .env: OPENROUTER_API_KEY=sk-or-v1-your-key-here

# 3. Install dependencies (uses the existing uv venv)
uv pip install -e . --python path/to/your/venv/python.exe

# 4. Install LibreOffice (optional — for native .docx/.csv parsing)
# Windows: choco install libreoffice-fresh   (run as admin)
# Without it, python-docx and plain-text fallbacks work fine.
```

### Configuration

All settings in `.env` (see `.env.example`):

```bash
OPENROUTER_API_KEY=sk-or-v1-...          # Required
LLM_MODEL=deepseek/deepseek-v4-flash     # Any OpenRouter model
EMBEDDING_MODEL=all-MiniLM-L6-v2         # Local SentenceTransformer model
CHUNK_SIZE=2048                          # Max tokens per chunk
CHUNK_THRESHOLD=0.5                      # Semantic grouping (lower = bigger chunks)
LANCEDB_SEARCH_TYPE=hybrid               # hybrid | vector | keyword
MAX_SEARCH_RESULTS=10                    # Chunks retrieved per search
SESSION_HISTORY_RUNS=5                   # Past exchanges remembered
```

## Usage

### 1. Ingest Documents

Drop files into `documents/` (PDF, DOCX, TXT, MD, CSV, XLSX, PPTX, images), then:

```bash
python run_ingest.py

# Force re-process all files
python run_ingest.py --force

# Process a different directory
python run_ingest.py --dir /path/to/other/docs
```

The pipeline:
- Scans for new/changed files (SHA-256 hash check)
- Parses each file with the appropriate parser
- Chunks with `SemanticChunker`
- Embeds with `all-MiniLM-L6-v2`
- Stores in LanceDB with FTS index for hybrid search
- Updates `data/vectorized.json`

### 2. Start Chat Server

```bash
python main.py
```

Open **http://localhost:8000/chainlit** in your browser.

The agent:
- Decides when to search your documents
- Retrieves relevant chunks via hybrid search
- Generates answers grounded in your content
- Remembers conversation history (last 5 exchanges)

### 3. Ask Questions

```
You: "Who is Elizabeth Bennet and what is her role in Pride and Prejudice?"
Agent: [searches LanceDB → finds Pride and Prejudice chunks]
       "Elizabeth Bennet is the protagonist of Jane Austen's novel. She is
        the second eldest of five daughters, known for her intelligence
        and wit. Her relationship with Mr. Darcy drives the plot..."

You: "How does her relationship with Mr. Darcy evolve?"
Agent: [remembers context → searches again → synthesizes across chapters]
       "Their relationship evolves through several stages: initial
        prejudice, Darcy's first proposal and rejection, the revealing
        letter, and eventual reconciliation at Pemberley..."
```

## Viewing Traces & Logs

### Chat Log (JSONL)

Every interaction is logged to `data/chat_logs/interactions.jsonl`:

```json
{
  "timestamp": "2026-08-08T08:21:56+00:00",
  "session_id": "e29d4781-5965-4dd8-90d6-43f4eca1f164",
  "question": "Who is Elizabeth Bennet and what is her role in Pride and Prejudice?",
  "answer": "Based on the text of **Pride and Prejudice** by **Jane Austen**..."
}
```

Each line is one complete interaction. Open in any text editor or parse with:

```bash
cat data/chat_logs/interactions.jsonl | python -m json.tool
```

### Agno Traces (OpenTelemetry)

Traces are stored in `data/sessions.db` (SQLite). Query them programmatically:

```python
from agno.db.sqlite import SqliteDb

db = SqliteDb(db_file="data/sessions.db")

# List recent traces
traces, total = db.get_traces(limit=10)
for t in traces:
    print(f"Trace: {t.name}, status={t.status}, spans={t.total_spans}")

# Get spans for a trace (shows model calls, tool calls, search queries)
spans = db.get_spans(trace_id=traces[0].trace_id)
for s in spans:
    if s.name == "search_knowledge_base":
        # Shows the actual search query sent to LanceDB
        print(f"Search query: {s.attributes['tool.parameters']}")
```

### Server Logs

Runtime logs show retrieval operations:

```
INFO Found 5 documents    ← LanceDB returned 5 chunks for this search
INFO Found 3 documents    ← Another search returned 3 chunks
```

### Retrieval Statistics

```python
import lancedb, json

db = lancedb.connect("data/lancedb")
table = db.open_table("documents")
print(f"Total chunks: {table.count_rows()}")

# Per-source breakdown
df = table.to_pandas()
sources = {}
for payload in df["payload"]:
    data = json.loads(payload)
    src = data.get("meta_data", {}).get("source_file", "unknown")
    sources[src] = sources.get(src, 0) + 1
for src, count in sorted(sources.items()):
    print(f"  {src}: {count} chunks")
```

## File Structure

```
AgenticRag V2/
├── src/
│   ├── config.py         # All configuration (env vars with defaults)
│   ├── ingest.py         # Ingestion pipeline (parse → chunk → embed → store)
│   ├── agent.py          # Agno agent factory + chat logging
│   └── chainlit_app.py   # Chainlit event handlers
├── main.py               # FastAPI server + Chainlit mount
├── run_ingest.py         # CLI for document ingestion
├── documents/            # Drop files here for ingestion
├── data/                 # Auto-created at runtime:
│   ├── lancedb/          #   Vector store
│   ├── sessions.db       #   Agent sessions + traces
│   ├── chat_logs/        #   interactions.jsonl
│   └── vectorized.json   #   File tracking
├── .env.example          # Environment template
├── chainlit.md           # Welcome screen
└── pyproject.toml        # Dependencies
```

## Supported File Formats

| Format | Parser | External Deps |
|---|---|---|
| PDF | liteparse (native) | None |
| PNG, JPG, GIF, BMP, TIFF, SVG | liteparse (native) | Tesseract (for OCR) |
| DOCX, DOC, DOCM, ODT, RTF | python-docx (fallback) | None |
| XLSX, XLS, XLSM, ODS | openpyxl (fallback) | None |
| PPTX, PPT, PPTM, ODP | python-pptx (fallback) | None |
| CSV, TSV | Plain text read | None |
| TXT | Chonkie TextChef | None |
| MD, Markdown | Chonkie MarkdownChef | None |

With LibreOffice installed, `.docx`, `.csv`, `.xlsx`, and `.pptx` use liteparse directly for higher-quality extraction.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `OPENROUTER_API_KEY` | *(required)* | OpenRouter API key |
| `LLM_MODEL` | `deepseek/deepseek-v4-flash` | Any OpenRouter model ID |
| `LLM_MAX_TOKENS` | `4096` | Max tokens per response |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | SentenceTransformer model |
| `CHUNK_SIZE` | `2048` | Max tokens per chunk |
| `CHUNK_THRESHOLD` | `0.5` | Semantic grouping threshold |
| `LANCEDB_SEARCH_TYPE` | `hybrid` | hybrid / vector / keyword |
| `MAX_SEARCH_RESULTS` | `10` | Chunks per search |
| `SESSION_HISTORY_RUNS` | `5` | Past exchanges in context |