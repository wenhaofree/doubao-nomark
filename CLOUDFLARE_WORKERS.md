# Cloudflare Workers Deployment

This project can run on Cloudflare Workers through Python Workers. The Worker entry point is `worker.py`; it reuses the parser functions in `doubao_parser/`, so the deployed endpoints match the local API paths without requiring an ASGI server.

## Requirements

- `uv`
- Node.js
- Cloudflare account with Workers enabled

Python Workers are currently beta and require the `python_workers` compatibility flag. This repository already includes that flag in `wrangler.jsonc`.

## Deploy

1. Install Python dependencies locally:

```bash
uv sync
```

2. Log in to Cloudflare:

```bash
./scripts/cloudflare-worker.sh login
```

3. Test locally with the Workers runtime:

```bash
./scripts/cloudflare-worker.sh dev
```

4. Deploy:

```bash
./scripts/cloudflare-worker.sh deploy
```

After deploy, Cloudflare prints the Worker URL, for example:

```text
https://doubao-nomark.<your-subdomain>.workers.dev
```

Use that value as `BASE_URL` in the examples below.

The wrapper script builds from a temporary Worker project using `cloudflare_worker/pyproject.toml`. This keeps the local FastAPI/Pydantic app dependencies untouched while deploying only the Cloudflare-compatible Worker dependency set.

## API Endpoints

### Image Parsing API

Endpoint:

```text
GET /parse?url=<image-share-url>&return_raw=false
POST /parse
```

Use it for Doubao thread links and Qianwen share chat links.

GET example:

```bash
curl --get "$BASE_URL/parse" \
  --data-urlencode "url=https://www.doubao.com/thread/xxxxxx" \
  --data-urlencode "return_raw=false"


curl --get "https://doubao-nomark.wenhaofree.workers.dev/parse" \
  --data-urlencode "url=https://www.doubao.com/thread/wb02b5cfd1e252028" \
  --data-urlencode "return_raw=false"
```

POST example:

```bash
curl -X POST "$BASE_URL/parse" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.doubao.com/thread/xxxxxx","return_raw":false}'


curl -X POST "https://doubao-nomark.wenhaofree.workers.dev/parse" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.doubao.com/thread/wb02b5cfd1e252028","return_raw":false}'
```

Success response:

```json
{
  "success": true,
  "image_count": 1,
  "images": [
    {
      "url": "https://...",
      "width": 1024,
      "height": 1024
    }
  ]
}
```

Set `return_raw=true` to return upstream raw data:

```json
{
  "success": true,
  "data": {}
}
```

### Video Parsing API

Endpoint:

```text
GET /parse-video?url=<video-share-url>&return_raw=false
POST /parse-video
```

Use it for Doubao video share links and Yunque video share links.

GET example:

```bash
curl --get "$BASE_URL/parse-video" \
  --data-urlencode "url=https://www.doubao.com/video-sharing?share_id=xxx&video_id=xxx" \
  --data-urlencode "return_raw=false"
```

POST example:

```bash
curl -X POST "$BASE_URL/parse-video" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.doubao.com/video-sharing?share_id=xxx&video_id=xxx","return_raw":false}'

curl -X POST "https://doubao-nomark.wenhaofree.workers.dev/parse-video" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.doubao.com/video-sharing?share_id=38779230228040962&video_id=v0369cg10004d69dh7fog65md3ncqvg0","return_raw":false}'
```

Success response:

```json
{
  "success": true,
  "video": {
    "url": "https://...",
    "width": 1920,
    "height": 1080,
    "definition": "1080p",
    "poster_url": "https://..."
  }
}
```

## Error Responses

Invalid or expired share links return `400`:

```json
{
  "detail": "链接格式不正确，请使用豆包对话链接（包含 /thread/）"
}
```

Unexpected upstream or parsing failures return `500`:

```json
{
  "detail": "图片解析失败，请检查链接是否正确"
}
```
