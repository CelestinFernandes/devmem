# DevMeM - Living Memory System for Developers

## Overview
DevMeM captures engineering learnings, embeds them semantically, and retrieves past insights to answer questions.

## Tech Stack
- CockroachDB (vector indexing)
- Hugging Face FLAN‑T5 (extraction & synthesis)
- MiniLM (embeddings)
- FastAPI + Python
- AWS Lambda (deployment)

## How to Run
1. Set up `.env` with CockroachDB URL.
2. Run `python main.py`.
3. Open `http://localhost:8000/static/index.html`.

## Endpoints
- `POST /capture` – save a learning
- `GET /memories` – list all memories
- `GET /memory/{id}` – memory details + relations
- `POST /ask` – ask a question
- `POST /seed` – load the seed dataset

## CockroachDB Tools Used
- Distributed Vector Indexing (embedding column)
- MCP Server (connected via endpoint)