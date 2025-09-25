# Papers RAG Agent (MVP)

This project is a **minimum viable product (MVP) of a RAG × Agent chatbot specialized for academic paper learning**. When users input paper titles or questions, the following processes are executed:

1. **Query Planner**
   Analyzes user input and generates search queries (e.g., HyDE/query expansion).

2. **Retriever**
   Retrieves papers from arXiv, converts PDFs to text → chunks by IMRaD/formulas → stores in vector DB (FAISS) and performs search.

3. **Summarizer**
   Generates **Cornell Note format (Cue / Notes / Summary)** based on search results and creates **3 quiz questions** to deepen understanding.

4. **Judge**
   Cross-references answers with citations and retries if there are deficiencies or errors.

---

## MVP Goals

- Ability to verify the following through **Chainlit UI**:
  - Chat questions → answers returned with citations
  - Cornell Note output (Cue / Notes / Summary)
  - Auto-generated 3 quiz questions

- **Evaluation postponed** (LangSmith Evals and RAGAS are for the next phase)

---

## Project Structure (Planned)

papers-rag-agent/
├── src/
│ ├── agents/ # Query Planner, Retriever, Summarizer, Judge
│ ├── ui/ # Chainlit app
│ └── utils/ # Common processing (PDF→text, chunker etc.)
├── data/ # Sample paper PDFs
├── tests/ # Test code
├── scripts/ # Supporting scripts for eval etc.
└── README.md

---

## Setup and Running

### Install Dependencies

```bash
uv install
```

### Launch UI

```bash
uv run chainlit run src/ui/app.py -w
```

Access `http://localhost:8000` in your browser to use the chat UI.

### Current Features

- **Mock Implementation**: LangGraph not yet implemented, returns fixed data
- **Type-Safe**: Uses Pydantic models
- **UI Display**: Shows answers, Cornell Notes, quizzes, and citations

---

## Future Extensions

- Evaluation: Introduce LangSmith Evals, RAGAS to measure Faithfulness / Recall / Relevance
- Guardrails: Suppress unsourced assertions and NG words
- Vector DB: Replace FAISS → Pinecone/Weaviate
- CI/CD: Gate quality with LangSmith regression tests

---
