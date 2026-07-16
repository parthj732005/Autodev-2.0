from fastapi import APIRouter, HTTPException

from app.config import load_settings, save_settings

router = APIRouter()

# Static, non-secret reference data only. Per-user provider selection, model
# choice, and API keys now live in the Java platform-service's per-user,
# encrypted-at-rest settings (GET/POST /api/settings there) — this endpoint
# intentionally no longer reports a "configured" flag, since that's now a
# per-user concept, not a single global one tied to backend/settings.json.
_PROVIDER_CATALOG = [
    {"value": "openai", "label": "OpenAI", "defaultModel": "gpt-5.4-mini"},
    {"value": "anthropic", "label": "Anthropic", "defaultModel": "claude-sonnet-5"},
    {"value": "groq", "label": "Groq", "defaultModel": "llama-3.3-70b-versatile"},
    {"value": "huggingface", "label": "HuggingFace", "defaultModel": "Qwen/Qwen3-Coder-30B-A3B-Instruct"},
    {"value": "ollama", "label": "Ollama (Local • Slow on CPU)", "defaultModel": "qwen2.5-coder:7b"},
]


@router.get("/providers")
def get_available_providers():
    """Static catalog of supported providers + suggested default models. Not
    tied to any user or credential state — see platform-service's per-user
    /api/settings for actual configuration/status."""
    return {"providers": _PROVIDER_CATALOG}


@router.get("/")
def get_settings():
    """Server/machine-scoped configuration only. Provider credentials were
    removed from this route entirely — this is no longer a credential-
    management path. See platform-service's per-user /api/settings."""
    settings = load_settings()
    return {"output_directory": settings.get("output_directory", "")}


@router.post("/")
def update_settings(body: dict):
    """Server/machine-scoped configuration only (currently just
    output_directory). Any provider/API-key fields in the request body are
    intentionally ignored — they are no longer stored globally."""
    current = load_settings()
    if "output_directory" in body and body["output_directory"]:
        current["output_directory"] = body["output_directory"]
    try:
        save_settings(current)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Could not write settings file: {exc}")
    return {"output_directory": current.get("output_directory", "")}
