"""임시 진단 5차: gateway 호스트와 경로 매핑 가설 확인 (확인 후 삭제)."""
import gzip
import io
import json
import urllib.request
import urllib.error

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
BODY = json.dumps({"order": "closing", "limit": 2, "offset": 0}).encode("utf-8")
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": UA,
    "Referer": "https://www.wadiz.kr/",
    "Origin": "https://www.wadiz.kr",
    "Accept-Language": "ko-KR,ko;q=0.9",
}


def try_req(label, url, method="POST", body=BODY):
    req = urllib.request.Request(url, data=body if method == "POST" else None, headers=HEADERS, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        raw = resp.read()
        if raw[:2] == b"\x1f\x8b":
            raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
        print(f"[{label}] {resp.status} len={len(raw)} server={resp.headers.get('server')}")
        print("  body:", raw[:400].decode("utf-8", "replace").replace("\n", " "))
    except urllib.error.HTTPError as e:
        raw = e.read()
        print(f"[{label}] {e.code} server={e.headers.get('server')} :: {raw[:200].decode('utf-8', 'replace')}")
    except Exception as e:
        print(f"[{label}] {type(e).__name__}: {e}")


tests = [
    ("service 이중접두(핵심 가설)", "POST", "https://service.wadiz.kr/api/search/api/search/funding"),
    ("service 기존(대조군)", "POST", "https://service.wadiz.kr/api/search/funding"),
    ("gateway /api/search/funding", "POST", "https://gateway.wadiz.kr/api/search/funding"),
    ("gateway /search/funding", "POST", "https://gateway.wadiz.kr/search/funding"),
    ("gateway /funding", "POST", "https://gateway.wadiz.kr/funding"),
    ("gateway 루트", "GET", "https://gateway.wadiz.kr/"),
    ("service /api/search/search/funding", "POST", "https://service.wadiz.kr/api/search/search/funding"),
    ("service /api/search/v1/funding", "POST", "https://service.wadiz.kr/api/search/v1/funding"),
    ("service 루트", "GET", "https://service.wadiz.kr/"),
]
for label, method, url in tests:
    try_req(label, url, method)
