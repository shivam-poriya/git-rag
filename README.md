# GitRAG

GitRAG clones Git repositories, chunks and embeds their files into PostgreSQL/pgvector with Google Gemini embeddings, and serves semantic code search and retrieval-augmented chat over them through a FastAPI backend and a React frontend.

## How it works

1. **Queue**: `POST /v1/git-repo/repo/clone/` (or `/clone-private/`) inserts a `repositories` row with status `processing` and returns `{"status": "accepted", "repo_id": ...}` right away. `services/repo/process.py:process_repo` then runs as a FastAPI `BackgroundTasks` job in the same process.
2. **Clone** (`services/repo/clone.py`): `git ls-remote <url>` checks that the repository is reachable, then `git clone` writes it to **`backend/media/repos/<name>`**. `<name>` is the last URL segment with `.git` removed. For private repositories the token is inserted into the URL as `https://<token>@...`.
3. **Collect and load** (`collect.py`, `load.py`): walks the clone with `rglob` and skips:
   - directories `.git`, `node_modules`, `venv`, `.venv`, `__pycache__`, `dist`, `build`, `.next`, `.cache`
   - binary extensions (images, `.pdf`, archives, audio/video, `.exe`/`.dll`/`.so`/`.dylib`/`.bin`, `.class`, `.jar`, `.pyc`)
   - files larger than 2 MB

   Each remaining file is read as UTF-8 (undecodable bytes dropped). Empty files are discarded, and the rest become LangChain `Document`s with `path`, `filename` and `extension` metadata.
4. **Chunk** (`chunking/splitter_router.py`): tags each document with a language from `LANGUAGE_REGISTRY`, falling back to `text`. Files at or below a size threshold stay as one chunk: 3000 chars for Markdown, 2000 for `.json/.yaml/.yml/.toml/.ini`, 5000 for everything else. Larger files go to a `langchain-text-splitters` splitter chosen by extension (sizes are characters, not tokens):
   - `.py`, `.pyi`: `RecursiveCharacterTextSplitter.from_language(Language.PYTHON)`, size 1500, overlap 200
   - `.js`, `.jsx`, `.ts`, `.tsx`: `Language.JS`, 1500/200
   - `.java`: `Language.JAVA`, 1500/200
   - `.md`, `.markdown`: `MarkdownHeaderTextSplitter` on `#`–`######` (headers kept), then `RecursiveCharacterTextSplitter` 1000/100
   - anything else: `RecursiveCharacterTextSplitter` 1000/100
5. **Embed** (`embeddings/`): `GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")` embeds chunks in batches of 100, producing 3072-dimensional vectors.
6. **Store** (`db/`): bulk-inserts the chunks into `repository_chunks.embedding vector(3072)` and sets the repository status to `completed`. Any exception sets it to `failed`. The `total_files` and `total_chunks` counters are written before embedding starts, so they appear in the UI while the status is still `processing`.
7. **Search** (`services/search/semantic_search.py`): embeds the query with the same Gemini model, then runs `ORDER BY embedding <=> :query LIMIT top_k` (pgvector cosine distance). The query joins `repositories` to restrict results to the caller's repositories, optionally to one `repo_id`. The returned score is `1 - distance/2`, rounded to 4 decimals.
8. **Chat** (`services/chat/rag_chat.py`): saves the user message, then:
   - retrieves the top 5 chunks from the session's repository (`CONTEXT_TOP_K`)
   - loads the session's last 10 messages (`HISTORY_WINDOW`)
   - builds a `ChatPromptTemplate`: a system prompt containing the chunks (file, language, relevance %), then the history, then the question
   - calls `ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)`
   - stores the answer with the unique source file paths

Everything runs in one uvicorn process. Indexing has no job queue: it runs after the HTTP response in the same process, so restarting the server mid-index leaves that repository stuck in `processing`. Embeddings and generation are Gemini API calls, so the backend loads no local models and needs no GPU. Cloning, indexing, search and chat all need internet access. `POST /v1/chat/chat/` is synchronous and returns only after Gemini answers. The only infrastructure is PostgreSQL 16 with pgvector, run from `backend/docker-compose.yml`. On startup the backend runs `CREATE EXTENSION IF NOT EXISTS vector` and `Base.metadata.create_all`. There are no migrations, so column changes to existing tables are not applied. No ANN index is defined on `embedding`, so each search is an exact scan over the user's chunks. The frontend polls the repository list every 5 s to pick up status changes.

