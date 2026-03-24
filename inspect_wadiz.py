import asyncio
from playwright.async_api import async_playwright

async def inspect():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="ko-KR",
        )
        page = await context.new_page()
        await page.goto("https://www.wadiz.kr/web/wreward/category?order=closing")
        await page.wait_for_selector("a[href*='/web/campaign/detail']", timeout=15000)
        await page.wait_for_timeout(2000)

        # 오늘 마감 첫 번째 카드 HTML 구조 출력
        first = page.locator("a[href*='/web/campaign/detail']:has([class*='LabelBadge_badge']:has-text('오늘 마감'))").first
        html = await first.inner_html()
        print(html[:2000])

        await browser.close()

asyncio.run(inspect())