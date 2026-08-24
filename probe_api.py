"""임시 진단 4차: Save Page Now로 현재 페이지를 아카이브해 번들에서 새 API 경로 찾기 (확인 후 삭제)."""
import gzip
import io
import json
import re
import socket
import time
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
TARGET = "https://www.wadiz.kr/web/wreward/main"


def fetch(url, timeout=90):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
    resp = urllib.request.urlopen(req, timeout=timeout)
    raw = resp.read()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
    return raw


print("=== 0) 서브도메인 DNS 확인 ===")
for host in ["service.wadiz.kr", "api.wadiz.kr", "gateway.wadiz.kr", "search.wadiz.kr", "appapi.wadiz.kr", "static.wadiz.kr", "cdn.wadiz.kr"]:
    try:
        print("  ", host, "->", socket.gethostbyname(host))
    except Exception as e:
        print("  ", host, "-> 실패", e)

print("=== 1) robots.txt 전체 ===")
try:
    print(fetch("https://www.wadiz.kr/robots.txt").decode("utf-8", "replace"))
except Exception as e:
    print("robots 실패:", e)

print("=== 2) Save Page Now 요청 ===")
try:
    raw = fetch("https://web.archive.org/save/" + TARGET, timeout=120)
    print("  save 응답 길이:", len(raw))
except Exception as e:
    print("  save 요청 결과:", type(e).__name__, e)

print("  60초 대기 후 최신 스냅샷 조회...")
time.sleep(60)

snap_html = None
snap_ts = None
for attempt in range(3):
    q = ("https://web.archive.org/cdx/search/cdx?url=" + urllib.parse.quote(TARGET, safe="")
         + "&output=json&limit=3&filter=statuscode:200&sort=reverse")
    try:
        rows = json.loads(fetch(q).decode("utf-8", "replace"))
    except Exception as e:
        print("  cdx 실패:", e)
        rows = []
    for r in rows[1:]:
        print("  스냅샷:", r[1], r[2])
    fresh = [r for r in rows[1:] if r[1] >= "20260822"]
    if fresh:
        snap_ts = fresh[0][1]
        url = f"https://web.archive.org/web/{snap_ts}id_/{fresh[0][2]}"
        try:
            snap_html = fetch(url).decode("utf-8", "replace")
            print("  현재 스냅샷 확보:", url, "len", len(snap_html))
            break
        except Exception as e:
            print("  스냅샷 fetch 실패:", e)
    if attempt < 2:
        print("  30초 더 대기...")
        time.sleep(30)

if snap_html:
    print("=== 3) HTML에서 api 문자열 ===")
    for h in sorted(set(re.findall(r"[^\"'\s()<>]*api/[^\"'\s()<>]{0,90}", snap_html)))[:50]:
        print("  html:", h[:150])
    srcs = re.findall(r'(?:src|href)="([^"]+\.js[^"]*)"', snap_html)
    print("=== 4) JS", len(srcs), "개에서 api 경로 ===")
    seen = set()
    for s in srcs[:25]:
        if s.startswith("//"):
            s = "https:" + s
        elif s.startswith("/") :
            s = "https://www.wadiz.kr" + s
        # 웨이백 경유로 받기 (원본 도메인은 차단 가능)
        wb = f"https://web.archive.org/web/{snap_ts}id_/{s}"
        js = None
        for candidate in [wb, s]:
            try:
                js = fetch(candidate).decode("utf-8", "replace")
                break
            except Exception:
                continue
        if js is None:
            print("  실패:", s[-80:])
            continue
        hits = set(re.findall(r"[^\"'\s()<>]{0,70}api/[a-zA-Z][^\"'\s()<>]{0,90}", js))
        hits |= set(re.findall(r"service\.wadiz\.kr[^\"'\s()<>]{0,110}", js))
        new = {h for h in hits if "search" in h or "funding" in h or "service.wadiz" in h} - seen
        if new:
            print("  --", s[-90:])
            for m in sorted(new)[:50]:
                print("     hit:", m[:160])
            seen |= new
else:
    print("현재 스냅샷 확보 실패")
