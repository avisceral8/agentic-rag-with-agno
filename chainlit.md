# Agentic RAG 🔍

Ask questions about your documents. The agent will search the knowledge base and ground its answers in your content.

## How it works

1. **Ingest**: Drop files in the `documents/` folder and run `uv run python run_ingest.py`
2. **Chat**: Ask questions — the agent decides when to search and retrieves relevant passages
3. **Hybrid Search**: Combines vector similarity with keyword matching for better results

## Supported file types

PDF, DOCX, XLSX, PPTX, CSV, Markdown, images (with OCR), and more.