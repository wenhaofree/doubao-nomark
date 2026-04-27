import html
import json
import re

import httpx


def _json_loads(value):
    if isinstance(value, str):
        return json.loads(value)
    return value


def _extract_router_data_args(html_str: str):
    for match in re.finditer(r'data-fn-args="([^"]*)"', html_str, re.DOTALL):
        try:
            json_data = json.loads(html.unescape(match.group(1)))
        except json.JSONDecodeError:
            continue

        if any(_iter_share_data(json_data)):
            return json_data
    return None


def _iter_share_data(json_data):
    if isinstance(json_data, list):
        for item in json_data:
            if isinstance(item, dict):
                if item.get("data") and item["data"].get("message_snapshot"):
                    yield item["data"]
                elif item.get("message_snapshot"):
                    yield item

        if len(json_data) >= 2 and isinstance(json_data[1], list):
            for loader in json_data[1]:
                if not isinstance(loader, dict) or loader.get("key") != "shareInfo":
                    continue

                for arg in loader.get("routerDataFnArgs", []):
                    try:
                        payload = json.loads(arg)
                    except (TypeError, json.JSONDecodeError):
                        continue

                    if isinstance(payload, dict) and payload.get("data") and payload["data"].get("message_snapshot"):
                        yield payload["data"]
                    elif isinstance(payload, dict) and payload.get("message_snapshot"):
                        yield payload
    elif isinstance(json_data, dict):
        if json_data.get("data") and json_data["data"].get("message_snapshot"):
            yield json_data["data"]
        elif json_data.get("message_snapshot"):
            yield json_data


def _iter_message_blocks(message: dict):
    content_block = message.get("content_block")
    if isinstance(content_block, list) and content_block:
        yield from content_block
        return

    content = message.get("content")
    if not content:
        return

    try:
        blocks = json.loads(content)
    except (TypeError, json.JSONDecodeError):
        return

    if isinstance(blocks, list):
        yield from blocks


def _extract_images_from_messages(message_list: list[dict]):
    image_list = []
    seen_urls = set()

    for message in message_list:
        for block in _iter_message_blocks(message):
            try:
                content_v2 = _json_loads(block.get("content_v2") or block.get("content") or "{}")
            except (TypeError, json.JSONDecodeError):
                continue

            creation_block = content_v2.get("creation_block") if isinstance(content_v2, dict) else None
            if not creation_block:
                continue

            for creation in creation_block.get("creations", []):
                image = creation.get("image", {})
                image_raw = image.get("image_ori_raw")
                if not image_raw or not image_raw.get("url"):
                    continue

                image_raw = dict(image_raw)
                image_raw["url"] = image_raw["url"].replace("&amp;", "&")
                if image_raw["url"] in seen_urls:
                    continue

                seen_urls.add(image_raw["url"])
                image_list.append(image_raw)

    return image_list


def _extract_doubao_share_id(url: str) -> str:
    return url.split("?")[0].rstrip("/").rsplit("/", maxsplit=1)[-1]


async def _fetch_doubao_share_snapshot(client: httpx.AsyncClient, url: str, headers: dict):
    share_id = _extract_doubao_share_id(url)
    api = "https://www.doubao.com/samantha/thread/share/snapshot/get"
    params = {
        "aid": "497858",
        "device_platform": "web",
        "language": "zh",
        "pc_version": "3.16.3",
        "pkg_type": "release_version",
        "real_aid": "497858",
        "region": "CN",
        "samantha_web": "1",
        "sys_region": "CN",
        "use-olympus-account": "1",
        "version_code": "20800",
    }
    api_headers = {
        **headers,
        "content-type": "application/json; encoding=utf-8",
        "origin": "https://www.doubao.com",
        "referer": url,
    }
    response = await client.post(
        api,
        params=params,
        json={"share_id": share_id, "need_bot": False},
        headers=api_headers,
    )
    data = response.json()
    if data.get("code") != 0 or not data.get("data", {}).get("message_snapshot"):
        raise KeyError("无法解析页面数据，请确认链接是否有效")
    return data


async def doubao_image_parse(url: str, return_raw: bool = False):
    if "doubao.com/thread/" not in url:
        raise ValueError("链接格式不正确，请使用豆包对话链接（包含 /thread/）")

    headers = {
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            html_str = response.text
            json_data = _extract_router_data_args(html_str)
            if not json_data:
                json_data = await _fetch_doubao_share_snapshot(client, url, headers)
    except httpx.RequestError as e:
        raise ValueError(f"网络请求失败，请检查网络连接: {str(e)}")

    if not json_data:
        raise KeyError("无法解析页面数据，请确认链接是否有效")

    try:
        if return_raw:
            return json_data

        image_list = []
        for share_data in _iter_share_data(json_data):
            message_snapshot = share_data["message_snapshot"]["message_list"]
            image_list.extend(_extract_images_from_messages(message_snapshot))
    except KeyError as e:
        print(f"Exception: {e}")
        raise KeyError("页面结构发生变化，无法解析图片数据")
    except json.JSONDecodeError:
        raise ValueError("页面数据格式错误，无法解析")

    return image_list


async def qianwen_image_parse(url: str, return_raw: bool = False):
    if "qianwen.com/share/chat/" not in url:
        raise ValueError("链接格式不正确，请使用豆包对话链接（包含 qianwen.com/share/chat/）")

    headers = {
        "origin": "https://www.qianwen.com",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0",
    }

    try:
        share_id = url.split("?")[0].rsplit("chat/", maxsplit=1)[-1]
        json_data = {
            "share_id": share_id,
            "biz_id": "ai_qwen",
        }

        async with httpx.AsyncClient() as client:
            api = "https://chat2-api.qianwen.com/api/v1/share/info"
            response = await client.post(api, json=json_data, headers=headers)
            json_data = response.json()
            if return_raw:
                return json_data
    except httpx.RequestError as e:
        raise ValueError(f"网络请求失败，请检查网络连接: {str(e)}")

    try:
        image_list = []
        record_list = json_data["data"]["session"]["record_list"]
        for record in record_list:
            response_messages = record["response_messages"]
            for message in response_messages:
                if message["mime_type"] == "multi_load/iframe" and message["status"] == "complete":
                    multi_load = message["meta_data"]["multi_load"]
                    for item in multi_load:
                        display_list = item["content"]["display_list"]
                        for i in display_list:
                            image_info = i["image"][0]
                            image_list.append(image_info)
    except KeyError as e:
        print(f"Exception: {e}")
        raise KeyError("页面结构发生变化，无法解析图片数据")
    except json.JSONDecodeError:
        raise ValueError("页面数据格式错误，无法解析")

    return image_list


if __name__ == "__main__":
    import asyncio

    print(asyncio.run(doubao_image_parse("https://www.doubao.com/thread/aef4c7a4c78c2")))
    # print(asyncio.run(qianwen_image_parse("https://www.qianwen.com/share/chat/1b7641042a7c4f2fae8111f732c31f7f")))
