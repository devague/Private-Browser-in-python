"""Local-first search interface powered by SearXNG and optional Ollama."""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024  # Keep incoming requests small.

SEARXNG_URL = os.environ.get("SEARXNG_URL", "http://127.0.0.1:8080").rstrip("/")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
MAX_RESULTS = 6
TIMEOUT_SECONDS = 12


def get_json(url, timeout=TIMEOUT_SECONDS):
    """Fetch and decode a JSON response using only Python's standard library."""
    req = Request(url, headers={"User-Agent": "PrivateSearchEngine/1.0"})
    with urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(url, payload, timeout=90):
    """POST JSON using only Python's standard library."""
    data = json.dumps(payload).encode("utf-8")
    req = Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "PrivateSearchEngine/1.0",
        },
        method="POST",
    )
    with urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def search_web(query):
    """Return a small list of validated HTTP(S) results from SearXNG."""
    params = urlencode({
        "q": query,
        "format": "json",
        "language": "en",
        "safesearch": 2,
    })
    data = get_json(f"{SEARXNG_URL}/search?{params}")
    results = []

    for item in data.get("results", []):
        url = (item.get("url") or "").strip()
        if not url.startswith(("https://", "http://")):
            continue
        results.append({
            "title": (item.get("title") or "Untitled result").strip(),
            "url": url,
            "content": (item.get("content") or "No summary provided.").strip(),
            "engine": ", ".join(item.get("engines") or []) or "Web",
        })
        if len(results) >= MAX_RESULTS:
            break
    return results


def generate_answer(query, results):
    """Ask a local Ollama model to summarize snippets; search still works without it."""
    if not results:
        return None, "No search results were returned."

    snippets = "\n\n".join(
        f"[{index}] {item['title']}\nURL: {item['url']}\nSnippet: {item['content']}"
        for index, item in enumerate(results, start=1)
    )
    prompt = (
        "Answer the question using only the supplied web search snippets. "
        "Be concise, say when information is insufficient, and cite claims using "
        "source numbers such as [1]. Do not invent facts.\n\n"
        f"Question: {query}\n\nSearch results:\n{snippets}"
    )

    try:
        data = post_json(
            f"{OLLAMA_URL}/api/chat",
            {
                "model": OLLAMA_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            },
        )
        answer = data.get("message", {}).get("content", "").strip()
        if answer:
            return answer, None
        return None, "The AI service returned an empty answer."
    except HTTPError as exc:
        if exc.code == 404:
            return None, (
                f"The Ollama model '{OLLAMA_MODEL}' may not be installed. "
                f"Run `ollama pull {OLLAMA_MODEL}` to enable AI answers."
            )
        return None, f"Ollama returned HTTP {exc.code}; showing web results only."
    except (URLError, TimeoutError, OSError):
        return None, "AI is offline; showing web results only. Install and start Ollama to enable AI answers."


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "Private Search Engine"})


@app.post("/api/search")
def api_search():
    body = request.get_json(silent=True) or {}
    query = str(body.get("query", "")).strip()

    if not query:
        return jsonify({"error": "Enter a question or search term."}), 400
    if len(query) > 300:
        return jsonify({"error": "Search queries must be 300 characters or fewer."}), 400

    try:
        results = search_web(query)
    except HTTPError as exc:
        if exc.code == 403:
            message = (
                "SearXNG rejected JSON output. Enable 'json' under search.formats "
                "in SearXNG settings.yml, then restart its core service."
            )
        else:
            message = f"SearXNG returned HTTP {exc.code}. Check its container and configuration."
        return jsonify({"error": message}), 502
    except (URLError, TimeoutError, OSError):
        return jsonify({
            "error": f"Cannot connect to SearXNG at {SEARXNG_URL}. Check Docker Desktop and the SearXNG container."
        }), 502
    except (json.JSONDecodeError, ValueError):
        return jsonify({
            "error": "SearXNG did not return valid JSON. Check that JSON output is enabled."
        }), 502

    answer, ai_notice = generate_answer(query, results)
    return jsonify({
        "query": query,
        "answer": answer,
        "ai_notice": ai_notice,
        "sources": results,
    })


if __name__ == "__main__":
    print("Private Search Engine is starting.")
    print("Open http://127.0.0.1:5000 in your browser.")
    print("SearXNG:", SEARXNG_URL)
    # Local-only binding; do not change to 0.0.0.0 for a private local project.
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)
