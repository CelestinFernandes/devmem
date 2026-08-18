# DevMeM - Living Memory System

## Overview
DevMeM is an AI-powered system that captures, organizes, and retrieves developer memories using semantic search and vector embeddings. It learns from past issues, solutions, and lessons to help developers solve problems faster.

## CockroachDB Tools Integration

This project meets hackathon requirements by using **2 CockroachDB tools**:

### 1. **CockroachDB Cloud Managed MCP Server**
- **Endpoint**: `https://cockroachlabs.cloud/mcp`
- **Use Case**: Secure agent connection to CockroachDB cluster
- **Configuration** (`.env`):
  ```
  MCP_SERVER_ENDPOINT="https://cockroachlabs.cloud/mcp"
  MCP_CLUSTER_ID="j228c0103-4981-4f6d-a0f9-806bbc2a4b9d"
  DATABASE_URL="postgresql://user:password@jagged-otter-31419.j77.aws-ap-south-1.cockroachlabs.cloud:26257/devmem_db?sslmode=require"
  ```
- **Benefits**: 
  - Safe by default with read-only mode option
  - Full audit logging
  - Zero custom proxy required
  - Native integration with AI agents

### 2. **CockroachDB Distributed Vector Indexing**
- **Use Case**: Store, index, and query embeddings for semantic search & RAG pipeline
- **Implementation**:
  - Vector extension enabled in `setup_db.py`:
    ```sql
    CREATE EXTENSION IF NOT EXISTS vector;
    ```
  - 384-dimensional embeddings stored in memories table:
    ```sql
    embedding vector(384)
    ```
  - Fast similarity search using `<=>` operator (`repositories/cockroach_repository.py`):
    ```python
    cur.execute("""
        SELECT id, title, problem, cause, fix, lesson, technologies,
               1 - (embedding <=> %s::vector) AS similarity
        FROM memories
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """)
    ```
- **Benefits**:
  - No separate vector store needed
  - Distributed indexing for scale
  - No consistency gaps between vector data and operational DB
  - Ideal for long-term agent memory

---

## Architecture

### Core Components

1. **CockroachDB Backend** - Distributed vector database for memories
2. **Embedding Service** - Generates 384-dim embeddings via Hugging Face API
3. **Memory Service** - RAG pipeline with semantic search & deduplication
4. **Extraction Service** - Parses developer memories (problem, cause, fix, lesson)
5. **Synthesis Service** - Generates contextual responses using AI
6. **FastAPI Frontend** - REST API for capture, search, and retrieval

### Data Flow

```
Developer Input
    ↓
Extraction Service (AI extraction)
    ↓
Embedding Service (Hugging Face)
    ↓
CockroachDB Vector Search (find similar memories)
    ↓
Duplicate Detection (similarity > 0.90) → bump confidence
Related Detection (similarity > 0.75) → create relationships
    ↓
Store in CockroachDB (with vector embedding)
    ↓
Synthesis Service (generate response using related memories)
    ↓
Return to Developer
```

---

## API Endpoints

### Capture Memory
```
POST /capture
{
  "raw_text": "Fixed OOM by increasing heap size to 2GB"
}
```

### Search Memories
```
GET /memories?query=memory%20optimization
```

### Ask AI with Memory Context
```
POST /ask
{
  "question": "How do I optimize memory usage?"
}
```

### Seed Database
```
POST /seed
```

---

## Database Schema

### Memories Table
```sql
CREATE TABLE memories (
    id UUID PRIMARY KEY,
    title TEXT,
    problem TEXT,
    cause TEXT,
    fix TEXT,
    lesson TEXT,
    technologies TEXT[],
    embedding vector(384),           -- CockroachDB Vector Type
    confidence FLOAT DEFAULT 0.8,
    needs_review BOOLEAN DEFAULT FALSE,
    importance FLOAT DEFAULT 0.5,
    frequency INT DEFAULT 1,
    status TEXT DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT now(),
    last_used_at TIMESTAMP DEFAULT now()
);
```

