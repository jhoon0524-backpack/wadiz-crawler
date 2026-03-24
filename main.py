import asyncio
import os
import urllib.request
import json
from crawler import crawl_wadiz_closing
from sheets import upload_to_sheets

def notify_slack(count):
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return
    message = {"text": f"✅ 와디즈 오늘 마감 프로젝트 {count}건이 구글 시트에 업데이트됐습니다."}
    data = json.dumps(message).encode("utf-8")
    req = urllib.request.Request(webhook_url, data=data, headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req)

async def main():
    print("크롤링 시작...")
    data = await crawl_wadiz_closing()
    if not data:
        print("데이터 없음")
        return
    upload_to_sheets(data)
    notify_slack(len(data))

asyncio.run(main())