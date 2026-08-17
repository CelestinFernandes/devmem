```markdown
# DevMeM – Living Memory System for Developers

**Version:** 3.2 (MVP)

DevMeM is a **semantic memory system** that captures engineering learnings, stores them with vector embeddings, detects duplicates and relationships, and answers questions using past knowledge – all powered by CockroachDB and open‑source AI models.

---

## 📖 Overview

DevMeM turns raw engineering notes into structured memories. The system:

- **Captures** raw text and extracts `problem`, `cause`, `fix`, `lesson`, and `technologies` using FLAN‑T5.
- **Embeds** memories with `all‑MiniLM‑L6‑v2` (384‑dim vectors).
- **Detects** duplicates (≥ 0.90 similarity) and related memories (≥ 0.75 similarity).
- **Stores** everything in CockroachDB with a native vector index.
- **Answers** questions by retrieving similar memories and synthesising a response.
- **Visualises** relationships in a simple Knowledge Graph.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Capture Learning** | Submit raw text; extract structured fields. |
| **Semantic Embeddings** | 384‑dim vectors with `all‑MiniLM‑L6‑v2`. |
| **Duplicate Detection** | If similarity ≥ 0.90, confidence and frequency are bumped. |
| **Related Detection** | If similarity ≥ 0.75, a relationship edge is created. |
| **Timeline** | List all memories with title, confidence, and date. |
| **Memory Detail** | View all fields and related memories. |
| **Ask AI** | Ask a question; retrieve top‑K memories and synthesise an answer. |
| **Knowledge Graph** | Visualise a memory and its direct neighbours. |
| **Seed Data** | Pre‑load 80+ labelled entries for calibration. |
| **Calibration** | Compute pairwise cosine similarities to validate thresholds. |

---

## 🧰 Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.12+, FastAPI, Uvicorn |
| Database | CockroachDB (PostgreSQL‑compatible) with `pgvector` |
| AI – Extraction | `google/flan‑t5‑large` (or `‑base`) |
| AI – Synthesis | `google/flan‑t5‑base` |
| AI – Embeddings | `sentence‑transformers/all‑MiniLM‑L6‑v2` |
| Frontend | HTML5, CSS3, JavaScript (no framework) |
| Deployment | Local or AWS Lambda (optional) |

---

## 📁 Project Structure

```
.
├── api/                   # FastAPI route handlers
│   ├── capture.py
│   ├── ask.py
│   ├── memories.py
│   └── seed.py
├── services/              # Core business logic
│   ├── extraction_service.py
│   ├── synthesis_service.py
│   └── memory_service.py
├── repositories/          # Database layer
│   └── cockroach_repository.py
├── prompts/               # Prompt templates
│   ├── extract_memory.md
│   └── ask_ai.md
├── frontend/              # Static UI
│   └── index.html
├── output/                # Seed and calibration data (JSON)
├── data/                  # Raw CSV datasets (optional)
├── main.py                # Application entry point
├── lambda_deploy.py       # Script to package for AWS Lambda
├── .env                   # Environment variables (not in repo)
├── .gitignore
└── README.md
```

---

## ⚙️ Installation & Setup

### Prerequisites

- Python 3.12 or higher
- A CockroachDB Cloud cluster (free tier works) – get the connection string.
- (Optional) Hugging Face account – models are downloaded automatically.

### 1. Clone the repository

```bash
git clone https://github.com/CelestinFernandes/devmem.git
cd devmem
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install fastapi uvicorn mangum sentence-transformers transformers torch psycopg2-binary python-dotenv
```

### 4. Set up environment variables

Create a `.env` file in the root directory with:

```env
DATABASE_URL="postgresql://user:password@host:port/dbname?sslmode=require"
USE_BEDROCK="false"
HF_MODEL="google/flan-t5-large"
MCP_SERVER_ENDPOINT="https://cockroachlabs.cloud/mcp"
CRDB_CLUSTER_ID="your-cluster-id"
```

Replace the placeholders with your actual CockroachDB credentials.  
The `MCP_SERVER_ENDPOINT` and `CRDB_CLUSTER_ID` are optional – they satisfy the CockroachDB tool requirement for the hackathon.

### 5. Initialise the database

```bash
python setup_db.py   # (or migrate_db.py if you have it)
```

This creates:
- The `devmem_db` database (if not exists)
- The `memories` table with a `vector(384)` column
- The `relationships` table
- An `ivfflat` vector index for fast similarity search

### 6. (Optional) Seed the database with sample memories

```bash
python seed_good_memories.py   # inserts 3 clean example memories
```

Or use the `/seed` endpoint via the frontend (see below).

---

## 🚀 Running Locally

Start the server:

```bash
python main.py
```

The API will be available at `http://localhost:8000`.  
Open the frontend at `http://localhost:8000/static/index.html`.