## Project structure

```
git-rag/
├── backend/                            # FastAPI API + indexing/RAG services; run backend commands from here
│   ├── main.py                         # Entry point: app, CORS, settings import, uvicorn on HOST:PORT
│   ├── requirement.txt                 # Pinned Python deps (FastAPI, SQLAlchemy, pgvector, LangChain, Gemini)
│   ├── docker-compose.yml              # pgvector/pgvector:pg16, host port 5435 -> container 5432
│   ├── config/
│   │   ├── urls.py                     # Mounts each app's router under /v1/<app>
│   │   └── settings/
│   │       ├── base.py                 # Loads .env file, JWT constants, 400 validation handler, /media mount
│   │       ├── development.py          # DB engine, CREATE EXTENSION vector, create_all, SMTP + Gemini keys
│   │       ├── production.py           # Variant without vector extension/SMTP/Gemini; never selected by main.py
│   │       ├── utils.py                # load_env(): env/.env.<env> -> os.environ
│   │       └── env/                    # .env.development, .env.production (not committed)
│   ├── apps/                           # HTTP layer, one package per router
│   │   ├── db_models.py                # SQLAlchemy models: users, repositories, repository_chunks, chat_*
│   │   ├── custom_auth/                # /v1/custom-auth: register, login (JWT), profile; welcome_email.html
│   │   ├── git_repo/                   # /v1/git-repo: queue clone+index, list, delete
│   │   ├── search/                     # /v1/search: semantic search endpoint
│   │   ├── chat/                       # /v1/chat: sessions and messages -> services/chat
│   │   ├── dashboard/                  # /v1/dashboard: per-user counts
│   │   └── utils/                      # Bearer-token check, Gmail SMTP sender
│   ├── services/
│   │   ├── repo/
│   │   │   ├── process.py              # Orchestrator: clone -> collect -> load -> chunk -> embed -> store
│   │   │   ├── clone.py                # git ls-remote + git clone -> media/repos/<name>
│   │   │   ├── collect.py              # File filter: ignored dirs, binary extensions, > 2 MB
│   │   │   ├── load.py                 # Files -> LangChain Documents (path, filename, extension, size)
│   │   │   ├── chunking/               # constants.py (thresholds, registries), splitter_router.py, splitters/
│   │   │   ├── embeddings/             # gemini-embedding-001 client (module singleton), batches of 100
│   │   │   └── db/                     # Insert repository row, bulk-insert chunks, update status/counters
│   │   ├── search/semantic_search.py   # Query embedding -> pgvector cosine distance -> top-k
│   │   └── chat/rag_chat.py            # Top-5 chunks + last 10 messages -> gemini-2.5-flash
│   ├── test/
│   │   ├── login.py                    # unittest against a running server
│   │   └── test_gemini.py              # One-off Gemini connectivity check
│   ├── venv/                           # (not committed) local virtualenv
│   └── media/                          # (not committed) clones and uploads, created at runtime
└── frontend/                           # React 19 + Vite 8 single-page app
    ├── package.json                    # Scripts: dev, build, lint, preview
    ├── vite.config.js                  # Only @vitejs/plugin-react; no port or proxy configured
    ├── index.html
    └── src/
        ├── api.js                      # All backend calls; BASE_URL = 'http://localhost:8000'
        ├── App.jsx                     # Shell; switches pages via React state (no router)
        ├── contexts/                   # Auth (tokens in localStorage), Repo (polls list every 5 s), Toast
        ├── components/Sidebar.jsx
        ├── pages/                      # Auth, Dashboard, Repositories, Search, Chat, Profile
        └── index.css                   # All styles
```

## Indexed data

GitRAG has no bundled dataset. The data is whatever Git repositories users add at runtime: a public HTTPS URL, or a private one plus an access token.

1. In the UI, open **Repositories → Add Repository** and enter the URL (and a token for private repositories). You can also call `POST /v1/git-repo/repo/clone/` directly.
2. Wait for the status to change from `processing` to `completed`. The frontend re-fetches the list every 5 s.
3. Only `completed` repositories appear in the Search and Chat repository pickers. The API also rejects search and chat on a repository that is not `completed`.

The backend creates `backend/media/repos/` at import time (`clone.py`). Do not create it by hand. `backend/.gitignore` excludes `/media/`, so clones are never committed.

