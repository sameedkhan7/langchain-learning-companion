# Learning Companion Chatbot

A small local chat service. It exposes an OpenAI-compatible chat endpoint backed by a LangChain prompt and a Grok model, so the Open WebUI you already use can talk to it. See [docs/architecture.md](docs/architecture.md).

## Setup

```
uv sync
copy .env.example .env      # PowerShell / cmd   (macOS/Linux: cp .env.example .env)
```

Edit `.env`:

- `GROK_MODEL_NAME` — **supplied by your instructor**.
- `GROK_API_KEY` — your real key. Put it **only** in `.env`. That file is untracked; never commit or share it.

## Run

```
uv run uvicorn learning_companion.api:app --host 127.0.0.1 --port 8000
```

Check it:

```
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/v1/models
```

The app starts even with a blank key. A chat request without a key or model name returns HTTP 503 with a plain message.

## Open WebUI connection

Open WebUI is already installed; do not change it beyond the existing connection entry. Point that connection at:

- Base URL: `http://127.0.0.1:8000/v1` (use `http://host.docker.internal:8000/v1` if Open WebUI runs in Docker)
- API key: any placeholder, if it insists on one
- Then select the configured Grok model in the model picker.

If Docker cannot reach `127.0.0.1`, tell your instructor rather than changing `HOST`.

## Non-streaming test

```
curl -X POST http://127.0.0.1:8000/v1/chat/completions -H "Content-Type: application/json" -d "{\"model\":\"<your model>\",\"stream\":false,\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}]}"
```