---

## 📡 API Endpoints

| Method | Endpoint | Request Body | Response |
|--------|----------|--------------|----------|
| `POST` | `/capture` | `{"raw_text": "..."}` | `{"status": "new"|"duplicate", "memory_id": "...", "related_count": n}` |
| `GET`  | `/memories` | – | `{"memories": [ {id, title, confidence, created_at, ...} ]}` |
| `GET`  | `/memory/{id}` | – | `{...all fields..., "related_memories": [...]}` |
| `POST` | `/ask` | `{"question": "..."}` | `{"answer": "...", "sources": [ {id, title, similarity} ]}` |
| `POST` | `/seed` | – | `{"status": "success", "memories_created": n, "relationships_created": m}` |

All responses are JSON.

---

## 🖥️ Frontend Usage

1. Open `http://localhost:8000/static/index.html`.
2. **Capture** – enter any engineering learning and click "Save Memory".
3. **Timeline** – all memories are listed; click any to see details.
4. **Ask AI** – type a question; the system will retrieve similar memories and generate an answer.
5. **Knowledge Graph** – on a memory detail, click "🌐 View Graph" to see it with its related nodes.

---

## 🧠 AI Models

- **Extraction** – `flan-t5-large` is used for accuracy; it parses raw text into structured fields. If JSON parsing fails, a fallback heuristic extracts sentences containing keywords.
- **Synthesis** – `flan-t5-base` generates concise answers based on the top‑3 retrieved memories.
- **Embeddings** – `all-MiniLM-L6-v2` runs locally via `sentence-transformers`.

All models are downloaded from Hugging Face at first launch.  
You can switch to `google/flan-t5-base` for lower memory usage by changing `HF_MODEL` in `.env`.

---

## 🧪 Calibration & Seed Data

The `output/` folder contains:
- `labeled_clusters.json` – generated from Hadoop bug reports (80 memories in `duplicate`/`related`/`distinct` clusters).
- `calibration_results.json` – pairwise similarity statistics used to validate the thresholds (0.90 for duplicate, 0.75 for related).

To regenerate the seed data, run `generate_seed.py`.  
To re‑run calibration, run `embed_and_calibrate.py`.

---

## 🔐 Security & Secrets

**Never commit `.env` or any file containing secrets.**  
The `.gitignore` is already configured to exclude:
- `.env`
- `*password*`, `*secret*`
- Large model files (`*.safetensors`, `*.bin`)
- Build artifacts (`deployment_package/`, `lambda_package.zip`)

All sensitive variables are loaded from the environment using `python-dotenv`.

---

## ☁️ Deployment to AWS Lambda (Optional)

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

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Re‑run `pip install -r requirements.txt` (or the manual install) |
| `FileNotFoundError: prompts/...` | Make sure the `prompts/` folder exists and contains both `.md` files. |
| `psycopg2.errors.InvalidTextRepresentation` | Ensure `technologies` is passed as a list (the repository converts it to a PostgreSQL array). |
| Model download fails | Set a Hugging Face token (`HF_TOKEN`) in your environment or log in with `hf auth login`. |
| High memory usage | Use `flan-t5-base` instead of `-large` by changing `HF_MODEL`. |

---

## 🤝 Contributing

This project was built for the CockroachDB Hackathon. Contributions, issues, and feature requests are welcome.  
Please ensure:
- All secrets are externalized.
- New AI models are documented.
- API contracts remain backward‑compatible.

---

## 📄 License

To add

---

## 🙏 Acknowledgements

- **CockroachDB** for the cloud database with native vector indexing.
- **Hugging Face** for the transformer models.
- **Open‑source community** for `sentence-transformers`, FastAPI, and `vis-network`.

---