# web_search.py
# Provider-agnostic web search facade — OpenRouter (:online) default
# - No plugins used; relies on the model's :online capability
# - Parses OpenRouter "annotations.url_citation" when available
# - Falls back to URL extraction from content
# - Simple disk cache + retry with backoff
#
# Env:
#   OPENROUTER_API_KEY     (required)
#   OPENROUTER_SITE_URL    (optional; helps with OpenRouter routing/limits)
#   OPENROUTER_APP_NAME    (optional; human-readable app name for headers)

from __future__ import annotations

import os
import re
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Callable

import requests

DEFAULT_MODEL = "openai/gpt-4o-mini-search-preview:online"

def _cache_path(cache_dir: Path, key: str) -> Path:
    return cache_dir / f"{key}.json"

def _cache_get(cache_dir: Path, key: str, ttl_s: int) -> Optional[dict]:
    p = _cache_path(cache_dir, key)
    if not p.exists():
        return None
    if ttl_s > 0 and (time.time() - p.stat().st_mtime) > ttl_s:
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None

def _cache_set(cache_dir: Path, key: str, data: dict) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    _cache_path(cache_dir, key).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

def _hash_key(*parts: str) -> str:
    h = hashlib.md5()
    for p in parts:
        h.update(p.encode("utf-8"))
        h.update(b"|")
    return h.hexdigest()

def _normalize_results(raw: List[dict], limit: int) -> Dict[str, object]:
    # Shape: {"results": [{"title":..., "url":..., "snippet":..., "source":"openrouter:online"}], "count": N}
    items = []
    for r in raw[:limit]:
        items.append({
            "title": r.get("title"),
            "url": r.get("url"),
            "snippet": r.get("snippet"),
            "source": "openrouter:online",
        })
    return {"results": items, "count": len(items)}

def _extract_urls_from_text(text: str) -> List[str]:
    url_re = re.compile(r"https?://[^\s)>\]]+", re.I)
    return url_re.findall(text or "")

def create_web_search_function(
    api: str = "openrouter_online",
    api_key: Optional[str] = None,
    cache_results: bool = True,
    cache_ttl_s: int = 3600,
    max_results: int = 3,
    openrouter_model: str = DEFAULT_MODEL,
) -> Callable[[str], Dict[str, object]]:
    """
    Returns a callable `search(query: str) -> {results: [...], count: int}`
    Only the OpenRouter :online path is implemented per spec.
    """
    if api != "openrouter_online":
        raise ValueError("Only 'openrouter_online' is supported in this build.")
    cache_dir = Path(".cache/websearch")

    # Resolve api key and headers
    key = api_key or os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("Missing OPENROUTER_API_KEY")
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    # Optional but recommended headers
    if os.getenv("OPENROUTER_SITE_URL"):
        headers["HTTP-Referer"] = os.getenv("OPENROUTER_SITE_URL")  # exact header name per OpenRouter docs
    if os.getenv("OPENROUTER_APP_NAME"):
        headers["X-Title"] = os.getenv("OPENROUTER_APP_NAME")

    def _search_openrouter_online(q: str) -> Dict[str, object]:
        ck = _hash_key("openrouter_online", openrouter_model, str(max_results), q)
        if cache_results:
            cached = _cache_get(cache_dir, ck, cache_ttl_s)
            if cached is not None:
                return cached

        url = "https://openrouter.ai/api/v1/chat/completions"
        body = {
            "model": openrouter_model,  # e.g., "openai/gpt-4o-mini-search-preview:online"
            # NO plugins — defer plugin form per spec
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You can browse the web. For the user topic, look up the best 3 supporting sources. "
                        "Return a single concise line of prose (<=200 chars) followed by your sources. "
                        "If possible, include structured citations so the API attaches URL annotations."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Find high-quality sources to clarify this user task: {q}",
                },
            ],
            "temperature": 0.0,
        }

        # Basic retry/backoff (max 3 attempts)
        last_err = None
        for attempt in range(3):
            try:
                resp = requests.post(url, headers=headers, json=body, timeout=45)
                # Handle HTTP-level rate limiting
                if resp.status_code == 429:
                    time.sleep(0.8 * (attempt + 1))
                    continue
                resp.raise_for_status()
                data = resp.json()
                choice = (data.get("choices") or [{}])[0]
                msg = choice.get("message") or {}
                annotations = msg.get("annotations") or []

                # Preferred path: parse annotations.url_citation
                results = []
                for a in annotations:
                    if a.get("type") == "url_citation":
                        uc = a.get("url_citation") or {}
                        results.append({
                            "title": uc.get("title"),
                            "url": uc.get("url"),
                            "snippet": uc.get("content"),
                        })

                # Fallback: scrape URLs from message content
                if not results:
                    content = (msg.get("content") or "").strip()
                    urls = _extract_urls_from_text(content)
                    for u in urls:
                        results.append({"title": None, "url": u, "snippet": None})

                out = _normalize_results(results, max_results)
                if cache_results:
                    _cache_set(cache_dir, ck, out)
                return out
            except Exception as e:
                last_err = e
                time.sleep(0.8 * (attempt + 1))
        raise RuntimeError(f"OpenRouter online search failed after retries: {last_err}")

    def _search(q: str) -> Dict[str, object]:
        return _search_openrouter_online(q)

    return _search