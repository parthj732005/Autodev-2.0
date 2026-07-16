"""
Isolated client for the Java/Spring Boot platform service (auth + project
metadata persistence). This is the ONLY module in the FastAPI backend that
knows the platform service's base URL, endpoint paths, or HTTP details.

FastAPI never decodes or trusts JWT claims itself — identity is always
resolved by asking the platform service's own /api/auth/me, so there is
exactly one place (Spring Boot) that verifies token signatures.

Every function here fails soft: a network error, timeout, or non-2xx
response never raises out to the caller. Callers get None/False and decide
what that means for their flow (e.g. a failed metadata sync must never
undo a successful generation).
"""
import os

import httpx

from app.services.logger import log

PLATFORM_SERVICE_URL = os.environ.get("PLATFORM_SERVICE_URL", "http://localhost:8081")

# Explicit, short timeouts — the platform service is a local/adjacent
# dependency, never worth waiting long on.
_TIMEOUT = httpx.Timeout(connect=3.0, read=5.0, write=5.0, pool=3.0)


def _safe_log(message: str) -> None:
    """A logging failure (e.g. app/logs/ missing in some run context) must
    never mask the actual platform-service error being reported."""
    try:
        log(message)
    except OSError:
        pass


async def get_current_user(token: str) -> dict | None:
    """Resolve the authenticated user via GET /api/auth/me.

    Returns the user dict ({id, email, createdAt}) on success, or None if
    the token is missing/invalid/expired, or the platform service itself
    is unreachable. None is always treated as "not authenticated" by
    callers — never as a hard error.
    """
    if not token:
        return None
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{PLATFORM_SERVICE_URL}/api/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )
        if resp.status_code == 200:
            return resp.json()
        return None
    except httpx.HTTPError as exc:
        _safe_log(f"platform_client: /api/auth/me unreachable — {exc}")
        return None


async def sync_completed_project(
    token: str,
    project_key: str,
    name: str,
    tech_stack: str,
    output_path: str,
) -> bool:
    """Create a project metadata record for a just-completed generation and
    mark it COMPLETED. Returns True only if both calls succeed.

    On ANY failure (network error, timeout, non-2xx response) this returns
    False and logs a clear message — it never raises. Generated files on
    disk are the source of truth and must never be affected by this.
    """
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            headers = {"Authorization": f"Bearer {token}"}

            create_resp = await client.post(
                f"{PLATFORM_SERVICE_URL}/api/projects",
                headers=headers,
                json={
                    "projectKey": project_key,
                    "name": name,
                    "techStack": tech_stack,
                    "outputPath": output_path,
                },
            )
            if create_resp.status_code != 201:
                _safe_log(
                    f"platform_client: metadata sync failed for '{project_key}' — "
                    f"create returned {create_resp.status_code}: {create_resp.text[:300]}"
                )
                return False

            project_id = create_resp.json().get("id")
            status_resp = await client.patch(
                f"{PLATFORM_SERVICE_URL}/api/projects/{project_id}/status",
                headers=headers,
                json={"status": "COMPLETED"},
            )
            if status_resp.status_code != 200:
                _safe_log(
                    f"platform_client: metadata sync partially failed for '{project_key}' — "
                    f"status update returned {status_resp.status_code}: {status_resp.text[:300]}"
                )
                return False

            return True
    except httpx.HTTPError as exc:
        _safe_log(f"platform_client: metadata sync unreachable for '{project_key}' — {exc}")
        return False


async def get_provider_settings(token: str) -> dict | None:
    """Fetch this user's decrypted provider configuration exactly once, via
    GET /api/settings/resolved, and translate it into the same dict shape
    app.services.model_provider.get_provider() already expects (e.g.
    "provider", "groq_api_key", "groq_model", ...) — so get_provider() itself
    needs no changes at all.

    Returns None if the token is invalid or the platform service is
    unreachable. Callers MUST treat None as "cannot start generation" — never
    fall back to another user's settings or the old global settings.json.
    """
    if not token:
        return None
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{PLATFORM_SERVICE_URL}/api/settings/resolved",
                headers={"Authorization": f"Bearer {token}"},
            )
        if resp.status_code != 200:
            return None
        data = resp.json()
    except httpx.HTTPError as exc:
        _safe_log(f"platform_client: /api/settings/resolved unreachable — {exc}")
        return None

    mapped = {
        "provider": data.get("selectedProvider"),
        "openai_api_key": data.get("openaiApiKey"),
        "openai_model": data.get("openaiModel"),
        "anthropic_api_key": data.get("anthropicApiKey"),
        "anthropic_model": data.get("anthropicModel"),
        "groq_api_key": data.get("groqApiKey"),
        "groq_model": data.get("groqModel"),
        "huggingface_api_key": data.get("huggingfaceApiKey"),
        "huggingface_model": data.get("huggingfaceModel"),
        "ollama_base_url": data.get("ollamaBaseUrl"),
        "ollama_model": data.get("ollamaModel"),
    }
    # Omit (not just null-out) unset fields so get_provider()'s own
    # settings.get(key, default) fallbacks still apply — a key present with
    # value None would shadow that default instead of falling through to it.
    return {k: v for k, v in mapped.items() if v is not None}


async def get_owned_project(token: str, project_key: str) -> dict | None:
    """Look up project metadata by projectKey, scoped to the authenticated
    user via the platform service. Returns None both when the project
    doesn't exist AND when it exists but belongs to someone else — the same
    response either way, so existence is never leaked to the caller.
    """
    if not token or not project_key:
        return None
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{PLATFORM_SERVICE_URL}/api/projects/by-key/{project_key}",
                headers={"Authorization": f"Bearer {token}"},
            )
        if resp.status_code == 200:
            return resp.json()
        return None
    except httpx.HTTPError as exc:
        _safe_log(f"platform_client: project lookup unreachable for '{project_key}' — {exc}")
        return None


async def list_owned_projects(token: str) -> list | None:
    """List every project owned by the authenticated user. Returns None on
    any failure (invalid token / platform service unreachable) — callers
    must not silently show a global/legacy list as a fallback.
    """
    if not token:
        return None
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{PLATFORM_SERVICE_URL}/api/projects",
                headers={"Authorization": f"Bearer {token}"},
            )
        if resp.status_code == 200:
            return resp.json()
        return None
    except httpx.HTTPError as exc:
        _safe_log(f"platform_client: project list unreachable — {exc}")
        return None
