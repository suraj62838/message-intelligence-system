# Message Intelligence System

A privacy-first message intelligence system built with:

- Next.js App Router + TypeScript
- Tailwind CSS
- FastAPI
- SQLite
- Groq API for AI classification
- Regex-based sensitive-data masking before any Groq call

## Privacy

The system is designed for the assignment requirement that raw messages must not be sent to external AI services.

Sensitive-looking values are detected and masked locally first. Only the masked message may be sent to a local Ollama model.

## Architecture

CSV -> FastAPI -> Privacy Layer -> Groq -> Structured JSON -> SQLite -> Next.js Dashboard

The LLM is optional. If Ollama is unavailable, the backend falls back to deterministic local classification so the application still works.

## 1. Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## 2. Groq AI

Create a Groq API key and place it in `backend/.env`:

```env
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

Install dependencies and start the backend. The backend sends only the **masked** message to Groq.

Groq supports JSON output modes for structured application responses. The model is configurable through `GROQ_MODEL`.

## 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

## 4. Process the provided dataset

Use the dashboard's Upload CSV button and select:

- messages.csv

The 15 mandatory IDs can be loaded separately using the Mandatory Demo page.

## API

- `GET /api/health`
- `POST /api/messages/upload`
- `POST /api/messages/process`
- `GET /api/messages`
- `GET /api/messages/{message_id}`
- `GET /api/tasks`
- `GET /api/events`
- `GET /api/sensitive`
- `GET /api/dashboard/stats`
- `GET /api/demo/mandatory`

## Notes

- Dates/times/persons are never invented. Missing values are `null`.
- Sensitive values are masked locally before any Groq request.
- The database stores the masked message, not the original raw message.
- Confidence is a model/rule confidence score, not a calibrated probability.
