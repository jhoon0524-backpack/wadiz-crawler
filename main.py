import asyncio
from crawler import crawl_wadiz_closing
from sheets import upload_to_sheets

async def main():
    print("크롤링 시작...")
    data = await crawl_wadiz_closing()
    if not data:
        print("데이터 없음")
        return
    upload_to_sheets(data)

asyncio.run(main())