```
backend/
├── config/settings/env/.env.development    # you create (folder is git-ignored)
└── media/                                   # generated at runtime (git-ignored)
    ├── repos/<repo-name>/                   # git clone of each added repository
    └── user_profile/<uuid4>_<filename>      # photos uploaded via /update-user-profile/
```

Each chunk becomes one row in `repository_chunks`. The examples below come from running the project's own collect → load → chunk code on this repository:

| Column | Type | Example |
|---|---|---|
| `repo_id` | UUID, FK → `repositories.id`, `ON DELETE CASCADE` | the UUID4 returned by the clone request |
| `path` | text | `<abs path to backend>/media/repos/git-rag/backend/main.py` (absolute server path) |
| `filename` | varchar(255) | `main.py` |
| `extension` | varchar(50) | `.py`; suffix-less dotfiles use the whole name, e.g. `.gitignore` |
| `language` | varchar(50) | `python`; unknown extensions are `text` |
| `chunk_index` / `chunk_count` | int | `1` / `1` for `backend/main.py` (971 chars, under the 5000-char threshold); `1`…`6` for `services/chat/rag_chat.py`; `1`…`16` for `pages/ChatPage.jsx` |
| `content` | text | the chunk text |
| `embedding` | `vector(3072)` | Gemini embedding of `content` |
| `created_at` | timestamptz | `now()` |

Conventions the code relies on:
- `chunk_index` is 1-based. `extension` is lower-cased.
- `repositories.status` takes the values `processing`, `completed` or `failed`. `repositories.embedding_model` is always `models/gemini-embedding-001`.
- `chat_messages.role` is `user` or `assistant`. `chat_messages.sources` stores a JSON-encoded list of file paths as text.
- Lock files and CSS are not filtered. In this repository's 93 tracked files, the pipeline collects 92 (the PNG is skipped), keeps 79 non-empty documents and produces 306 chunks. 94 of those chunks come from `frontend/package-lock.json` and 38 from `frontend/src/index.css`. Embedding them takes 4 batches.

## Generated artifacts

| Artifact | Created by | Location | Notes |
|---|---|---|---|
| Repository clones | `services/repo/clone.py` | `backend/media/repos/<name>/` | Needs network access and `git` on `PATH`. An existing folder with the same name is reused without `git pull`. |
| Chunks + embeddings | `services/repo/process.py` | Postgres volume `postgres_data` (container `repo-postgres`) | Needs the Gemini API. Local to each machine: re-add repositories after resetting the volume. |
| Profile photos | `POST /v1/custom-auth/update-user-profile/` | `backend/media/user_profile/` | |
| Frontend bundle | `npm run build` | `frontend/dist/` | Git-ignored. |

## Getting started

Prerequisites:
- Python 3.11
- Node.js `^20.19.0` or `>=22.12.0` (required by Vite 8)
- Docker
- `git` on `PATH`. The backend shells out to `git`; if it is missing, every clone fails with "Repository does not exist or is inaccessible".
- A Google Gemini API key
- Optional: Gmail SMTP credentials for welcome emails

```bash
# 1. Clone
git clone https://github.com/shivam-poriya/git-rag.git
cd git-rag/backend

# 2. Start Postgres 16 + pgvector (localhost:5435, user postgres, password 123, db postgres)
docker compose up -d

# 3. Python dependencies (note the file name: requirement.txt)
python -m venv venv
source venv/bin/activate              # Windows: venv\Scripts\activate
pip install -r requirement.txt

# 4. Env file; the whole env/ folder is git-ignored, so create it
mkdir -p config/settings/env
cat > config/settings/env/.env.development <<'EOF'
HOST=127.0.0.1
PORT=8000
DB_URI=postgresql://postgres:123@localhost:5435/postgres
DB_NAME=postgres
GEMINI_API_KEY=<your-gemini-api-key>
SMTP_USERNAME=
SMTP_PASSWORD=
EOF

# 5. Start the API from backend/ (media/ is resolved against the working directory)
python main.py                        # creates the vector extension + tables, serves on HOST:PORT
                                      # Swagger UI: http://127.0.0.1:8000/docs

# 6. Frontend, in another terminal
cd git-rag/frontend                   # from the directory you cloned into
npm install
npm run dev                           # Vite dev server; open the URL it prints
```

## Configuration

Environment variables are read from **`backend/config/settings/env/.env.<ENVIRONMENT>`** by `config/settings/utils.py:load_env`. `load_dotenv` is called without `override`, so variables already set in the shell take precedence over the file.

