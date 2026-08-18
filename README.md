# DevMeM - Living Memory System

> An AI-powered system that captures, organizes, and retrieves developer memories using semantic search and vector embeddings.

**🎬 [Demo](https://devmem.netlify.app/) | 📹 [Video Demo](#) (coming soon) | 🏗️ [Architecture](#architecture)**

---

## ⚡ Quick Start

### 1. Clone & Install
```bash
pip install -r requirements.txt
cp .env.example .env
# Fill in your DATABASE_URL, HF_TOKEN, GEMINI_API_KEY
```

### 2. Initialize Database
```bash
python setup_db.py
```

This creates:
- `devmem_db` database (if not exists)
- `memories` table with `vector(384)` column for embeddings
- `relationships` table for linking related memories
- Vector indexing for fast similarity search

### 3. (Optional) Seed with Sample Memories

**Option A: Quick local test with 3 examples**
```bash
python seed_good_memories.py
```

**Option B: Bulk seed via API/UI**
- Use the **Seed Database** button in the web UI, or
- `POST /seed` endpoint (loads from `output/labeled_clusters.json`)

### 4. Run Locally
```bash
python main.py
# Visit http://localhost:8000
```

### 5. Deploy to Netlify (Frontend) + AWS Lambda (Backend)
See [Deployment Guide](#-deployment) below.

---

## 🎯 What Is DevMeM?

DevMeM learns from your past issues and solutions. When you:
- **Capture** a learning (problem + fix + lesson)
- **Ask** a question

...it searches your memory for similar past experiences and gives you context-aware answers.

**Key features:**
- 🔍 Semantic search via vector embeddings
- 🚫 Automatic deduplication (no duplicate learnings)
- 🔗 Relationship mapping between related memories
- 📊 Confidence scoring & frequency tracking
- 🧠 RAG pipeline for AI responses
- 📈 Scales to 10K+ memories with CockroachDB

---

## 🏗️ Architecture

### High-Level Flow
```
Developer Input (raw text)
    ↓
Extraction Service (AI parses: problem, cause, fix, lesson)
    ↓
Embedding Service (Hugging Face: 384-dim vector)
    ↓
Vector Search (find similar memories in CockroachDB)
    ↓
Duplicate Detection (>90% match) → bump confidence
Related Detection (>75% match) → create relationship
    ↓
Store in CockroachDB with embedding
    ↓
Synthesis Service (AI generates response using retrieved memories)
    ↓
Return answer to developer
```

### Components

| Component | Purpose | Tech |
|-----------|---------|------|
| **Frontend** | Web UI for capture/ask/explore | Static HTML/JS, Netlify |
| **Backend API** | REST endpoints | FastAPI, AWS Lambda |
| **Database** | Store memories + vectors | CockroachDB Cloud |
| **Embedding** | Generate vectors | Hugging Face (MiniLM) |
| **Extraction** | Parse learnings | Gemini 3.6 Flash |
| **Synthesis** | Generate answers | Gemini 3.6 Flash |

---

## 📋 API Documentation

### 1. Capture Learning
**Save a new learning to memory**

```bash
POST /capture
Content-Type: application/json

{
  "raw_text": "Pod crashed with OOMKilled. Increased memory from 512Mi to 1Gi and it resolved."
}
```

**Response:**
```json
{
  "status": "new",
  "memory_id": "550e8400-e29b-41d4-a716-446655440000",
  "duplicate": false,
  "related_count": 2,
  "message": "New memory saved with 2 related links."
}
```

**Status codes:**
- `"new"` → Memory saved
- `"duplicate"` → Already exists; confidence bumped

---

### 2. Ask Question
**Search memories and get an AI answer**

```bash
POST /ask
Content-Type: application/json

{
  "question": "How do I fix OOM errors in Kubernetes?"
}
```

**Response:**
```json
{
  "answer": "Based on past experience:\nProblem: Pod crashed with OOMKilled\nSolution: Increase memory request/limit\nLesson: Always profile memory before deployment",
  "sources": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Kubernetes OOM issue fixed",
      "similarity": 0.92
    }
  ]
}
```

---

### 3. Get All Memories
**Retrieve memory timeline**

```bash
GET /memories
```

**Response:**
```json
{
  "memories": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Kubernetes OOM issue fixed",
      "problem": "Pod crashed with OOMKilled",
      "cause": "Memory request too low",
      "fix": "Increased from 512Mi to 1Gi",
      "lesson": "Always profile memory",
      "technologies": ["kubernetes", "docker"],
      "confidence": 0.85,
      "frequency": 3,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

### 4. Get Single Memory
**Retrieve a memory with related learnings**

```bash
GET /memory/{memory_id}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Kubernetes OOM issue fixed",
  "problem": "Pod crashed with OOMKilled",
  "related_memories": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "title": "Memory profiling best practices",
      "relation_type": "related"
    }
  ]
}
```

---

### 5. Seed Database
**Load example learnings (demo data)**

```bash
POST /seed
```

**Response:**
```json
{
  "memories_created": 15,
  "relationships_created": 8
}
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | HTML5, JavaScript, vis-network (graph visualization) |
| **Backend** | Python 3.10+, FastAPI |
| **Database** | CockroachDB Cloud (distributed, vector-native) |
| **Embeddings** | Hugging Face `sentence-transformers/all-MiniLM-L6-v2` (384-dim) |
| **AI Models** | Google Gemini 3.6 Flash (extraction & synthesis) |
| **Deployment** | AWS Lambda + API Gateway, Netlify (frontend) |
| **Libraries** | psycopg2, requests, numpy, uvicorn, mangum |

