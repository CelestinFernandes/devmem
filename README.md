# DevMeM - Living Memory System

> An AI-powered system that captures, organizes, and retrieves developer memories using semantic search and vector embeddings.

**🎬 [Demo](https://devmem.netlify.app/) | 📹 [Video Demo](https://youtu.be/oAqDkIEe6oU) | 🏗️ [Architecture](#architecture)**

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

### 3. Run Locally
```bash
python main.py
# Visit http://localhost:8000
```

### 4. Deploy to Netlify (Frontend) + AWS Lambda (Backend)
See [Deployment Guide](#deployment) below.

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

### System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DEVELOPER (User)                                   │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
            ┌───────▼────────┐        ┌──────▼──────────┐
            │   NETLIFY CDN  │        │  AWS API GW     │
            │  (Frontend)    │        │  (REST Proxy)   │
            │ index.html     │        │                 │
            └────────────────┘        └────────┬────────┘
                                               │
                                      ┌────────▼─────────┐
                                      │  AWS LAMBDA      │
                                      │  (main.handler)  │
                                      │                  │
                                      │ ┌──────────────┐ │
                                      │ │ FastAPI App  │ │
                                      │ │              │ │
                                      │ │ • /capture   │ │
                                      │ │ • /ask       │ │
                                      │ │ • /memories  │ │
                                      │ │ • /seed      │ │
                                      │ └──────────────┘ │
                                      └─────────┬────────┘
                                                │
                    ┌───────────────────────────┼───────────────────────────┐
                    │                           │                           │
         ┌──────────▼─────────┐      ┌─────────▼──────────┐    ┌──────────▼──────┐
         │ HUGGING FACE       │      │ GOOGLE GEMINI      │    │ COCKROACHDB     │
         │ (Embeddings)       │      │ (AI Agent)         │    │ CLOUD           │
         │                    │      │                    │    │                 │
         │ • MiniLM           │      │ • Extract memory   │    │ ┌─────────────┐ │
         │ • 384-dim vectors  │      │   (problem, cause) │    │ │  memories   │ │
         │ • Encode text      │      │ • Synthesize       │    │ │  table      │ │
         │                    │      │   answers          │    │ │             │ │
         └────────────────────┘      └────────────────────┘    │ │ • id (UUID) │ │
                  ▲                                            │ │ • title     │ │
                  │                                            │ │ • problem   │ │
                  │                                            │ │ • cause     │ │
                  │                                            │ │ • fix       │ │
                  │                                            │ │ • lesson    │ │
                  └────────────────────────────────────────────┼─┤ • embedding │ │
                                                               │ │   (384-dim) │ │
                         ┌─────────────────────────────────────┼─┤ • confidence│ │
                         │                                     │ │ • frequency │ │
                         │                                     │ │ • created_at│ │
                         │                                     │ │             │ │
                         │                                     │ ├─────────────┤ │
                         │                                     │ │relationshps │ │
                         │                                     │ │  table      │ │
                         │                                     │ │             │ │
                         │                                     │ │ • memory_a  │ │
                         │                                     │ │ • memory_b  │ │
                         │                                     │ │ • rel_type  │ │
                         │                                     │ └─────────────┘ │
                         │                                     │                 │
                         │                                     │ Vector Search: │
                         │                                     │ <=> operator   │
                         │                                     │ (IVFFlat idx)  │
                         │                                     └─────────────────┘
                         │
                ┌────────▼──────────┐
                │ MCP (optional)    │
                │ Model Context     │
                │ Protocol          │
                │                   │
                │ • Read-only agent │
                │   connectivity    │
                │ • Audit logging   │
                │ • Role-based      │
                │   access          │
                └───────────────────┘
```

### Data Flow: Capture Learning

```
┌────────────────────────────────────────────────────────────────┐
│ 1. Developer enters raw text in frontend                       │
│    "Pod crashed with OOMKilled. Increased memory to 1Gi"       │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────────┐
│ 2. POST /capture → Lambda → ExtractionService                 │
│    Gemini parses: problem, cause, fix, lesson, technologies   │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────────┐
│ 3. EmbeddingService (HuggingFace MiniLM)                       │
│    Generates 384-dim vector from: problem + cause + techs      │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────────┐
│ 4. CockroachDB Vector Search (similarity > 0.90)              │
│    If duplicate found:                                         │
│    • Bump confidence (+0.05)                                   │
│    • Increment frequency (+1)                                  │
│    • Return "duplicate" status                                 │
│    Else: Continue                                              │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────────┐
│ 5. Save Memory to CockroachDB                                  │
│    • Insert into memories table with embedding                 │
│    • Generate relationships (similarity > 0.75)                │
│    • Return memory_id + related_count                          │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────────┐
│ 6. Frontend receives response                                  │
│    Status: "new" | "duplicate"                                 │
│    Refresh timeline                                            │
└────────────────────────────────────────────────────────────────┘
```

### Data Flow: Ask Question

```
┌────────────────────────────────────────────────────────────────┐
│ 1. Developer asks: "How do I fix OOM errors?"                  │
│    POST /ask                                                   │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────────┐
│ 2. EmbeddingService (HuggingFace)                             │
│    Encode question to 384-dim vector                           │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────────┐
│ 3. CockroachDB Vector Search                                   │
│    Find top-3 most similar memories                            │
│    ORDER BY: embedding <=> query_vector                        │
│    (Using IVFFlat index for speed)                             │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────────┐
│ 4. SynthesisService (Gemini)                                   │
│    Build prompt with retrieved memories:                       │
│    • Problem 1, Fix 1, Lesson 1                                │
│    • Problem 2, Fix 2, Lesson 2                                │
│    • Problem 3, Fix 3, Lesson 3                                │
│    + original question                                         │
│    Generate answer using Gemini                                │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────────┐
│ 5. Return Response                                             │
│    {                                                           │
│      "answer": "Based on past experience...",                  │
│      "sources": [                                              │
│        {id, title, similarity},                                │
│        {id, title, similarity},                                │
│        {id, title, similarity}                                 │
│      ]                                                         │
│    }                                                           │
└────────────────────────────────────────────────────────────────┘
```

### Component Interaction Matrix

| Component | CockroachDB | Gemini | HF Embed | AWS Lambda | Netlify |
|-----------|-------------|--------|----------|-----------|---------|
| **Frontend** | ← → (via Lambda) | ← (via Lambda) | ← (via Lambda) | ← → | ✓ Hosted |
| **Lambda/FastAPI** | ← → (SQL) | ← → (REST) | ← → (REST) | ✓ Host | ← GET |
| **CockroachDB** | ✓ DB | - | - | ← → (queries) | - |
| **Gemini** | - | ✓ API | - | ← → (requests) | - |
| **HF Embed** | - | - | ✓ API | ← → (requests) | - |

---

### High-Level Flow

```
Developer Input
    ↓
Extraction Service (Gemini parses: problem, cause, fix, lesson)
    ↓
Embedding Service (HuggingFace generates 384-dim vector)
    ↓
Vector Search (CockroachDB finds similar memories via <=> operator)
    ↓
Decision Point:
    ├─ Similarity > 0.90? → Mark as duplicate, bump confidence
    ├─ Similarity > 0.75? → Create relationship link
    └─ Otherwise → Save as new memory
    ↓
Store in CockroachDB (memory + embedding + metadata)
    ↓
Synthesis Service (Gemini generates answer using retrieved context)
    ↓
Return to Frontend (answer + sources with similarity scores)
```

---

### Key Technologies by Layer

| Layer | Technology | Purpose | Why |
|-------|-----------|---------|-----|
| **Presentation** | HTML5 + JS | Web UI | Lightweight, no build required |
| **API Gateway** | AWS API Gateway | REST proxy | Routing, CORS, rate-limiting |
| **Compute** | AWS Lambda | Serverless backend | Auto-scaling, pay-per-request |
| **Application** | FastAPI + Python | Business logic | Fast, type-safe, async |
| **Vectors** | CockroachDB vector type | Semantic search | Native support, no separate store |
| **Embeddings** | HuggingFace MiniLM | 384-dim vectors | Fast, lightweight, accurate |
| **AI** | Google Gemini 3.6 Flash | Extraction & synthesis | Low cost, high quality |
| **Deployment** | Netlify (frontend) | Static hosting | Fast CDN, auto-deploy |
| **Deployment** | AWS Lambda + API GW | Backend | Serverless, scalable |

---

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