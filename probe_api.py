"""임시 진단 스크립트 3차: 웨이백 머신으로 와디즈 번들에서 API 경로 찾기 (확인 후 삭제)."""
import gzip
import io
import json
import re
import urllib.request
import urllib.error

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"


def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
    resp = urllib.request.urlopen(req, timeout=timeout)
    raw = resp.read()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
    return raw


def cdx(url_pattern, extra=""):
    q = (
        "https://web.archive.org/cdx/search/cdx?url=" + urllib.parse.quote(url_pattern, safe="")
        + "&output=json&limit=8&from=20260601&filter=statuscode:200&collapse=urlkey" + extra
    )
    try:
        return json.loads(fetch(q).decode("utf-8", "replace"))
    except Exception as e:
        print("cdx 실패:", url_pattern, type(e).__name__, e)
        return []


import urllib.parse

print("=== 1) 최근 스냅샷 목록 ===")
rows = cdx("www.wadiz.kr/web/wreward/main*")
for r in rows[1:]:
    print("  ", r[1], r[2])
if len(rows) < 2:
    rows = cdx("www.wadiz.kr/")
    for r in rows[1:]:
        print("  (root)", r[1], r[2])

snap = None
if len(rows) >= 2:
    ts, orig = rows[-1][1], rows[-1][2]
    snap_url = f"https://web.archive.org/web/{ts}id_/{orig}"
    print("스냅샷:", snap_url)
    try:
        snap = fetch(snap_url).decode("utf-8", "replace")
    except Exception as e:
        print("스냅샷 fetch 실패:", type(e).__name__, e)

if snap:
    print("=== 2) HTML 내 api 경로 ===")
    for h in sorted(set(re.findall(r"[^\"'\s]*api/[^\"'\s]{0,80}", snap)))[:40]:
        print("  html:", h[:140])
    scripts = re.findall(r'src="([^"]+\.js[^"]*)"', snap)
    print("=== 3) 스크립트", len(scripts), "개 ===")
    seen_hits = set()
    for s in scripts[:15]:
        if s.startswith("//"):
            s = "https:" + s
        if s.startswith("/") and not s.startswith("//"):
            s = "https://www.wadiz.kr" + s
        # 웨이백 스냅샷 경유 원본 자산
        for candidate in [s, f"https://web.archive.org/web/{rows[-1][1]}id_/{s.split('id_/')[-1]}"]:
            try:
                js = fetch(candidate).decode("utf-8", "replace")
            except Exception as e:
                print("  js 실패:", candidate[:100], type(e).__name__)
                continue
            hits = set(re.findall(r"[^\"'\s]{0,60}api/search[^\"'\s]{0,80}", js))
            hits |= set(re.findall(r"service\.wadiz\.kr[^\"'\s]{0,100}", js))
            new = hits - seen_hits
            if new:
                print("  --", candidate[:110])
                for m in sorted(new)[:40]:
                    print("     hit:", m[:150])
                seen_hits |= new
            break