---

## 🚀 Deployment

### Frontend → Netlify

1. **Update API Base URL** in `frontend/index.html`:
   ```javascript
   const API_BASE = 'https://your-lambda-endpoint.execute-api.region.amazonaws.com/default';
   ```

2. **Deploy**:
   - Go to [app.netlify.com/drop](https://app.netlify.com/drop)
   - Drag `frontend/index.html` into the drop zone
   - Done! Your frontend is live

---

### Backend → AWS Lambda

1. **Package the app**:
   ```bash
   python lambda_deploy.py
   ```

2. **Upload `lambda_package.zip` to AWS Lambda**:
   - Create a new Lambda function or update existing
   - Upload the ZIP file
   - Set handler to `main.handler`
   - Configure environment variables (copy from `.env`)
   - Set memory to ≥1024 MB, timeout to ≥30 seconds

3. **Create API Gateway trigger**:
   - Create REST API in API Gateway
   - Set up `ANY` method on `/{proxy+}` resource
   - Point to your Lambda function
   - Deploy to stage (e.g., `default`)
   - Get the invoke URL

4. **Update frontend** with your Lambda API URL and redeploy to Netlify

---

## 🗄️ Database Schema

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

## ⚙️ Configuration

Create a `.env` file from `.env.example`:

```env
# Database (required)
DATABASE_URL="postgresql://user:pass@host:26257/devmem_db?sslmode=require"

# Embeddings (required)
HF_TOKEN="hf_your_token_here"
HF_MODEL="sentence-transformers/all-MiniLM-L6-v2"

# AI Extraction & Synthesis (required)
GEMINI_API_KEY="your_gemini_api_key_here"

# AWS / Optional
AWS_REGION="ap-south-1"
USE_BEDROCK="false"

# MCP (optional)
MCP_SERVER_ENDPOINT="https://cockroachlabs.cloud/mcp"
MCP_CLUSTER_ID="your-cluster-id"
```

---

## 🔧 CockroachDB Integration

DevMeM uses **2 CockroachDB features**:

### 1. Vector Indexing
- Stores 384-dimensional embeddings in `memories.embedding`
- Fast similarity search via `<=>` operator:
  ```sql
  SELECT id, similarity
  FROM memories
  ORDER BY embedding <=> query_vector
  LIMIT 3
  ```
- No separate vector store needed; vectors live with operational data

### 2. MCP (Model Context Protocol)
- Secure agent connectivity to CockroachDB cluster
- Audit logging + role-based access
- Configuration in `.env` + `setup_db.py`

---

## 📊 AWS Usage

| Service | Purpose | Cost |
|---------|---------|------|
| **Lambda** | API backend (pay-per-request) | ~$0.20/million requests |
| **API Gateway** | REST endpoint + CORS | ~$3.50/million requests |
| **CloudWatch** | Logs | ~$0.50/GB |
| **VPC** (optional) | Network isolation | Free (shared) |

**Typical monthly cost**: <$5 if <1M API calls/month

---

## 🐛 Known Issues & Limitations

| Issue | Impact | Workaround |
|-------|--------|-----------|
| **Gemini timeout** | Extraction/synthesis may fail | Falls back to keyword-based extraction |
| **No auth** | Anyone can call the API | Add API key validation (TODO) |
| **MiniLM embedding** | Fixed to 384 dimensions | Fine for most use cases |
| **Single Lambda** | Cold starts (~3-5s) | Use Lambda Provisioned Concurrency for production |
| **No caching** | Repeated queries re-search DB | Add Redis caching (TODO) |
| **Frontend**: Graph nodes | Very long titles wrap poorly | Implemented text truncation + tooltips |

---

## 🧪 Testing Locally

### Test Capture
```bash
curl -X POST http://localhost:8000/capture \
  -H "Content-Type: application/json" \
  -d '{"raw_text": "My Docker container kept crashing. Added health checks and it fixed the issue."}'
```

### Test Ask
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I debug container crashes?"}'
```

### Test Get Memories
```bash
curl http://localhost:8000/memories
```

---

## 🔐 Hackathon Requirements

✅ **CockroachDB Cloud Managed MCP** - Secure cluster connectivity  
✅ **Distributed Vector Indexing** - Semantic search & RAG  
✅ **Scalable to 10K+ memories** - Production-ready distributed DB  
✅ **Full audit trail** - Via MCP  
✅ **Production-ready** - Lambda + API Gateway deployment  

---

## 📝 License

MIT

---

## 🙏 Acknowledgements

- **CockroachDB** for native vector support
- **Hugging Face** for open-source embeddings
- **Google Gemini** for extraction & synthesis
- **Open-source community** for FastAPI, vis-network, and psycopg2

---