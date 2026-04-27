# TODO：
1. 更新最新代码✅
2. 部署到worker-验证接口✅
3. 更新域名
4. 小程序验证更新

```bash
curl -X POST "https://doubao-nomark.wenhaofree.workers.dev/parse-video" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.doubao.com/video-sharing?share_id=38779230228040962&video_id=v0369cg10004d69dh7fog65md3ncqvg0","return_raw":false}'


curl -X POST "https://doubao-nomark.wenhaofree.workers.dev/parse" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.doubao.com/thread/wb02b5cfd1e252028","return_raw":false}'
```