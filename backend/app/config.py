import json
from pathlib import Path

SETTINGS_FILE = Path(__file__).parent.parent / "settings.json"

DEFAULT_SETTINGS = {
    "provider": "openai",
    # OpenAI
    "openai_api_key": "",
    "openai_model": "gpt-5.4-mini",
    # Anthropic
    "anthropic_api_key": "",
    "anthropic_model": "claude-sonnet-5",
    # Groq (free, fast)
    "groq_api_key": "",
    "groq_model": "llama-3.3-70b-versatile",
    # HuggingFace Router
    "huggingface_api_key": "",
    "huggingface_model": "Qwen/Qwen3-Coder-30B-A3B-Instruct",
    # Ollama (local)
    "ollama_base_url": "http://localhost:11434",
    "ollama_model": "qwen2.5-coder:7b",
    # Output
    "output_directory": str(Path.home() / "autodev-projects"),
}


def load_settings() -> dict:
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {**DEFAULT_SETTINGS, **data}
        except (json.JSONDecodeError, OSError):
            # Corrupted or unreadable settings file — fall back to defaults
            # rather than taking down every route that depends on settings.
            return DEFAULT_SETTINGS.copy()
    return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
