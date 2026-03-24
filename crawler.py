import asyncio
import json
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

async def crawl_wadiz_closing():
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="ko-KR",
        )
        page = await context.new_page()
        await stealth_async(page)  # ← 이 한 줄 추가
        await page.goto("https://www.wadiz.kr/web/wreward/category?order=closing")
        await page.wait_for_selector("a[href*='/web/campaign/detail']", timeout=15000)

        for _ in range(10):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1500)

        cards = page.locator("a[href*='/web/campaign/detail']:has([class*='LabelBadge_badge']:has-text('오늘 마감'))")
        count = await cards.count()
        print(f"오늘 마감 카드 수: {count}")

        seen_urls = set()

        for i in range(count):
            try:
                card = cards.nth(i)

                href = await card.get_attribute("href")
                if not href:
                    continue
                base_url = href.split("?")[0]
                if base_url in seen_urls:
                    continue
                seen_urls.add(base_url)
                url = f"https://www.wadiz.kr{base_url}"

                title_el = card.locator("div[class^='Title_container']")
                title = await title_el.first.inner_text() if await title_el.count() > 0 else ""

                rate_el = card.locator("[class*='KeyTitle_container']")
                rate = await rate_el.first.inner_text() if await rate_el.count() > 0 else ""

                amount_el = card.locator("[class*='LabelBadge_gray']")
                amount = await amount_el.first.inner_text() if await amount_el.count() > 0 else ""

                results.append({
                    "title": title.strip().replace("\n", " "),
                    "url": url,
                    "category": "",
                    "funding_amount": amount.strip(),
                    "achievement_rate": rate.strip(),
                })

            except Exception:
                continue

        await browser.close()

    print(f"오늘 마감 프로젝트: {len(results)}건")
    return results

if __name__ == "__main__":
    data = asyncio.run(crawl_wadiz_closing())
    print(json.dumps(data, ensure_ascii=False, indent=2))