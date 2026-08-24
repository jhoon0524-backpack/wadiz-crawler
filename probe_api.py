"""임시 진단 스크립트 2차: 새 API 경로 탐색 (확인 후 삭제)."""
import gzip
import io
import json
import re
import urllib.request
import urllib.error

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
)
BODY = json.dumps({"order": "closing", "limit": 2, "offset": 0}).encode("utf-8")

API_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": UA,
    "Referer": "https://www.wadiz.kr/",
    "Origin": "https://www.wadiz.kr",
    "Accept-Language": "ko-KR,ko;q=0.9",
}
HTML_HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
    "Accept-Encoding": "gzip",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive",
}


def read_body(resp_or_err):
    raw = resp_or_err.read()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
    return raw


def try_req(label, url, method="GET", body=None, headers=None, show=200):
    req = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        raw = read_body(resp)
        print(f"[{label}] {resp.status} len={len(raw)}")
        print("  body:", raw[:show].decode("utf-8", "replace").replace("\n", " "))
        return raw
    except urllib.error.HTTPError as e:
        raw = read_body(e)
        print(f"[{label}] HTTPError {e.code} :: {raw[:show].decode('utf-8', 'replace')[:show]}")
    except Exception as e:
        print(f"[{label}] {type(e).__name__}: {e}")
    return None


print("=== 후보 경로 스캔 (404=없음, 그 외=존재 가능) ===")
candidates = [
    "/api/search/funding",
    "/api/search/funding/v2",
    "/api/search/v2/funding",
    "/api/search/v3/funding",
    "/api/search/fundings",
    "/api/search/funding-list",
    "/api/search/campaign",
    "/api/search/campaigns",
    "/api/search/project",
    "/api/search/projects",
    "/api/search/integrated",
    "/api/search/total",
    "/api/search/main",
    "/api/search/keyword",
    "/api/search/recommend",
    "/api/search/reward",
    "/api/search/store",
    "/api/search/comingsoon",
    "/api/search",
]
for path in candidates:
    try_req(f"POST {path}", f"https://service.wadiz.kr{path}", "POST", BODY, API_HEADERS, show=120)

print("=== 웹 페이지/번들에서 실제 경로 찾기 ===")
for page_url in [
    "https://www.wadiz.kr/robots.txt",
    "https://www.wadiz.kr/web/wreward/main",
    "https://m.wadiz.kr/web/wreward/main",
]:
    page = try_req(f"GET {page_url}", page_url, "GET", None, HTML_HEADERS, show=150)
    if page and b"<html" in page[:2000].lower():
        html = page.decode("utf-8", "replace")
        for h in sorted(set(re.findall(r"[\"'][^\"']*api/search[^\"']{0,80}", html)))[:30]:
            print("  html-hit:", h)
        scripts = re.findall(r'src="(https?://[^"]+\.js[^"]*)"', html)
        print("  scripts:", len(scripts))
        for s in scripts[:10]:
            js = try_req(f"  JS {s[-60:]}", s, "GET", None, {"User-Agent": UA, "Accept-Encoding": "gzip"}, show=0)
            if js:
                text = js.decode("utf-8", "replace")
                for m in sorted(set(re.findall(r"[\"'][^\"']*api/search[^\"']{0,80}", text)))[:30]:
                    print("   js-hit:", m[:140])
        break
