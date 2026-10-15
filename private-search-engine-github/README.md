# Private Search Engine

A local-first search interface built with **Python**, **Flask**, **SearXNG**, and optional **Ollama**. Search the web through your own SearXNG instance and optionally generate an answer using a local language model.

> Status: beginner-friendly prototype. It is not a fully anonymous search service or a production-hardened application.

## Features

- Search results from a configured SearXNG instance
- Optional AI-generated summaries via Ollama
- Works in web-search-only mode when Ollama is unavailable
- Responsive dark interface
- Clear error messages for common connection/configuration issues
- Built-in health endpoint and unit tests
- Uses Python's built-in `urllib`; no `requests` dependency

## How it works

```text
Browser
   |
   v
Flask app (127.0.0.1:5000)
   |
   +----> SearXNG (127.0.0.1:8080) ----> configured search engines
   |
   +----> Ollama (127.0.0.1:11434) [optional local AI]
```

## Requirements

- Windows 10/11 (the commands below use PowerShell)
- Python 3.10+
- Docker Desktop and a working SearXNG instance
- Optional: Ollama for AI answers

## Quick start on Windows

### 1. Start SearXNG

Start Docker Desktop. In the folder containing your existing SearXNG Compose file, run:

```powershell
docker ps
```

You should see your SearXNG container (for example, `searxng-core`) running and exposing port 8080.

Test the JSON API:

```powershell
Invoke-RestMethod "http://127.0.0.1:8080/search?q=python&format=json" | Select-Object query
```

If JSON output is disabled, add `json` to the existing `search.formats` list in the SearXNG `settings.yml`, preserving existing settings. If the `search:` section already exists, edit it; do not create a duplicate section. Restart the core service using Compose from the folder that contains the Compose file.

### 2. Download and open this repository

Clone it with Git:

```powershell
git clone <YOUR-GITHUB-REPOSITORY-URL>
cd private-search-engine-github
```

Or download the repository ZIP from GitHub and extract it, then open that folder in VS Code.

### 3. Create the Python environment

Run in the folder containing `app.py`:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Or double-click `run.bat`, which creates the environment and installs the dependency if needed.

### 4. Start the application

```powershell
.\.venv\Scripts\python.exe app.py
```

Open <http://127.0.0.1:5000>. Keep the terminal open while using the site.

Health check: <http://127.0.0.1:5000/health>

## Optional AI answers with Ollama

Install Ollama from <https://ollama.com/download>. Open a new terminal and run:

```powershell
ollama pull llama3.2:3b
```

Ollama usually runs as a background application on Windows. Test the API:

```powershell
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```

If Ollama is unavailable, web results should still appear with an AI-offline notice.

## Configuration

Default local endpoints are defined in `app.py` and can be overridden with environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `SEARXNG_URL` | `http://127.0.0.1:8080` | SearXNG base URL |
| `OLLAMA_URL` | `http://127.0.0.1:11434` | Ollama base URL |
| `OLLAMA_MODEL` | `llama3.2:3b` | Local model name |
| `PORT` | `5000` | Flask development port |

`.env.example` is a reference file only; this project does not automatically load `.env`. Set environment variables in the terminal if you need custom values. Never commit secrets or private configuration.

Example PowerShell override for the current terminal session:

```powershell
$env:SEARXNG_URL = "http://127.0.0.1:8080"
$env:OLLAMA_MODEL = "llama3.2:3b"
```

## Run tests

Install the requirements first, then run:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The tests use mocked search/AI functions; they do not require live SearXNG or Ollama.

## GitHub setup

From the project root:

```powershell
git init
git add .
git status
git commit -m "Initial private search engine prototype"
```

Create an empty repository on GitHub, then connect it using the repository URL GitHub provides:

```powershell
git branch -M main
git remote add origin <YOUR-GITHUB-REPOSITORY-URL>
git push -u origin main
```

Replace the placeholder with your actual repository URL. Do not paste tokens or passwords into source code or commit them.

Before pushing, review `git status` and confirm `.venv`, `.env`, caches, and personal configuration files are not staged. `.gitignore` excludes common local files.

## Troubleshooting

- **Blank homepage:** ensure `templates/index.html` is next to `app.py` inside the `templates` folder.
- **Cannot connect to SearXNG:** verify Docker is running and the JSON API test succeeds.
- **SearXNG JSON error / HTTP 403:** enable JSON in SearXNG's `search.formats`.
- **AI unavailable:** web search can still work; start Ollama and pull the selected model.
- **Compose says no configuration file:** run `docker compose` only from the folder containing the Compose YAML. `docker ps` works from any folder.

## Privacy and security notes

- Flask binds to `127.0.0.1` by default, making it local-only on the same machine.
- SearXNG forwards searches to the search engines configured in its settings. This app is not fully offline or automatically anonymous.
- Ollama can run the language model locally, but search queries still go to SearXNG.
- Search snippets and results may be inaccurate. Verify important claims against source pages.
- Do not expose the Flask development server to the public internet. Do not deploy this prototype as-is for multiple users.
- Never commit passwords, API keys, `.env` files, personal data, or machine-specific configuration.
- If you later add API keys or authentication, store secrets in environment variables or a proper secret manager.
