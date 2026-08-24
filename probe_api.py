"""임시 진단 스크립트: 와디즈 API 404 원인 확인용 (확인 후 삭제)."""
import json
import re
import urllib.request
import urllib.error

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
)
API_URL = "https://service.wadiz.kr/api/search/funding"
BODY = json.dumps({"order": "closing", "limit": 2, "offset": 0}).encode("utf-8")


def try_req(label, url, method="GET", body=None, headers=None):
    req = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        raw = resp.read()
        print(f"[{label}] {resp.status} len={len(raw)}")
        print("  body:", raw[:300].decode("utf-8", "replace").replace("\n", " "))
        return raw
    except urllib.error.HTTPError as e:
        raw = e.read()
        print(f"[{label}] HTTPError {e.code}")
        print("  headers:", dict(e.headers))
        print("  body:", raw[:300].decode("utf-8", "replace").replace("\n", " "))
    except Exception as e:
        print(f"[{label}] {type(e).__name__}: {e}")
    return None


json_headers = {"Content-Type": "application/json", "Accept": "application/json"}
browser_headers = {
    **json_headers,
    "User-Agent": UA,
    "Referer": "https://www.wadiz.kr/",
    "Origin": "https://www.wadiz.kr",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

try_req("1. 기존 그대로 (POST, 기본 UA)", API_URL, "POST", BODY, json_headers)
try_req("2. POST + 브라우저 헤더", API_URL, "POST", BODY, browser_headers)
try_req("3. GET + 브라우저 헤더", API_URL, "GET", None, browser_headers)

# 웹 페이지에서 현재 API 경로 탐색
page = try_req(
    "4. 펀딩 목록 페이지",
    "https://www.wadiz.kr/web/wreward/main?order=closing",
    "GET",
    None,
    {"User-Agent": UA, "Accept": "text/html", "Accept-Language": "ko-KR,ko;q=0.9"},
)
if page:
    html = page.decode("utf-8", "replace")
    hits = set(re.findall(r"[\"'][^\"']*api/[^\"']{0,80}", html))
    print("HTML 내 api 경로 후보:")
    for h in sorted(hits)[:40]:
        print("  ", h)
    scripts = re.findall(r'src="(https?://[^"]+\.js[^"]*)"', html)[:8]
    for s in scripts:
        js = try_req(f"JS {s[:80]}", s, "GET", None, {"User-Agent": UA})
        if js:
            text = js.decode("utf-8", "replace")
            for m in set(re.findall(r"[\"'][^\"']*(?:search|ajax)[^\"']{0,60}", text)):
                if "api" in m or "search" in m:
                    print("   js-hit:", m[:120])
