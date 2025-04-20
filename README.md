
```markdown
### 🚀 GenAI Summarizer API

A production-ready API for text summarization using [Cohere](https://cohere.com)'s AI models, FastAPI, Celery, and Redis.

---

## 📑 Table of Contents

- [Architecture](#architecture)
- [Setup Instructions](#setup-instructions)
- [Docker Setup and Usage](#docker-setup-and-usage)
- [API Reference](#api-reference)
- [Usage Guide](#usage-guide)
- [Example Input/Output Pairs](#example-inputoutput-pairs)
- [Assumptions and Limitations](#assumptions-and-limitations)
- [Troubleshooting](#troubleshooting)
- [Development](#development)

---

## 🏗 Architecture

The GenAI Summarizer API follows a microservices architecture for scalability, reliability, and performance.

### Components

#### 1. **FastAPI Backend**
- Handles HTTP requests and responses
- Provides RESTful API endpoints
- Implements rate limiting and validation
- Manages task creation and result retrieval

#### 2. **Celery Workers**
- Process summarization tasks asynchronously
- Handle retries and error recovery
- Scale horizontally for high throughput

#### 3. **Redis**
- Acts as message broker for Celery
- Caches summarization results
- Maintains task state

#### 4. **Cohere API**
- External AI service for summarization
- Delivers high-quality summaries

### Data Flow

1. Client submits text to summarize
2. API validates input and checks Redis cache
3. Returns cached summary if available
4. Else, creates Celery task to process it
5. Celery calls Cohere API and stores result
6. Result is returned and cached

---

## ⚙️ Setup Instructions

### Prerequisites

- Docker + Docker Compose
- Cohere API Key
- Git (optional)

### Environment Setup

1. Clone the repo:

```bash
git clone https://github.com/yourusername/genai-summarizer.git
cd genai-summarizer
```

2. Create a `.env` file:

```bash
echo "COHERE_API_KEY=your_cohere_api_key_here" > .env
```

---

## 🐳 Docker Setup and Usage

### Build and Start

```bash
docker-compose up -d
```

Verify running containers:

```bash
docker-compose ps
```

Expected: `genai-summarizer-api`, `genai-summarizer-worker`, `genai-summarizer-redis`.

### Stop and Clean

```bash
docker-compose down
docker-compose down -v  # also removes volumes
```

### Logs

```bash
docker-compose logs           # all containers
docker-compose logs api       # API only
docker-compose logs worker    # Worker only
docker-compose logs redis     # Redis only
docker-compose logs -f api    # live logs
```

### Scaling Workers

```bash
docker-compose up -d --scale worker=3
```

---

## 🔌 API Reference

### Base URL

```
http://localhost:8000
```

---

### 🔹 `GET /health`

Check API health.

#### Response

```json
{
  "status": "ok",
  "version": "1.0.0",
  "components": {
    "redis": {"status": "up", "details": "Connected"},
    "celery": {"status": "up", "details": "Connected"},
    "cohere": {"status": "up", "details": "Connected"}
  }
}
```

---

### 🔹 `POST /api/summarize`

Submit a summarization request.

#### Request Body

```json
{
  "text": "Text to summarize...",
  "length": "medium",
  "format": "paragraph",
  "extractiveness": "low"
}
```

#### Response

```json
{
  "task_id": "uuid-task-id",
  "status": "pending"
}
```

---

### 🔹 `GET /api/result/{task_id}`

Check task result.

#### Responses

- **Pending**:

```json
{
  "detail": "Task is still pending."
}
```

- **Success**:

```json
{
  "result": "Summarized text...",
  "meta": {
    "task_id": "uuid-task-id",
    "state": "SUCCESS"
  }
}
```

- **Errors**: `404`, `500`, etc.

---

### 🔹 `DELETE /api/result/{task_id}`

Revoke a pending or running task.

#### Response

```
204 No Content
```

---

## 🧪 Usage Guide

### Basic Flow

```bash
curl -X POST http://localhost:8000/api/summarize \
  -H "Content-Type: application/json" \
  -d '{"text": "Your long text here..."}'
```

Use the returned `task_id` to check the result:

```bash
curl http://localhost:8000/api/result/<task_id>
```

---

### Advanced Usage

#### Customization

```bash
curl -X POST http://localhost:8000/api/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your text here...",
    "length": "short",
    "format": "bullets",
    "extractiveness": "high"
  }'
```

#### Caching

Identical inputs are cached:

```json
{
  "task_id": "cached:summary-result",
  "status": "completed"
}
```

---

## 🧾 Example Input/Output Pairs

### 🔸 Example 1 – Short News Article

**Input:**

```json
{
  "text": "NASA's Perseverance rover has discovered organic molecules on Mars...",
  "length": "short"
}
```

**Output:**

```json
{
  "result": "NASA's Perseverance rover found organic molecules on Mars possibly indicating past life."
}
```

---

### 🔸 Example 2 – Technical Doc (Bullets)

**Input:**

```json
{
  "text": "Kubernetes is an open-source container orchestration platform...",
  "format": "bullets",
  "extractiveness": "high"
}
```

**Output:**

```json
{
  "result": "• Kubernetes automates deployment and scaling of containers\n• Created by Google, maintained by CNCF..."
}
```

---

### 🔸 Example 3 – Academic Paper (Long)

**Input:**

```json
{
  "text": "[Long academic text on climate change]",
  "length": "long",
  "extractiveness": "low"
}
```

**Output:**

```json
{
  "result": "[Detailed summary here]"
}
```

---

## 📌 Assumptions and Limitations

### Assumptions

- Text should be non-trivial in length
- Primarily supports English
- Best for factual/informative content
- Requires stable Cohere connectivity

### Limitations

- Rate limit: 10 requests/minute/IP
- Input length limited by Cohere API
- Large texts may take several seconds
- Summaries may lack accuracy occasionally
- Cache expires after 1 hour

---

## 🛠 Troubleshooting

### 🔧 API 500 Error

- Check: `docker-compose logs api`
- Verify API key
- Confirm Redis is up

### 🔧 Task Stuck Pending

- Logs: `docker-compose logs worker`
- Restart: `docker-compose restart worker`
- Ensure Redis connectivity

### 🔧 Redis Down

- Restart: `docker-compose restart redis`
- Logs: `docker-compose logs redis`

### 🔧 Cohere Down

- Check `.env` for correct key
- Verify Cohere status
- Restart API

---

## 🧑‍💻 Development

### Project Structure

```plaintext
.
├── app/
│   ├── ai_utils.py      # Cohere API integration
│   ├── api.py           # FastAPI routes
│   ├── cache.py         # Redis caching
│   ├── main.py          # FastAPI app entrypoint
│   ├── models.py        # Request/response models
│   └── tasks.py         # Celery tasks
├── worker/
│   └── worker.py        # Celery worker config
├── tests/
│   └── test_api.py      # Unit tests
├── .env                 # Environment config
├── docker-compose.yml
├── Dockerfile
├── README.md
└── requirements.txt
```

---

### Running Locally (No Docker)

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
docker-compose up redis -d
uvicorn app.main:app --reload
celery -A worker.worker worker --loglevel=info
```

---

### Run Tests

```bash
python -m pytest tests/
# OR
python tests/test_api.py
```

---

### Contributing

1. Fork this repo
2. Create a branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push: `git push origin feature-name`
5. Create a Pull Request 🎉

---
