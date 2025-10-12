# Papers RAG Agent

## Overview

A paper search and RAG (Retrieval Augmented Generation) system application.

## Features

- **Paper Search**: Search papers from ArXiv database
- **RAG Q&A**: Question answering based on existing paper database
- **Streaming Responses**: Real-time response generation

## Usage

### Paper Search

- `arxiv: <query>` - Search papers on ArXiv
- "Find papers about transformers" - Natural language paper search

### RAG Question Answering

- Enter regular questions and the RAG system will generate answers
- Answers are based on the existing paper database

## Technical Specifications

- **Backend**: FastAPI
- **Frontend**: Chainlit
- **Search Engine**: ArXiv API
- **RAG System**: LangGraph + OpenAI

## Notes

- RAG system initialization may take time
- Internet connection is required
- OpenAI API key is required
