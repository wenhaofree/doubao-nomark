# Repository Guidelines

## Project Structure & Module Organization

This repository provides a FastAPI service and browser-extension helpers for extracting unmarked media from Doubao, Qianwen, and related share links.

- `app.py`: FastAPI entry point, models, and `/parse` plus `/parse-video` routes.
- `doubao_parser/`: reusable parser package; keep image logic in `image.py` and video logic in `video.py`.
- `index.html`, `icons/`, `docs/images/`: static UI and documentation assets.
- `extension/tampermonkey-script/`: Tampermonkey userscript.
- `extension/edge/`: Edge extension manifest, popup, and content script.
- `.github/workflows/`: Python lint and Docker build CI.

## Build, Test, and Development Commands

- `uv sync`: create/update the local virtual environment from `pyproject.toml` and `uv.lock`.
- `source .venv/bin/activate`: activate the uv-created environment on macOS/Linux.
- `uvicorn app:app --host 0.0.0.0 --port 8000`: run the API; docs are at `http://localhost:8000/docs`.
- `ruff check app.py doubao_parser/ --config .ruff.toml`: run the same linter used by CI.
- `ruff format app.py doubao_parser/ --config .ruff.toml`: format Python sources.
- `docker build -t doubao-nomark .`: build the local container image.
- `docker run -p 8000:8000 doubao-nomark`: run the service in Docker.

## Coding Style & Naming Conventions

Python targets 3.10+ and is formatted with Ruff. Use 4-space indentation, double quotes, and a 120-character line limit. Prefer async functions for network parsing paths because the API handlers await parser calls. Use `snake_case` for functions and variables, `PascalCase` for Pydantic models, and route names that describe the media type, such as `parse_video_get`.

Keep parser-specific branching inside `doubao_parser/`; `app.py` should stay focused on validation, routing, and response shaping.

## Testing Guidelines

There is no committed automated test suite yet. For parser changes, add focused `pytest` tests under `tests/`, named like `test_image_parse.py` or `test_video_parse.py`. Until tests exist, validate manually:

- `GET /parse?url=<share-url>`
- `POST /parse` with `{"url": "...", "return_raw": false}`
- `GET /parse-video?url=<share-url>`

Always run Ruff before opening a pull request.

## Commit & Pull Request Guidelines

Recent history uses short messages such as `feat: add qianwen image generate parse` and `fix`. Prefer concise prefixes: `feat:`, `fix:`, `docs:`, `chore:`, or `refactor:`. English or Chinese subjects are both present; keep them specific.

Pull requests should include a summary, affected endpoints or extension files, manual verification steps, and screenshots for `index.html` or extension UI changes. Link issues when available.

## Security & Configuration Tips

Do not commit real share-link payloads that expose private conversations. Keep CORS changes deliberate in `app.py`; the current service allows all origins for easy extension and browser use.