### Relationships Table
```sql
CREATE TABLE relationships (
    memory_id_a UUID REFERENCES memories(id),
    memory_id_b UUID REFERENCES memories(id),
    relation_type TEXT DEFAULT 'related',
    PRIMARY KEY (memory_id_a, memory_id_b)
);
```

---

## Setup & Installation

### Prerequisites
- Python 3.10+
- CockroachDB Cloud account
- Hugging Face API token
- AWS region configured

### Environment Variables
```env
DATABASE_URL=postgresql://user:password@host:26257/devmem_db?sslmode=require
MCP_SERVER_ENDPOINT=https://cockroachlabs.cloud/mcp
MCP_CLUSTER_ID=your-cluster-id
HF_TOKEN=your-hugging-face-token
HF_MODEL=google/flan-t5-large
GEMINI_API_KEY=your-gemini-api-key
AWS_REGION=ap-south-1
USE_BEDROCK=false
```

### Installation
```bash
pip install -r requirements.txt
python setup_db.py              # Initialize database
python main.py                  # Start API server
```

---

## Key Features

✅ **Semantic Memory Search** - Find similar issues & solutions instantly  
✅ **Automatic Deduplication** - Prevent duplicate memories from cluttering the database  
✅ **Relationship Mapping** - Discover connections between related memories  
✅ **Confidence Scoring** - Track how reliable each memory is  
✅ **Vector-Powered RAG** - Context-aware AI responses using retrieved memories  
✅ **Scalable Storage** - CockroachDB distributed indexing for 10K+ memories  

---

## Tech Stack

- **Database**: CockroachDB Cloud (distributed vector database)
- **Backend**: FastAPI + Python
- **Embeddings**: Hugging Face (sentence-transformers)
- **AI Models**: Google Flan-T5 + Gemini API
- **Frontend**: Static HTML/JS
- **Deployment**: AWS Lambda + API Gateway

---

## Hackathon Submission Checklist

✅ Uses **CockroachDB Cloud Managed MCP Server** for secure cluster connectivity  
✅ Uses **CockroachDB Distributed Vector Indexing** for semantic search & RAG  
✅ Full audit trail with MCP  
✅ Production-ready distributed database  
✅ Scalable to thousands of memories  

---

## License
MIT
- Build artifacts (`deployment_package/`, `lambda_package.zip`)

All sensitive variables are loaded from the environment using `python-dotenv`.

---

## Deployment to AWS Lambda (Optional)

The included `lambda_deploy.py` script packages the application and its dependencies into `lambda_package.zip`. To deploy:

```bash
python lambda_deploy.py
```

Then upload the ZIP to your Lambda function and set:
- **Handler**: `main.handler`
- **Memory**: ≥ 1024 MB
- **Timeout**: ≥ 30 seconds
- **Environment variables**: the same as your `.env` file

**Note:** This is optional – the system runs perfectly locally without any AWS services.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Re‑run `pip install -r requirements.txt` (or the manual install) |
| `FileNotFoundError: prompts/...` | Make sure the `prompts/` folder exists and contains both `.md` files. |
| `psycopg2.errors.InvalidTextRepresentation` | Ensure `technologies` is passed as a list (the repository converts it to a PostgreSQL array). |
| Model download fails | Set a Hugging Face token (`HF_TOKEN`) in your environment or log in with `hf auth login`. |
| High memory usage | Use `flan-t5-base` instead of `-large` by changing `HF_MODEL`. |

---

## Contributing

This project was built for the CockroachDB Hackathon. Contributions, issues, and feature requests are welcome.  
Please ensure:
- All secrets are externalized.
- New AI models are documented.
- API contracts remain backward‑compatible.

---

## License

To add

---

## Acknowledgements

- **CockroachDB** for the cloud database with native vector indexing.
- **Hugging Face** for the transformer models.
- **Open‑source community** for `sentence-transformers`, FastAPI, and `vis-network`.

---