| Variable | Default | Meaning |
|---|---|---|
| `ENVIRONMENT` | `development` | Selects which `.env.<ENVIRONMENT>` file `base.py` loads. It does not switch the settings module: `main.py` hardcodes `environment = "development"`, so `development.py` is always used. |
| `HOST`, `PORT` | none (required) | Bind address for `python main.py`. `PORT` goes through `int()`, so a missing value crashes startup. Must match the frontend's `BASE_URL`. |
| `DB_URI` | none (required) | SQLAlchemy URL. With the bundled compose file: `postgresql://postgres:123@localhost:5435/postgres`. |
| `DB_NAME` | none | Only printed at startup. The database comes from `DB_URI`. |
| `GEMINI_API_KEY` | `""` | Used for embeddings (`gemini-embedding-001`) and chat (`gemini-2.5-flash`). Effectively required: the embedding client is built at import time, and with an empty key (and no Google default credentials) the backend fails to start with `DefaultCredentialsError`. |
| `SMTP_USERNAME`, `SMTP_PASSWORD` | none | Gmail account for the welcome email. `smtp.gmail.com:587` with STARTTLS is hardcoded in `apps/utils/send_email.py`. Optional: send failures are printed and registration still succeeds. |
| `API_KEY` | none | Read into `settings.api_key` but not used anywhere. |

Settings that live in code rather than in the environment:

| Setting | Value | Where | Effect / trade-off |
|---|---|---|---|
| `SECRET_KEY`, `REFRESH_TOKEN_SECRET_KEY` | hardcoded strings | `config/settings/base.py` | JWT signing keys (HS256). Change them before deploying. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` / `REFRESH_TOKEN_EXPIRE_DAYS` | `300` / `7` | `base.py` | Token lifetimes. There is no refresh endpoint; the frontend only stores the refresh token. |
| `CODE_SPLIT_THRESHOLD` / `MARKDOWN_SPLIT_THRESHOLD` / `CONFIG_SPLIT_THRESHOLD` | `5000` / `3000` / `2000` chars | `services/repo/chunking/constants.py` | Files at or below the threshold stay as one chunk. Higher means fewer, larger chunks: fewer embedding calls, coarser retrieval. |
| `chunk_size` / `chunk_overlap` | `1500/200` (code), `1000/100` (Markdown, fallback) | `chunking/splitters/*.py` | Smaller chunks give more precise hits but more vectors. |
| `batch_size` | `100` | `embeddings/embed_chunks.py` | Texts per `embed_documents` call. |
| `CONTEXT_TOP_K` | `5` | `services/chat/rag_chat.py` | Chunks passed to the LLM. Higher gives more context and longer prompts. |
| `HISTORY_WINDOW` | `10` | `rag_chat.py` | Past messages included as conversation memory. |
| LLM `temperature` | `0.3` | `rag_chat.py` | |
| `top_k` (search API) | default `5`, allowed `1`–`50` | `apps/search/router/models/v1_model.py` | The UI offers 3, 5, 10 or 20. |

Other components:
- **Frontend → backend**: `BASE_URL` is hardcoded as `http://localhost:8000` in `frontend/src/api.js`. There is no Vite env variable, so edit this file if `HOST`/`PORT` change.
- **CORS**: `main.py` allows all origins (`allow_origins=["*"]`), so the Vite dev server works on any port.
- **Working directory**: start the backend from `backend/`. `StaticFiles(directory="media")` and the repository delete handler (`os.path.join("media", "repos", ...)`) resolve paths against the working directory.
- **Production settings**: `config/settings/production.py` is never imported unless you edit `main.py`. It also does not define `GEMINI_API_KEY`, `SMTP_USERNAME` or `SMTP_PASSWORD`, so chat and welcome emails would fail under it.

## API reference

All routes are under `http://127.0.0.1:8000` (`HOST`:`PORT`). All of them except `test`, `register` and `login` require `Authorization: Bearer <access_token>`.

| Method | Path | Body / params | Response |
|---|---|---|---|
| GET | `/v1/custom-auth/test` | | `{"message": "Custom Auth API Root"}` |
| POST | `/v1/custom-auth/register/` | JSON `username` (3–32), `email`, `password` (8–32), `address` (≤32, optional) | `{"message", "user_id"}`; welcome email sent in the background |
| POST | `/v1/custom-auth/login/` | form-urlencoded `username`, `password` | `{"access_token", "token_type": "bearer", "user", "refresh_token"}` |
| GET | `/v1/custom-auth/get-user-profile/` | | profile fields, plus `profile_photo_path` if a photo exists |
| POST | `/v1/custom-auth/update-user-profile/` | multipart: `phone`, `username`, `email` required; `first_name`, `last_name`, `organization_name`, `location`, `birthday` optional (3–70 chars); `photo` file optional | updated profile |
| POST | `/v1/git-repo/repo/clone/` | JSON `repo_url`, `branch_name` (optional) | `{"status": "accepted", "repo_id", "message": "Repository processing started."}` |
| POST | `/v1/git-repo/repo/clone-private/` | JSON `repo_url`, `token`, `branch_name` (optional) | same as above |
| GET | `/v1/git-repo/repos/repositories` | | list of repositories with `status`, `total_files`, `total_chunks` |
| DELETE | `/v1/git-repo/repos/repository/{repo_id}/` | | `204`; deletes the row (chunks and chat sessions cascade) and the clone folder |
| GET | `/v1/dashboard/stats` | | `{"total_repositories", "total_chunks", "processing_repositories"}` |
| POST | `/v1/search/semantic/` | JSON `query`, `repo_id` (optional), `top_k` (1–50, default 5) | list of `{file, path, filename, language, extension, chunk_index, content, score, repo_id}` |
| POST | `/v1/chat/session/` | JSON `name`, `repo_id` (must be `completed`) | `201` session object |
| GET | `/v1/chat/sessions/` | | sessions, newest first, with `repo_name`, `message_count` |
| GET | `/v1/chat/session/{session_id}/messages/` | | messages, oldest first, with `sources` |
| POST | `/v1/chat/chat/` | JSON `session_id`, `message` | `{"user_message", "assistant_message"}` |
| DELETE | `/v1/chat/session/{session_id}/` | | `204` |

Example:

```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/v1/custom-auth/login/ \
  -d 'username=alice&password=Example@123' | python -c 'import sys, json; print(json.load(sys.stdin)["access_token"])')

curl -X POST http://127.0.0.1:8000/v1/git-repo/repo/clone/ \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"repo_url": "https://github.com/shivam-poriya/git-rag.git"}'

curl -X POST http://127.0.0.1:8000/v1/search/semantic/ \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"query": "where is the Gemini chat model configured", "top_k": 3}'
```

## Testing

There is no test runner configuration. The two scripts in `backend/test/` are run directly:

```bash
cd backend
python test/login.py        # unittest; needs the API on 127.0.0.1:8000 and an existing user raj / Test@123
python test/test_gemini.py  # sends "Hello" to gemini-2.5-flash
```

- `login.py` posts to `/login`, but the route is `/v1/custom-auth/login/`, so `test_valid_login` fails as written.
- `test_gemini.py` reads `GOOGLE_API_KEY`, not `GEMINI_API_KEY`, from the environment or a `.env` file found by `python-dotenv`.

Frontend linting: `cd frontend && npm run lint`.

## Known issues

- **`python main.py` serves an app without the `/media` mount or the 400 validation handler.** `base.py` does `from main import app`, which imports `main.py` a second time as module `main`. Those registrations land on that second app instance, not on the one passed to `uvicorn.run`. As a result, `profile_photo_path` URLs return 404, and validation errors come back as FastAPI's default 422 with a list `detail`.
- **Chat breaks on curly braces.** History messages are added to `ChatPromptTemplate` as template strings. Once any of the last 10 messages in a session contains `{` or `}` (for example code in a previous answer), every later message in that session fails with `500 LLM pipeline failed`.
- **`branch_name` is ignored.** It is accepted by the clone endpoints but never passed to `git clone` or stored, so the default branch is always indexed.
- **Clones are keyed by repository name only.** An existing `media/repos/<name>` folder is reused without pulling, two repositories with the same name share one folder, and deleting either removes the folder for both.
- **Private-repository problems:**
  - The existence check (`git ls-remote`) uses the URL without the token, so it only passes if the server's own git credentials can reach the repository.
  - The token is embedded in the clone URL, so it is stored in that clone's `.git/config`.
- **Absolute server paths are exposed.** Chat sources and search results show the server's absolute file paths (for example `.../backend/media/repos/<name>/src/app.py`) rather than repository-relative ones.
- **Unsanitized HTML in chat.** Assistant replies are rendered with `marked` into `dangerouslySetInnerHTML` without sanitization.
- **Password length mismatch.** The register form accepts 6-character passwords, but the API requires at least 8.
