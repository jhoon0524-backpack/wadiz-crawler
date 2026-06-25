import json
import urllib.request

API_URL = "https://service.wadiz.kr/api/search/funding"
PAGE_SIZE = 100


def _fetch_page(offset):
    body = json.dumps({"order": "closing", "limit": PAGE_SIZE, "offset": offset}).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    resp = urllib.request.urlopen(req, timeout=30)
    return json.loads(resp.read().decode("utf-8"))


def crawl_wadiz_closing():
    results = []
    offset = 0

    while True:
        data = _fetch_page(offset)
        items = data.get("data", {}).get("list", [])
        if not items:
            break

        found_non_closing = False
        for item in items:
            if item.get("endYn") == 1:
                continue
            if item.get("remainingDay", -1) != 0:
                found_non_closing = True
                continue

            amount = item.get("totalBackedAmount", 0)
            if amount >= 100_000_000:
                display = f"{amount / 100_000_000:.1f}억 원+"
            elif amount >= 10_000:
                display = f"{amount // 10_000}만 원+"
            else:
                display = f"{amount}원"

            results.append({
                "title": item.get("title", "").strip(),
                "url": f"https://www.wadiz.kr/web/campaign/detail/{item['campaignId']}",
                "category": item.get("categoryName", ""),
                "maker": item.get("nickName", ""),
                "funding_amount": display,
                "achievement_rate": f"{item.get('achievementRate', 0)}% 달성",
            })

        if found_non_closing:
            break
        offset += PAGE_SIZE

    print(f"오늘 마감 프로젝트: {len(results)}건")
    return results


if __name__ == "__main__":
    data = crawl_wadiz_closing()
    print(json.dumps(data, ensure_ascii=False, indent=2))
