import json
from urllib.parse import parse_qs, urlparse

from workers import Response, WorkerEntrypoint

from doubao_parser.image import doubao_image_parse, qianwen_image_parse
from doubao_parser.video import doubao_video_parse, yunque_video_parse

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
}


def json_response(data: dict, status: int = 200):
    headers = {"Content-Type": "application/json; charset=utf-8", **CORS_HEADERS}
    return Response(json.dumps(data, ensure_ascii=False), status=status, headers=headers)


def get_value(data, key: str, default=None):
    if isinstance(data, dict):
        return data.get(key, default)
    return getattr(data, key, default)


def parse_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).lower() in {"1", "true", "yes", "on"}


async def read_payload(request, params: dict):
    if request.method == "GET":
        return {
            "url": params.get("url", [""])[0],
            "return_raw": parse_bool(params.get("return_raw", ["false"])[0]),
        }

    try:
        body = await request.json()
    except Exception:
        body = {}

    return {
        "url": str(get_value(body, "url", "")),
        "return_raw": parse_bool(get_value(body, "return_raw", False)),
    }


async def parse_image(payload: dict):
    url = payload["url"]
    return_raw = payload["return_raw"]
    if not url:
        raise ValueError("缺少 url 参数")

    if "doubao.com" in url:
        result = await doubao_image_parse(url, return_raw=return_raw)
    else:
        result = await qianwen_image_parse(url, return_raw=return_raw)

    if return_raw:
        return {"success": True, "data": result}
    return {"success": True, "image_count": len(result), "images": result}


async def parse_video(payload: dict):
    url = payload["url"]
    return_raw = payload["return_raw"]
    if not url:
        raise ValueError("缺少 url 参数")

    if "doubao.com" in url:
        result = await doubao_video_parse(url, return_raw=return_raw)
    else:
        result = await yunque_video_parse(url, return_raw=return_raw)

    if return_raw:
        return {"success": True, "data": result}
    return {"success": True, "video": result}


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        if request.method == "OPTIONS":
            return Response(None, status=204, headers=CORS_HEADERS)

        parsed_url = urlparse(request.url)
        params = parse_qs(parsed_url.query)

        try:
            if parsed_url.path == "/parse":
                return json_response(await parse_image(await read_payload(request, params)))

            if parsed_url.path == "/parse-video":
                return json_response(await parse_video(await read_payload(request, params)))

            if parsed_url.path in {"/", "/health"}:
                return json_response(
                    {
                        "message": "Doubao Parser - Cloudflare Worker",
                        "endpoints": ["/parse", "/parse-video"],
                        "version": "1.0.5",
                    }
                )

            return json_response({"detail": "Not Found"}, status=404)
        except (ValueError, KeyError) as exc:
            return json_response({"detail": str(exc)}, status=400)
        except Exception as exc:
            if parsed_url.path == "/parse-video":
                print(f"Exception: {exc}")
                return json_response({"detail": "视频解析失败，请检查链接是否正确"}, status=500)

            print(f"Exception: {exc}")
            return json_response({"detail": "图片解析失败，请检查链接是否正确"}, status=500)
